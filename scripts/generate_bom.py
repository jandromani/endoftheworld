#!/usr/bin/env python3
"""Generate an artifact-level CycloneDX BOM from an ENDWORLD frozen lock."""
from __future__ import annotations
import argparse, datetime as dt, json, pathlib, uuid

def component(rec: dict, kind: str) -> dict:
    name=rec.get("id") or rec.get("filename") or rec.get("image") or "unknown"
    version=rec.get("release_tag") or rec.get("ref") or "frozen"
    c={"type":"container" if kind=="containers" else "file","name":name,"version":str(version),
       "bom-ref":"urn:endworld:"+name}
    hashes=[]
    if rec.get("sha256"):hashes.append({"alg":"SHA-256","content":rec["sha256"]})
    if hashes:c["hashes"]=hashes
    props=[]
    for k in ("family","kind","repo","url","resolved_url","path","bytes","upstream_sha256","upstream_checksum_verified"):
        if rec.get(k) is not None:props.append({"name":"endworld:"+k,"value":str(rec[k])})
    if rec.get("repo"):c["externalReferences"]=[{"type":"vcs","url":"https://github.com/"+rec["repo"]}]
    if props:c["properties"]=props
    return c

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--vault",default="vault/nano");args=ap.parse_args()
    vault=pathlib.Path(args.vault).resolve();lock_path=vault/"lock/nano.lock.json"
    lock=json.loads(lock_path.read_text(encoding="utf-8"))
    components=[]
    for group in ("artifacts","containers"):
        components.extend(component(r,group) for r in lock.get(group,[]) if r.get("path") or r.get("image"))
    doc={"bomFormat":"CycloneDX","specVersion":"1.6","serialNumber":"urn:uuid:"+str(uuid.uuid4()),"version":1,
         "metadata":{"timestamp":dt.datetime.now(dt.timezone.utc).isoformat(),
                     "component":{"type":"application","name":"ENDWORLD "+lock.get("profile","nano").upper(),
                                  "version":lock.get("generated_at","frozen")}},
         "components":components}
    out=vault/"lock/nano.cdx.json";out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Wrote {out} with {len(components)} components")
if __name__=="__main__":main()
