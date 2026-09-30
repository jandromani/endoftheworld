#!/usr/bin/env python3
"""Materialize package ecosystems into immutable CIVILIZATION snapshot TARs.

The connected builder resolves and downloads package closure. Downloaded package
code is never executed: apt uses apt-get download, pip uses download, and npm
uses --ignore-scripts. Each ecosystem is packed into one deterministic TAR and
recorded in the profile lock for normal SHA-256/BOM verification.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tarfile, tempfile
import yaml

class SnapshotError(RuntimeError): pass

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def validate_manifest(data, profile_id):
    if data.get("schema")!=1: raise SnapshotError("unsupported package manifest schema")
    if data.get("profile")!=profile_id: raise SnapshotError("package manifest/profile mismatch")
    snaps=data.get("snapshots")
    if not isinstance(snaps,dict) or not snaps: raise SnapshotError("no package snapshots declared")
    for name,spec in snaps.items():
        pkgs=spec.get("packages") if isinstance(spec,dict) else None
        if not isinstance(pkgs,list) or not pkgs or any(not isinstance(x,str) or not x.strip() for x in pkgs):
            raise SnapshotError(f"{name}: packages must be a non-empty string list")
    return snaps

def deterministic_tar(source:pathlib.Path, output:pathlib.Path):
    output.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(output,"w") as tf:
        for p in sorted(source.rglob("*")):
            if not p.is_file(): continue
            rel=p.relative_to(source)
            info=tf.gettarinfo(str(p),arcname=str(rel))
            info.uid=info.gid=0; info.uname=info.gname=""; info.mtime=0
            with p.open("rb") as f: tf.addfile(info,f)

def apt_snapshot(pkgs, dest):
    for tool in ("apt-cache","apt-get"):
        if not shutil.which(tool): raise SnapshotError(f"{tool} missing")
    out=subprocess.check_output(["apt-cache","depends","--recurse","--no-recommends","--no-suggests","--no-conflicts","--no-breaks","--no-replaces","--no-enhances",*pkgs],text=True,stderr=subprocess.STDOUT)
    deps=set(pkgs)
    for line in out.splitlines():
        m=re.match(r"\s*(?:Pre)?Depends:\s*([A-Za-z0-9.+:-]+)",line)
        if m and not m.group(1).startswith("<"): deps.add(m.group(1))
    subprocess.run(["apt-get","download",*sorted(deps)],cwd=dest,check=True)

def pypi_snapshot(pkgs,dest):
    subprocess.run([sys.executable,"-m","pip","download","--only-binary=:all:","--dest",str(dest),*pkgs],check=True)

def npm_snapshot(pkgs,dest):
    if not shutil.which("npm"): raise SnapshotError("npm missing")
    cache=dest/"cache"; work=dest/"work"; work.mkdir(parents=True,exist_ok=True)
    subprocess.run(["npm","install","--ignore-scripts","--no-audit","--no-fund","--cache",str(cache),"--prefix",str(work),*pkgs],check=True)
    lock=work/"package-lock.json"
    if lock.exists(): shutil.copy2(lock,dest/"package-lock.json")
    shutil.rmtree(work,ignore_errors=True)

def upsert(lock,rec):
    items=lock.setdefault("artifacts",[])
    for i,x in enumerate(items):
        if x.get("id")==rec["id"]: items[i]=rec; return
    items.append(rec)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--profile",required=True); ap.add_argument("--vault",required=True)
    ap.add_argument("--manifest",default="manifests/civilization-packages.yml")
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    profile=yaml.safe_load(pathlib.Path(args.profile).read_text(encoding="utf-8"))
    pid=str(profile["profile"]["id"])
    data=yaml.safe_load(pathlib.Path(args.manifest).read_text(encoding="utf-8"))
    snaps=validate_manifest(data,pid)
    if args.dry_run:
        print(json.dumps({"profile":pid,"snapshots":{k:len(v["packages"]) for k,v in snaps.items()},"ok":True},indent=2)); return 0
    vault=pathlib.Path(args.vault).resolve(); lock_path=vault/"lock"/f"{pid}.lock.json"
    if not lock_path.exists(): raise SnapshotError(f"acquire {pid} first; lock missing")
    lock=json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("profile")!=pid: raise SnapshotError("lock/profile mismatch")
    runners={"apt":apt_snapshot,"pypi":pypi_snapshot,"npm":npm_snapshot}
    with tempfile.TemporaryDirectory(prefix="endworld-packages-",dir=os.getenv("ENDWORLD_BUILD_TMP")) as td:
        base=pathlib.Path(td)
        for name,spec in snaps.items():
            if name not in runners: raise SnapshotError(f"unsupported ecosystem: {name}")
            src=base/name; src.mkdir()
            print(f"Snapshotting {name} ({len(spec['packages'])} seeds)...")
            runners[name](spec["packages"],src)
            out=vault/"packages"/f"{name}.snapshot.tar"
            deterministic_tar(src,out)
            upsert(lock,{"id":f"civilization-{name}-snapshot","family":"packages","kind":"snapshot","required":bool(spec.get("required",False)),"path":str(out.relative_to(vault)),"filename":out.name,"bytes":out.stat().st_size,"sha256":sha256_file(out),"status":"frozen","seed_packages":spec["packages"]})
    total=0
    for group in ("artifacts","containers"):
        for rec in lock.get(group,[]):
            rel=rec.get("path")
            if rel and (vault/rel).is_file(): total+=(vault/rel).stat().st_size
    usable=int(lock["target_bytes"])-int(lock["reserve_bytes"])
    if total>usable: raise SnapshotError(f"package snapshots exceed usable profile budget: {total} > {usable}")
    lock["payload_bytes"]=total; lock["package_snapshots"]=sorted(snaps)
    tmp=lock_path.with_suffix(".tmp"); tmp.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); os.replace(tmp,lock_path)
    print(f"CIVILIZATION package snapshots frozen; payload {total} / {usable} bytes")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (SnapshotError,subprocess.CalledProcessError,OSError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise SystemExit(2)
