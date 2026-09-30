# ENDWORLD FAMILY

**Target:** a household-scale, offline-first, 256 GB amd64 appliance.

FAMILY is the second ENDWORLD profile. It keeps NANO's reproducible acquisition,
verification and boot model, but adds enough storage and services for several
people to use the node as a local household infrastructure appliance rather than
only as an emergency reference device.

## Storage contract

- Raw target: **256,000,000,000 bytes**.
- Reserved for OS, filesystem overhead and mutable state: **24 GB**.
- Frozen payload envelope: **232 GB**.
- Acquisition ceiling before containers and derived artifacts: **212 GB**.
- Reserved headroom for frozen containers and derived PMTiles: **20 GB**.
- Root partition: **12,288 MiB**; the remaining disk is the ENDWORLD data partition.

Required artifacts are always reserved before optional artifacts. Optional
collections are admitted only if they fit the acquisition ceiling.

## What FAMILY adds over NANO

### Bilingual library

Required:

- Spanish Wikipedia, full maxi ZIM.
- English Wikipedia, full no-picture ZIM.
- Spanish medical Wikipedia.
- Spanish Wikisource.

Optional, budget permitting:

- Spanish Wikivoyage.
- Spanish Wikibooks.
- Spanish Project Gutenberg.
- Stack Overflow archive.
- Free Programming Books source snapshot.

All ZIM files are served by the same frozen Kiwix service on port 8081.

### Stronger local AI

FAMILY replaces NANO's 4B model with:

- **Qwen3 8B Q4_K_M** through frozen llama.cpp.
- **Whisper medium** through frozen whisper.cpp.
- 8,192-token default context.
- 8 CPU threads by default, configurable in `config/family.env`.

The portal remains an OpenAI-compatible local chat client and local transcription
front end. No Internet is required at runtime.

### Iberian maps

FAMILY freezes dated Geofabrik extracts for Spain and Portugal and derives:

- `spain.pmtiles`
- `portugal.pmtiles`

The portal discovers every PMTiles archive at runtime through `/api/maps`, so
future profiles can add regions without changing the map application.

### Family replication

A frozen Syncthing container is included and exposed on:

- GUI: **8384/tcp**
- Sync: **22000/tcp + 22000/udp**
- Local discovery: **21027/udp**

Its mutable database/configuration lives in:

`/srv/endworld/state/syncthing`

This directory is deliberately outside the frozen lock records. It may change
during normal household use without invalidating the immutable capability vault.

### Local software forge

A frozen Forgejo LTS container is included and exposed on:

- Web: **3000/tcp**
- Git SSH: **2222/tcp**

Mutable Forgejo data lives in:

`/srv/endworld/state/forgejo`

The frozen Forgejo source snapshot is also retained separately for reconstruction
and provenance.

### Communications and mobile recovery

FAMILY keeps the NANO communications layer and makes the richer mobile set
required:

- Bitchat Android APK.
- Meshtastic Android APK.
- Organic Maps Android APK.
- Meshtastic ESP32 firmware.
- Reticulum source; Reticulum CLI is installed into the appliance image.

Project NOMAD source is preserved, but the full NOMAD Command Center remains a
separate future profile to avoid operating two competing control planes.

## Builder workflow

On an x86_64 Debian/Ubuntu builder with ample temporary disk space:

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld

make builder-deps
make setup
make doctor

make family-plan
make family-acquire
make family-prepare
make family-verify
make family-selftest
```

Or:

```bash
make family-all
```

The frozen vault is created at `vault/family/`.

## Local test runtime

```bash
make family-run
```

Services:

- Portal: http://localhost:8080
- Kiwix: http://localhost:8081
- llama.cpp API: http://localhost:8082
- Whisper: http://localhost:8083
- Forgejo: http://localhost:3000
- Syncthing: http://localhost:8384

Stop the stack with:

```bash
make family-stop
```

## Build and flash

```bash
make family-image
make family-flash DEVICE=/dev/sdX
```

Outputs:

```text
dist/endworld-family-amd64.img
dist/endworld-family-amd64.img.sha256
```

The builder reads image size, root partition size, profile id and title directly
from `profiles/family.yml`; there is no separate hard-coded 256 GB image path.

## Boot behavior

At boot FAMILY:

1. mounts the frozen data partition at `/srv/endworld`;
2. starts Docker;
3. reloads every required service image from the frozen container TAR before use;
4. starts Kiwix, llama.cpp and Whisper;
5. starts Syncthing and Forgejo with persistent state directories;
6. starts the ENDWORLD portal;
7. advertises `endworld-family.local` via mDNS;
8. attempts to create the `ENDWORLD-FAMILY` Wi-Fi access point;
9. provides wildcard offline DNS including `end.world`, `git.end.world` and `sync.end.world`;
10. runs the profile-aware health check every five minutes.

## Immutable vs mutable data

The **frozen vault** is verified by SHA-256 and represented in
`family.lock.json` and `family.cdx.json`.

Runtime state under `/srv/endworld/state/` is intentionally mutable. It is not
included in frozen hashes because Syncthing and Forgejo must be able to operate
normally after deployment.

Unknown software is never auto-promoted into the stable image.

## Security note

The first image remains optimized for isolated/offline deployment and inherits
the simple ENDWORLD first-boot credentials. Change the console password, Wi-Fi
password, Syncthing GUI security and Forgejo administrator credentials before
placing the node on an untrusted LAN.

## Hardware

Practical FAMILY baseline:

- x86_64 CPU.
- **16 GB RAM minimum recommended**; 32 GB gives more headroom for the 8B model
  plus household services.
- SSD/NVMe with at least 256,000,000,000 bytes.
- Ethernet strongly recommended.
- Linux-supported Wi-Fi adapter with AP mode if the node must create its own LAN.

GPU acceleration is optional. The default profile remains CPU-safe.

## Acceptance

See [FAMILY_ACCEPTANCE.md](FAMILY_ACCEPTANCE.md).
