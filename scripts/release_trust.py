#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, pathlib, subprocess

ROOT=pathlib.Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def display_path(path):
    try:return str(path.resolve().relative_to(ROOT))
    except ValueError:return path.name

def keygen(private,public,bits):
    private.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["openssl","genpkey","-algorithm","RSA","-pkeyopt",f"rsa_keygen_bits:{bits}","-out",str(private)],check=True)
    os.chmod(private,0o600)
    subprocess.run(["openssl","pkey","-in",str(private),"-pubout","-out",str(public)],check=True)

def create(profile,image,vault,out):
    lock=vault/"lock"/f"{profile}.lock.json"
    bom=vault/"lock"/f"{profile}.cdx.json"
    for p in (image,lock,bom):
        if not p.is_file():raise FileNotFoundError(p)
    try:commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except Exception:commit="unknown"
    rows=[]
    for role,p in (("image",image),("lock",lock),("bom",bom)):
        rows.append({"role":role,"path":display_path(p),"bytes":p.stat().st_size,"sha256":digest(p)})
    data={"schema":1,"project":"THE ARK","profile":profile,"git_commit":commit,
          "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"files":rows}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(out)

def sign(file,key,sig):
    subprocess.run(["openssl","dgst","-sha256","-sign",str(key),"-out",str(sig),str(file)],check=True)
    print(sig)

def verify(file,public,sig):
    subprocess.run(["openssl","dgst","-sha256","-verify",str(public),"-signature",str(sig),str(file)],check=True)
    print("VERIFIED")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    k=sub.add_parser("keygen");k.add_argument("--private",required=True);k.add_argument("--public",required=True);k.add_argument("--bits",type=int,default=3072)
    c=sub.add_parser("create");c.add_argument("--profile",required=True);c.add_argument("--image",required=True);c.add_argument("--vault",required=True);c.add_argument("--out",required=True)
    s=sub.add_parser("sign");s.add_argument("--file",required=True);s.add_argument("--key",required=True);s.add_argument("--signature",required=True)
    v=sub.add_parser("verify");v.add_argument("--file",required=True);v.add_argument("--public-key",required=True);v.add_argument("--signature",required=True)
    a=ap.parse_args()
    if a.cmd=="keygen":keygen(pathlib.Path(a.private),pathlib.Path(a.public),a.bits)
    elif a.cmd=="create":create(a.profile,pathlib.Path(a.image).resolve(),pathlib.Path(a.vault).resolve(),pathlib.Path(a.out).resolve())
    elif a.cmd=="sign":sign(pathlib.Path(a.file),pathlib.Path(a.key),pathlib.Path(a.signature))
    else:verify(pathlib.Path(a.file),pathlib.Path(a.public_key),pathlib.Path(a.signature))
    return 0
if __name__=="__main__":raise SystemExit(main())
