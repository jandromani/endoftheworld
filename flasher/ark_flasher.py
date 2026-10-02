#!/usr/bin/env python3
"""Cross-platform THE ARK public-release verifier/flasher.

This tool consumes an already-built signed release. It does not build an Ark.
Raw-disk flashing is destructive and requires an exact typed confirmation.
"""
from __future__ import annotations

import argparse, hashlib, json, os, pathlib, platform, plistlib, subprocess, sys, tempfile, threading
from dataclasses import dataclass

CHUNK=8*1024*1024

def sha256(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(CHUNK),b""):h.update(b)
    return h.hexdigest()

def key_fingerprint(public_pem:bytes)->str:
    from cryptography.hazmat.primitives import serialization
    key=serialization.load_pem_public_key(public_pem)
    der=key.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(der).hexdigest()

def load_release(directory:pathlib.Path):
    manifests=sorted(directory.glob("*.release.json"))
    if len(manifests)!=1:raise RuntimeError("release directory must contain exactly one *.release.json")
    manifest=manifests[0];data=json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("protocol")!="ark-public-release-v1":raise RuntimeError("unsupported release protocol")
    sig=manifest.with_suffix(".json.sig")
    pub=directory/"THE-ARK-release-public.pem"
    for p in (sig,pub):
        if not p.is_file():raise FileNotFoundError(p)
    return manifest,sig,pub,data

def verify_release(directory:pathlib.Path)->dict:
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    manifest,sig,pub,data=load_release(directory)
    public_bytes=pub.read_bytes()
    fp=key_fingerprint(public_bytes)
    if fp!=data.get("release_key_sha256"):raise RuntimeError("release key fingerprint mismatch")
    key=serialization.load_pem_public_key(public_bytes)
    key.verify(sig.read_bytes(),manifest.read_bytes(),padding.PKCS1v15(),hashes.SHA256())
    roles={}
    for rec in data.get("files",[]):
        p=directory/str(rec.get("file") or "")
        if not p.is_file():raise FileNotFoundError(p)
        if p.stat().st_size!=int(rec.get("bytes") or -1):raise RuntimeError("size mismatch: "+p.name)
        if sha256(p)!=rec.get("sha256"):raise RuntimeError("SHA-256 mismatch: "+p.name)
        roles[str(rec.get("role"))]=p
    if "distribution" not in roles:raise RuntimeError("distribution file missing")
    src=data.get("source_image") or {}
    if not src.get("sha256") or int(src.get("bytes") or 0)<=0:raise RuntimeError("raw source image identity missing")
    return {"manifest":manifest,"data":data,"roles":roles,"fingerprint":fp}

def mounted_tree(node):
    if any(x for x in (node.get("mountpoints") or []) if x):return True
    return any(mounted_tree(ch) for ch in (node.get("children") or []))

def linux_disks():
    raw=subprocess.check_output(["lsblk","--json","-b","-o","NAME,PATH,SIZE,MODEL,TYPE,TRAN,RM,MOUNTPOINTS"],text=True)
    data=json.loads(raw)
    root=""
    try:
        src=subprocess.check_output(["findmnt","-n","-o","SOURCE","/"],text=True).strip()
        pk=subprocess.check_output(["lsblk","-no","PKNAME",src],text=True).strip()
        root="/dev/"+pk if pk else src
    except Exception:pass
    out=[]
    for d in data.get("blockdevices",[]):
        if d.get("type")!="disk":continue
        path=str(d.get("path") or "")
        out.append({"device":path,"size":int(d.get("size") or 0),"model":str(d.get("model") or "").strip(),
                    "bus":d.get("tran"),"system":bool(root and (path==root or root.startswith(path))),
                    "mounted":mounted_tree(d)})
    return out

def windows_disks():
    cmd=["powershell","-NoProfile","-Command",
         "Get-Disk | Select-Object Number,FriendlyName,Size,BusType,IsBoot,IsSystem,OperationalStatus | ConvertTo-Json -Compress"]
    raw=subprocess.check_output(cmd,text=True)
    data=json.loads(raw);rows=data if isinstance(data,list) else [data]
    return [{"device":r"\\.\PhysicalDrive"+str(x["Number"]),"disk_number":int(x["Number"]),
             "size":int(x.get("Size") or 0),"model":str(x.get("FriendlyName") or ""),
             "bus":str(x.get("BusType") or ""),"system":bool(x.get("IsBoot") or x.get("IsSystem")),"mounted":False}
            for x in rows]

def mac_disks():
    data=plistlib.loads(subprocess.check_output(["diskutil","list","-plist","physical"]))
    out=[]
    for row in data.get("AllDisksAndPartitions",[]):
        ident=row.get("DeviceIdentifier")
        if not ident:continue
        info=plistlib.loads(subprocess.check_output(["diskutil","info","-plist","/dev/"+ident]))
        out.append({"device":str(info.get("DeviceNode") or "/dev/"+ident),"size":int(info.get("TotalSize") or 0),
                    "model":str(info.get("MediaName") or info.get("DeviceModel") or ""),
                    "bus":str(info.get("BusProtocol") or ""),"system":bool(info.get("Internal",True)),
                    "mounted":False})
    return out

def list_disks():
    sysname=platform.system()
    if sysname=="Linux":return linux_disks()
    if sysname=="Windows":return windows_disks()
    if sysname=="Darwin":return mac_disks()
    raise RuntimeError("unsupported operating system: "+sysname)

def candidate(device):
    return next((x for x in list_disks() if x["device"]==device),None)

def preflight(device,raw_bytes):
    row=candidate(device)
    if not row:raise RuntimeError("target is not a current physical disk")
    if row.get("system"):raise RuntimeError("refusing system/internal boot disk")
    if row.get("mounted"):raise RuntimeError("refusing disk with mounted filesystems")
    if int(row.get("size") or 0)<raw_bytes:raise RuntimeError("target disk is too small")
    return row

def prepare_target(row):
    sysname=platform.system()
    if sysname=="Darwin":
        subprocess.run(["diskutil","unmountDisk",row["device"]],check=True)
        return row["device"].replace("/dev/disk","/dev/rdisk")
    if sysname=="Windows":
        n=row.get("disk_number")
        subprocess.run(["powershell","-NoProfile","-Command",f"Set-Disk -Number {int(n)} -IsOffline $true"],check=True)
    return row["device"]

def finish_target(row):
    if platform.system()=="Windows" and row.get("disk_number") is not None:
        subprocess.run(["powershell","-NoProfile","-Command",f"Set-Disk -Number {int(row['disk_number'])} -IsOffline $false"],check=False)

def chunks_from_distribution(path,compressed):
    if not compressed:
        with path.open("rb") as f:
            while True:
                b=f.read(CHUNK)
                if not b:break
                yield b
        return
    import zstandard as zstd
    with path.open("rb") as source:
        with zstd.ZstdDecompressor().stream_reader(source) as reader:
            while True:
                b=reader.read(CHUNK)
                if not b:break
                yield b

def write_stream(target,dist,compressed,expected_bytes,expected_sha,progress=None):
    h=hashlib.sha256();written=0
    fd=os.open(target,os.O_WRONLY)
    try:
        with os.fdopen(fd,"wb",buffering=0,closefd=False) as out:
            for b in chunks_from_distribution(dist,compressed):
                out.write(b);h.update(b);written+=len(b)
                if written>expected_bytes:raise RuntimeError("decompressed image exceeds signed byte count")
                if progress:progress(written,expected_bytes)
            out.flush()
        try:os.fsync(fd)
        except OSError:pass
    finally:
        os.close(fd)
    if written!=expected_bytes:raise RuntimeError(f"written byte count mismatch: {written} != {expected_bytes}")
    if h.hexdigest()!=expected_sha:raise RuntimeError("raw image SHA-256 mismatch after decompression/write")
    return {"bytes":written,"sha256":h.hexdigest()}

def flash_release(directory,device,confirmation,progress=None):
    verified=verify_release(directory)
    data=verified["data"];raw=data["source_image"];dist=verified["roles"]["distribution"]
    if confirmation!="ERASE "+device:raise RuntimeError("confirmation must be exactly: ERASE "+device)
    row=preflight(device,int(raw["bytes"]))
    target=prepare_target(row)
    try:
        result=write_stream(target,dist,bool((data.get("distribution") or {}).get("compressed")),
                            int(raw["bytes"]),str(raw["sha256"]),progress)
    finally:
        finish_target(row)
    result.update(device=device,release_key_sha256=verified["fingerprint"])
    return result

def selftest():
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.asymmetric import padding,rsa
    import zstandard as zstd
    with tempfile.TemporaryDirectory(prefix="ark-flasher-") as td:
        d=pathlib.Path(td);raw=d/"fixture.img";raw.write_bytes((b"THE-ARK-FLASHER-CI\n"*65536)[:1024*1024])
        comp=d/"fixture.img.zst"
        with raw.open("rb") as src,comp.open("wb") as dst:zstd.ZstdCompressor(level=3).copy_stream(src,dst)
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        pub=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        (d/"THE-ARK-release-public.pem").write_bytes(pub)
        manifest=d/"fixture.release.json"
        data={"schema":1,"protocol":"ark-public-release-v1","profile":"nano","version":"ci","release_key_sha256":key_fingerprint(pub),
              "source_image":{"bytes":raw.stat().st_size,"sha256":sha256(raw)},
              "distribution":{"compressed":True,"format":"raw-disk-image","compression":"zstd"},
              "files":[{"role":"distribution","file":comp.name,"bytes":comp.stat().st_size,"sha256":sha256(comp)},
                       {"role":"public_key","file":"THE-ARK-release-public.pem","bytes":len(pub),"sha256":sha256(d/"THE-ARK-release-public.pem")}]}
        manifest.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        sig=manifest.with_suffix(".json.sig")
        sig.write_bytes(key.sign(manifest.read_bytes(),padding.PKCS1v15(),hashes.SHA256()))
        verify_release(d)
        out=d/"written.img";out.write_bytes(b"\0"*raw.stat().st_size)
        result=write_stream(str(out),comp,True,raw.stat().st_size,sha256(raw))
        if out.read_bytes()!=raw.read_bytes():raise RuntimeError("selftest flashed bytes differ")
        print(json.dumps({"ok":True,"platform":platform.system(),"bytes":result["bytes"]}))
        print("THE_ARK_FLASHER_SELFTEST=PASS")

def gui():
    import tkinter as tk
    from tkinter import filedialog,messagebox,ttk
    root=tk.Tk();root.title("THE ARK Release Flasher");root.geometry("760x520")
    release=tk.StringVar();target=tk.StringVar();confirm=tk.StringVar();status=tk.StringVar(value="Select a signed release directory.")
    tk.Label(root,text="THE ARK",font=("TkDefaultFont",22,"bold")).pack(pady=(18,2))
    tk.Label(root,text="Signed release verifier + destructive disk flasher").pack()
    top=tk.Frame(root);top.pack(fill="x",padx=18,pady=14)
    tk.Entry(top,textvariable=release).pack(side="left",fill="x",expand=True)
    def choose():release.set(filedialog.askdirectory() or release.get())
    tk.Button(top,text="Release…",command=choose).pack(side="left",padx=8)
    box=ttk.Combobox(root,textvariable=target,state="readonly",width=80);box.pack(padx=18,fill="x")
    def refresh():
        try:
            rows=list_disks();box["values"]=[x["device"]+" | "+str(round(x["size"]/1e9,1))+" GB | "+x["model"]+(" | BLOCKED" if x["system"] or x["mounted"] else "") for x in rows]
            box._rows=rows
        except Exception as e:messagebox.showerror("Disk scan failed",str(e))
    tk.Button(root,text="Refresh disks",command=refresh).pack(pady=8)
    tk.Label(root,text="Type ERASE <device> exactly:").pack()
    tk.Entry(root,textvariable=confirm,width=80).pack(padx=18,fill="x")
    tk.Label(root,textvariable=status,wraplength=700,justify="left").pack(padx=18,pady=18,fill="x")
    def verify_btn():
        try:
            x=verify_release(pathlib.Path(release.get()).resolve());status.set("VERIFIED · "+x["data"].get("profile","")+" "+x["data"].get("version","")+" · key "+x["fingerprint"])
        except Exception as e:messagebox.showerror("Verification failed",str(e))
    def do_flash():
        sel=box.current()
        if sel<0:return messagebox.showerror("Target","Select a target disk.")
        row=getattr(box,"_rows",[])[sel];dev=row["device"]
        if not messagebox.askyesno("ERASE DISK","This permanently erases "+dev+". Continue?"):return
        def work():
            try:
                def prog(n,total):root.after(0,lambda:status.set(f"Writing {n/1e9:.2f} / {total/1e9:.2f} GB to {dev}"))
                result=flash_release(pathlib.Path(release.get()).resolve(),dev,confirm.get(),prog)
                root.after(0,lambda:messagebox.showinfo("Complete","THE ARK image written and raw SHA-256 verified.\n"+result["sha256"]))
            except Exception as e:root.after(0,lambda:messagebox.showerror("Flash failed",str(e)))
        threading.Thread(target=work,daemon=True).start()
    buttons=tk.Frame(root);buttons.pack()
    tk.Button(buttons,text="VERIFY RELEASE",command=verify_btn).pack(side="left",padx=8)
    tk.Button(buttons,text="FLASH SELECTED DISK",command=do_flash).pack(side="left",padx=8)
    refresh();root.mainloop()

def main():
    ap=argparse.ArgumentParser(prog="ark-release-flasher")
    sub=ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    v=sub.add_parser("verify");v.add_argument("directory")
    f=sub.add_parser("flash");f.add_argument("directory");f.add_argument("device");f.add_argument("--confirm",required=True)
    sub.add_parser("selftest");sub.add_parser("gui")
    a=ap.parse_args()
    cmd=a.cmd or "gui"
    if cmd=="list":print(json.dumps(list_disks(),indent=2));return 0
    if cmd=="verify":
        x=verify_release(pathlib.Path(a.directory).resolve());print(json.dumps({"ok":True,"profile":x["data"].get("profile"),"version":x["data"].get("version"),"release_key_sha256":x["fingerprint"]},indent=2));return 0
    if cmd=="flash":print(json.dumps(flash_release(pathlib.Path(a.directory).resolve(),a.device,a.confirm),indent=2));return 0
    if cmd=="selftest":selftest();return 0
    gui();return 0
if __name__=="__main__":raise SystemExit(main())
