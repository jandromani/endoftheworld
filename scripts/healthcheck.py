#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, shutil, socket, urllib.request


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status
    except Exception:
        return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--local",action="store_true")
    ap.add_argument("--vault")
    ap.add_argument("--profile-id",default=os.getenv("ENDWORLD_PROFILE","nano"))
    args=ap.parse_args()
    profile=args.profile_id
    vault=pathlib.Path(args.vault or (f"vault/{profile}" if args.local else "/srv/endworld"))
    portal="http://127.0.0.1:8080/health" if args.local else "http://127.0.0.1/health"
    lock_path=vault/"lock"/f"{profile}.lock.json"
    try:
        lock=json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:
        lock={}
    container_ids={str(x.get("id")) for x in lock.get("containers",[])}

    reticulum=(vault/"source/comms").exists() if args.local else shutil.which("rnstatus") is not None
    maps_dir=vault/"maps/tiles"
    checks={
        "portal":get(portal)==200,
        "kiwix":get("http://127.0.0.1:8081/") is not None,
        "ai":get("http://127.0.0.1:8082/health") is not None,
        "voice":get("http://127.0.0.1:8083/") is not None,
        "lock":lock_path.exists(),
        "bom":(vault/"lock"/f"{profile}.cdx.json").exists(),
        "map":maps_dir.exists() and any(maps_dir.glob("*.pmtiles")),
        "reticulum":reticulum,
    }
    if "syncthing" in container_ids:
        checks["syncthing"]=get("http://127.0.0.1:8384/") is not None
    if "forgejo" in container_ids:
        checks["forgejo"]=get("http://127.0.0.1:3000/") is not None

    out={"node":socket.gethostname(),"profile":profile,"checks":checks,"ok":all(checks.values())}
    print(json.dumps(out,indent=2))
    return 0 if out["ok"] else 1


if __name__=="__main__":
    raise SystemExit(main())
