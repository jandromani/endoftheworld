#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pathlib,shutil,socket,urllib.request
def get(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as r:return r.status
    except Exception:return None
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--local",action="store_true");ap.add_argument("--vault");ap.add_argument("--profile-id",default=os.getenv("ENDWORLD_PROFILE","nano"));args=ap.parse_args()
    p=args.profile_id;v=pathlib.Path(args.vault or (f"vault/{p}" if args.local else "/srv/endworld"));lp=v/"lock"/f"{p}.lock.json"
    try:lock=json.loads(lp.read_text())
    except Exception:lock={}
    ids={str(x.get("id")) for x in lock.get("containers",[])};maps=v/"maps/tiles"
    c={"portal":get("http://127.0.0.1:8080/health" if args.local else "http://127.0.0.1/health")==200,"kiwix":get("http://127.0.0.1:8081/") is not None,"ai":get("http://127.0.0.1:8082/health") is not None,"voice":get("http://127.0.0.1:8083/") is not None,"lock":lp.exists(),"bom":(v/"lock"/f"{p}.cdx.json").exists(),"map":maps.exists() and any(maps.glob("*.pmtiles")),"reticulum":(v/"source/comms").exists() if args.local else shutil.which("rnstatus") is not None}
    for cid,url in {"syncthing":"http://127.0.0.1:8384/","forgejo":"http://127.0.0.1:3000/","qdrant":"http://127.0.0.1:6333/healthz","code-server":"http://127.0.0.1:8443/","project-nomad-admin":"http://127.0.0.1:8090/api/health"}.items():
        if cid in ids:c[cid]=get(url) is not None
    out={"node":socket.gethostname(),"profile":p,"checks":c,"ok":all(c.values())};print(json.dumps(out,indent=2));return 0 if out["ok"] else 1
if __name__=="__main__":raise SystemExit(main())
