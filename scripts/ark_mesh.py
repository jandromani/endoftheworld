#!/usr/bin/env python3
"""THE ARK mesh exchange protocol.

Creates content-addressed inventories from frozen vaults, compares peers,
builds verified capability packs containing only missing chunks, applies packs
to a local chunk store, restores immutable vault payloads, and exports/imports
mutable state separately.

The protocol never executes transferred payloads. Integrity is SHA-256 based.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import pathlib
import shutil
import tarfile
import tempfile
from typing import Iterable

DEFAULT_CHUNK = 8 * 1024 * 1024
SCHEMA = 1


class MeshError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(value: str) -> pathlib.PurePosixPath:
    p = pathlib.PurePosixPath(value)
    if not value or p.is_absolute() or ".." in p.parts:
        raise MeshError(f"unsafe relative path: {value!r}")
    return p


def chunk_path(store: pathlib.Path, digest: str) -> pathlib.Path:
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
        raise MeshError("invalid sha256")
    return store / "objects" / "sha256" / digest[:2] / digest[2:]


def ensure_chunk(store: pathlib.Path, digest: str, data: bytes) -> pathlib.Path:
    if sha256_bytes(data) != digest:
        raise MeshError("chunk digest mismatch before store")
    dst = chunk_path(store, digest)
    if dst.exists():
        if dst.stat().st_size != len(data) or sha256_file(dst) != digest:
            raise MeshError(f"corrupt existing object: {dst}")
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    tmp.write_bytes(data)
    if sha256_file(tmp) != digest:
        tmp.unlink(missing_ok=True)
        raise MeshError("chunk digest mismatch after write")
    os.replace(tmp, dst)
    return dst


def load_lock(vault: pathlib.Path, profile: str) -> tuple[pathlib.Path, dict]:
    p = vault / "lock" / f"{profile}.lock.json"
    if not p.is_file():
        raise FileNotFoundError(p)
    lock = json.loads(p.read_text(encoding="utf-8"))
    if lock.get("profile") != profile:
        raise MeshError("lock/profile mismatch")
    return p, lock


def record_paths(lock: dict) -> list[dict]:
    rows = []
    for group in ("artifacts", "containers"):
        for rec in lock.get(group, []):
            rel = rec.get("path")
            if rel:
                rows.append({
                    "id": str(rec.get("id") or rel),
                    "group": group,
                    "path": str(safe_rel(str(rel))),
                    "declared_sha256": rec.get("sha256"),
                    "required": bool(rec.get("required", False)),
                })
    return rows


def file_chunks(path: pathlib.Path, chunk_bytes: int) -> Iterable[tuple[str, bytes]]:
    with path.open("rb") as f:
        while True:
            data = f.read(chunk_bytes)
            if not data:
                break
            yield sha256_bytes(data), data


def inventory(vault: pathlib.Path, profile: str, output: pathlib.Path, store: pathlib.Path | None, chunk_bytes: int) -> dict:
    if chunk_bytes < 1024 * 1024:
        raise MeshError("chunk size must be at least 1 MiB")
    lock_path, lock = load_lock(vault, profile)
    items = []
    total = 0

    rows = record_paths(lock)
    bom = vault / "lock" / f"{profile}.cdx.json"
    rows.append({"id": "__lock__", "group": "metadata", "path": f"lock/{profile}.lock.json", "declared_sha256": sha256_file(lock_path), "required": True})
    if bom.is_file():
        rows.append({"id": "__bom__", "group": "metadata", "path": f"lock/{profile}.cdx.json", "declared_sha256": sha256_file(bom), "required": True})

    for rec in rows:
        rel = safe_rel(rec["path"])
        path = vault / rel
        if not path.is_file():
            if rec["required"]:
                raise FileNotFoundError(path)
            continue
        digest = sha256_file(path)
        declared = rec.get("declared_sha256")
        if declared and declared != digest:
            raise MeshError(f"frozen artifact hash mismatch: {rel}")
        chunks = []
        for cdigest, data in file_chunks(path, chunk_bytes):
            if store is not None:
                ensure_chunk(store, cdigest, data)
            chunks.append({"sha256": cdigest, "bytes": len(data)})
        total += path.stat().st_size
        items.append({
            "id": rec["id"], "group": rec["group"], "path": str(rel),
            "bytes": path.stat().st_size, "sha256": digest,
            "required": rec["required"], "chunks": chunks,
        })

    data = {
        "schema": SCHEMA,
        "protocol": "ark-mesh-v1",
        "profile": profile,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "chunk_bytes": chunk_bytes,
        "lock_sha256": sha256_file(lock_path),
        "total_bytes": total,
        "items": items,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"inventory": str(output), "items": len(items), "bytes": total, "store": str(store) if store else None}, indent=2))
    return data


def load_inventory(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or data.get("protocol") != "ark-mesh-v1":
        raise MeshError("unsupported inventory")
    for rec in data.get("items", []):
        safe_rel(str(rec["path"]))
        for c in rec.get("chunks", []):
            if int(c.get("bytes") or 0) <= 0:
                raise MeshError("invalid chunk size")
            chunk_path(pathlib.Path("."), str(c["sha256"]))
    return data


def chunk_set(inv: dict) -> set[str]:
    return {str(c["sha256"]) for rec in inv.get("items", []) for c in rec.get("chunks", [])}


def diff(source: pathlib.Path, target: pathlib.Path | None) -> dict:
    src = load_inventory(source)
    have = chunk_set(load_inventory(target)) if target else set()
    missing = []
    missing_bytes = 0
    seen = set()
    for rec in src.get("items", []):
        for c in rec.get("chunks", []):
            h = str(c["sha256"])
            if h in have or h in seen:
                continue
            seen.add(h)
            missing.append(h)
            missing_bytes += int(c["bytes"])
    out = {
        "profile": src["profile"],
        "source_chunks": len(chunk_set(src)),
        "target_chunks": len(have),
        "missing_chunks": len(missing),
        "missing_bytes": missing_bytes,
        "missing_sha256": missing,
    }
    print(json.dumps(out, indent=2))
    return out


def add_bytes(tf: tarfile.TarFile, name: str, data: bytes) -> None:
    i = tarfile.TarInfo(name)
    i.size = len(data)
    i.mtime = 0
    i.uid = i.gid = 0
    i.uname = i.gname = ""
    tf.addfile(i, io.BytesIO(data))


def pack(source_inventory: pathlib.Path, store: pathlib.Path, out: pathlib.Path, target_inventory: pathlib.Path | None) -> dict:
    src = load_inventory(source_inventory)
    have = chunk_set(load_inventory(target_inventory)) if target_inventory else set()
    all_chunks = {}
    for rec in src.get("items", []):
        for c in rec.get("chunks", []):
            all_chunks[str(c["sha256"])] = int(c["bytes"])
    needed = {h: n for h, n in all_chunks.items() if h not in have}

    manifest = {
        "schema": SCHEMA,
        "protocol": "ark-pack-v1",
        "profile": src["profile"],
        "source_inventory_sha256": sha256_file(source_inventory),
        "chunks": [{"sha256": h, "bytes": needed[h]} for h in sorted(needed)],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w") as tf:
        add_bytes(tf, "ark-pack.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        add_bytes(tf, "inventory.json", source_inventory.read_bytes())
        for h in sorted(needed):
            p = chunk_path(store, h)
            if not p.is_file() or p.stat().st_size != needed[h] or sha256_file(p) != h:
                raise MeshError(f"missing/corrupt source chunk: {h}")
            info = tf.gettarinfo(str(p), arcname=f"objects/sha256/{h[:2]}/{h[2:]}")
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with p.open("rb") as f:
                tf.addfile(info, f)
    result = {"pack": str(out), "chunks": len(needed), "bytes": out.stat().st_size}
    print(json.dumps(result, indent=2))
    return result


def _read_pack_manifest(tf: tarfile.TarFile) -> dict:
    f = tf.extractfile("ark-pack.json")
    if not f:
        raise MeshError("ark-pack.json missing")
    data = json.load(f)
    if data.get("schema") != SCHEMA or data.get("protocol") != "ark-pack-v1":
        raise MeshError("unsupported pack")
    return data


def verify_pack(bundle: pathlib.Path) -> dict:
    with tarfile.open(bundle, "r") as tf:
        m = _read_pack_manifest(tf)
        inv = tf.extractfile("inventory.json")
        if not inv:
            raise MeshError("inventory missing")
        inv_bytes = inv.read()
        if sha256_bytes(inv_bytes) != m["source_inventory_sha256"]:
            raise MeshError("inventory digest mismatch")
        for c in m.get("chunks", []):
            h, n = str(c["sha256"]), int(c["bytes"])
            f = tf.extractfile(f"objects/sha256/{h[:2]}/{h[2:]}")
            if not f:
                raise MeshError(f"pack chunk missing: {h}")
            hasher = hashlib.sha256()
            count = 0
            for data in iter(lambda: f.read(8 * 1024 * 1024), b""):
                hasher.update(data)
                count += len(data)
            if hasher.hexdigest() != h or count != n:
                raise MeshError(f"pack chunk verification failed: {h}")
    print("VERIFIED")
    return m


def apply_pack(bundle: pathlib.Path, store: pathlib.Path, inventory_out: pathlib.Path | None) -> dict:
    m = verify_pack(bundle)
    with tarfile.open(bundle, "r") as tf:
        for c in m.get("chunks", []):
            h, n = str(c["sha256"]), int(c["bytes"])
            dst = chunk_path(store, h)
            if dst.is_file() and dst.stat().st_size == n and sha256_file(dst) == h:
                continue
            f = tf.extractfile(f"objects/sha256/{h[:2]}/{h[2:]}")
            if not f:
                raise MeshError(f"pack chunk missing: {h}")
            data = f.read()
            if len(data) != n:
                raise MeshError(f"pack chunk size mismatch: {h}")
            ensure_chunk(store, h, data)
        inv = tf.extractfile("inventory.json")
        inv_bytes = inv.read() if inv else b""
    if inventory_out:
        inventory_out.parent.mkdir(parents=True, exist_ok=True)
        inventory_out.write_bytes(inv_bytes)
    result = {"store": str(store), "chunks_applied": len(m.get("chunks", []))}
    print(json.dumps(result, indent=2))
    return result


def restore(inventory_path: pathlib.Path, store: pathlib.Path, target: pathlib.Path) -> dict:
    inv = load_inventory(inventory_path)
    restored = 0
    for rec in inv.get("items", []):
        rel = safe_rel(str(rec["path"]))
        dst = target / rel
        if dst.is_file() and dst.stat().st_size == int(rec["bytes"]) and sha256_file(dst) == rec["sha256"]:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_suffix(dst.suffix + ".arkmesh.tmp")
        with tmp.open("wb") as out:
            for c in rec.get("chunks", []):
                h = str(c["sha256"])
                p = chunk_path(store, h)
                if not p.is_file() or p.stat().st_size != int(c["bytes"]) or sha256_file(p) != h:
                    raise MeshError(f"required chunk unavailable: {h}")
                with p.open("rb") as f:
                    shutil.copyfileobj(f, out)
        if tmp.stat().st_size != int(rec["bytes"]) or sha256_file(tmp) != rec["sha256"]:
            tmp.unlink(missing_ok=True)
            raise MeshError(f"restored artifact verification failed: {rel}")
        os.replace(tmp, dst)
        restored += 1
    print(json.dumps({"target": str(target), "restored_items": restored, "profile": inv["profile"]}, indent=2))
    return {"restored_items": restored}


def state_export(vault: pathlib.Path, profile: str, out: pathlib.Path) -> None:
    state = vault / "state"
    if not state.is_dir():
        raise FileNotFoundError(state)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w") as tf:
        meta = {
            "schema": 1, "protocol": "ark-state-v1", "profile": profile,
            "warning": "Mutable state may contain credentials or personal data. Protect this archive.",
        }
        add_bytes(tf, "state-manifest.json", (json.dumps(meta, indent=2, sort_keys=True) + "\n").encode())
        for p in sorted(state.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(state)
            info = tf.gettarinfo(str(p), arcname=f"state/{rel}")
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with p.open("rb") as f:
                tf.addfile(info, f)
    print(json.dumps({"archive": str(out), "sha256": sha256_file(out), "bytes": out.stat().st_size}, indent=2))


def state_import(bundle: pathlib.Path, vault: pathlib.Path, replace: bool) -> None:
    with tarfile.open(bundle, "r") as tf:
        mf = tf.extractfile("state-manifest.json")
        if not mf:
            raise MeshError("state manifest missing")
        meta = json.load(mf)
        if meta.get("protocol") != "ark-state-v1":
            raise MeshError("unsupported state archive")
        stage = pathlib.Path(tempfile.mkdtemp(prefix="ark-state-", dir=str(vault)))
        try:
            for member in tf.getmembers():
                if not member.isfile() or not member.name.startswith("state/"):
                    continue
                rel = safe_rel(member.name[len("state/"):])
                src = tf.extractfile(member)
                if not src:
                    continue
                dst = stage / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                with dst.open("wb") as f:
                    shutil.copyfileobj(src, f)
            target = vault / "state"
            if replace:
                backup = vault / "state.pre-ark-import"
                shutil.rmtree(backup, ignore_errors=True)
                if target.exists():
                    os.replace(target, backup)
                os.replace(stage, target)
            else:
                target.mkdir(parents=True, exist_ok=True)
                for p in sorted(stage.rglob("*")):
                    if p.is_file():
                        rel = p.relative_to(stage)
                        dst = target / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(p, dst)
        finally:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
    print("STATE IMPORTED")


def main() -> int:
    ap = argparse.ArgumentParser(prog="ark-mesh")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("inventory")
    i.add_argument("--vault", required=True)
    i.add_argument("--profile", required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--store")
    i.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK)

    d = sub.add_parser("diff")
    d.add_argument("--source", required=True)
    d.add_argument("--target")

    p = sub.add_parser("pack")
    p.add_argument("--source-inventory", required=True)
    p.add_argument("--store", required=True)
    p.add_argument("--target-inventory")
    p.add_argument("--out", required=True)

    v = sub.add_parser("verify-pack")
    v.add_argument("bundle")

    a = sub.add_parser("apply-pack")
    a.add_argument("bundle")
    a.add_argument("--store", required=True)
    a.add_argument("--inventory-out")

    r = sub.add_parser("restore")
    r.add_argument("--inventory", required=True)
    r.add_argument("--store", required=True)
    r.add_argument("--target-vault", required=True)

    se = sub.add_parser("state-export")
    se.add_argument("--vault", required=True)
    se.add_argument("--profile", required=True)
    se.add_argument("--out", required=True)

    si = sub.add_parser("state-import")
    si.add_argument("bundle")
    si.add_argument("--vault", required=True)
    si.add_argument("--replace", action="store_true")

    args = ap.parse_args()
    if args.cmd == "inventory":
        inventory(pathlib.Path(args.vault).resolve(), args.profile, pathlib.Path(args.out).resolve(),
                  pathlib.Path(args.store).resolve() if args.store else None, args.chunk_bytes)
    elif args.cmd == "diff":
        diff(pathlib.Path(args.source).resolve(), pathlib.Path(args.target).resolve() if args.target else None)
    elif args.cmd == "pack":
        pack(pathlib.Path(args.source_inventory).resolve(), pathlib.Path(args.store).resolve(),
             pathlib.Path(args.out).resolve(), pathlib.Path(args.target_inventory).resolve() if args.target_inventory else None)
    elif args.cmd == "verify-pack":
        verify_pack(pathlib.Path(args.bundle).resolve())
    elif args.cmd == "apply-pack":
        apply_pack(pathlib.Path(args.bundle).resolve(), pathlib.Path(args.store).resolve(),
                   pathlib.Path(args.inventory_out).resolve() if args.inventory_out else None)
    elif args.cmd == "restore":
        restore(pathlib.Path(args.inventory).resolve(), pathlib.Path(args.store).resolve(), pathlib.Path(args.target_vault).resolve())
    elif args.cmd == "state-export":
        state_export(pathlib.Path(args.vault).resolve(), args.profile, pathlib.Path(args.out).resolve())
    else:
        state_import(pathlib.Path(args.bundle).resolve(), pathlib.Path(args.vault).resolve(), args.replace)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MeshError, OSError, ValueError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2)
