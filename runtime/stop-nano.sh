#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker compose -f "$ROOT/runtime/compose.nano.yml" down || true
if [[ -f "$ROOT/runtime/.portal.pid" ]]; then
  kill "$(cat "$ROOT/runtime/.portal.pid")" 2>/dev/null || true
  rm -f "$ROOT/runtime/.portal.pid"
fi
echo "ENDWORLD NANO stopped."
