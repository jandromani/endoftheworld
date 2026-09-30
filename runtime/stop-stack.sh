#!/usr/bin/env bash
set -euo pipefail
docker rm -f endworld-kiwix endworld-ai endworld-whisper endworld-syncthing endworld-forgejo endworld-qdrant endworld-code-server endworld-nomad-admin endworld-nomad-mysql endworld-nomad-redis >/dev/null 2>&1 || true
