#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib,sys
def sha(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--factory",required=True);a=ap.parse_args()
    root=pathlib.Path(a.factory).resolve();meta=root/"factory-manifest.json"
    if not meta.is_file():print("factory manifest missing",file=sys.stderr);return 2
    data=json.loads(meta.read_text())
    if data.get("kind")!="ark-offline-factory-v1":print("unsupported factory",file=sys.stderr);return 2
    for rec in data.get("files",[]):
        p=root/rec["name"]
        if not p.is_file() or p.stat().st_size!=int(rec["bytes"]) or sha(p)!=rec["sha256"]:
            print(f"factory verification failed: {p.name}",file=sys.stderr);return 1
    print(f"FACTORY VERIFIED: {data['profile']} {data['suite']} {len(data.get('packages',[]))} packages")
    return 0
if __name__=="__main__":raise SystemExit(main())
