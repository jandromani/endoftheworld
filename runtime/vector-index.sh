#!/usr/bin/env bash
set -euo pipefail
VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
for _ in $(seq 1 90); do
  curl -fsS http://127.0.0.1:8084/health >/dev/null 2>&1 &&
  curl -fsS http://127.0.0.1:6333/healthz >/dev/null 2>&1 && break
  sleep 2
done
curl -fsS http://127.0.0.1:8084/health >/dev/null
curl -fsS http://127.0.0.1:6333/healthz >/dev/null
exec python3 /opt/endworld/scripts/vector_index.py --vault "$VAULT"
