#!/usr/bin/env bash
set -euo pipefail
docker rm -f endworld-kiwix endworld-ai endworld-whisper endworld-syncthing endworld-forgejo >/dev/null 2>&1 || true
