#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${ENDWORLD_PROFILE:-nano}"
VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
[[ -d "$VAULT" ]] || VAULT="$ROOT/vault/$PROFILE"
LOCK="$VAULT/lock/$PROFILE.lock.json"
if [[ -f /etc/endworld/profile.env ]]; then set -a; source /etc/endworld/profile.env; set +a
elif [[ -f "$ROOT/config/$PROFILE.env" ]]; then set -a; source "$ROOT/config/$PROFILE.env"; set +a; fi
[[ -f "$LOCK" ]] || { echo "Frozen lock missing: $LOCK" >&2; exit 2; }
command -v docker >/dev/null || { echo "docker missing" >&2; exit 2; }
docker info >/dev/null 2>&1 || { echo "docker daemon unavailable" >&2; exit 2; }

lock_field(){ local group="$1" id="$2" field="$3"; python3 - "$LOCK" "$group" "$id" "$field" <<'PY'
import json,sys
lock=json.load(open(sys.argv[1],encoding="utf-8"))
for rec in lock.get(sys.argv[2],[]):
    if rec.get("id")==sys.argv[3]:
        v=rec.get(sys.argv[4])
        if v is not None: print(v)
        break
PY
}
artifact_path(){ local rel; rel="$(lock_field artifacts "$1" path)"; [[ -n "$rel" ]] || return 1; printf '%s/%s\n' "$VAULT" "$rel"; }
load_image(){ local id="$1" image rel tar; image="$(lock_field containers "$id" image)"; rel="$(lock_field containers "$id" path)"; [[ -n "$image" && -n "$rel" ]] || return 1; tar="$VAULT/$rel"; [[ -f "$tar" ]] || { echo "Frozen container missing: $tar" >&2; return 1; }; if [[ "${ENDWORLD_RELOAD_CONTAINERS:-0}" != "1" ]] && docker image inspect "$image" >/dev/null 2>&1; then echo "Using already loaded frozen image $id" >&2; else echo "Loading frozen container $id" >&2; docker load -i "$tar" >/dev/null; fi; printf '%s\n' "$image"; }

KIWIX_IMAGE="$(load_image kiwix)" || exit 2
LLAMA_IMAGE="$(load_image llama-server)" || exit 2
WHISPER_IMAGE="$(load_image whisper-server)" || exit 2
docker rm -f endworld-kiwix endworld-ai endworld-whisper endworld-syncthing endworld-forgejo endworld-qdrant endworld-code-server endworld-nomad-admin endworld-nomad-mysql endworld-nomad-redis >/dev/null 2>&1 || true

mapfile -t ZIMS < <(find "$VAULT/knowledge/zim" -maxdepth 1 -type f -name '*.zim' -printf '%f\n' | sort)
(( ${#ZIMS[@]} > 0 )) || { echo "No ZIM files found" >&2; exit 2; }
ZIM_ARGS=(); for z in "${ZIMS[@]}"; do ZIM_ARGS+=("/data/$z"); done
docker run -d --name endworld-kiwix --restart unless-stopped --network host -e PORT=8081 -v "$VAULT/knowledge/zim:/data:ro" "$KIWIX_IMAGE" "${ZIM_ARGS[@]}" >/dev/null

MODEL_ID="${ENDWORLD_AI_MODEL_ID:-qwen3-4b-q4}"; MODEL="$(artifact_path "$MODEL_ID")" || exit 2
[[ -f "$MODEL" ]] || { echo "AI model missing: $MODEL" >&2; exit 2; }
docker run -d --name endworld-ai --restart unless-stopped --network host -v "$VAULT/ai/models:/models:ro" "$LLAMA_IMAGE" -m "/models/$(basename "$MODEL")" --host 0.0.0.0 --port 8082 -c "${ENDWORLD_AI_CONTEXT:-4096}" --threads "${ENDWORLD_AI_THREADS:-$(nproc)}" >/dev/null
mkdir -p "$VAULT/state/runtime"; printf '%s\n' "${ENDWORLD_AI_MODE:-default}" > "$VAULT/state/runtime/ai-mode"

WHISPER_ID="${ENDWORLD_WHISPER_MODEL_ID:-whisper-small}"; WHISPER_MODEL="$(artifact_path "$WHISPER_ID")" || exit 2
docker run -d --name endworld-whisper --restart unless-stopped --network host -v "$VAULT/ai/models:/models:ro" --entrypoint whisper-server "$WHISPER_IMAGE" --host 0.0.0.0 --port 8083 -m "/models/$(basename "$WHISPER_MODEL")" -l "${ENDWORLD_WHISPER_LANGUAGE:-auto}" >/dev/null

if [[ "${ENDWORLD_ENABLE_SYNCTHING:-0}" == "1" ]]; then
  I="$(load_image syncthing)" || exit 2; mkdir -p "$VAULT/state/syncthing"; chown 1000:1000 "$VAULT/state/syncthing" 2>/dev/null || true
  docker run -d --name endworld-syncthing --restart unless-stopped -p 8384:8384 -p 22000:22000/tcp -p 22000:22000/udp -p 21027:21027/udp -v "$VAULT/state/syncthing:/var/syncthing" "$I" >/dev/null
fi
if [[ "${ENDWORLD_ENABLE_FORGEJO:-0}" == "1" ]]; then
  I="$(load_image forgejo)" || exit 2; mkdir -p "$VAULT/state/forgejo"; chown 1000:1000 "$VAULT/state/forgejo" 2>/dev/null || true
  docker run -d --name endworld-forgejo --restart unless-stopped -e USER_UID=1000 -e USER_GID=1000 -p 3000:3000 -p 2222:22 -v "$VAULT/state/forgejo:/data" "$I" >/dev/null
fi
if [[ "${ENDWORLD_ENABLE_QDRANT:-0}" == "1" ]]; then
  I="$(load_image qdrant)" || exit 2; mkdir -p "$VAULT/state/qdrant"
  docker run -d --name endworld-qdrant --restart unless-stopped -p 6333:6333 -p 6334:6334 -v "$VAULT/state/qdrant:/qdrant/storage" "$I" >/dev/null
fi
if [[ "${ENDWORLD_ENABLE_CODE_SERVER:-0}" == "1" ]]; then
  I="$(load_image code-server)" || exit 2; mkdir -p "$VAULT/state/dev/workspace" "$VAULT/state/dev/code-server"
  docker run -d --name endworld-code-server --restart unless-stopped -e PASSWORD="${ENDWORLD_CODE_PASSWORD:-endworld-nomad}" -p 8443:8080 -v "$VAULT/state/dev/workspace:/home/coder/project" -v "$VAULT/state/dev/code-server:/home/coder/.config" "$I" >/dev/null
fi
if [[ "${ENDWORLD_ENABLE_NOMAD:-0}" == "1" ]]; then
  NI="$(load_image project-nomad-admin)" || exit 2; MI="$(load_image project-nomad-mysql)" || exit 2; RI="$(load_image project-nomad-redis)" || exit 2
  NS="$VAULT/state/project-nomad"; mkdir -p "$NS/storage" "$NS/mysql" "$NS/redis"; SECRETS="$NS/secrets.env"
  if [[ ! -f "$SECRETS" ]]; then python3 - "$SECRETS" <<'PY'
import pathlib,secrets,sys
p=pathlib.Path(sys.argv[1]); p.write_text("ENDWORLD_NOMAD_APP_KEY="+secrets.token_hex(32)+"\nENDWORLD_NOMAD_DB_PASSWORD="+secrets.token_hex(24)+"\nENDWORLD_NOMAD_DB_ROOT_PASSWORD="+secrets.token_hex(24)+"\n"); p.chmod(0o600)
PY
  fi
  set -a; source "$SECRETS"; set +a
  docker network inspect endworld-nomad >/dev/null 2>&1 || docker network create endworld-nomad >/dev/null
  docker run -d --name endworld-nomad-mysql --restart unless-stopped --network endworld-nomad -e MYSQL_ROOT_PASSWORD="$ENDWORLD_NOMAD_DB_ROOT_PASSWORD" -e MYSQL_DATABASE=nomad -e MYSQL_USER=nomad_user -e MYSQL_PASSWORD="$ENDWORLD_NOMAD_DB_PASSWORD" -v "$NS/mysql:/var/lib/mysql" "$MI" >/dev/null
  docker run -d --name endworld-nomad-redis --restart unless-stopped --network endworld-nomad -v "$NS/redis:/data" "$RI" >/dev/null
  for _ in {1..60}; do docker exec endworld-nomad-mysql mysqladmin ping -h 127.0.0.1 -uroot -p"$ENDWORLD_NOMAD_DB_ROOT_PASSWORD" --silent >/dev/null 2>&1 && break; sleep 2; done
  docker exec endworld-nomad-mysql mysqladmin ping -h 127.0.0.1 -uroot -p"$ENDWORLD_NOMAD_DB_ROOT_PASSWORD" --silent >/dev/null 2>&1 || { echo "Project NOMAD MySQL did not become ready" >&2; exit 2; }
  NP="${ENDWORLD_PROJECT_NOMAD_PORT:-8090}"
  docker run -d --name endworld-nomad-admin --restart unless-stopped --network endworld-nomad --add-host host.docker.internal:host-gateway -p "$NP:8080" -v "$NS/storage:/app/storage" -v /var/run/docker.sock:/var/run/docker.sock -e NODE_ENV=production -e PORT=8080 -e HOST=0.0.0.0 -e URL="http://endworld-nomad.local:$NP" -e APP_KEY="$ENDWORLD_NOMAD_APP_KEY" -e NOMAD_STORAGE_PATH="$NS/storage" -e DB_HOST=endworld-nomad-mysql -e DB_PORT=3306 -e DB_DATABASE=nomad -e DB_NAME=nomad -e DB_USER=nomad_user -e DB_PASSWORD="$ENDWORLD_NOMAD_DB_PASSWORD" -e DB_SSL=false -e REDIS_HOST=endworld-nomad-redis -e REDIS_PORT=6379 "$NI" >/dev/null
fi
echo "ENDWORLD $PROFILE stack started."
