#!/usr/bin/env python3
"""Offline redundancy planner for a multi-node THE ARK cluster."""
from __future__ import annotations
import argparse, json, pathlib, sys, yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:sys.path.insert(0,str(ROOT/"scripts"))
import ark_mesh

def load_yaml(path):
    d=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict) or d.get("schema")!=1:raise SystemExit("unsupported cluster/node schema")
    return d

def inventory_digest_map(path):
    inv=ark_mesh.load_inventory(path)
    return inv,{str(x["sha256"]):x for x in inv.get("items",[]) if x.get("sha256")}

def plan(policy_path,nodes_path):
    policy=load_yaml(policy_path);cfg=load_yaml(nodes_path)
    nodes=cfg.get("nodes") or []
    if not nodes:raise SystemExit("nodes config has no nodes")
    base=nodes_path.parent
    seen_ids=set();loaded=[];roles=set();sites=set()
    for n in nodes:
        nid=str(n.get("id") or "").strip();role=str(n.get("role") or "").strip();site=str(n.get("site") or "").strip()
        if not nid or nid in seen_ids:raise SystemExit("node id missing/duplicate")
        if not site:raise SystemExit(f"{nid}: site required")
        ip=pathlib.Path(str(n.get("inventory") or ""))
        if not ip.is_absolute():ip=(base/ip).resolve()
        inv,items=inventory_digest_map(ip)
        loaded.append({"id":nid,"role":role,"site":site,"inventory":str(ip),"profile":inv["profile"],
                       "items":items,"state_backup":bool(n.get("state_backup")),"cold_storage":bool(n.get("cold_storage"))})
        seen_ids.add(nid);roles.add(role);sites.add(site)
    rep=policy.get("replication") or {}
    imm=int(rep.get("immutable_min_copies") or 1);mut=int(rep.get("mutable_state_min_copies") or 1);cold=int(rep.get("cold_storage_min_copies") or 0)
    geo=bool(rep.get("geographic_separation_required",False))
    all_digests=sorted({d for n in loaded for d in n["items"]})
    deficits=[];coverage=[]
    for digest in all_digests:
        holders=[n for n in loaded if digest in n["items"]]
        holder_sites=sorted({n["site"] for n in holders})
        sample=holders[0]["items"][digest]
        ok=len(holders)>=imm and (not geo or len(holder_sites)>=min(imm,len(holders)))
        row={"sha256":digest,"id":sample.get("id"),"path":sample.get("path"),"copies":len(holders),
             "sites":holder_sites,"nodes":[n["id"] for n in holders],"required_copies":imm,"ok":ok}
        coverage.append(row)
        if not ok:deficits.append(row)
    state_nodes=[n["id"] for n in loaded if n["state_backup"]]
    cold_nodes=[n["id"] for n in loaded if n["cold_storage"]]
    role_policy={x.get("id") for x in (policy.get("node_roles") or []) if x.get("id")}
    missing_roles=sorted(role_policy-roles)
    checks={
        "immutable":not deficits,
        "mutable_state":len(state_nodes)>=mut,
        "cold_storage":len(cold_nodes)>=cold,
        "roles":not missing_roles,
        "geographic_sites":(not geo) or len(sites)>=min(imm,len(loaded)),
    }
    ready=all(checks.values())
    return {"schema":1,"protocol":"ark-cluster-plan-v1","ready":ready,"checks":checks,
            "policy":{"immutable_min_copies":imm,"mutable_state_min_copies":mut,"cold_storage_min_copies":cold,"geographic_separation_required":geo},
            "nodes":[{k:n[k] for k in ("id","role","site","profile","inventory","state_backup","cold_storage")} for n in loaded],
            "state_backup_nodes":state_nodes,"cold_storage_nodes":cold_nodes,"missing_roles":missing_roles,
            "content_objects":len(coverage),"deficits":deficits,"coverage":coverage}

def main():
    ap=argparse.ArgumentParser(prog="ark-cluster")
    ap.add_argument("--policy",default=str(ROOT/"config/ark-cluster.yml"))
    ap.add_argument("--nodes",required=True);ap.add_argument("--out")
    a=ap.parse_args();r=plan(pathlib.Path(a.policy).resolve(),pathlib.Path(a.nodes).resolve())
    if a.out:
        p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2))
    if r["ready"]:print("THE_ARK_CLUSTER_REDUNDANCY=PASS")
    return 0 if r["ready"] else 2
if __name__=="__main__":raise SystemExit(main())
