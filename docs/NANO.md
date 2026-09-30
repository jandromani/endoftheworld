# ENDWORLD NANO

Target: **64 GB class**.

NANO is the first usable ENDWORLD profile. It is intentionally biased toward the capabilities that remain valuable on a small SSD: a broad Spanish knowledge base, medical reference, local inference, speech recognition, Spain map data, mesh/off-grid communication software and enough source material to rebuild the core.

## Current payload

The exact size changes with upstream releases. The builder enforces a 64,000,000,000-byte target with 8 GB reserved for filesystem/runtime growth.

Core payload:

- Spanish Wikipedia, full MAXI ZIM (largest component)
- Spanish medicine ZIM
- optional Spanish Wikisource if budget permits
- Qwen3 4B Q4_K_M GGUF
- Whisper small
- Geofabrik Spain OSM PBF
- Bitchat Android APK
- Meshtastic Android APK
- Organic Maps Android APK when a compatible release asset is available
- Meshtastic firmware release bundle when available
- frozen Reticulum source
- frozen Project NOMAD source
- Kiwix server container
- llama.cpp server container

## Build

NANO has an **online acquisition phase** and an **offline runtime phase**.

### 1. Prepare a Linux builder

Recommended:

- Debian/Ubuntu
- Python 3.11+
- Docker + Docker Compose v2
- at least 80 GB free storage
- a reliable Internet connection for acquisition

### 2. Install the builder dependency

```bash
make setup
```

### 3. Resolve everything without downloading it

```bash
make nano-plan
```

This contacts upstream indexes/APIs and shows what would be acquired. It does not execute downloaded artifacts.

### 4. Acquire and freeze

```bash
make nano-acquire
```

Downloads are written below:

```
vault/nano/
```

Interrupted large downloads use `.part` files and can be resumed by running the command again.

The completed acquisition writes:

```
vault/nano/lock/nano.lock.json
```

Every frozen file is recorded with provenance, byte size and SHA-256.

### 5. Verify

```bash
make nano-verify
```

Verification re-hashes the entire frozen vault and fails on missing, changed or corrupted artifacts.

## Go offline

Disconnect the WAN and run:

```bash
make nano-run
```

The runtime:

1. verifies the vault;
2. loads the saved Kiwix and llama.cpp container images from disk;
3. starts the Kiwix library on port 8081;
4. starts local Qwen inference on port 8082;
5. starts the ENDWORLD portal on port 8080;
6. exposes the APK/firmware/source vault over the local HTTP server.

Open:

```
http://NODE-IP:8080
```

A phone or tablet only needs to join the same LAN/Wi-Fi and open a browser.

## What NANO deliberately does not do yet

NANO v0.1 is the minimum end-to-end skeleton. It does not yet create a bootable disk image, configure a Wi-Fi access point/DNS captive portal, pre-render OSM into browser tiles, or install NOMAD itself into the runtime. Those belong to the next NANO milestones after the acquisition/runtime path is proven.

## Trust model

A frozen artifact is not automatically trusted just because it downloaded successfully. The SHA-256 lock protects against later corruption/change; provenance and promotion policy remain separate concerns. Unknown capabilities must not be auto-executed or auto-promoted.
