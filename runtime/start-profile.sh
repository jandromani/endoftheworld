#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-${ENDWORLD_PROFILE:-nano}}"
VAULT="${ENDWORLD_VAULT:-$ROOT/vault/$PROFILE}"
PIDFILE="$ROOT/runtime/.portal-$PROFILE.pid"
LOGFILE="$ROOT/runtime/portal-$PROFILE.log"
ENVFILE="$ROOT/config/$PROFILE.env"

[[ -f "$VAULT/lock/$PROFILE.lock.json" ]] || {
  echo "$PROFILE not acquired. Run: python scripts/endworld.py --profile $PROFILE acquire" >&2
  exit 2
}
[[ -f "$ENVFILE" ]] && set -a && source "$ENVFILE" && set +a
python3 "$ROOT/scripts/verify_vault.py" --vault "$VAULT" --profile-id "$PROFILE"

ENDWORLD_PROFILE="$PROFILE" ENDWORLD_VAULT="$VAULT" bash "$ROOT/runtime/start-stack.sh"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
fi
nohup env ENDWORLD_PROFILE="$PROFILE" ENDWORLD_VAULT="$VAULT"   python3 "$ROOT/runtime/server.py" --profile "$PROFILE" --bind 0.0.0.0 --port 8080   --portal "$ROOT/runtime/portal" --vault "$VAULT" >"$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"; IP="${IP:-127.0.0.1}"
echo
echo "ENDWORLD ${PROFILE^^} ONLINE"
echo "Portal:    http://$IP:8080"
echo "Knowledge: http://$IP:8081"
echo "AI API:    http://$IP:8082"
echo "Maps:      http://$IP:8080/map.html"
[[ "${ENDWORLD_ENABLE_SYNCTHING:-0}" == "1" ]] && echo "Syncthing: http://$IP:8384"
[[ "${ENDWORLD_ENABLE_FORGEJO:-0}" == "1" ]] && echo "Forgejo:   http://$IP:3000"
echo
