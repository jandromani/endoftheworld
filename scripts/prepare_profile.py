#!/usr/bin/env python3
"""Prepare profile-defined derived ENDWORLD artifacts.

Profiles may declare prepare.maps entries. Each map is generated with the
frozen Planetiler artifact from a frozen OSM PBF source and inserted into the
same immutable lock. The script is profile-generic and preserves the budget
contract after derivation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PrepareError(RuntimeError):
    pass


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def human(n: int) -> str:
    return f"{n / 1_000_000_000:.2f} GB"


def find_artifact(lock: dict, artifact_id: str) -> dict:
    for item in lock.get("artifacts", []):
        if item.get("id") == artifact_id:
            return item
    raise PrepareError(f"Required locked artifact not found: {artifact_id}")


def upsert_artifact(lock: dict, record: dict) -> None:
    items = lock.setdefault("artifacts", [])
    for i, item in enumerate(items):
        if item.get("id") == record["id"]:
            items[i] = record
            return
    items.append(record)


def build_map(vault: pathlib.Path, lock: dict, spec: dict, java_memory: str) -> None:
    source_id = str(spec["source_artifact"])
    derived_id = str(spec["id"])
    filename = str(spec.get("filename") or f"{derived_id}.pmtiles")
    osm_rec = find_artifact(lock, source_id)
    tool_rec = find_artifact(lock, "planetiler")
    osm = vault / osm_rec["path"]
    jar = vault / tool_rec["path"]
    output_dir = vault / "maps" / "tiles"
    output_dir.mkdir(parents=True, exist_ok=True)
    pmtiles = output_dir / filename

    if not pmtiles.exists():
        if not shutil.which("java"):
            raise PrepareError("Java 21+ is required to build offline maps")
        free = shutil.disk_usage(os.getenv("ENDWORLD_BUILD_TMP", str(vault.parent))).free
        recommended = max(8_000_000_000, osm.stat().st_size * 5)
        if free < recommended:
            raise PrepareError(
                f"{derived_id}: temporary map space {human(free)}; "
                f"recommend at least {human(recommended)}"
            )
        temp_parent = os.getenv("ENDWORLD_BUILD_TMP")
        with tempfile.TemporaryDirectory(prefix=f"endworld-{derived_id}-", dir=temp_parent) as td:
            cmd = [
                "java", f"-Xmx{java_memory}", "-XX:MaxHeapFreeRatio=40",
                "-jar", str(jar), "--osm-path", str(osm), "--output", str(pmtiles),
                "--download", "--force", "--storage", "mmap", "--building-merge-z13=false",
            ]
            print(f"Building {derived_id} with Planetiler...")
            print(" ".join(cmd))
            subprocess.run(cmd, cwd=td, check=True)

    upsert_artifact(lock, {
        "id": derived_id,
        "family": "maps",
        "kind": "derived",
        "required": True,
        "source_artifact": source_id,
        "builder_artifact": "planetiler",
        "filename": pmtiles.name,
        "path": str(pmtiles.relative_to(vault)),
        "bytes": pmtiles.stat().st_size,
        "sha256": sha256_file(pmtiles),
        "status": "derived",
    })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--java-memory", default=os.getenv("ENDWORLD_PLANETILER_MEMORY", "6g"))
    ap.add_argument("--skip-maps", action="store_true")
    args = ap.parse_args()

    profile_path = pathlib.Path(args.profile).resolve()
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    pid = str(profile["profile"]["id"])
    vault = pathlib.Path(args.vault).resolve()
    lock_path = vault / "lock" / f"{pid}.lock.json"
    if not lock_path.exists():
        raise PrepareError(f"Acquire {pid} first; {lock_path.name} is missing")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("profile") != pid:
        raise PrepareError(f"Lock/profile mismatch: {lock.get('profile')} != {pid}")

    if not args.skip_maps:
        for spec in (profile.get("prepare") or {}).get("maps", []):
            build_map(vault, lock, spec, args.java_memory)

    target = int(lock["target_bytes"])
    reserve = int(lock["reserve_bytes"])
    usable = target - reserve
    total = 0
    for group in ("artifacts", "containers"):
        for rec in lock.get(group, []):
            rel = rec.get("path")
            if not rel:
                continue
            path = vault / rel
            if path.exists():
                total += path.stat().st_size
    if total > usable:
        raise PrepareError(f"Prepared {pid} payload {human(total)} exceeds usable budget {human(usable)}")

    lock["payload_bytes"] = total
    lock["prepared"] = True
    lock["derived_count"] = sum(1 for x in lock.get("artifacts", []) if x.get("kind") == "derived")
    tmp = lock_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, lock_path)
    print(f"{pid.upper()} prepared: {human(total)} / {human(usable)} usable")
    print(f"Lock updated: {lock_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PrepareError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
