#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VAULT="${1:-$ROOT/vault/nano-mini}"
rm -rf "$VAULT"
mkdir -p "$VAULT"/{knowledge/zim,ai/models,maps/raw,maps/tiles,apps/android,source/comms,source/core,tools/planetiler,web/vendor,containers,lock,state/private}

printf 'mini wikipedia fixture\n' > "$VAULT/knowledge/zim/mini_es.zim"
printf 'mini medicine fixture\n' > "$VAULT/knowledge/zim/medicine_es.zim"
printf 'GGUF-CI\n' > "$VAULT/ai/models/mini.gguf"
printf 'WHISPER-CI\n' > "$VAULT/ai/models/whisper-mini.bin"
printf 'OSM-PBF-CI\n' > "$VAULT/maps/raw/spain-mini.osm.pbf"
python3 - "$VAULT/maps/tiles/spain.pmtiles" <<'PY'
import pathlib,sys
pathlib.Path(sys.argv[1]).write_bytes(bytes(range(256))*16)
PY
printf 'APK-CI\n' > "$VAULT/apps/android/bitchat.apk"
printf 'APK-CI\n' > "$VAULT/apps/android/meshtastic.apk"
printf 'JAR-CI\n' > "$VAULT/tools/planetiler/planetiler.jar"
printf 'console.log("maplibre-ci")\n' > "$VAULT/web/vendor/maplibre-gl.js"
printf '/* maplibre-ci */\n' > "$VAULT/web/vendor/maplibre-gl.css"
printf 'console.log("pmtiles-ci")\n' > "$VAULT/web/vendor/pmtiles.js"
printf 'PRIVATE-CI-SECRET\n' > "$VAULT/state/private/secret.txt"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/reticulum-source-ci"
cat > "$tmp/reticulum-source-ci/setup.py" <<'PY'
from setuptools import setup
setup(name="ark-reticulum-ci",version="0.0.1",py_modules=["rns_stub"],
      entry_points={"console_scripts":["rnstatus=rns_stub:main"]})
PY
cat > "$tmp/reticulum-source-ci/rns_stub.py" <<'PY'
def main():
    print("Reticulum CI stub")
PY
tar -C "$tmp" -czf "$VAULT/source/comms/reticulum-source-ci.tar.gz" reticulum-source-ci
mkdir -p "$tmp/project-nomad-ci"
printf 'PROJECT NOMAD CI SOURCE\n' > "$tmp/project-nomad-ci/README.md"
tar -C "$tmp" -czf "$VAULT/source/core/project-nomad-source-ci.tar.gz" project-nomad-ci

mkdir -p "$tmp/kiwix"
cat > "$tmp/kiwix/server.py" <<'PY'
from http.server import BaseHTTPRequestHandler,HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/search?"):
            body=b'<html><body><a href="/content/mini_es/A/Quemadura">Quemadura</a></body></html>'
        elif self.path.startswith("/content/"):
            body=b'<html><head><title>Quemadura</title></head><body><h1>Quemadura</h1><p>Enfriar la quemadura con agua corriente limpia durante varios minutos.</p></body></html>'
        else: body=b'KIWIX-MINI-OK'
        self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass
HTTPServer(("0.0.0.0",8081),H).serve_forever()
PY
cat > "$tmp/kiwix/Dockerfile" <<'EOF'
FROM python:3.12-alpine
COPY server.py /server.py
ENTRYPOINT ["python3","/server.py"]
EOF

mkdir -p "$tmp/llama"
cat > "$tmp/llama/server.py" <<'PY'
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'{"status":"ok"}'
        self.send_response(200);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"));raw=self.rfile.read(n)
        try: req=json.loads(raw or b"{}")
        except Exception: req={}
        msgs=req.get("messages") or []
        system=str(msgs[0].get("content","")) if msgs else ""
        if "THE ARK offline field agent" in system:
            transcript="\n".join(str(m.get("content","")) for m in msgs)
            if '"internet": false' in transcript:
                out={"action":"final","answer":"Offline confirmed. Burn guidance was read from frozen source [E1] and field note was written."}
            elif '"written": true' in transcript:
                out={"action":"tool","tool":"ark.status","args":{}}
            elif "Enfriar la quemadura" in transcript:
                out={"action":"tool","tool":"ark.write_note","args":{"name":"burn-field-note","text":"# Burn field note\n\nLocal frozen guidance: Enfriar la quemadura con agua corriente limpia durante varios minutos. Source [E1]."}}
            elif '"id": "E1"' in transcript:
                out={"action":"tool","tool":"ark.read_source","args":{"id":"E1"}}
            else:
                out={"action":"tool","tool":"ark.search","args":{"query":"como trato una quemadura","limit":4}}
            content=json.dumps(out,ensure_ascii=False)
        else:
            content="mini-ai-ok"
        body=json.dumps({"choices":[{"message":{"content":content}}]}).encode()
        self.send_response(200);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass
HTTPServer(("0.0.0.0",8082),H).serve_forever()
PY
cat > "$tmp/llama/Dockerfile" <<'EOF'
FROM python:3.12-alpine
COPY server.py /server.py
ENTRYPOINT ["python3","/server.py"]
EOF

mkdir -p "$tmp/whisper"
cat > "$tmp/whisper/server.py" <<'PY'
from http.server import BaseHTTPRequestHandler,HTTPServer
import argparse,json
ap=argparse.ArgumentParser(add_help=False);ap.add_argument("--port",type=int,default=8080)
args,_=ap.parse_known_args()
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'WHISPER-MINI-OK';self.send_response(200);self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"));self.rfile.read(n)
        body=json.dumps({"text":"mini-whisper-ok"}).encode()
        self.send_response(200);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass
HTTPServer(("0.0.0.0",args.port),H).serve_forever()
PY
cat > "$tmp/whisper/whisper-server" <<'EOF'
#!/bin/sh
exec python3 /server.py "$@"
EOF
chmod +x "$tmp/whisper/whisper-server"
cat > "$tmp/whisper/Dockerfile" <<'EOF'
FROM python:3.12-alpine
COPY server.py /server.py
COPY whisper-server /usr/local/bin/whisper-server
ENTRYPOINT ["sh","-c"]
EOF

docker build -q -t endworld/nano-mini-kiwix:ci "$tmp/kiwix" >/dev/null
docker build -q -t endworld/nano-mini-llama:ci "$tmp/llama" >/dev/null
docker build -q -t endworld/nano-mini-whisper:ci "$tmp/whisper" >/dev/null
docker save -o "$VAULT/containers/kiwix.tar" endworld/nano-mini-kiwix:ci
docker save -o "$VAULT/containers/llama-server.tar" endworld/nano-mini-llama:ci
docker save -o "$VAULT/containers/whisper-server.tar" endworld/nano-mini-whisper:ci

python3 - "$ROOT" "$VAULT" <<'PY'
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);vault=pathlib.Path(sys.argv[2])
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def rec(i,fam,rel,kind="fixture",required=True):
    p=vault/rel
    return {"id":i,"family":fam,"kind":kind,"required":required,"path":rel,
            "bytes":p.stat().st_size,"sha256":sha(p),"status":"fixture"}
arts=[
 rec("wikipedia-es","knowledge","knowledge/zim/mini_es.zim"),
 rec("wikipedia-medicine-es","medical","knowledge/zim/medicine_es.zim"),
 rec("qwen3-4b-q4","ai","ai/models/mini.gguf"),
 rec("whisper-small","ai","ai/models/whisper-mini.bin"),
 rec("spain-osm","maps","maps/raw/spain-mini.osm.pbf"),
 rec("spain-pmtiles","maps","maps/tiles/spain.pmtiles","derived"),
 rec("bitchat-android","comms","apps/android/bitchat.apk"),
 rec("meshtastic-android","comms","apps/android/meshtastic.apk"),
 rec("reticulum-source","comms","source/comms/reticulum-source-ci.tar.gz"),
 rec("project-nomad-source","core","source/core/project-nomad-source-ci.tar.gz"),
 rec("planetiler","maps","tools/planetiler/planetiler.jar"),
 rec("maplibre-js","runtime","web/vendor/maplibre-gl.js"),
 rec("maplibre-css","runtime","web/vendor/maplibre-gl.css"),
 rec("pmtiles-js","runtime","web/vendor/pmtiles.js"),
]
containers=[]
for i,image,name in [
 ("kiwix","endworld/nano-mini-kiwix:ci","kiwix.tar"),
 ("llama-server","endworld/nano-mini-llama:ci","llama-server.tar"),
 ("whisper-server","endworld/nano-mini-whisper:ci","whisper-server.tar")]:
    p=vault/"containers"/name
    containers.append({"id":i,"image":image,"required":True,"path":"containers/"+name,
                       "bytes":p.stat().st_size,"sha256":sha(p),"status":"frozen"})
payload=sum(x["bytes"] for x in arts+containers)
lock={"schema":1,"profile":"nano-mini","title":"THE ARK NANO-MINI CI",
      "target_bytes":7_000_000_000,"reserve_bytes":1_500_000_000,
      "payload_bytes":payload,"prepared":True,"derived_count":1,
      "artifacts":arts,"containers":containers,"failures":[]}
(vault/"lock/nano-mini.lock.json").write_text(json.dumps(lock,indent=2)+"\n")
bom={"bomFormat":"CycloneDX","specVersion":"1.5","version":1,"metadata":{"component":{"type":"application","name":"the-ark-nano-mini-ci"}},"components":[]}
(vault/"lock/nano-mini.cdx.json").write_text(json.dumps(bom,indent=2)+"\n")
print("fixture payload",payload)
PY

python3 "$ROOT/scripts/verify_vault.py" --vault "$VAULT" --profile-id nano-mini
