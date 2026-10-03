#!/usr/bin/env python3
"""Periodic frozen-vault integrity scrub with persistent evidence."""
from __future__ import annotations
import argparse,datetime as dt,json,os,pathlib,subprocess,sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vault",default=os.getenv("ENDWORLD_VAULT","/srv/endworld"))
    ap.add_argument("--profile",default=os.getenv("ENDWORLD_PROFILE","nano"))
    ap.add_argument("--out")
    a=ap.parse_args()
    vault=pathlib.Path(a.vault).resolve()
    out=pathlib.Path(a.out).resolve() if a.out else vault/"state/field/integrity-last.json"
    cmd=[sys.executable,str(ROOT/"scripts/verify_vault.py"),"--vault",str(vault),"--profile-id",a.profile]
    started=dt.datetime.now(dt.timezone.utc)
    p=subprocess.run(cmd,text=True,capture_output=True)
    ended=dt.datetime.now(dt.timezone.utc)
    report={
      "schema":1,"protocol":"ark-integrity-scrub-v1","profile":a.profile,
      "started_utc":started.isoformat(),"ended_utc":ended.isoformat(),
      "ok":p.returncode==0,"returncode":p.returncode,
      "output_tail":(p.stdout+p.stderr)[-12000:],
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(".tmp");tmp.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");os.replace(tmp,out)
    print(json.dumps({k:v for k,v in report.items() if k!="output_tail"},indent=2))
    print("THE_ARK_INTEGRITY_SCRUB="+("PASS" if report["ok"] else "FAIL"))
    return p.returncode
if __name__=="__main__":raise SystemExit(main())
