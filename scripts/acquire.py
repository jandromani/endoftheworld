#!/usr/bin/env python3
"""ENDWORLD profile acquisition engine.

Resolves Internet sources while online, downloads into an isolated vault,
captures provenance + SHA-256, and produces a frozen lock file. Downloaded
artifacts are never executed by this script.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "profiles" / "nano.yml"
UA = "ENDWORLD/0.1 (+https://github.com/jandromani/endoftheworld)"


class BuildError(RuntimeError):
    pass


def req(url: str, method: str = "GET", headers: dict | None = None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        h["Authorization"] = f"Bearer {token}"
        h["Accept"] = "application/vnd.github+json"
        h["X-GitHub-Api-Version"] = "2022-11-28"
    return urllib.request.Request(url, method=method, headers=h)


def urlopen_retry(request, timeout: int = 45, attempts: int | None = None):
    """Open an HTTP request with bounded retries for transient upstream failures."""
    tries = attempts or int(os.environ.get("ENDWORLD_HTTP_ATTEMPTS", "4"))
    last = None
    for attempt in range(1, max(1, tries) + 1):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        if attempt < tries:
            time.sleep(min(8.0, 1.5 * (2 ** (attempt - 1))))
    assert last is not None
    raise last


def get_json(url: str) -> dict:
    with urlopen_retry(req(url), timeout=45) as r:
        return json.load(r)


def get_text(url: str) -> str:
    with urlopen_retry(req(url), timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def response_size(response) -> int | None:
    content_range = response.headers.get("Content-Range", "")
    m = re.search(r"/(\d+)$", content_range)
    if m:
        return int(m.group(1))
    length = response.headers.get("Content-Length")
    if length and length.isdigit():
        return int(length)
    return None


def resolve_final_url(url: str) -> tuple[str, int | None]:
    # Prefer HEAD: modern mirrors increasingly implement "latest" as a
    # redirect. Both HEAD and the one-byte GET are retried because large public
    # mirrors can transiently return 502/503/504 or time out under load.
    head_final = None
    try:
        with urlopen_retry(req(url, method="HEAD"), timeout=45) as r:
            head_final = r.geturl()
            size = response_size(r)
            if size is not None:
                return head_final, size
    except Exception:
        pass

    probe_url = head_final or url
    request = req(probe_url, headers={"Range": "bytes=0-0"})
    with urlopen_retry(request, timeout=45) as r:
        return r.geturl(), response_size(r)


def latest_from_index(index_url: str, href_regex: str) -> tuple[str, str]:
    html = get_text(index_url)
    rx = re.compile(href_regex)
    found = []
    # Directory indexes can use quoted hrefs or just visible filenames.
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I):
        name = urllib.parse.unquote(href.rsplit("/", 1)[-1])
        if rx.fullmatch(name):
            found.append((name, urllib.parse.urljoin(index_url, href)))
    if not found:
        for name in set(rx.findall(html)):
            if isinstance(name, tuple):
                continue
            if rx.fullmatch(name):
                found.append((name, urllib.parse.urljoin(index_url, name)))
    if not found:
        # Final generic scan: regex itself may match the filename in visible text.
        matches = sorted(set(re.findall(href_regex, html)))
        for name in matches:
            if isinstance(name, tuple):
                continue
            found.append((name, urllib.parse.urljoin(index_url, name)))
    if not found:
        raise BuildError(f"No artifact matched {href_regex!r} at {index_url}")
    found.sort(key=lambda x: x[0])
    return found[-1]


def github_latest_release(repo: str) -> dict | None:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        return get_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def resolve_artifact(spec: dict) -> dict:
    kind = spec["kind"]
    out = {
        "id": spec["id"],
        "family": spec.get("family"),
        "kind": kind,
        "required": bool(spec.get("required", False)),
        "destination": spec.get("destination", "misc"),
        "budget_bytes": spec.get("budget_bytes"),
    }

    if kind == "url":
        url = spec["url"]
        final, size = resolve_final_url(url)
        out.update(
            url=url,
            resolved_url=final,
            filename=spec.get("filename") or pathlib.PurePosixPath(urllib.parse.urlparse(final).path).name,
            expected_bytes=size,
            checksum_url=spec.get("checksum_url"),
        )
        return out

    if kind == "index_latest":
        name, url = latest_from_index(spec["index_url"], spec["href_regex"])
        final, size = resolve_final_url(url)
        out.update(
            url=url,
            resolved_url=final,
            filename=name,
            expected_bytes=size,
            index_url=spec["index_url"],
            href_regex=spec["href_regex"],
        )
        return out

    if kind == "github_release_asset":
        rel = github_latest_release(spec["repo"])
        if not rel:
            raise BuildError(f"{spec['repo']} has no GitHub latest release")
        rx = re.compile(spec["asset_regex"], re.I)
        assets = [a for a in rel.get("assets", []) if rx.fullmatch(a.get("name", ""))]
        if not assets:
            raise BuildError(
                f"No release asset matching {spec['asset_regex']!r} in {spec['repo']} {rel.get('tag_name')}"
            )
        def rank(a):
            n = a.get("name", "").lower()
            preferred = int(any(k in n for k in ("universal", "full", "foss")))
            return (preferred, int(a.get("size") or 0), n)
        asset = sorted(assets, key=rank)[-1]
        checksum_url = None
        checksum_rx = spec.get("checksum_asset_regex")
        if checksum_rx:
            crx = re.compile(checksum_rx, re.I)
            checksum_assets = [a for a in rel.get("assets", []) if crx.fullmatch(a.get("name", ""))]
            if checksum_assets:
                checksum_url = sorted(checksum_assets, key=lambda a: a.get("name", ""))[0]["browser_download_url"]
        out.update(
            repo=spec["repo"],
            release_tag=rel.get("tag_name"),
            release_url=rel.get("html_url"),
            url=asset["browser_download_url"],
            resolved_url=asset["browser_download_url"],
            filename=asset["name"],
            expected_bytes=int(asset.get("size") or 0) or None,
            checksum_url=checksum_url,
        )
        return out

    if kind == "github_snapshot":
        repo = spec["repo"]
        ref = spec.get("ref")
        release_url = None
        if not ref or ref == "default":
            info = get_json(f"https://api.github.com/repos/{repo}")
            ref = info["default_branch"]
        elif ref == "latest-release":
            rel = github_latest_release(repo)
            if rel:
                ref = rel["tag_name"]
                release_url = rel.get("html_url")
            else:
                info = get_json(f"https://api.github.com/repos/{repo}")
                ref = info["default_branch"]
        safe_ref = re.sub(r"[^A-Za-z0-9._-]+", "-", ref)
        url = f"https://api.github.com/repos/{repo}/tarball/{urllib.parse.quote(ref, safe='')}"
        final, size = resolve_final_url(url)
        out.update(
            repo=repo,
            ref=ref,
            release_url=release_url,
            url=url,
            resolved_url=final,
            filename=f"{spec['id']}-{safe_ref}.tar.gz",
            expected_bytes=size,
        )
        return out

    raise BuildError(f"Unsupported artifact kind: {kind}")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def upstream_sha256(url: str | None, filename: str) -> str | None:
    if not url:
        return None
    text = get_text(url)
    hashes = []
    for line in text.splitlines():
        m = re.search(r"(?i)\b([0-9a-f]{64})\b", line)
        if not m:
            continue
        hashes.append(m.group(1).lower())
        if filename in line:
            return m.group(1).lower()
    unique = sorted(set(hashes))
    if len(unique) == 1:
        return unique[0]
    raise BuildError(f"Could not unambiguously resolve upstream SHA-256 for {filename} from {url}")


def finalize_download(resolved: dict, dest: pathlib.Path, vault: pathlib.Path, status: str) -> dict:
    digest = sha256_file(dest)
    expected = upstream_sha256(resolved.get("checksum_url"), resolved["filename"])
    if expected and digest.lower() != expected.lower():
        rejected = dest.with_suffix(dest.suffix + ".rejected")
        os.replace(dest, rejected)
        raise BuildError(
            f"Upstream SHA-256 mismatch for {resolved['id']}: "
            f"expected {expected}, got {digest}; moved to {rejected}"
        )
    return {
        **resolved,
        "path": str(dest.relative_to(vault)),
        "bytes": dest.stat().st_size,
        "sha256": digest,
        "upstream_sha256": expected,
        "upstream_checksum_verified": bool(expected),
        "status": status,
    }


def download(resolved: dict, vault: pathlib.Path) -> dict:
    dest_dir = vault / resolved["destination"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / resolved["filename"]
    part = dest.with_suffix(dest.suffix + ".part")

    if dest.exists():
        return finalize_download(resolved, dest, vault, "present")

    start = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={start}-"} if start else {}
    source_url = resolved.get("resolved_url") or resolved["url"]
    request = req(source_url, headers=headers)

    try:
        response = urllib.request.urlopen(request, timeout=90)
    except Exception:
        # Some servers reject range requests. Retry from zero.
        if start:
            part.unlink(missing_ok=True)
            start = 0
            response = urllib.request.urlopen(req(source_url), timeout=90)
        else:
            raise

    status = getattr(response, "status", 200)
    if start and status != 206:
        response.close()
        part.unlink(missing_ok=True)
        start = 0
        response = urllib.request.urlopen(req(source_url), timeout=90)

    mode = "ab" if start else "wb"
    written = start
    last_print = time.monotonic()
    with response, part.open(mode) as f:
        while True:
            chunk = response.read(4 * 1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            written += len(chunk)
            if time.monotonic() - last_print > 3:
                print(f"  {resolved['id']}: {written / 1e9:.2f} GB", flush=True)
                last_print = time.monotonic()

    os.replace(part, dest)
    resolved = {
        **resolved,
        "resolved_url": response.geturl() if hasattr(response, "geturl") else resolved.get("resolved_url"),
    }
    return finalize_download(resolved, dest, vault, "downloaded")


def acquire_container(spec: dict, vault: pathlib.Path, dry_run: bool) -> dict:
    image = spec["image"]
    record = {"id": spec["id"], "image": image, "required": bool(spec.get("required", False))}
    if dry_run:
        record["status"] = "planned"
        return record
    if not shutil.which("docker"):
        raise BuildError("Docker is required to freeze container images")
    subprocess.run(["docker", "pull", image], check=True)
    inspect = subprocess.check_output(
        ["docker", "image", "inspect", image, "--format", "{{json .RepoDigests}}"],
        text=True,
    ).strip()
    digests = json.loads(inspect) if inspect else []
    out_dir = vault / "containers"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{spec['id']}.tar"
    subprocess.run(["docker", "save", "-o", str(out), image], check=True)
    return {
        **record,
        "repo_digests": digests,
        "path": str(out.relative_to(vault)),
        "bytes": out.stat().st_size,
        "sha256": sha256_file(out),
        "status": "frozen",
    }


def load_profile(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data.get("schema") != 1:
        raise BuildError("Unsupported profile schema")
    return data


def human(n: int | None) -> str:
    if n is None:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1000 or u == units[-1]:
            return f"{x:.2f} {u}"
        x /= 1000
    return str(n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["plan", "acquire"])
    ap.add_argument("--profile", default=str(DEFAULT_PROFILE))
    ap.add_argument("--vault")
    args = ap.parse_args()

    profile_path = pathlib.Path(args.profile).resolve()
    vault = pathlib.Path(args.vault).resolve()
    profile = load_profile(profile_path)
    pmeta = profile["profile"]
    target = int(pmeta["target_bytes"])
    reserve = int(pmeta.get("reserve_bytes", 0))
    usable = target - reserve
    acquisition_headroom = int(pmeta.get("acquisition_headroom_bytes", 0))
    artifact_limit = usable - acquisition_headroom
    if artifact_limit <= 0:
        raise BuildError("Profile acquisition headroom leaves no artifact budget")

    print(f"{pmeta['title']} — target {human(target)}, usable {human(usable)}")
    print(f"Artifact acquisition ceiling: {human(artifact_limit)}; "
          f"reserved for containers/derived outputs: {human(acquisition_headroom)}")
    print("Resolving sources...")

    candidates = []
    failures = []
    for spec in profile.get("artifacts", []):
        try:
            item = resolve_artifact(spec)
            size = item.get("expected_bytes")
            budget = spec.get("budget_bytes")
            if size and budget and size > int(budget):
                msg = f"{spec['id']} resolved to {human(size)}, above item budget {human(int(budget))}"
                if spec.get("required"):
                    raise BuildError(msg)
                print(f"SKIP optional: {msg}")
                continue
            planning_bytes = int(size if size is not None else (budget or 0))
            if planning_bytes <= 0 and not spec.get("required"):
                print(f"SKIP optional: {spec['id']} has unknown size and no budget")
                continue
            candidates.append((item, planning_bytes))
            shown = size if size is not None else planning_bytes
            suffix = "" if size is not None else " budget-reserved"
            print(f"  OK {item['id']:<28} {human(shown):>12}{suffix}  {item['filename']}")
        except Exception as exc:
            failures.append({"id": spec["id"], "required": bool(spec.get("required")), "error": str(exc)})
            print(f"  FAIL {spec['id']}: {exc}")

    required_failures = [f for f in failures if f["required"]]
    required_estimate = sum(plan for item, plan in candidates if item["required"])
    if required_estimate > artifact_limit:
        raise BuildError(
            f"Required artifact envelope {human(required_estimate)} exceeds acquisition ceiling {human(artifact_limit)}"
        )

    # Optionals are selected only after reserving space for every required
    # artifact, including the declared budget for required sources whose
    # remote size is unknown. This makes selection independent of manifest
    # ordering and prevents an early optional from crowding out a later
    # required capability.
    resolved = []
    estimated = required_estimate
    for item, planning_bytes in candidates:
        if item["required"]:
            resolved.append(item)
            continue
        if estimated + planning_bytes > artifact_limit:
            print(f"SKIP optional: {item['id']} would exceed profile acquisition ceiling")
            continue
        resolved.append(item)
        estimated += planning_bytes

    print(f"Planned artifact envelope: {human(estimated)} before container images/derived artifacts.")

    if args.command == "plan":
        if required_failures:
            print(f"PLAN FAILED: {len(required_failures)} required source(s) unresolved.")
            return 2
        print("PLAN OK. Nothing downloaded.")
        return 0

    if required_failures:
        raise BuildError(f"Refusing acquisition: {len(required_failures)} required source(s) unresolved")

    vault.mkdir(parents=True, exist_ok=True)
    records = []
    current = 0
    for item in resolved:
        size = item.get("expected_bytes")
        if size and current + size > artifact_limit and not item["required"]:
            print(f"SKIP optional at acquire time: {item['id']}")
            continue
        print(f"Acquiring {item['id']}...")
        rec = download(item, vault)
        records.append(rec)
        current += int(rec["bytes"])
        if current > artifact_limit:
            raise BuildError(
                f"Profile artifacts exceeded acquisition ceiling after {item['id']}: "
                f"{human(current)} > {human(artifact_limit)}"
            )

    containers = []
    for spec in profile.get("containers", []):
        print(f"Freezing container {spec['id']}...")
        try:
            rec = acquire_container(spec, vault, dry_run=False)
            if current + int(rec.get("bytes") or 0) > usable and not spec.get("required"):
                pathlib.Path(vault / rec["path"]).unlink(missing_ok=True)
                print(f"SKIP optional container {spec['id']}: budget")
                continue
            containers.append(rec)
            current += int(rec.get("bytes") or 0)
        except Exception as exc:
            if spec.get("required"):
                raise
            print(f"SKIP optional container {spec['id']}: {exc}")

    if current > usable:
        raise BuildError(f"Profile payload {human(current)} exceeds usable budget {human(usable)}")

    lock_dir = vault / "lock"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = {
        "schema": 1,
        "profile": pmeta["id"],
        "title": pmeta["title"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "profile_source": str(profile_path),
        "target_bytes": target,
        "reserve_bytes": reserve,
        "payload_bytes": current,
        "artifacts": records,
        "containers": containers,
        "failures": failures,
    }
    lock_path = lock_dir / f"{pmeta['id']}.lock.json"
    tmp = lock_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, lock_path)
    print(f"LOCKED: {lock_path}")
    print(f"Payload: {human(current)}; reserved free space: at least {human(target-current)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted; partial downloads are resumable.", file=sys.stderr)
        raise SystemExit(130)
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
