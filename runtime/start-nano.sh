#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="${ENDWORLD_VAULT:-$ROOT/vault/nano}"
LOCK="$VAULT/lock/nano.lock.json"
PORTAL="$ROOT/runtime/portal"
PIDFILE="$ROOT/runtime/.portal.pid"
LOGFILE="$ROOT/runtime/portal.log"

if [[ ! -f "$LOCK" ]]; then
  echo "ENDWORLD NANO is not acquired yet: $LOCK is missing."
  echo "Run: make nano-acquire"
  exit 2
fi

python3 "$ROOT/scripts/verify_vault.py" --vault "$VAULT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for Kiwix and local AI runtime."
  exit 2
fi

for image_tar in "$VAULT"/containers/*.tar; do
  [[ -e "$image_tar" ]] || continue
  echo "Loading offline container: $(basename "$image_tar")"
  docker load -i "$image_tar" >/dev/null
done

docker compose -f "$ROOT/runtime/compose.nano.yml" up -d

rm -f "$PORTAL/files"
ln -s "$VAULT" "$PORTAL/files"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Portal already running."
else
  nohup python3 -m http.server 8080 --bind 0.0.0.0 --directory "$PORTAL" >"$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
fi

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
IP="${IP:-127.0.0.1}"

echo
echo "ENDWORLD NANO ONLINE"
echo "Portal:    http://$IP:8080"
echo "Knowledge: http://$IP:8081"
echo "Local AI:  http://$IP:8082"
echo "APKs:      http://$IP:8080/files/apps/android/"
echo
echo "No Internet connection is required after the vault is acquired."
