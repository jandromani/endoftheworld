#!/usr/bin/env python3
"""Create and verify distributable THE ARK release bundles.

The private key is supplied explicitly and is never generated or stored by this
command. A release bundle binds the distributable image, frozen lock, SBOM,
Git revision and public-key fingerprint.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, pathlib, re, shutil, subprocess, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
CHUNK=8*1024*1024

def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(CHUNK),b""):h.update(b)
    return h.hexdigest()

def pub_fingerprint(path:pathlib.Path)->str:
    der=subprocess.check_output(["openssl","pkey","-pubin","-in",str(path),"-outform","DER"])
    return hashlib.sha256(der).hexdigest()

def sign(path,key,sig):
    subprocess.run(["openssl","dgst","-sha256","-sign",str(key),"-out",str(sig),str(path)],check=True)

def verify_sig(path,public,sig):
    subprocess.run(["openssl","dgst","-sha256","-verify",str(public),"-signature",str(sig),str(path)],check=True,
                   stdout=subprocess.DEVNULL)

def git_commit():
    try:return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except Exception:return "unknown"

def copy_or_compress(image:pathlib.Path,out:pathlib.Path,compress:bool):
    if compress:
        if not shutil.which("zstd"):raise SystemExit("zstd is required for compressed releases")
        subprocess.run(["zstd","-T0","-19","--long=27","-f",str(image),"-o",str(out)],check=True)
    else:
        shutil.copy2(image,out)

def create(profile,version,image,vault,outdir,private,public,compress):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}",version):
        raise SystemExit("invalid version")
    lock=vault/"lock"/f"{profile}.lock.json"
    bom=vault/"lock"/f"{profile}.cdx.json"
    for p in (image,lock,bom,private,public):
        if not p.is_file():raise FileNotFoundError(p)
    outdir.mkdir(parents=True,exist_ok=True)
    stem=f"the-ark-{profile}-{version}-amd64"
    dist=outdir/(stem+".img.zst" if compress else stem+".img")
    copy_or_compress(image,dist,compress)
    lock_out=outdir/f"{stem}.lock.json";bom_out=outdir/f"{stem}.cdx.json"
    shutil.copy2(lock,lock_out);shutil.copy2(bom,bom_out)
    public_out=outdir/"THE-ARK-release-public.pem";shutil.copy2(public,public_out)
    files=[]
    for role,p in (("distribution",dist),("lock",lock_out),("sbom",bom_out),("public_key",public_out)):
        files.append({"role":role,"file":p.name,"bytes":p.stat().st_size,"sha256":digest(p)})
    manifest=outdir/f"{stem}.release.json"
    data={
        "schema":1,"protocol":"ark-public-release-v1","project":"THE ARK","profile":profile,"version":version,
        "architecture":"amd64","created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit":git_commit(),"release_key_sha256":pub_fingerprint(public_out),
        "distribution":{"compressed":compress,"format":"raw-disk-image","compression":"zstd" if compress else None},
        "files":files,
        "field_proof":{"claimed":False,"note":"Physical field proof must be established separately from release packaging."},
    }
    manifest.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    sig=manifest.with_suffix(".json.sig");sign(manifest,private,sig)
    sums=outdir/"SHA256SUMS"
    rows=[f"{digest(p)}  {p.name}" for p in (dist,lock_out,bom_out,public_out,manifest,sig)]
    sums.write_text("\n".join(rows)+"\n",encoding="utf-8")
    readme=outdir/"VERIFY.txt"
    readme.write_text(
        "THE ARK RELEASE VERIFICATION\n"
        "============================\n\n"
        f"Profile: {profile}\nVersion: {version}\n"
        f"Release key SHA-256 fingerprint: {data['release_key_sha256']}\n\n"
        "1. Compare the public-key fingerprint through an independent trusted channel.\n"
        "2. Run: python scripts/release_bundle.py verify --dir <release-dir>\n"
        "3. Only then decompress/flash the image.\n"
        "4. Physical field-proof is a separate evidence gate.\n",encoding="utf-8")
    print(json.dumps({"release_dir":str(outdir),"manifest":manifest.name,"distribution":dist.name,
                      "release_key_sha256":data["release_key_sha256"]},indent=2))

def verify(directory:pathlib.Path,public_override:pathlib.Path|None=None):
    manifests=sorted(directory.glob("*.release.json"))
    if len(manifests)!=1:raise SystemExit("release directory must contain exactly one *.release.json")
    manifest=manifests[0];sig=manifest.with_suffix(".json.sig")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("protocol")!="ark-public-release-v1":raise SystemExit("unsupported release protocol")
    public=public_override or directory/"THE-ARK-release-public.pem"
    for p in (sig,public):
        if not p.is_file():raise FileNotFoundError(p)
    if pub_fingerprint(public)!=data.get("release_key_sha256"):raise SystemExit("public key fingerprint mismatch")
    verify_sig(manifest,public,sig)
    checked=[]
    for rec in data.get("files",[]):
        p=directory/str(rec.get("file") or "")
        if not p.is_file():raise FileNotFoundError(p)
        if p.stat().st_size!=int(rec.get("bytes") or -1):raise SystemExit(f"size mismatch: {p.name}")
        actual=digest(p)
        if actual!=rec.get("sha256"):raise SystemExit(f"SHA-256 mismatch: {p.name}")
        checked.append(p.name)
    print(json.dumps({"ok":True,"protocol":data["protocol"],"profile":data.get("profile"),
                      "version":data.get("version"),"verified_files":checked,
                      "release_key_sha256":data.get("release_key_sha256")},indent=2))
    print("THE_ARK_PUBLIC_RELEASE=VERIFIED")

def main():
    ap=argparse.ArgumentParser(prog="ark-release")
    sub=ap.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("create");c.add_argument("--profile",required=True);c.add_argument("--version",required=True)
    c.add_argument("--image",required=True);c.add_argument("--vault",required=True);c.add_argument("--out",required=True)
    c.add_argument("--private-key",required=True);c.add_argument("--public-key",required=True)
    c.add_argument("--no-compress",action="store_true")
    v=sub.add_parser("verify");v.add_argument("--dir",required=True);v.add_argument("--public-key")
    a=ap.parse_args()
    if a.cmd=="create":
        create(a.profile,a.version,pathlib.Path(a.image).resolve(),pathlib.Path(a.vault).resolve(),
               pathlib.Path(a.out).resolve(),pathlib.Path(a.private_key).resolve(),
               pathlib.Path(a.public_key).resolve(),not a.no_compress)
    else:
        verify(pathlib.Path(a.dir).resolve(),pathlib.Path(a.public_key).resolve() if a.public_key else None)
    return 0
if __name__=="__main__":raise SystemExit(main())
