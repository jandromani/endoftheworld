#!/usr/bin/env python3
"""Offline multi-role orchestration above the already-gated single Ark Agent."""
from __future__ import annotations
import argparse, datetime as dt, json, os, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:sys.path.insert(0,str(ROOT/"scripts"))
from agent_runner import Agent, ROLE_GUIDANCE

DEFAULT_ROLES=("research","engineer","field")

def run(goal,vault,profile,roles,max_steps,timeout):
    run_id=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    specialists=[]
    for idx,role in enumerate(roles,1):
        task_id=f"orchestrator-{run_id}-{idx}-{role}"
        role_goal=(
            f"Original goal:\n{goal}\n\n"
            f"Work as the {role} specialist. Produce a bounded evidence-based report for the coordinator. "
            "Use local tools when useful. Do not assume another specialist has checked your claims."
        )
        try:
            result=Agent(vault,profile,role_goal,task_id,max_steps,timeout,role).run()
            specialists.append({"role":role,"task_id":task_id,"ok":True,"answer":result["answer"]})
        except Exception as exc:
            specialists.append({"role":role,"task_id":task_id,"ok":False,"error":str(exc)})
    reports="\n\n".join(
        f"[{x['role'].upper()}]\n"+(x.get("answer") or ("FAILED: "+x.get("error","unknown")))
        for x in specialists
    )
    coordinator_goal=(
        f"Original goal:\n{goal}\n\n"
        "Specialist reports follow. Reconcile them. Check local evidence again if needed. "
        "Do not invent capabilities, do not increase permissions, and explicitly surface unresolved conflicts.\n\n"
        +reports
    )
    coord_id=f"orchestrator-{run_id}-coordinator"
    result=Agent(vault,profile,coordinator_goal,coord_id,max_steps,timeout,"coordinator").run()
    return {"run_id":run_id,"goal":goal,"profile":profile,"specialists":specialists,
            "coordinator":{"task_id":coord_id,"answer":result["answer"]},"ok":True}

def main():
    ap=argparse.ArgumentParser(prog="ark-orchestrator")
    ap.add_argument("goal");ap.add_argument("--vault",default=os.getenv("ENDWORLD_VAULT","/srv/endworld"))
    ap.add_argument("--profile",default=os.getenv("ENDWORLD_PROFILE","nano"))
    ap.add_argument("--roles",default=",".join(DEFAULT_ROLES))
    ap.add_argument("--max-steps",type=int,default=6);ap.add_argument("--timeout",type=int,default=240)
    ap.add_argument("--json",action="store_true")
    a=ap.parse_args()
    roles=[x.strip() for x in a.roles.split(",") if x.strip()]
    if not roles or len(roles)>4:raise SystemExit("choose 1..4 specialist roles")
    bad=[x for x in roles if x not in ROLE_GUIDANCE or x=="coordinator"]
    if bad:raise SystemExit("invalid specialist roles: "+",".join(bad))
    try:r=run(a.goal,pathlib.Path(a.vault).resolve(),a.profile,roles,max(1,min(a.max_steps,12)),max(30,a.timeout))
    except Exception as exc:
        r={"ok":False,"error":str(exc)}
        print(json.dumps(r,ensure_ascii=False) if a.json else "ERROR: "+str(exc));return 2
    print(json.dumps(r,indent=2,ensure_ascii=False) if a.json else r["coordinator"]["answer"]);return 0
if __name__=="__main__":raise SystemExit(main())
