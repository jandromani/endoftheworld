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
          "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"files":rows,
          "boot_trust":{"strategy":"debian-shim-signed","fallback_efi":"EFI/BOOT/BOOTX64.EFI",
                        "signed_grub":"EFI/BOOT/grubx64.efi"}}
    pub=os.getenv("ENDWORLD_SIGNING_PUBLIC_KEY")
    if pub and pathlib.Path(pub).is_file():
        der=subprocess.check_output(["openssl","pkey","-pubin","-in",pub,"-outform","DER"])
        data["release_key_sha256"]=hashlib.sha256(der).hexdigest()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(out)

def fingerprint(public):
    der=subprocess.check_output(["openssl","pkey","-pubin","-in",str(public),"-outform","DER"])
    fp=hashlib.sha256(der).hexdigest()
    print(fp)
    return fp

def verify_materials(manifest,image,lock,bom):
    data=json.loads(manifest.read_text(encoding="utf-8"))
    supplied={"image":image,"lock":lock,"bom":bom}
    rows={x.get("role"):x for x in data.get("files",[])}
    for role,path in supplied.items():
        rec=rows.get(role)
        if not rec:raise RuntimeError(f"manifest role missing: {role}")
        if not path.is_file():raise FileNotFoundError(path)
        if path.stat().st_size!=int(rec.get("bytes") or -1):raise RuntimeError(f"{role} byte-size mismatch")
        if digest(path)!=rec.get("sha256"):raise RuntimeError(f"{role} SHA-256 mismatch")
    print("MATERIALS VERIFIED")

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
    f=sub.add_parser("fingerprint");f.add_argument("--public-key",required=True)
    m=sub.add_parser("verify-materials");m.add_argument("--manifest",required=True);m.add_argument("--image",required=True);m.add_argument("--lock",required=True);m.add_argument("--bom",required=True)
    a=ap.parse_args()
    if a.cmd=="keygen":keygen(pathlib.Path(a.private),pathlib.Path(a.public),a.bits)
    elif a.cmd=="create":create(a.profile,pathlib.Path(a.image).resolve(),pathlib.Path(a.vault).resolve(),pathlib.Path(a.out).resolve())
    elif a.cmd=="sign":sign(pathlib.Path(a.file),pathlib.Path(a.key),pathlib.Path(a.signature))
    elif a.cmd=="verify":verify(pathlib.Path(a.file),pathlib.Path(a.public_key),pathlib.Path(a.signature))
    elif a.cmd=="fingerprint":fingerprint(pathlib.Path(a.public_key))
    else:verify_materials(pathlib.Path(a.manifest),pathlib.Path(a.image),pathlib.Path(a.lock),pathlib.Path(a.bom))
    return 0
if __name__=="__main__":raise SystemExit(main())
