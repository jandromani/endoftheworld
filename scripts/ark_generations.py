#!/usr/bin/env python3
"""Generation, cold-storage export and rollback layer above ark_mesh."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, io, json, os, pathlib, shutil, tarfile, tempfile, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ark_mesh

def sha(p):return ark_mesh.sha256_file(p)
def add(tf,name,path):
    info=tf.gettarinfo(str(path),arcname=name);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=""
    with path.open("rb") as f:tf.addfile(info,f)
def add_bytes(tf,name,data):
    i=tarfile.TarInfo(name);i.size=len(data);i.mtime=0;i.uid=i.gid=0;i.uname=i.gname="";tf.addfile(i,io.BytesIO(data))

def create_generation(inventory,root,state_archive=None,release=None,label=None):
    inv=ark_mesh.load_inventory(inventory)
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    gid=stamp+"-"+sha(inventory)[:12]
    d=root/gid;d.mkdir(parents=True,exist_ok=False)
    shutil.copy2(inventory,d/"inventory.json")
    files={"inventory.json":sha(d/"inventory.json")}
    if state_archive:
        shutil.copy2(state_archive,d/"state.tar");files["state.tar"]=sha(d/"state.tar")
    if release:
        shutil.copy2(release,d/"release.json");files["release.json"]=sha(d/"release.json")
    data={"schema":1,"protocol":"ark-generation-v1","generation":gid,"created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
          "profile":inv["profile"],"label":label,"inventory_sha256":sha(d/"inventory.json"),"files":files}
    (d/"generation.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"generation":gid,"path":str(d)},indent=2));return d

def cold_export(generation,store,out):
    meta=json.loads((generation/"generation.json").read_text(encoding="utf-8"))
    inv=ark_mesh.load_inventory(generation/"inventory.json")
    chunks={}
    for rec in inv.get("items",[]):
        for c in rec.get("chunks",[]):chunks[c["sha256"]]=int(c["bytes"])
    cold={"schema":1,"protocol":"ark-cold-v1","generation":meta["generation"],"profile":inv["profile"],
          "inventory_sha256":sha(generation/"inventory.json"),"chunks":[{"sha256":h,"bytes":n} for h,n in sorted(chunks.items())],
          "metadata":{}}
    for name in ("generation.json","state.tar","release.json"):
        p=generation/name
        if p.is_file():cold["metadata"][name]={"sha256":sha(p),"bytes":p.stat().st_size}
    out.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(out,"w") as tf:
        add_bytes(tf,"cold-manifest.json",(json.dumps(cold,indent=2,sort_keys=True)+"\n").encode())
        for name in cold["metadata"]:add(tf,name,generation/name)
        add(tf,"inventory.json",generation/"inventory.json")
        for h,n in chunks.items():
            p=ark_mesh.chunk_path(store,h)
            if not p.is_file() or p.stat().st_size!=n or sha(p)!=h:raise ark_mesh.MeshError("missing/corrupt chunk "+h)
            add(tf,f"objects/sha256/{h[:2]}/{h[2:]}",p)
    print(json.dumps({"cold_export":str(out),"bytes":out.stat().st_size,"chunks":len(chunks)},indent=2))

def verify(bundle):
    with tarfile.open(bundle,"r") as tf:
        f=tf.extractfile("cold-manifest.json")
        if not f:raise ark_mesh.MeshError("cold-manifest.json missing")
        m=json.load(f)
        if m.get("protocol")!="ark-cold-v1":raise ark_mesh.MeshError("unsupported cold archive")
        inv=tf.extractfile("inventory.json")
        if not inv:raise ark_mesh.MeshError("inventory missing")
        raw=inv.read()
        if hashlib.sha256(raw).hexdigest()!=m["inventory_sha256"]:raise ark_mesh.MeshError("inventory hash mismatch")
        for rec in m.get("chunks",[]):
            h=rec["sha256"];n=int(rec["bytes"]);o=tf.extractfile(f"objects/sha256/{h[:2]}/{h[2:]}")
            if not o:raise ark_mesh.MeshError("chunk missing "+h)
            data=o.read()
            if len(data)!=n or hashlib.sha256(data).hexdigest()!=h:raise ark_mesh.MeshError("chunk mismatch "+h)
        for name,rec in (m.get("metadata") or {}).items():
            o=tf.extractfile(name)
            if not o:raise ark_mesh.MeshError("metadata missing "+name)
            data=o.read()
            if len(data)!=int(rec["bytes"]) or hashlib.sha256(data).hexdigest()!=rec["sha256"]:raise ark_mesh.MeshError("metadata mismatch "+name)
    print("THE_ARK_COLD_STORAGE=VERIFIED");return m

def restore_bundle(bundle,store,target_vault,state=False):
    verify(bundle)
    with tempfile.TemporaryDirectory(prefix="ark-cold-") as td:
        td=pathlib.Path(td)
        with tarfile.open(bundle,"r") as tf:tf.extractall(td,filter="data")
        inv=ark_mesh.load_inventory(td/"inventory.json")
        for rec in inv.get("items",[]):
            for c in rec.get("chunks",[]):
                h=c["sha256"];src=td/"objects/sha256"/h[:2]/h[2:]
                ark_mesh.ensure_chunk(store,h,src.read_bytes())
        ark_mesh.restore(td/"inventory.json",store,target_vault)
        if state and (td/"state.tar").is_file():ark_mesh.state_import(td/"state.tar",target_vault,True)
    print("THE_ARK_COLD_RESTORE=PASS")

def activate(generation,state_root):
    d=pathlib.Path(generation);meta=json.loads((d/"generation.json").read_text(encoding="utf-8"))
    state_root.mkdir(parents=True,exist_ok=True);p=state_root/"active-generation.json"
    history=[]
    if p.is_file():
        try:history=json.loads(p.read_text()).get("history",[])
        except Exception:history=[]
    history.append({"generation":meta["generation"],"path":str(d),"activated_utc":dt.datetime.now(dt.timezone.utc).isoformat()})
    p.write_text(json.dumps({"active":meta["generation"],"path":str(d),"history":history},indent=2)+"\n")
    print(meta["generation"])

def rollback(state_root):
    p=state_root/"active-generation.json";data=json.loads(p.read_text());h=data.get("history",[])
    if len(h)<2:raise SystemExit("no previous generation")
    h.pop();prev=h[-1];p.write_text(json.dumps({"active":prev["generation"],"path":prev["path"],"history":h},indent=2)+"\n")
    print(json.dumps(prev,indent=2))

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("create");c.add_argument("--inventory",required=True);c.add_argument("--root",required=True);c.add_argument("--state-archive");c.add_argument("--release");c.add_argument("--label")
    e=sub.add_parser("cold-export");e.add_argument("--generation",required=True);e.add_argument("--store",required=True);e.add_argument("--out",required=True)
    v=sub.add_parser("cold-verify");v.add_argument("bundle")
    r=sub.add_parser("restore");r.add_argument("bundle");r.add_argument("--store",required=True);r.add_argument("--target-vault",required=True);r.add_argument("--state",action="store_true")
    a=sub.add_parser("activate");a.add_argument("--generation",required=True);a.add_argument("--state-root",default="/srv/endworld/state/mesh/generations")
    rb=sub.add_parser("rollback");rb.add_argument("--state-root",default="/srv/endworld/state/mesh/generations")
    x=ap.parse_args()
    if x.cmd=="create":create_generation(pathlib.Path(x.inventory),pathlib.Path(x.root),pathlib.Path(x.state_archive) if x.state_archive else None,pathlib.Path(x.release) if x.release else None,x.label)
    elif x.cmd=="cold-export":cold_export(pathlib.Path(x.generation),pathlib.Path(x.store),pathlib.Path(x.out))
    elif x.cmd=="cold-verify":verify(pathlib.Path(x.bundle))
    elif x.cmd=="restore":restore_bundle(pathlib.Path(x.bundle),pathlib.Path(x.store),pathlib.Path(x.target_vault),x.state)
    elif x.cmd=="activate":activate(x.generation,pathlib.Path(x.state_root))
    else:rollback(pathlib.Path(x.state_root))
    return 0
if __name__=="__main__":raise SystemExit(main())
