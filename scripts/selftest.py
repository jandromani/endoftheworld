#!/usr/bin/env python3
"""Deterministic source/vault self-test for ENDWORLD profiles.

This test performs no network access and downloads nothing. It checks the
profile contract, path safety, NANO operator wiring, portal routing helpers and
(when supplied) the frozen lock envelope.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


class SelfTestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def safe_rel(value: str, label: str) -> pathlib.PurePosixPath:
    p = pathlib.PurePosixPath(value)
    require(bool(value), f"{label} is empty")
    require(not p.is_absolute(), f"{label} must be relative: {value}")
    require(".." not in p.parts, f"{label} contains traversal: {value}")
    return p


def load_server():
    path = ROOT / "runtime" / "server.py"
    spec = importlib.util.spec_from_file_location("endworld_runtime_server", path)
    require(spec is not None and spec.loader is not None, "cannot import runtime/server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_profile(profile_path: pathlib.Path) -> dict:
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "profile must be a mapping")
    require(data.get("schema") == 1, "unsupported profile schema")
    meta = data.get("profile") or {}
    pid = str(meta.get("id") or "")
    require(pid, "profile.id missing")
    target = int(meta.get("target_bytes") or 0)
    reserve = int(meta.get("reserve_bytes") or 0)
    headroom = int(meta.get("acquisition_headroom_bytes") or 0)
    require(target > 0, "target_bytes must be positive")
    require(0 <= reserve < target, "reserve_bytes must fit target")
    require(0 <= headroom < target - reserve, "acquisition headroom must fit usable payload")
    ceiling = target - reserve - headroom

    ids: set[str] = set()
    artifacts = data.get("artifacts") or []
    require(isinstance(artifacts, list) and artifacts, "profile has no artifacts")
    kind_fields = {
        "url": ("url",),
        "index_latest": ("index_url", "href_regex"),
        "github_release_asset": ("repo", "asset_regex"),
        "github_snapshot": ("repo",),
    }
    for i, rec in enumerate(artifacts):
        require(isinstance(rec, dict), f"artifact #{i} must be a mapping")
        rid = str(rec.get("id") or "")
        require(rid and rid not in ids, f"duplicate or missing artifact id: {rid!r}")
        ids.add(rid)
        kind = str(rec.get("kind") or "")
        require(kind in kind_fields, f"{rid}: unsupported artifact kind {kind!r}")
        for field in kind_fields[kind]:
            require(bool(rec.get(field)), f"{rid}: missing {field}")
        safe_rel(str(rec.get("destination") or "misc"), f"{rid}.destination")
        budget = int(rec.get("budget_bytes") or 0)
        require(budget > 0, f"{rid}: budget_bytes must be positive")
        require(budget <= target - reserve, f"{rid}: item budget exceeds usable profile")

    containers = data.get("containers") or []
    for rec in containers:
        rid = str(rec.get("id") or "")
        require(rid and rid not in ids, f"duplicate or missing component id: {rid!r}")
        ids.add(rid)
        image = str(rec.get("image") or "")
        require("/" in image and ":" in image, f"{rid}: container image must include repository and tag")

    for rel in (
        "runtime/server.py",
        "runtime/start-stack.sh",
        "runtime/portal/index.html",
        "scripts/acquire.py",
        "scripts/verify_vault.py",
        "scripts/build_disk_image.sh",
    ):
        require((ROOT / rel).is_file(), f"missing wired runtime file: {rel}")

    if pid == "nano":
        expected = {
            "wikipedia-es", "wikipedia-medicine-es", "qwen3-4b-q4", "whisper-small",
            "spain-osm", "bitchat-android", "meshtastic-android", "reticulum-source",
            "project-nomad-source", "planetiler", "maplibre-js", "maplibre-css", "pmtiles-js",
            "kiwix", "llama-server", "whisper-server",
        }
        require(expected.issubset(ids), f"NANO wiring missing ids: {sorted(expected - ids)}")
        require(target == 64_000_000_000, "NANO target must stay exactly 64,000,000,000 bytes")
        require(ceiling > 0, "NANO acquisition ceiling invalid")

    return {"id": pid, "target": target, "reserve": reserve, "headroom": headroom, "ceiling": ceiling}


def validate_runtime(profile: dict) -> None:
    server = load_server()
    base = pathlib.Path("/tmp/endworld-selftest-root")
    require(server.safe_join(base, "ok/file.bin") == (base / "ok/file.bin").resolve(), "safe_join rejected safe path")
    require(server.safe_join(base, "../escape") is None, "safe_join allowed parent traversal")
    require(server.safe_join(base, "%2e%2e/escape") is None, "safe_join allowed encoded traversal")

    if profile["id"] != "nano":
        return

    samples = {
        "wikipedia-es": ("knowledge/zim/wiki.zim", "service"),
        "qwen3-4b-q4": ("ai/models/model.gguf", "anchor"),
        "whisper-small": ("ai/models/whisper.bin", "anchor"),
        "bitchat-android": ("apps/android/bitchat.apk", "link"),
        "meshtastic-firmware": ("firmware/meshtastic/fw.zip", "link"),
        "reticulum-source": ("source/comms/reticulum.tar.gz", "link"),
        "project-nomad-source": ("source/core/nomad.tar.gz", "link"),
    }
    for rid, (path, action_kind) in samples.items():
        f = base / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")
        rec = {"id": rid, "family": "test", "path": path, "required": True, "bytes": 1}
        item = server.describe_capability(rec, base, reticulum_available=False)
        require(item.get("action") and item["action"].get("kind") == action_kind,
                f"{rid}: no operator action wired")

    builder = (ROOT / "scripts" / "build_disk_image.sh").read_text(encoding="utf-8")
    require("exec python3 /opt/endworld/scripts/endworld.py" in builder,
            "appliance endworld CLI wrapper is not installed")


def validate_vault(vault: pathlib.Path, profile: dict) -> dict:
    lock_path = vault / "lock" / f"{profile['id']}.lock.json"
    require(lock_path.is_file(), f"vault lock missing: {lock_path}")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    require(lock.get("profile") == profile["id"], "lock profile mismatch")
    require(int(lock.get("target_bytes") or 0) == profile["target"], "lock target mismatch")
    require(int(lock.get("reserve_bytes") or 0) == profile["reserve"], "lock reserve mismatch")
    for group in ("artifacts", "containers"):
        for rec in lock.get(group, []):
            rel = rec.get("path")
            if rel:
                safe_rel(str(rel), f"lock {rec.get('id')}.path")
    payload = int(lock.get("payload_bytes") or 0)
    usable = profile["target"] - profile["reserve"]
    require(payload <= usable, f"locked payload {payload} exceeds usable envelope {usable}")
    return {"lock": str(lock_path), "payload_bytes": payload, "prepared": bool(lock.get("prepared"))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=str(ROOT / "profiles" / "nano.yml"))
    ap.add_argument("--vault")
    args = ap.parse_args()
    try:
        profile = validate_profile(pathlib.Path(args.profile).resolve())
        validate_runtime(profile)
        result = {
            "profile": profile["id"],
            "source": "OK",
            "target_bytes": profile["target"],
            "acquisition_ceiling_bytes": profile["ceiling"],
        }
        if args.vault:
            result["vault"] = validate_vault(pathlib.Path(args.vault).resolve(), profile)
        print(json.dumps(result, indent=2))
        return 0
    except (SelfTestError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SELFTEST FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
