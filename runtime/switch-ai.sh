#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PROFILE="${ENDWORLD_PROFILE:-nomad}"; MODE="${1:-general}"; VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
[[ -d "$VAULT" ]] || VAULT="$ROOT/vault/$PROFILE"; LOCK="$VAULT/lock/$PROFILE.lock.json"
if [[ -f /etc/endworld/profile.env ]]; then set -a; source /etc/endworld/profile.env; set +a; elif [[ -f "$ROOT/config/$PROFILE.env" ]]; then set -a; source "$ROOT/config/$PROFILE.env"; set +a; fi
[[ "$PROFILE" == "nomad" && -f "$LOCK" ]] || { echo "NOMAD frozen lock required" >&2; exit 2; }
case "$MODE" in lite) MID="${ENDWORLD_AI_LITE_MODEL_ID:-qwen3-8b-q4}";; general) MID="${ENDWORLD_AI_GENERAL_MODEL_ID:-qwen3-30b-a3b-q4}";; coder) MID="${ENDWORLD_AI_CODER_MODEL_ID:-qwen3-coder-30b-a3b-q4s}";; *) echo "Usage: $0 {lite|general|coder}" >&2; exit 2;; esac
read_lock(){ python3 - "$LOCK" "$1" "$2" "$3" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
for r in d.get(sys.argv[2],[]):
    if r.get("id")==sys.argv[3]:
        v=r.get(sys.argv[4])
        if v is not None: print(v)
        break
PY
}
MREL="$(read_lock artifacts "$MID" path)"; IMG="$(read_lock containers llama-server image)"; IREL="$(read_lock containers llama-server path)"
[[ -f "$VAULT/$MREL" && -f "$VAULT/$IREL" ]] || { echo "Frozen AI assets missing" >&2; exit 2; }
docker load -i "$VAULT/$IREL" >/dev/null; docker rm -f endworld-ai >/dev/null 2>&1 || true
docker run -d --name endworld-ai --restart unless-stopped --network host -v "$VAULT/ai/models:/models:ro" "$IMG" -m "/models/$(basename "$MREL")" --host 0.0.0.0 --port 8082 -c "${ENDWORLD_AI_CONTEXT:-32768}" --threads "${ENDWORLD_AI_THREADS:-$(nproc)}" >/dev/null
mkdir -p "$VAULT/state/runtime"; printf '%s\n' "$MODE" > "$VAULT/state/runtime/ai-mode"; echo "ENDWORLD NOMAD AI mode: $MODE ($MID)"
