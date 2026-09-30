#!/usr/bin/env python3
"""ENDWORLD local appliance server.

Stdlib-only by design. Serves the portal and vault with HTTP Range support,
exposes health/status/app APIs, implements common captive-portal probes, and
proxies local chat requests to llama.cpp.
"""
from __future__ import annotations
import argparse, json, mimetypes, os, pathlib, shutil, socket, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

MAX_BODY = 1_000_000
MAX_AUDIO_BODY = 64 * 1024 * 1024

def safe_join(base: pathlib.Path, rel: str) -> pathlib.Path | None:
    rel = unquote(rel).lstrip("/")
    p = (base / rel).resolve()
    try: p.relative_to(base.resolve())
    except ValueError: return None
    return p

def internet_online() -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=0.35): return True
    except OSError: return False

def battery_status() -> dict:
    base=pathlib.Path("/sys/class/power_supply"); result={"present":False}
    if not base.exists(): return result
    for dev in base.iterdir():
        try: typ=(dev/"type").read_text().strip().lower()
        except OSError: continue
        if typ!="battery": continue
        result["present"]=True
        try: result["percent"]=int((dev/"capacity").read_text().strip())
        except Exception: pass
        try: result["status"]=(dev/"status").read_text().strip()
        except Exception: pass
        break
    return result

def service_alive(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.2) as r: return 200 <= r.status < 500
    except Exception: return False

def describe_capability(rec: dict, vault: pathlib.Path, reticulum_available: bool = False) -> dict:
    rid=str(rec.get("id") or "unknown")
    family=str(rec.get("family") or "runtime")
    rel=rec.get("path")
    suffix=pathlib.PurePosixPath(rel).suffix.lower() if rel else ""
    present=(vault/rel).is_file() if rel else True
    item={"id":rid,"family":family,"kind":rec.get("kind") or ("container" if rec.get("image") else "artifact"),
          "required":bool(rec.get("required",False)),"bytes":rec.get("bytes"),"path":rel,
          "state":"FROZEN" if present else "MISSING","action":None,"note":""}

    if rid=="kiwix" or (family in ("knowledge","medical") and suffix==".zim"):
        item.update(state="SERVICE",action={"kind":"service","port":8081,"label":"Open library"})
    elif rid=="llama-server" or rid.startswith("qwen"):
        item.update(state="SERVICE",action={"kind":"anchor","href":"#local-ai","label":"Open local AI"})
    elif rid=="whisper-server" or rid.startswith("whisper-"):
        item.update(state="SERVICE",action={"kind":"anchor","href":"#voice","label":"Open transcription"})
    elif rid=="syncthing":
        item.update(state="SERVICE",action={"kind":"service","port":8384,"label":"Open Syncthing"})
    elif rid=="forgejo":
        item.update(state="SERVICE",action={"kind":"service","port":3000,"label":"Open Forgejo"})
    elif rid=="qdrant":
        item.update(state="SERVICE",action={"kind":"service","port":6333,"label":"Open Qdrant"})
    elif rid=="code-server":
        item.update(state="SERVICE",action={"kind":"service","port":8443,"label":"Open IDE"})
    elif rid=="project-nomad-admin":
        item.update(state="SERVICE",action={"kind":"service","port":8090,"label":"Open Project NOMAD"})
    elif rid in ("project-nomad-mysql","project-nomad-redis"):
        item.update(state="RUNTIME",note="Frozen internal dependency for Project NOMAD.")
    elif rid.endswith("-pmtiles"):
        item.update(state="READY",action={"kind":"link","href":"/map.html","label":"Open map"})
    elif suffix==".apk" and rel:
        item.update(state="READY",action={"kind":"link","href":"/vault/"+rel,"label":"Download APK"})
    elif rel and rel.startswith("firmware/"):
        item.update(state="READY",action={"kind":"link","href":"/vault/"+rel,"label":"Download firmware"})
    elif rid=="reticulum-source":
        item.update(state="INSTALLED" if reticulum_available else "PRESERVED",
                    action={"kind":"link","href":"/vault/"+rel,"label":"Open frozen source"} if rel else None,
                    note="Reticulum CLI is installed in the appliance image when this source archive is present.")
    elif rid=="project-nomad-source":
        item.update(state="PRESERVED",
                    action={"kind":"link","href":"/vault/"+rel,"label":"Open frozen source"} if rel else None,
                    note="Project NOMAD source is preserved here; the full multi-container Command Center belongs in the dedicated NOMAD profile.")
    elif rid=="spain-osm" and rel:
        item.update(state="SOURCE",action={"kind":"link","href":"/vault/"+rel,"label":"Open OSM source"})
    elif rel and rel.startswith("source/"):
        item.update(state="PRESERVED",action={"kind":"link","href":"/vault/"+rel,"label":"Open frozen source"})
    elif rid in ("planetiler","maplibre-js","maplibre-css","pmtiles-js"):
        item.update(state="RUNTIME",note="Internal frozen runtime/build dependency.")
    elif rel:
        item["action"]={"kind":"link","href":"/vault/"+rel,"label":"Open artifact"}

    if not present and rel:
        item["state"]="MISSING"
        item["action"]=None
    return item

class App:
    def __init__(self, portal:pathlib.Path, vault:pathlib.Path, profile:str|None=None):
        self.portal=portal.resolve(); self.vault=vault.resolve(); self.started=time.time()
        self.profile=profile or os.getenv("ENDWORLD_PROFILE") or self.detect_profile()
    def detect_profile(self)->str:
        lockdir=self.vault/"lock"
        locks=sorted(lockdir.glob("*.lock.json")) if lockdir.exists() else []
        return locks[0].name.split(".lock.json",1)[0] if len(locks)==1 else "nano"
    def lock_path(self)->pathlib.Path:
        return self.vault/"lock"/f"{self.profile}.lock.json"
    def title(self)->str:
        try:return str(json.loads(self.lock_path().read_text(encoding="utf-8")).get("title") or f"ENDWORLD {self.profile.upper()}")
        except Exception:return f"ENDWORLD {self.profile.upper()}"
    def status(self)->dict:
        usage=shutil.disk_usage(self.vault if self.vault.exists() else "/")
        mode_path=self.vault/"state/runtime/ai-mode"
        try: ai_mode=mode_path.read_text(encoding="utf-8").strip()
        except Exception: ai_mode="default"
        return {"node":socket.gethostname(),"profile":self.profile,"title":self.title(),"uptime_seconds":int(time.time()-self.started),
        "internet":internet_online(),"storage":{"total":usage.total,"used":usage.used,"free":usage.free},"battery":battery_status(),"ai_mode":ai_mode,
        "services":{"portal":True,"knowledge":service_alive("http://127.0.0.1:8081/"),"ai":service_alive("http://127.0.0.1:8082/health"),"voice":service_alive("http://127.0.0.1:8083/"),"syncthing":service_alive("http://127.0.0.1:8384/"),"forgejo":service_alive("http://127.0.0.1:3000/"),"qdrant":service_alive("http://127.0.0.1:6333/healthz"),"code_server":service_alive("http://127.0.0.1:8443/"),"project_nomad":service_alive("http://127.0.0.1:8090/api/health")},"map_ready":any((self.vault/"maps/tiles").glob("*.pmtiles")) if (self.vault/"maps/tiles").exists() else False}
    def apps(self)->list[dict]:
        appdir=self.vault/"apps/android"
        if not appdir.exists(): return []
        return [{"name":p.name,"bytes":p.stat().st_size,"url":"/vault/apps/android/"+p.name} for p in sorted(appdir.glob("*.apk"))]
    def maps(self)->list[dict]:
        root=self.vault/"maps/tiles"
        if not root.exists(): return []
        return [{"id":p.stem,"name":p.stem.replace("-"," ").title(),"bytes":p.stat().st_size,"url":"/maps/"+p.name}
                for p in sorted(root.glob("*.pmtiles"))]
    def capabilities(self)->list[dict]:
        lock_path=self.lock_path()
        if not lock_path.exists(): return []
        try: lock=json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception: return []
        records=list(lock.get("artifacts",[]))+list(lock.get("containers",[]))
        installed=shutil.which("rnstatus") is not None
        return [describe_capability(rec,self.vault,installed) for rec in records]

class Handler(BaseHTTPRequestHandler):
    server_version="ENDWORLD/0.1"
    @property
    def app(self)->App: return self.server.app
    def log_message(self,fmt,*args): print("%s - %s"%(self.address_string(),fmt%args),flush=True)
    def send_json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store"); self.end_headers()
        if self.command!="HEAD": self.wfile.write(data)
    def redirect(self,target="/",status=302):
        self.send_response(status); self.send_header("Location",target); self.send_header("Cache-Control","no-store"); self.end_headers()
    def do_HEAD(self): self.route(False)
    def do_GET(self): self.route(True)
    def route(self,send_body=True):
        path=urlparse(self.path).path
        if path in ("/generate_204","/gen_204","/hotspot-detect.html","/library/test/success.html"): return self.redirect("/",302)
        if path=="/ncsi.txt":
            data=b"Microsoft NCSI"; self.send_response(200); self.send_header("Content-Type","text/plain")
            self.send_header("Content-Length",str(len(data))); self.end_headers()
            if send_body:self.wfile.write(data)
            return
        if path in ("/health","/api/health"): return self.send_json({"ok":True,"profile":self.app.profile})
        if path=="/api/status": return self.send_json(self.app.status())
        if path=="/api/apps": return self.send_json(self.app.apps())
        if path=="/api/maps": return self.send_json(self.app.maps())
        if path=="/api/capabilities": return self.send_json(self.app.capabilities())
        if path=="/api/lock":
            lock=self.app.lock_path()
            if not lock.exists(): return self.send_json({"error":"lock missing"},404)
            try:return self.send_json(json.loads(lock.read_text(encoding="utf-8")))
            except Exception as exc:return self.send_json({"error":str(exc)},500)
        for prefix,base in (("/vault/",self.app.vault),("/vendor/",self.app.vault/"web/vendor"),("/maps/",self.app.vault/"maps/tiles")):
            if path.startswith(prefix): return self.serve_path(safe_join(base,path[len(prefix):]),send_body)
        rel="index.html" if path=="/" else path.lstrip("/")
        return self.serve_path(safe_join(self.app.portal,rel),send_body)
    def do_POST(self):
        path=urlparse(self.path).path
        try:length=int(self.headers.get("Content-Length","0"))
        except ValueError:return self.send_json({"error":"bad content length"},400)

        if path=="/api/transcribe":
            if length<=0 or length>MAX_AUDIO_BODY:return self.send_json({"error":"invalid audio body size"},413)
            ctype=self.headers.get("Content-Type","")
            if "multipart/form-data" not in ctype:return self.send_json({"error":"multipart/form-data required"},400)
            body=self.rfile.read(length)
            req=urllib.request.Request("http://127.0.0.1:8083/inference",data=body,
                headers={"Content-Type":ctype},method="POST")
            try:
                with urllib.request.urlopen(req,timeout=600) as r:
                    data=r.read(); response_type=r.headers.get("Content-Type","application/json")
                self.send_response(200);self.send_header("Content-Type",response_type)
                self.send_header("Content-Length",str(len(data)));self.send_header("Cache-Control","no-store");self.end_headers()
                self.wfile.write(data);return
            except urllib.error.HTTPError as exc:return self.send_json({"error":f"whisper.cpp HTTP {exc.code}"},502)
            except Exception as exc:return self.send_json({"error":f"local transcription unavailable: {exc}"},503)

        if path!="/api/chat": return self.send_json({"error":"not found"},404)
        if length<=0 or length>MAX_BODY:return self.send_json({"error":"invalid body size"},413)
        try:payload=json.loads(self.rfile.read(length))
        except Exception:return self.send_json({"error":"invalid json"},400)
        messages=payload.get("messages")
        if not isinstance(messages,list) or not messages:return self.send_json({"error":"messages required"},400)
        llm_payload={"model":"local","messages":messages[-20:],"temperature":float(payload.get("temperature",0.3)),
        "max_tokens":int(payload.get("max_tokens",700)),"stream":False}
        req=urllib.request.Request("http://127.0.0.1:8082/v1/chat/completions",data=json.dumps(llm_payload).encode(),
        headers={"Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=180) as r:data=json.load(r)
            return self.send_json(data)
        except urllib.error.HTTPError as exc:return self.send_json({"error":f"llama.cpp HTTP {exc.code}"},502)
        except Exception as exc:return self.send_json({"error":f"local AI unavailable: {exc}"},503)
    def serve_path(self,file:pathlib.Path|None,send_body=True):
        if file is None:self.send_error(403);return
        if file.is_dir():
            index=file/"index.html"
            if index.exists():file=index
            else:return self.directory_json(file)
        if not file.exists() or not file.is_file():self.send_error(404);return
        size=file.stat().st_size;start,end=0,size-1;partial=False;rh=self.headers.get("Range")
        if rh and rh.startswith("bytes="):
            try:
                spec=rh[6:].split(",",1)[0];left,right=spec.split("-",1)
                if left:start=int(left);end=int(right) if right else end
                else:suffix=int(right);start=max(0,size-suffix)
                end=min(end,size-1)
                if start<0 or start>end:raise ValueError
                partial=True
            except Exception:
                self.send_response(416);self.send_header("Content-Range",f"bytes */{size}");self.end_headers();return
        length=end-start+1;ctype=mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        self.send_response(206 if partial else 200);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(length))
        self.send_header("Accept-Ranges","bytes")
        if partial:self.send_header("Content-Range",f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control","public, max-age=3600");self.end_headers()
        if not send_body:return
        with file.open("rb") as f:
            f.seek(start);remaining=length
            while remaining:
                chunk=f.read(min(1024*1024,remaining))
                if not chunk:break
                self.wfile.write(chunk);remaining-=len(chunk)
    def directory_json(self,directory:pathlib.Path):
        rows=[{"name":p.name,"directory":p.is_dir(),"bytes":p.stat().st_size if p.is_file() else None}
              for p in sorted(directory.iterdir(),key=lambda x:(not x.is_dir(),x.name.lower()))]
        self.send_json({"path":str(directory.relative_to(self.app.vault)),"items":rows})

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--bind",default="0.0.0.0");ap.add_argument("--port",type=int,default=8080)
    ap.add_argument("--profile",default=os.getenv("ENDWORLD_PROFILE"))
    ap.add_argument("--portal",default=str(pathlib.Path(__file__).parent/"portal"))
    ap.add_argument("--vault",default=os.getenv("ENDWORLD_VAULT","/srv/endworld"));args=ap.parse_args()
    httpd=ThreadingHTTPServer((args.bind,args.port),Handler);httpd.app=App(pathlib.Path(args.portal),pathlib.Path(args.vault),args.profile)
    print(f"ENDWORLD portal on http://{args.bind}:{args.port}",flush=True);httpd.serve_forever()
if __name__=="__main__":main()
