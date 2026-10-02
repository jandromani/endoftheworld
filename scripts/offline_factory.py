#!/usr/bin/env python3
"""Create/verify the connected-builder cache required to rebuild THE ARK without WAN."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, subprocess, tempfile
import yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()

def packages(manifest,profile):
    data=yaml.safe_load(manifest.read_text(encoding="utf-8"))
    rows=list(data["base"])
    if profile in ("nomad","civilization"): rows+=data.get("nomad",[])
    if profile=="civilization": rows+=data.get("civilization",[])
    return sorted(dict.fromkeys(rows))

def create(out,suite,mirror,manifest,profile):
    if os.geteuid()!=0:raise SystemExit("offline-factory create must run as root")
    for tool in ("debootstrap","chroot","dpkg-scanpackages"):
        if not shutil.which(tool):raise SystemExit(f"{tool} missing")
    out.mkdir(parents=True,exist_ok=True)
    boot=out/f"debootstrap-{suite}-amd64.tar"
    aptdir=out/"apt";aptdir.mkdir(exist_ok=True)
    pkgs=packages(manifest,profile)
    with tempfile.TemporaryDirectory(prefix="ark-factory-") as td:
        root=pathlib.Path(td)/"root";root.mkdir()
        if not boot.is_file():
            subprocess.run(["debootstrap","--arch=amd64","--variant=minbase",
                            f"--make-tarball={boot}",suite,str(root),mirror],check=True)
        subprocess.run(["debootstrap","--arch=amd64","--variant=minbase",
                        f"--unpack-tarball={boot}",suite,str(root),mirror],check=True)
        (root/"etc/apt/sources.list").write_text(
            f"deb {mirror} {suite} main contrib non-free-firmware\n"
            f"deb {mirror} {suite}-updates main contrib non-free-firmware\n"
            f"deb http://security.debian.org/debian-security {suite}-security main contrib non-free-firmware\n",
            encoding="utf-8")
        shutil.copy2("/etc/resolv.conf",root/"etc/resolv.conf")
        subprocess.run(["chroot",str(root),"apt-get","update"],check=True)
        subprocess.run(["chroot",str(root),"apt-get","-y","--download-only","--no-install-recommends","install",*pkgs],check=True)
        for p in (root/"var/cache/apt/archives").glob("*.deb"): shutil.copy2(p,aptdir/p.name)
    with (aptdir/"Packages").open("wb") as f:
        subprocess.run(["dpkg-scanpackages",".","/dev/null"],cwd=aptdir,stdout=f,check=True)
    subprocess.run(["gzip","-n","-f","-k",str(aptdir/"Packages")],check=True)
    rows=[]
    for p in sorted(x for x in out.rglob("*") if x.is_file() and x.name!="factory-manifest.json"):
        rows.append({"path":str(p.relative_to(out)),"bytes":p.stat().st_size,"sha256":sha(p)})
    data={"schema":1,"protocol":"ark-offline-factory-v1","suite":suite,"arch":"amd64",
          "profile":profile,"packages":pkgs,"files":rows}
    (out/"factory-manifest.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"factory":str(out),"files":len(rows),"packages":len(pkgs)},indent=2))

def verify(root):
    m=root/"factory-manifest.json";data=json.loads(m.read_text(encoding="utf-8"))
    if data.get("protocol")!="ark-offline-factory-v1":raise SystemExit("unsupported factory manifest")
    errors=[]
    for rec in data.get("files",[]):
        p=root/rec["path"]
        if not p.is_file():errors.append("missing "+rec["path"]);continue
        if p.stat().st_size!=int(rec["bytes"]) or sha(p)!=rec["sha256"]:errors.append("mismatch "+rec["path"])
    if errors:raise SystemExit("\n".join(errors))
    print("THE_ARK_OFFLINE_FACTORY=VERIFIED")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("create");c.add_argument("--out",required=True);c.add_argument("--suite",default="trixie")
    c.add_argument("--mirror",default="http://deb.debian.org/debian");c.add_argument("--profile",choices=["nano","family","nomad","civilization"],default="nano")
    c.add_argument("--manifest",default=str(ROOT/"manifests/appliance-os-packages.yml"))
    v=sub.add_parser("verify");v.add_argument("--factory",required=True)
    a=ap.parse_args()
    if a.cmd=="create":create(pathlib.Path(a.out).resolve(),a.suite,a.mirror,pathlib.Path(a.manifest),a.profile)
    else:verify(pathlib.Path(a.factory).resolve())
    return 0
if __name__=="__main__":raise SystemExit(main())
