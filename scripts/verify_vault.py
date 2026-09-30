#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys

def sha256_file(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def resolve_lock(vault:pathlib.Path,profile_id:str|None)->pathlib.Path:
    if profile_id:
        return vault/"lock"/f"{profile_id}.lock.json"
    locks=sorted((vault/"lock").glob("*.lock.json")) if (vault/"lock").exists() else []
    if len(locks)!=1:
        raise RuntimeError(f"Expected exactly one lock in {vault/'lock'}, found {len(locks)}; pass --profile-id")
    return locks[0]

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--vault",required=True);ap.add_argument("--profile-id");args=ap.parse_args()
    vault=pathlib.Path(args.vault).resolve()
    try:lock_path=resolve_lock(vault,args.profile_id)
    except RuntimeError as exc:print(str(exc),file=sys.stderr);return 2
    if not lock_path.exists():print(f"Missing lock file: {lock_path}",file=sys.stderr);return 2
    lock=json.loads(lock_path.read_text(encoding="utf-8"));records=list(lock.get("artifacts",[]))+list(lock.get("containers",[]))
    bad=0;total=0;checked=0
    for rec in records:
        rel=rec.get("path");expected_hash=rec.get("sha256");expected_bytes=rec.get("bytes")
        if not rel or not expected_hash:print(f"SKIP {rec.get('id')}: no frozen path/hash");continue
        path=vault/rel
        if not path.exists():print(f"MISSING {rec.get('id')}: {rel}");bad+=1;continue
        actual_bytes=path.stat().st_size;total+=actual_bytes
        if expected_bytes is not None and actual_bytes!=int(expected_bytes):
            print(f"SIZE FAIL {rec.get('id')}: {actual_bytes} != {expected_bytes}");bad+=1;continue
        actual_hash=sha256_file(path)
        if actual_hash!=expected_hash:print(f"HASH FAIL {rec.get('id')}");bad+=1;continue
        checked+=1;print(f"OK {rec.get('id')}  {actual_hash[:16]}…")
    if bad:print(f"VERIFY FAILED: {bad} problem(s)",file=sys.stderr);return 1
    print(f"VERIFY OK: profile={lock.get('profile')} checked={checked} {total/1e9:.2f} GB")
    return 0
if __name__=="__main__":raise SystemExit(main())
