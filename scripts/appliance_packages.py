#!/usr/bin/env python3
from __future__ import annotations
import argparse,pathlib,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
def groups(profile:str)->list[str]:
    out=["base"]
    if profile in ("nomad","civilization"):out.append("developer")
    if profile=="civilization":out.append("civilization")
    return out
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--profile",required=True);ap.add_argument("--manifest",default=str(ROOT/"manifests/appliance-packages.yml"));args=ap.parse_args()
    data=yaml.safe_load(pathlib.Path(args.manifest).read_text())
    seen=set()
    for g in groups(args.profile):
        for p in data.get(g,[]):
            if p not in seen:seen.add(p);print(p)
    return 0
if __name__=="__main__":raise SystemExit(main())
