#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${ENDWORLD_PROFILE:-nano}"
VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
[[ -d "$VAULT" ]] || VAULT="$ROOT/vault/$PROFILE"
LOCK="$VAULT/lock/$PROFILE.lock.json"

if [[ -f /etc/endworld/profile.env ]]; then
  set -a; source /etc/endworld/profile.env; set +a
elif [[ -f "$ROOT/config/$PROFILE.env" ]]; then
  set -a; source "$ROOT/config/$PROFILE.env"; set +a
fi

[[ -f "$LOCK" ]] || { echo "Frozen lock missing: $LOCK" >&2; exit 2; }
command -v docker >/dev/null || { echo "docker missing" >&2; exit 2; }
docker info >/dev/null 2>&1 || { echo "docker daemon unavailable" >&2; exit 2; }

lock_field(){
  local group="$1" id="$2" field="$3"
  python3 - "$LOCK" "$group" "$id" "$field" <<'PY'
import json,sys
lock=json.load(open(sys.argv[1],encoding="utf-8"))
for rec in lock.get(sys.argv[2],[]):
    if rec.get("id")==sys.argv[3]:
        value=rec.get(sys.argv[4])
        if value is not None: print(value)
        break
PY
}

artifact_path(){
  local rel
  rel="$(lock_field artifacts "$1" path)"
  [[ -n "$rel" ]] || return 1
  printf '%s/%s\n' "$VAULT" "$rel"
}

load_image(){
  local id="$1" image rel tar
  image="$(lock_field containers "$id" image)"
  rel="$(lock_field containers "$id" path)"
  [[ -n "$image" && -n "$rel" ]] || return 1
  tar="$VAULT/$rel"
  [[ -f "$tar" ]] || { echo "Frozen container missing: $tar" >&2; return 1; }
  echo "Loading frozen container $id" >&2
  docker load -i "$tar" >/dev/null
  printf '%s\n' "$image"
}

KIWIX_IMAGE="$(load_image kiwix)" || { echo "Kiwix container unavailable" >&2; exit 2; }
LLAMA_IMAGE="$(load_image llama-server)" || { echo "llama.cpp container unavailable" >&2; exit 2; }
WHISPER_IMAGE="$(load_image whisper-server)" || { echo "whisper.cpp container unavailable" >&2; exit 2; }

docker rm -f endworld-kiwix endworld-ai endworld-whisper endworld-syncthing endworld-forgejo >/dev/null 2>&1 || true

mapfile -t ZIMS < <(find "$VAULT/knowledge/zim" -maxdepth 1 -type f -name '*.zim' -printf '%f\n' | sort)
(( ${#ZIMS[@]} > 0 )) || { echo "No ZIM files found" >&2; exit 2; }
ZIM_ARGS=(); for z in "${ZIMS[@]}"; do ZIM_ARGS+=("/data/$z"); done

docker run -d --name endworld-kiwix --restart unless-stopped --network host   -e PORT=8081 -v "$VAULT/knowledge/zim:/data:ro" "$KIWIX_IMAGE" "${ZIM_ARGS[@]}" >/dev/null

MODEL_ID="${ENDWORLD_AI_MODEL_ID:-qwen3-4b-q4}"
MODEL="$(artifact_path "$MODEL_ID")" || { echo "AI model record missing: $MODEL_ID" >&2; exit 2; }
[[ -f "$MODEL" ]] || { echo "AI model missing: $MODEL" >&2; exit 2; }
THREADS="${ENDWORLD_AI_THREADS:-$(nproc)}"
CONTEXT="${ENDWORLD_AI_CONTEXT:-4096}"
docker run -d --name endworld-ai --restart unless-stopped --network host   -v "$VAULT/ai/models:/models:ro" "$LLAMA_IMAGE"   -m "/models/$(basename "$MODEL")" --host 0.0.0.0 --port 8082 -c "$CONTEXT" --threads "$THREADS" >/dev/null

WHISPER_ID="${ENDWORLD_WHISPER_MODEL_ID:-whisper-small}"
WHISPER_MODEL="$(artifact_path "$WHISPER_ID")" || { echo "Whisper record missing: $WHISPER_ID" >&2; exit 2; }
[[ -f "$WHISPER_MODEL" ]] || { echo "Whisper model missing: $WHISPER_MODEL" >&2; exit 2; }
docker run -d --name endworld-whisper --restart unless-stopped --network host   -v "$VAULT/ai/models:/models:ro" "$WHISPER_IMAGE"   whisper-server --host 0.0.0.0 --port 8083 -m "/models/$(basename "$WHISPER_MODEL")" >/dev/null

if [[ "${ENDWORLD_ENABLE_SYNCTHING:-0}" == "1" ]]; then
  SYN_IMAGE="$(load_image syncthing)" || { echo "Syncthing container unavailable" >&2; exit 2; }
  mkdir -p "$VAULT/state/syncthing"
  chown 1000:1000 "$VAULT/state/syncthing" 2>/dev/null || true
  docker run -d --name endworld-syncthing --restart unless-stopped     -p 8384:8384 -p 22000:22000/tcp -p 22000:22000/udp -p 21027:21027/udp     -v "$VAULT/state/syncthing:/var/syncthing" "$SYN_IMAGE" >/dev/null
fi

if [[ "${ENDWORLD_ENABLE_FORGEJO:-0}" == "1" ]]; then
  FORGEJO_IMAGE="$(load_image forgejo)" || { echo "Forgejo container unavailable" >&2; exit 2; }
  mkdir -p "$VAULT/state/forgejo"
  chown 1000:1000 "$VAULT/state/forgejo" 2>/dev/null || true
  docker run -d --name endworld-forgejo --restart unless-stopped     -e USER_UID=1000 -e USER_GID=1000     -p 3000:3000 -p 2222:22     -v "$VAULT/state/forgejo:/data" "$FORGEJO_IMAGE" >/dev/null
fi

echo "ENDWORLD $PROFILE stack started: Kiwix :8081, AI :8082, Whisper :8083."
[[ "${ENDWORLD_ENABLE_SYNCTHING:-0}" == "1" ]] && echo "Syncthing :8384 / sync :22000."
[[ "${ENDWORLD_ENABLE_FORGEJO:-0}" == "1" ]] && echo "Forgejo :3000 / SSH :2222."
