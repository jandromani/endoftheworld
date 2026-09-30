#!/usr/bin/env bash
set -euo pipefail
docker rm -f endworld-kiwix endworld-ai endworld-whisper >/dev/null 2>&1 || true
