#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v python3 >/dev/null || { echo "python3 is required." >&2; exit 2; }
[[ -x .venv/bin/python ]] || make setup
if ! .venv/bin/python scripts/endworld.py doctor >/dev/null 2>&1; then
  echo "Builder dependencies are incomplete."
  read -r -p "Install Debian/Ubuntu builder dependencies with sudo now? [y/N] " a
  [[ "$a" =~ ^[Yy]$ ]] || exit 2
  sudo bash scripts/install_builder_deps.sh
fi
echo "Authorizing privileged image/flash operations once..."
sudo -v
( while true; do sleep 45; sudo -n true 2>/dev/null || exit 0; done ) &
KEEP=$!
trap 'kill "$KEEP" 2>/dev/null || true' EXIT INT TERM
.venv/bin/python builder/ark_builder.py "$@"
