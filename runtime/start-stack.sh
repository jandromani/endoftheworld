#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="${ENDWORLD_VAULT:-/srv/endworld}"
[[ -d "$VAULT" ]] || VAULT="$ROOT/vault/nano"

command -v docker >/dev/null || { echo "docker missing" >&2; exit 2; }
docker info >/dev/null 2>&1 || { echo "docker daemon unavailable" >&2; exit 2; }

ensure_image(){
  local image="$1" tar="$2"
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    [[ -f "$tar" ]] || { echo "Frozen container missing: $tar" >&2; exit 2; }
    echo "Loading $(basename "$tar")"
    docker load -i "$tar" >/dev/null
  fi
}

ensure_image ghcr.io/kiwix/kiwix-serve:3.8.2 "$VAULT/containers/kiwix.tar"
ensure_image ghcr.io/ggml-org/llama.cpp:server "$VAULT/containers/llama-server.tar"
ensure_image ghcr.io/ggml-org/whisper.cpp:main "$VAULT/containers/whisper-server.tar"

docker rm -f endworld-kiwix endworld-ai endworld-whisper >/dev/null 2>&1 || true

mapfile -t ZIMS < <(find "$VAULT/knowledge/zim" -maxdepth 1 -type f -name '*.zim' -printf '%f\n' | sort)
(( ${#ZIMS[@]} > 0 )) || { echo "No ZIM files found" >&2; exit 2; }
ZIM_ARGS=(); for z in "${ZIMS[@]}"; do ZIM_ARGS+=("/data/$z"); done

docker run -d --name endworld-kiwix --restart unless-stopped --network host   -e PORT=8081   -v "$VAULT/knowledge/zim:/data:ro"   ghcr.io/kiwix/kiwix-serve:3.8.2   "${ZIM_ARGS[@]}" >/dev/null

MODEL="$VAULT/ai/models/Qwen3-4B-Q4_K_M.gguf"
[[ -f "$MODEL" ]] || { echo "AI model missing: $MODEL" >&2; exit 2; }
THREADS="${ENDWORLD_AI_THREADS:-$(nproc)}"
docker run -d --name endworld-ai --restart unless-stopped --network host   -v "$VAULT/ai/models:/models:ro"   ghcr.io/ggml-org/llama.cpp:server   -m /models/Qwen3-4B-Q4_K_M.gguf --host 0.0.0.0 --port 8082 -c 4096 --threads "$THREADS" >/dev/null

WHISPER_MODEL="$VAULT/ai/models/ggml-small.bin"
[[ -f "$WHISPER_MODEL" ]] || { echo "Whisper model missing: $WHISPER_MODEL" >&2; exit 2; }
docker run -d --name endworld-whisper --restart unless-stopped --network host   -v "$VAULT/ai/models:/models:ro"   ghcr.io/ggml-org/whisper.cpp:main   whisper-server --host 0.0.0.0 --port 8083 -m /models/ggml-small.bin >/dev/null

echo "Kiwix :8081, local AI :8082 and Whisper :8083 started."
