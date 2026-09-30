#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
[[ -d "$VAULT" ]] || VAULT="$ROOT/vault/nano"

if ! command -v docker >/dev/null; then echo "docker missing" >&2; exit 2; fi
if ! docker info >/dev/null 2>&1; then echo "docker daemon unavailable" >&2; exit 2; fi

mkdir -p "$VAULT/.state"
if [[ ! -f "$VAULT/.state/containers-loaded" ]]; then
  shopt -s nullglob
  for tar in "$VAULT"/containers/*.tar; do
    echo "Loading $(basename "$tar")"
    docker load -i "$tar" >/dev/null
  done
  date -u +%FT%TZ > "$VAULT/.state/containers-loaded"
fi

docker rm -f endworld-kiwix endworld-ai >/dev/null 2>&1 || true

mapfile -t ZIMS < <(find "$VAULT/knowledge/zim" -maxdepth 1 -type f -name '*.zim' -printf '%f\n' | sort)
if (( ${#ZIMS[@]} == 0 )); then echo "No ZIM files found" >&2; exit 2; fi
ZIM_ARGS=()
for z in "${ZIMS[@]}"; do ZIM_ARGS+=("/data/$z"); done

docker run -d --name endworld-kiwix --restart unless-stopped --network host   -v "$VAULT/knowledge/zim:/data:ro"   ghcr.io/kiwix/kiwix-serve:3.8.2   --port=8081 "${ZIM_ARGS[@]}" >/dev/null

MODEL="$VAULT/ai/models/Qwen3-4B-Q4_K_M.gguf"
if [[ ! -f "$MODEL" ]]; then echo "AI model missing: $MODEL" >&2; exit 2; fi
THREADS="${ENDWORLD_AI_THREADS:-$(nproc)}"
docker run -d --name endworld-ai --restart unless-stopped --network host   -v "$VAULT/ai/models:/models:ro"   ghcr.io/ggml-org/llama.cpp:server   -m /models/Qwen3-4B-Q4_K_M.gguf --host 0.0.0.0 --port 8082 -c 4096 --threads "$THREADS" >/dev/null

echo "Kiwix :8081 and local AI :8082 started."
