#!/usr/bin/env python3
"""Controlled capability evolution: discover -> assess -> quarantine -> approve."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, pathlib, re, tarfile, zipfile

def load(path):return json.loads(path.read_text(encoding="utf-8"))
def age_days(value):
    if not value:return 99999
    try:return (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(value.replace("Z","+00:00"))).days
    except Exception:return 99999

def assess(item):
    score=0;reasons=[];risks=[]
    stars=int(item.get("stars") or 0);age=age_days(item.get("pushed_at"))
    if item.get("license"):score+=25;reasons.append("declared-license")
    else:risks.append("license-unknown")
    if stars>=1000:score+=20
    elif stars>=100:score+=12
    elif stars>=25:score+=5
    if age<=90:score+=20;reasons.append("recently-maintained")
    elif age<=365:score+=12
    elif age<=730:score+=5
    else:risks.append("stale")
    if item.get("archived"):score-=100;risks.append("archived")
    desc=(item.get("description") or "").lower()
    if any(x in desc for x in ("offline","local","mesh","map","emergency","archive","llm")):score+=8
    return {"score":score,"reasons":reasons,"risks":risks}

def propose(scout,out,limit):
    d=load(scout);rows=[]
    for x in d.get("candidate_capabilities",[]):
        a=assess(x);rows.append({**x,**a,"trust_state":"PROPOSED_UNTRUSTED"})
    rows.sort(key=lambda x:(-x["score"],-(x.get("stars") or 0),x.get("repo") or ""))
    selected=[];per={}
    for r in rows:
        fam=r.get("family","other")
        if per.get(fam,0)>=limit:continue
        selected.append(r);per[fam]=per.get(fam,0)+1
    data={"schema":1,"protocol":"ark-evolution-proposal-v1","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
          "source_report":scout.name,"policy":{"execute_candidates":False,"auto_promote":False,"human_approval_required":True},
          "candidates":selected}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"proposal":str(out),"candidates":len(selected)},indent=2))

def archive_members(path):
    if tarfile.is_tarfile(path):
        with tarfile.open(path,"r:*") as tf:
            for m in tf.getmembers():yield m.name,m.size,m.mode,m.issym() or m.islnk()
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                mode=(i.external_attr>>16)&0o7777
                yield i.filename,i.file_size,mode,False
    else:raise SystemExit("unsupported quarantine archive")

def inspect(path,out,max_bytes,max_files):
    total=0;files=0;execs=[];links=[];unsafe=[];licenses=[];hooks=[]
    for name,size,mode,islink in archive_members(path):
        files+=1;total+=int(size)
        p=pathlib.PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts:unsafe.append(name)
        if islink:links.append(name)
        if mode & 0o111:execs.append(name)
        low=p.name.lower()
        if low.startswith(("license","copying","notice")):licenses.append(name)
        if low in ("setup.py","package.json","pyproject.toml","pom.xml","build.rs","makefile"):hooks.append(name)
        if files>max_files or total>max_bytes:break
    passed=not unsafe and files<=max_files and total<=max_bytes
    data={"schema":1,"protocol":"ark-evolution-sandbox-v1","archive":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
          "static_only":True,"executed":False,"passed":passed,"files":files,"bytes":total,
          "unsafe_paths":unsafe[:50],"symlinks":links[:50],"executables":execs[:100],"license_files":licenses[:50],
          "build_or_install_metadata":hooks[:100]}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data,indent=2));return 0 if passed else 2

def validate(path):
    d=load(path)
    if d.get("protocol")!="ark-evolution-proposal-v1":raise SystemExit("bad proposal protocol")
    pol=d.get("policy") or {}
    if pol.get("execute_candidates") is not False or pol.get("auto_promote") is not False or pol.get("human_approval_required") is not True:
        raise SystemExit("unsafe evolution policy")
    for c in d.get("candidates",[]):
        if c.get("trust_state")!="PROPOSED_UNTRUSTED":raise SystemExit("candidate incorrectly trusted")
    print("THE_ARK_EVOLUTION_PROPOSAL=VALID")

def agent_prompt(path,out):
    d=load(path)
    brief=[{"repo":x.get("repo"),"family":x.get("family"),"description":x.get("description"),
            "license":x.get("license"),"score":x.get("score"),"risks":x.get("risks")} for x in d.get("candidates",[])]
    text=("Review this untrusted capability proposal for THE ARK. Use only the supplied metadata. "
          "Identify overlap with existing frozen capabilities, likely offline value, dependency/maintenance/licensing risks, "
          "and what static or sandbox evidence should be required before any human-approved promotion. "
          "Do not recommend executing candidate code and do not mark anything trusted.\n\n"+
          json.dumps(brief,ensure_ascii=False,indent=2))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text+"\n",encoding="utf-8");print(out)

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("propose");p.add_argument("--scout",required=True);p.add_argument("--out",required=True);p.add_argument("--per-family",type=int,default=3)
    v=sub.add_parser("validate");v.add_argument("proposal")
    s=sub.add_parser("inspect-archive");s.add_argument("archive");s.add_argument("--out",required=True);s.add_argument("--max-bytes",type=int,default=2*1024**3);s.add_argument("--max-files",type=int,default=100000)
    g=sub.add_parser("agent-prompt");g.add_argument("proposal");g.add_argument("--out",required=True)
    a=ap.parse_args()
    if a.cmd=="propose":propose(pathlib.Path(a.scout),pathlib.Path(a.out),a.per_family)
    elif a.cmd=="validate":validate(pathlib.Path(a.proposal))
    elif a.cmd=="inspect-archive":return inspect(pathlib.Path(a.archive),pathlib.Path(a.out),a.max_bytes,a.max_files)
    else:agent_prompt(pathlib.Path(a.proposal),pathlib.Path(a.out))
    return 0
if __name__=="__main__":raise SystemExit(main())
