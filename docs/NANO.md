# ENDWORLD NANO

**Target:** a self-contained, offline-first, 64 GB-class amd64 appliance.

NANO is the reference implementation for every future ENDWORLD profile. Larger
profiles should change content, hardware expectations and storage budgets while
keeping the same lifecycle and operator commands.

## Lifecycle

```
SCOUT
  ↓
PLAN
  ↓
ACQUIRE → frozen source/binaries/data/container images
  ↓
PREPARE → derived offline artifacts (for example Spain PMTiles)
  ↓
VERIFY → SHA-256 integrity
  ↓
BUILD-IMAGE → Debian appliance + frozen vault
  ↓
FLASH
  ↓
BOOT
  ↓
OFFLINE RUNTIME
```

Internet is required only before the image is frozen.

## NANO payload

The manifest is `profiles/nano.yml`. It currently reserves 12 GB of the
64,000,000,000-byte envelope for the operating system, filesystem overhead and
runtime headroom. The frozen payload is therefore capped at approximately 52 GB.

Required capability families:

- **Knowledge:** Spanish Wikipedia and Spanish medical ZIM content.
- **Local AI:** Qwen3 4B Q4 GGUF through llama.cpp.
- **Speech asset:** Whisper small model is preserved for later/offline tooling.
- **Maps:** Geofabrik Spain OSM PBF plus a derived PMTiles vector map.
- **Android recovery apps:** Bitchat and Meshtastic; Organic Maps when available.
- **Mesh firmware:** Meshtastic ESP32 firmware bundle when available.
- **Network source:** Reticulum source snapshot.
- **Core source:** Project NOMAD source snapshot.
- **Offline web runtime:** pinned MapLibre GL JS and PMTiles browser libraries.
- **Knowledge runtime:** frozen Kiwix container.
- **AI runtime:** frozen llama.cpp server container.

Optional items are skipped automatically if they would break the storage budget.

## Builder quickstart

Use an x86_64 Debian/Ubuntu machine with significantly more than 64 GB free
space because the map derivation phase needs temporary working space.

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld

make builder-deps
make setup
make doctor

make nano-plan
make nano-acquire
make nano-prepare
make nano-verify
```

Or:

```bash
make nano-all
```

The acquisition result lives in `vault/nano/`. Large vault content is
intentionally excluded from Git.

## Build the appliance

```bash
make nano-image
```

This produces:

```
dist/endworld-nano-amd64.img
dist/endworld-nano-amd64.img.sha256
```

The raw disk image uses GPT:

```
1  BIOS_GRUB       ~2 MiB
2  ENDWORLD_EFI   512 MiB   FAT32
3  ENDWORLD_ROOT  ~7.5 GiB  ext4
4  ENDWORLD_DATA  remainder ext4
```

The system partition contains Debian 13 stable, the kernel, GRUB, Docker,
network services and the ENDWORLD runtime. The data partition contains the
frozen vault.

The image supports legacy BIOS and UEFI boot. Secure Boot is not currently
configured; machines enforcing Secure Boot may require it to be disabled.

## Flash

Identify the target device carefully:

```bash
lsblk
make nano-flash DEVICE=/dev/sdX
```

The flasher:

- refuses non-block devices;
- refuses a device containing the running root filesystem;
- checks target capacity;
- verifies the image SHA-256 when present;
- requires the exact device path to be typed before destructive write.

## Boot behavior

At boot NANO automatically:

1. mounts `ENDWORLD_DATA` at `/srv/endworld`;
2. starts Docker;
3. loads frozen container images if needed;
4. starts Kiwix on TCP 8081;
5. starts llama.cpp on TCP 8082;
6. starts the ENDWORLD portal on HTTP port 80;
7. advertises `endworld-nano.local` via mDNS;
8. detects a Wi-Fi device capable of AP mode;
9. when possible, creates the `ENDWORLD-NANO` access point;
10. serves local DNS/DHCP on that isolated Wi-Fi network;
11. runs a health check every five minutes.

Default appliance credentials are intentionally simple for an isolated first
boot and **must be changed if the node will be used around untrusted people**:

```
console user: endworld
console password: endworld

Wi-Fi SSID: ENDWORLD-NANO
Wi-Fi password: endworld-nano
```

Edit `/etc/endworld/nano.env` to change runtime defaults.

## Access from another device

On the ENDWORLD Wi-Fi network:

```
http://end.world/
```

On a normal LAN with mDNS:

```
http://endworld-nano.local/
```

The portal exposes:

- health/storage/battery state;
- Kiwix library;
- local AI chat;
- static Spain PMTiles map;
- downloadable Android APK vault;
- frozen manifest/integrity metadata.

## Local development runtime

A prepared vault can be tested without building the disk image:

```bash
make nano-run
```

The development portal uses port 8080 instead of privileged port 80.

```
http://localhost:8080
http://localhost:8081  # Kiwix
http://localhost:8082  # llama.cpp API
```

Stop it with:

```bash
make nano-stop
```

## Integrity model

Acquisition never executes APKs, firmware or downloaded source code.

The lock records acquired files with provenance, resolved version/release,
byte count and SHA-256. The prepare phase adds derived artifacts to the same
lock. `nano-verify` recalculates every represented file before the appliance
image can be built.

The runtime is intentionally treated as an immutable field node. Updates are
built and tested on a connected Builder, then a new frozen image is flashed.
NANO does not mutate itself from the Internet.

## Hardware expectations

Storage is fixed by the profile. Compute is not.

Recommended practical minimum for the current local AI model:

- x86_64 CPU;
- 8 GB RAM or more;
- 64 GB target flash/SSD with actual capacity >= 64,000,000,000 bytes;
- Ethernet and/or a Linux-supported Wi-Fi adapter with AP mode.

GPU acceleration is not required. A supported GPU can be used in later
profiles, but NANO defaults to CPU-safe llama.cpp execution.

## Known boundaries

These are deliberate NANO boundaries rather than hidden TODOs:

- amd64 appliance image only; ARM64 is a separate future image target.
- no Secure Boot chain yet.
- browser map is a lightweight offline vector map; Organic Maps APK provides
  a richer mobile application path, but NANO does not currently pre-seed its
  proprietary app storage with regional routing data.
- local AI is not yet a full RAG index over the Kiwix corpus; Kiwix and the LLM
  are independent offline capabilities in NANO.
- Wi-Fi AP availability depends on the physical adapter/driver; Ethernet+mDNS
  remains the deterministic fallback.
- GitHub-hosted CI validates code/configuration but cannot prove physical boot
  or radio behavior. See `NANO_ACCEPTANCE.md`.

