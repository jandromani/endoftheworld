#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, os, pathlib, shutil, subprocess, tarfile

def sha256_path(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(8*1024*1024),b""):h.update(c)
    return h.hexdigest()

def sha256_bytes(data):return hashlib.sha256(data).hexdigest()

def safe_rel(value):
    p=pathlib.PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:raise RuntimeError("unsafe bundle path: "+value)
    return p

def load_lock(vault,profile):
    p=vault/"lock"/f"{profile}.lock.json"
    return p,json.loads(p.read_text(encoding="utf-8"))

def recs(lock):
    return {str(r.get("id")):r for group in ("artifacts","containers") for r in lock.get(group,[]) if r.get("id")}

def add_bytes(tf,name,data):
    i=tarfile.TarInfo(name);i.size=len(data);i.mtime=0;i.uid=i.gid=0;i.uname=i.gname=""
    tf.addfile(i,io.BytesIO(data))

def create(base_vault,new_vault,profile,out):
    base_path,base=load_lock(base_vault,profile);new_path,new=load_lock(new_vault,profile)
    br,nr=recs(base),recs(new);changed=[]
    for rid,rec in nr.items():
        rel=rec.get("path");digest=rec.get("sha256")
        if not rel or not digest:continue
        old=br.get(rid)
        if old and old.get("sha256")==digest and old.get("path")==rel:continue
        p=new_vault/safe_rel(str(rel))
        if not p.is_file():raise FileNotFoundError(p)
        if sha256_path(p)!=digest:raise RuntimeError("new vault hash mismatch: "+str(p))
        changed.append({"id":rid,"path":str(rel),"sha256":digest,"bytes":p.stat().st_size})
    lock_bytes=new_path.read_bytes();bom=new_vault/"lock"/f"{profile}.cdx.json";bom_bytes=bom.read_bytes() if bom.exists() else b""
    manifest={"schema":1,"profile":profile,"base_lock_sha256":sha256_path(base_path),"new_lock_sha256":sha256_bytes(lock_bytes),
              "bom_sha256":sha256_bytes(bom_bytes) if bom_bytes else None,
              "files":changed,"removed_ids":sorted(set(br)-set(nr))}
    out.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(out,"w") as tf:
        add_bytes(tf,"bundle-manifest.json",(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode())
        add_bytes(tf,f"metadata/{profile}.lock.json",lock_bytes)
        if bom_bytes:add_bytes(tf,f"metadata/{profile}.cdx.json",bom_bytes)
        for rec in changed:
            p=new_vault/safe_rel(rec["path"])
            info=tf.gettarinfo(str(p),arcname="payload/"+rec["path"]);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=""
            with p.open("rb") as f:tf.addfile(info,f)
    print(json.dumps({"bundle":str(out),"changed":len(changed),"bytes":out.stat().st_size},indent=2))

def read_manifest(tf):
    f=tf.extractfile("bundle-manifest.json")
    if not f:raise RuntimeError("bundle manifest missing")
    m=json.load(f)
    if m.get("schema")!=1:raise RuntimeError("unsupported bundle schema")
    return m

def verify(bundle):
    with tarfile.open(bundle,"r") as tf:
        m=read_manifest(tf)
        for rec in m.get("files",[]):
            safe_rel(rec["path"]);src=tf.extractfile("payload/"+rec["path"])
            if not src:raise RuntimeError("payload missing: "+rec["path"])
            h=hashlib.sha256();n=0
            for c in iter(lambda:src.read(8*1024*1024),b""):h.update(c);n+=len(c)
            if h.hexdigest()!=rec["sha256"] or n!=int(rec["bytes"]):raise RuntimeError("payload verification failed: "+rec["path"])
        lock=tf.extractfile(f"metadata/{m['profile']}.lock.json")
        if not lock or sha256_bytes(lock.read())!=m["new_lock_sha256"]:raise RuntimeError("new lock verification failed")
    print("VERIFIED");return m

def sign(bundle,key,sig):
    subprocess.run(["openssl","dgst","-sha256","-sign",str(key),"-out",str(sig),str(bundle)],check=True)
    print(sig)

def verify_signature(bundle,public,sig):
    subprocess.run(["openssl","dgst","-sha256","-verify",str(public),"-signature",str(sig),str(bundle)],check=True)
    print("SIGNATURE VERIFIED")

def apply(bundle,target,public=None,signature=None,require_signature=False):
    if require_signature or public or signature:
        if not public or not signature:raise RuntimeError("signed update requires both public key and signature")
        verify_signature(bundle,public,signature)
    m=verify(bundle);profile=m["profile"];lock_path=target/"lock"/f"{profile}.lock.json"
    if not lock_path.is_file():raise FileNotFoundError(lock_path)
    if sha256_path(lock_path)!=m["base_lock_sha256"]:raise RuntimeError("target vault is not the declared base generation")
    stage=target/".updates"/("stage-"+m["new_lock_sha256"][:12]);shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
    with tarfile.open(bundle,"r") as tf:
        for rec in m.get("files",[]):
            rel=safe_rel(rec["path"]);dst=stage/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            src=tf.extractfile("payload/"+rec["path"])
            with dst.open("wb") as f:shutil.copyfileobj(src,f)
            if sha256_path(dst)!=rec["sha256"]:raise RuntimeError("staged hash mismatch: "+str(dst))
        new_lock=tf.extractfile(f"metadata/{profile}.lock.json").read()
        try:
            bf=tf.extractfile(f"metadata/{profile}.cdx.json");new_bom=bf.read() if bf else None
        except KeyError:new_bom=None
    for rec in m.get("files",[]):
        rel=safe_rel(rec["path"]);src=stage/rel;dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.replace(src,dst)
    tmp=lock_path.with_suffix(".update");tmp.write_bytes(new_lock);os.replace(tmp,lock_path)
    if new_bom:
        bp=target/"lock"/f"{profile}.cdx.json";bt=bp.with_suffix(".update");bt.write_bytes(new_bom);os.replace(bt,bp)
    shutil.rmtree(stage,ignore_errors=True);print("APPLIED")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("create");c.add_argument("--base-vault",required=True);c.add_argument("--new-vault",required=True);c.add_argument("--profile",required=True);c.add_argument("--out",required=True)
    v=sub.add_parser("verify");v.add_argument("bundle")
    s=sub.add_parser("sign");s.add_argument("bundle");s.add_argument("--key",required=True);s.add_argument("--signature",required=True)
    vs=sub.add_parser("verify-signed");vs.add_argument("bundle");vs.add_argument("--public-key",required=True);vs.add_argument("--signature",required=True)
    a=sub.add_parser("apply");a.add_argument("bundle");a.add_argument("--target-vault",required=True);a.add_argument("--public-key");a.add_argument("--signature");a.add_argument("--require-signature",action="store_true")
    x=ap.parse_args()
    if x.cmd=="create":create(pathlib.Path(x.base_vault).resolve(),pathlib.Path(x.new_vault).resolve(),x.profile,pathlib.Path(x.out).resolve())
    elif x.cmd=="verify":verify(pathlib.Path(x.bundle).resolve())
    elif x.cmd=="sign":sign(pathlib.Path(x.bundle).resolve(),pathlib.Path(x.key).resolve(),pathlib.Path(x.signature).resolve())
    elif x.cmd=="verify-signed":verify_signature(pathlib.Path(x.bundle).resolve(),pathlib.Path(x.public_key).resolve(),pathlib.Path(x.signature).resolve())
    else:apply(pathlib.Path(x.bundle).resolve(),pathlib.Path(x.target_vault).resolve(),
               pathlib.Path(x.public_key).resolve() if x.public_key else None,
               pathlib.Path(x.signature).resolve() if x.signature else None,
               x.require_signature)
    return 0
if __name__=="__main__":raise SystemExit(main())
