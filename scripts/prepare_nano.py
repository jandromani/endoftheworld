#!/usr/bin/env python3
"""Prepare derived ENDWORLD NANO artifacts after acquisition.

Currently:
- Converts Spain OSM PBF into a static PMTiles vector archive.
- Adds the derived artifact to the frozen lock with SHA-256.
- Enforces the NANO payload budget after derivation.

This phase is intentionally online-capable because Planetiler may download
Natural Earth/water-polygon build inputs. The resulting runtime artifact is
fully offline.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=str(ROOT / "vault" / "nano"))
    ap.add_argument("--java-memory", default=os.getenv("ENDWORLD_PLANETILER_MEMORY", "4g"))
    ap.add_argument("--skip-map", action="store_true")
    args = ap.parse_args()

    vault = pathlib.Path(args.vault).resolve()
    lock_path = vault / "lock" / "nano.lock.json"
    if not lock_path.exists():
        raise PrepareError("Acquire NANO first; nano.lock.json is missing")

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    target = int(lock["target_bytes"])
    reserve = int(lock["reserve_bytes"])
    usable = target - reserve

    if not args.skip_map:
        osm_rec = find_artifact(lock, "spain-osm")
        tool_rec = find_artifact(lock, "planetiler")
        osm = vault / osm_rec["path"]
        jar = vault / tool_rec["path"]
        output_dir = vault / "maps" / "tiles"
        output_dir.mkdir(parents=True, exist_ok=True)
        pmtiles = output_dir / "spain.pmtiles"

        if not pmtiles.exists():
            if not shutil.which("java"):
                raise PrepareError("Java 21+ is required to build the offline web map")

            free = shutil.disk_usage(os.getenv("ENDWORLD_BUILD_TMP", str(vault.parent))).free
            recommended = max(8_000_000_000, osm.stat().st_size * 5)
            if free < recommended:
                raise PrepareError(
                    f"Map build needs temporary space; have {human(free)}, "
                    f"recommend at least {human(recommended)}"
                )

            temp_parent = os.getenv("ENDWORLD_BUILD_TMP")
            with tempfile.TemporaryDirectory(prefix="endworld-map-", dir=temp_parent) as td:
                work = pathlib.Path(td)
                cmd = [
                    "java",
                    f"-Xmx{args.java_memory}",
                    "-XX:MaxHeapFreeRatio=40",
                    "-jar", str(jar),
                    "--osm-path", str(osm),
                    "--output", str(pmtiles),
                    "--download",
                    "--force",
                    "--storage", "mmap",
                    "--building-merge-z13=false",
                ]
                print("Building Spain PMTiles with Planetiler...")
                print(" ".join(cmd))
                subprocess.run(cmd, cwd=work, check=True)

        record = {
            "id": "spain-pmtiles",
            "family": "maps",
            "kind": "derived",
            "required": True,
            "source_artifact": "spain-osm",
            "builder_artifact": "planetiler",
            "filename": pmtiles.name,
            "path": str(pmtiles.relative_to(vault)),
            "bytes": pmtiles.stat().st_size,
            "sha256": sha256_file(pmtiles),
            "status": "derived",
        }
        upsert_artifact(lock, record)

    # Recalculate the payload from files represented in the lock. This avoids
    # double-counting replaced derived records.
    represented = []
    total = 0
    for group in ("artifacts", "containers"):
        for rec in lock.get(group, []):
            rel = rec.get("path")
            if not rel:
                continue
            path = vault / rel
            if path.exists():
                total += path.stat().st_size
                represented.append(rel)

    if total > usable:
        raise PrepareError(
            f"Prepared NANO payload {human(total)} exceeds usable budget {human(usable)}"
        )

    lock["payload_bytes"] = total
    lock["prepared"] = True
    lock["derived_count"] = sum(1 for x in lock.get("artifacts", []) if x.get("kind") == "derived")

    tmp = lock_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, lock_path)

    print(f"NANO prepared: {human(total)} / {human(usable)} usable")
    print(f"Lock updated: {lock_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PrepareError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
