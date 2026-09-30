# Local AI

## Runtime

THE ARK uses a frozen llama.cpp container and GGUF models stored in `ai/models`.

The stable local endpoint is:

`http://NODE:8082`

The portal proxies chat to that endpoint.

## Profile models

### NANO

Qwen3 4B Q4_K_M.

Goal: compact CPU-friendly assistant.

### FAMILY

Qwen3 8B Q4_K_M.

Goal: stronger household/general assistant.

### NOMAD

Three modes:

- **lite** — Qwen3 8B Q4_K_M;
- **general** — Qwen3 30B-A3B Q4_K_M;
- **coder** — Qwen3-Coder 30B-A3B Instruct Q4_K_S.

Switch with:

```bash
make nomad-ai-lite
make nomad-ai-general
make nomad-ai-coder
```

## Why switch instead of serving everything

Keeping multiple large GGUFs loaded simultaneously would unnecessarily raise RAM requirements.

NOMAD keeps the API stable while replacing the model behind it.

## Context

Current defaults:

- NANO: 4096;
- FAMILY: 8192;
- NOMAD: 32768.

Real usable context depends on model behavior, RAM and runtime performance.

## GPU

GPU acceleration can materially improve throughput, but the portability baseline is CPU operation.

## RAG direction

Qdrant exists in NOMAD as the vector layer. Full automatic RAG ingestion over the Ark's document/code corpus remains a roadmap item; Kiwix knowledge and llama.cpp are currently separate operational capabilities.


## CIVILIZATION

CIVILIZATION deliberately reuses NOMAD's three-model policy. Its storage increase is spent primarily on dependency closure, maps and reconstruction corpora rather than loading ever-larger models by default. The same `lite/general/coder` switch is supported.
