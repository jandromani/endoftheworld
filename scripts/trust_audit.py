#!/usr/bin/env python3
"""Static trust-policy checks for frozen locks, release manifests and reproducibility."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, yaml

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_yaml(path):
    d=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict) or d.get("schema")!=1:raise SystemExit("unsupported trust policy")
    return d

def audit_lock(lock,policy):
    d=json.loads(lock.read_text(encoding="utf-8"))
    rows=list(d.get("artifacts",[]))+list(d.get("containers",[]))
    if not rows:raise SystemExit("lock has no artifacts/containers")
    local=sum(1 for x in rows if x.get("sha256"))
    upstream=sum(1 for x in rows if x.get("upstream_sha256") or x.get("upstream_checksum_verified") is True)
    unknown_license=[str(x.get("id")) for x in rows if not x.get("license") and (x.get("kind")!="container")]
    result={"schema":1,"protocol":"ark-trust-audit-v1","items":len(rows),
            "local_sha256":local,"upstream_verified":upstream,
            "upstream_verification_percent":round(100*upstream/len(rows),1),
            "unknown_license_count":len(unknown_license),"unknown_license_ids":unknown_license[:100],
            "policy":{"unknown_license_requires_review":bool((policy.get("policy") or {}).get("licenses",{}).get("unknown_requires_review",True))}}
    result["pass"]=local==len(rows)
    return result

def audit_release(manifest,policy):
    d=json.loads(manifest.read_text(encoding="utf-8"))
    p=policy.get("policy") or {}
    errors=[]
    if d.get("protocol") not in ("ark-public-release-v1",None):errors.append("unsupported release protocol")
    if p.get("public_key_fingerprint_required") and not d.get("release_key_sha256"):errors.append("release key fingerprint missing")
    if p.get("sbom_required"):
        roles={x.get("role") for x in d.get("files",[])}
        if not ({"sbom"}<=roles or {"bom"}<=roles):errors.append("SBOM file binding missing")
    if not d.get("git_commit"):errors.append("git commit missing")
    return {"schema":1,"protocol":"ark-release-policy-audit-v1","pass":not errors,"errors":errors,
            "profile":d.get("profile"),"version":d.get("version"),"git_commit":d.get("git_commit")}

def vulnerability_audit(report,allowlist,policy):
    data=json.loads(report.read_text(encoding="utf-8"))
    allow=load_yaml(allowlist).get("allow") or []
    allowed={str(x.get("id")) for x in allow if isinstance(x,dict) and x.get("id")}
    findings=[]
    if isinstance(data.get("Results"),list):
        for result in data["Results"]:
            for v in result.get("Vulnerabilities") or []:
                findings.append({"id":v.get("VulnerabilityID"),"severity":str(v.get("Severity") or "").upper(),
                                 "package":v.get("PkgName"),"version":v.get("InstalledVersion")})
    elif isinstance(data.get("matches"),list):
        for m in data["matches"]:
            v=m.get("vulnerability") or {};a=m.get("artifact") or {}
            findings.append({"id":v.get("id"),"severity":str(v.get("severity") or "").upper(),
                             "package":a.get("name"),"version":a.get("version")})
    block=set((((policy.get("policy") or {}).get("vulnerabilities") or {}).get("block_severity") or ["CRITICAL"]))
    blocked=[x for x in findings if x["severity"] in block and str(x.get("id")) not in allowed]
    return {"schema":1,"protocol":"ark-vulnerability-policy-v1","pass":not blocked,
            "findings":len(findings),"blocked":blocked,"allowed_ids":sorted(allowed)}

def compare(a,b,label):
    ha,hb=sha(a),sha(b)
    same=ha==hb and a.stat().st_size==b.stat().st_size
    return {"schema":1,"protocol":"ark-reproducible-compare-v1","label":label,"reproducible":same,
            "a":{"file":a.name,"bytes":a.stat().st_size,"sha256":ha},
            "b":{"file":b.name,"bytes":b.stat().st_size,"sha256":hb}}

def main():
    ap=argparse.ArgumentParser(prog="ark-trust-audit")
    ap.add_argument("--policy",default="config/trust-policy.yml")
    sub=ap.add_subparsers(dest="cmd",required=True)
    l=sub.add_parser("lock");l.add_argument("lock")
    r=sub.add_parser("release");r.add_argument("manifest")
    c=sub.add_parser("compare");c.add_argument("a");c.add_argument("b");c.add_argument("--label",default="artifact")
    v=sub.add_parser("vulnerabilities");v.add_argument("report");v.add_argument("--allowlist",default="config/vulnerability-allowlist.yml")
    a=ap.parse_args();policy=load_yaml(pathlib.Path(a.policy).resolve())
    if a.cmd=="lock":out=audit_lock(pathlib.Path(a.lock).resolve(),policy)
    elif a.cmd=="release":out=audit_release(pathlib.Path(a.manifest).resolve(),policy)
    elif a.cmd=="compare":out=compare(pathlib.Path(a.a).resolve(),pathlib.Path(a.b).resolve(),a.label)
    else:out=vulnerability_audit(pathlib.Path(a.report).resolve(),pathlib.Path(a.allowlist).resolve(),policy)
    print(json.dumps(out,indent=2))
    return 0 if out.get("pass",out.get("reproducible",False)) else 2
if __name__=="__main__":raise SystemExit(main())
