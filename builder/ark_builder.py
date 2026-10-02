#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, re, shutil, subprocess, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]
WEB=ROOT/"builder"
PROFILES=("nano","family","nomad","civilization")
DEVICE_RE=re.compile(r"^/dev/(?:sd[a-z]+|vd[a-z]+|nvme\d+n\d+|mmcblk\d+)$")

def cards():
    out=[]
    for pid in PROFILES:
        data=yaml.safe_load((ROOT/"profiles"/f"{pid}.yml").read_text(encoding="utf-8"))
        meta=data["profile"]
        out.append({"id":pid,"title":meta.get("title") or pid.upper(),
                    "target_bytes":int(meta["target_bytes"]),
                    "description":str(meta.get("description") or "").strip()})
    return out

def profile_meta(pid):
    if pid not in PROFILES: raise ValueError("unknown profile")
    data=yaml.safe_load((ROOT/"profiles"/f"{pid}.yml").read_text(encoding="utf-8"))
    return data["profile"]

def mounted_tree(node):
    if any(x for x in (node.get("mountpoints") or []) if x): return True
    return any(mounted_tree(ch) for ch in (node.get("children") or []))

def root_disk():
    try:
        src=subprocess.check_output(["findmnt","-n","-o","SOURCE","/"],text=True).strip()
        pk=subprocess.check_output(["lsblk","-no","PKNAME",src],text=True).strip()
        return "/dev/"+pk if pk else src
    except Exception:
        return ""

def disks():
    try:
        raw=subprocess.check_output(["lsblk","--json","-b","-o","NAME,PATH,SIZE,MODEL,TYPE,TRAN,RM,MOUNTPOINTS"],text=True)
        data=json.loads(raw)
    except Exception as exc:
        return {"error":str(exc),"items":[]}
    root=root_disk(); rows=[]
    for d in data.get("blockdevices",[]):
        if d.get("type")!="disk": continue
        path=str(d.get("path") or "")
        rows.append({"path":path,"size":int(d.get("size") or 0),
                     "model":(d.get("model") or "").strip(),"transport":d.get("tran"),
                     "removable":bool(d.get("rm")),"mounted":mounted_tree(d),
                     "root_related":bool(root and (path==root or root.startswith(path)))})
    return {"root_disk":root,"items":rows}

class Runner:
    def __init__(self):
        self.mu=threading.Lock(); self.running=False; self.profile=None; self.action=None
        self.returncode=None; self.logs=[]; self.started=None; self.ended=None

    def state(self):
        with self.mu:
            return {"running":self.running,"profile":self.profile,"action":self.action,
                    "returncode":self.returncode,"logs":self.logs[-1200:],
                    "started":self.started,"ended":self.ended}

    def command(self,profile,action,device=None):
        py=str(ROOT/".venv/bin/python") if (ROOT/".venv/bin/python").exists() else sys.executable
        base=[py,"scripts/endworld.py","--profile",profile]
        allowed={"plan","acquire","prepare","verify","selftest","build-image","snapshot-packages"}
        if action=="flash":
            if not device or not DEVICE_RE.fullmatch(device): raise ValueError("unsupported block device path")
            return base+["flash",device]
        if action not in allowed: raise ValueError("unsupported action")
        if action=="snapshot-packages" and profile!="civilization": raise ValueError("package snapshots are CIVILIZATION-only")
        return base+[action]

    def start(self,profile,action,device=None):
        if profile not in PROFILES: raise ValueError("unknown profile")
        cmd=self.command(profile,action,device)
        with self.mu:
            if self.running: raise RuntimeError("another task is already running")
            self.running=True; self.profile=profile; self.action=action; self.returncode=None
            self.logs=["$ "+" ".join(cmd)]; self.started=time.time(); self.ended=None
        threading.Thread(target=self._work,args=(cmd,),daemon=True).start()

    def _work(self,cmd):
        rc=127
        try:
            p=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            assert p.stdout is not None
            for line in p.stdout:
                with self.mu:
                    self.logs.append(line.rstrip())
                    if len(self.logs)>5000:self.logs=self.logs[-4000:]
            rc=p.wait()
        except Exception as exc:
            with self.mu:self.logs.append("ERROR: "+str(exc))
        finally:
            with self.mu:self.running=False; self.returncode=rc; self.ended=time.time()

RUNNER=Runner()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*_): pass
    def send_json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data))); self.send_header("Cache-Control","no-store"); self.end_headers()
        self.wfile.write(data)
    def payload(self):
        n=int(self.headers.get("Content-Length","0"))
        if n<=0 or n>65536: raise ValueError("invalid request size")
        return json.loads(self.rfile.read(n))
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/profiles": return self.send_json(cards())
        if path=="/api/state": return self.send_json(RUNNER.state())
        if path=="/api/disks": return self.send_json(disks())
        if path=="/api/estimate":
            q=urlparse(self.path).query
            params=parse_qs(q)
            pid=(params.get("profile") or ["nano"])[0]
            try:
                meta=profile_meta(pid); target=int(meta["target_bytes"])
                free=shutil.disk_usage(ROOT).free
                vault=ROOT/"vault"/pid
                existing=sum(p.stat().st_size for p in vault.rglob("*") if p.is_file()) if vault.exists() else 0
                return self.send_json({"profile":pid,"target_bytes":target,"builder_free_bytes":free,
                    "existing_vault_bytes":existing,"recommended_builder_free_bytes":target*2,
                    "enough_builder_space":free>=target*2})
            except Exception as exc:return self.send_json({"error":str(exc)},400)
        rel="index.html" if path=="/" else path.lstrip("/")
        f=(WEB/rel).resolve()
        try:f.relative_to(WEB.resolve())
        except ValueError:return self.send_error(403)
        if not f.is_file():return self.send_error(404)
        ctype={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8"}.get(f.suffix,"application/octet-stream")
        data=f.read_bytes(); self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        try:p=self.payload()
        except Exception:return self.send_json({"error":"invalid request"},400)
        path=urlparse(self.path).path
        try:
            if path=="/api/action":
                RUNNER.start(str(p.get("profile")),str(p.get("action"))); return self.send_json({"ok":True},202)
            if path=="/api/flash":
                profile,device,confirm=str(p.get("profile")),str(p.get("device")),str(p.get("confirm"))
                if confirm!=device+" ERASE": raise ValueError("confirmation phrase does not match")
                row=next((x for x in disks().get("items",[]) if x["path"]==device),None)
                if not row: raise ValueError("device is not a current disk")
                if row.get("root_related"): raise ValueError("refusing the running root disk")
                if row.get("mounted"): raise ValueError("refusing a disk with mounted filesystems; unmount it first")
                target=int(profile_meta(profile)["target_bytes"])
                if int(row.get("size") or 0) < target:
                    raise ValueError(f"disk is too small for {profile}: need at least {target} bytes")
                RUNNER.start(profile,"flash",device); return self.send_json({"ok":True},202)
            return self.send_json({"error":"not found"},404)
        except RuntimeError as exc:return self.send_json({"error":str(exc)},409)
        except ValueError as exc:return self.send_json({"error":str(exc)},400)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--bind",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8787)
    ap.add_argument("--no-browser",action="store_true"); ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    if args.check:
        assert [x["id"] for x in cards()]==list(PROFILES)
        assert int(profile_meta("nano")["target_bytes"])>0
        print(json.dumps({"ok":True,"profiles":list(PROFILES),"safe_flash_checks":["root","mounted","capacity","confirmation"]})); return 0
    url=f"http://{args.bind}:{args.port}/"; print("THE ARK Builder:",url,flush=True)
    if not args.no_browser: threading.Timer(.5,lambda:webbrowser.open(url)).start()
    srv=ThreadingHTTPServer((args.bind,args.port),Handler); srv.serve_forever()
if __name__=="__main__": raise SystemExit(main())
