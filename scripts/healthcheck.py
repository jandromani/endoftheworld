#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, socket, sys, urllib.request

def get(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as r:return r.status
    except Exception:return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--local",action="store_true");ap.add_argument("--vault");args=ap.parse_args()
    vault=pathlib.Path(args.vault or ("vault/nano" if args.local else "/srv/endworld"))
    portal="http://127.0.0.1:8080/health" if args.local else "http://127.0.0.1/health"
    checks={"portal":get(portal)==200,"kiwix":get("http://127.0.0.1:8081/") is not None,
            "ai":get("http://127.0.0.1:8082/health") is not None,
            "lock":(vault/"lock/nano.lock.json").exists(),"map":(vault/"maps/tiles/spain.pmtiles").exists()}
    out={"node":socket.gethostname(),"profile":"nano","checks":checks,"ok":all(checks.values())}
    print(json.dumps(out,indent=2))
    return 0 if out["ok"] else 1
if __name__=="__main__":raise SystemExit(main())
