#!/usr/bin/env bash
set -euo pipefail
VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
PROFILE="${ENDWORLD_PROFILE:-nano}"
LOCK="$VAULT/lock/$PROFILE.lock.json"
[[ -x /usr/local/bin/whisper-server-portable ]] || { echo "portable whisper-server missing" >&2; exit 2; }
[[ -f "$LOCK" ]] || { echo "lock missing: $LOCK" >&2; exit 2; }
MODEL_ID="${ENDWORLD_WHISPER_MODEL_ID:-whisper-small}"
MODEL_REL="$(python3 - "$LOCK" "$MODEL_ID" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
for r in d.get("artifacts",[]):
    if r.get("id")==sys.argv[2]:
        print(r.get("path") or "")
        break
PY
)"
[[ -n "$MODEL_REL" && -f "$VAULT/$MODEL_REL" ]] || { echo "Whisper model missing: $MODEL_ID" >&2; exit 2; }
exec /usr/local/bin/whisper-server-portable \
  --host 0.0.0.0 --port 8083 --convert \
  -m "$VAULT/$MODEL_REL" -l "${ENDWORLD_WHISPER_LANGUAGE:-auto}"
