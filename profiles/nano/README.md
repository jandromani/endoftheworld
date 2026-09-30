# 🛟 THE ARK · NANO

**64 GB · SURVIVE**

NANO is the smallest complete Ark profile: a portable offline reference and communications node.

## Mission

Keep a useful core available on modest hardware: Spanish knowledge, medicine, local AI, speech transcription, Spain maps, field communications tools and verified frozen provenance.

## Core stack

- Kiwix
- Qwen3 4B Q4
- whisper.cpp Small
- Spain OSM → PMTiles
- Bitchat Android
- Meshtastic Android
- Reticulum
- preserved Project NOMAD source

## Storage contract

- Target: 64,000,000,000 bytes
- Reserve: 12 GB
- Acquisition headroom: 4 GB
- Root boundary: 8192 MiB

## Build

```bash
make nano-plan
make nano-acquire
make nano-prepare
make nano-verify
make nano-selftest
make nano-image
```

## Acceptance

Software/CI implemented. Physical field proof still requires a full real acquisition, image build, flash and disconnected hardware boot.
