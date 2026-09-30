#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-${ENDWORLD_PROFILE:-nano}}"
bash "$ROOT/runtime/stop-stack.sh" || true
PIDFILE="$ROOT/runtime/.portal-$PROFILE.pid"
if [[ -f "$PIDFILE" ]]; then
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
  rm -f "$PIDFILE"
fi
echo "ENDWORLD ${PROFILE^^} stopped."
