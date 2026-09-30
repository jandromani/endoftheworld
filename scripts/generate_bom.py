#!/usr/bin/env python3
"""Generate an artifact-level CycloneDX BOM from an ENDWORLD frozen lock."""
from __future__ import annotations
import argparse, datetime as dt, json, pathlib, uuid

def component(rec:dict,kind:str)->dict:
    name=rec.get("id") or rec.get("filename") or rec.get("image") or "unknown"
    version=rec.get("release_tag") or rec.get("ref") or "frozen"
    c={"type":"container" if kind=="containers" else "file","name":name,"version":str(version),"bom-ref":"urn:endworld:"+name}
    if rec.get("sha256"):c["hashes"]=[{"alg":"SHA-256","content":rec["sha256"]}]
    props=[]
    for k in ("family","kind","repo","url","resolved_url","path","bytes","upstream_sha256","upstream_checksum_verified"):
        if rec.get(k) is not None:props.append({"name":"endworld:"+k,"value":str(rec[k])})
    if rec.get("repo"):c["externalReferences"]=[{"type":"vcs","url":"https://github.com/"+rec["repo"]}]
    if props:c["properties"]=props
    return c

def find_lock(vault:pathlib.Path,profile_id:str|None)->pathlib.Path:
    if profile_id:return vault/"lock"/f"{profile_id}.lock.json"
    locks=sorted((vault/"lock").glob("*.lock.json"))
    if len(locks)!=1:raise RuntimeError(f"Expected one lock, found {len(locks)}")
    return locks[0]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--vault",required=True);ap.add_argument("--profile-id");args=ap.parse_args()
    vault=pathlib.Path(args.vault).resolve();lock_path=find_lock(vault,args.profile_id)
    lock=json.loads(lock_path.read_text(encoding="utf-8"));profile=str(lock["profile"])
    components=[]
    for group in ("artifacts","containers"):components.extend(component(r,group) for r in lock.get(group,[]) if r.get("path") or r.get("image"))
    doc={"bomFormat":"CycloneDX","specVersion":"1.6","serialNumber":"urn:uuid:"+str(uuid.uuid4()),"version":1,
         "metadata":{"timestamp":dt.datetime.now(dt.timezone.utc).isoformat(),
                     "component":{"type":"application","name":"ENDWORLD "+profile.upper(),"version":lock.get("generated_at","frozen")}},
         "components":components}
    out=vault/"lock"/f"{profile}.cdx.json";out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Wrote {out} with {len(components)} components")
if __name__=="__main__":main()
