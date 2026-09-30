#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="${ENDWORLD_VAULT:-$ROOT/vault/nano}"
PIDFILE="$ROOT/runtime/.portal.pid"
LOGFILE="$ROOT/runtime/portal.log"

[[ -f "$VAULT/lock/nano.lock.json" ]] || { echo "NANO not acquired. Run: make nano-acquire"; exit 2; }
python3 "$ROOT/scripts/verify_vault.py" --vault "$VAULT"

ENDWORLD_VAULT="$VAULT" bash "$ROOT/runtime/start-stack.sh"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
fi
nohup python3 "$ROOT/runtime/server.py" --bind 0.0.0.0 --port 8080 --portal "$ROOT/runtime/portal" --vault "$VAULT" >"$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"; IP="${IP:-127.0.0.1}"
echo
echo "ENDWORLD NANO ONLINE"
echo "Portal:    http://$IP:8080"
echo "Knowledge: http://$IP:8081"
echo "AI API:    http://$IP:8082"
echo "Map:       http://$IP:8080/map.html"
echo
