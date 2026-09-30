# ENDWORLD

**Civilization-in-a-box.**

ENDWORLD builds reproducible offline capability packs from public upstream projects and datasets while the Internet is available, freezes them with provenance and integrity metadata, and serves them locally when the Internet is not.

## Model

```
Internet -> SCOUT -> QUARANTINE -> VERIFY -> FREEZE -> ENDWORLD IMAGE -> OFFLINE NODE
```

ENDWORLD is not one giant Git repository and it is not just a pile of ISOs. This repository is the **control plane**: manifests, acquisition policy, build logic, verification, orchestration and offline runtime configuration. Large artifacts live in a content store/NAS/SSD and are assembled into profiles.

## Capability lifecycle

1. **Scout** — discover new releases and candidate capabilities.
2. **Quarantine** — download without trusting or activating them.
3. **Verify** — license, hashes/signatures, SBOM, malware/vulnerability checks and architecture support.
4. **Test** — install and exercise offline.
5. **Freeze** — pin exact version/commit/digest and retain source + binaries + docs where licensing permits.
6. **Promote** — include only approved capabilities in a stable ENDWORLD profile.
7. **Replicate** — export to SSD/NAS/another ENDWORLD node.

Unknown software is never auto-promoted to the stable image.

## Update cadence

- **Known upstream versions:** scout monthly.
- **Security-critical metadata:** can be checked more frequently.
- **New capability discovery:** monthly report, human review.
- **Stable image rebuild:** quarterly or on demand.
- **Emergency rebuild:** only for an explicitly approved critical fix.

The scheduled GitHub job updates lightweight metadata only. Multi-GB/TB acquisition belongs on an ENDWORLD Builder or self-hosted runner.

## Initial capability families

- Core / offline portal: Project NOMAD
- Knowledge: Kiwix / ZIM
- AI: llama.cpp / Ollama-compatible models
- Communications: Bitchat, Meshtastic, Reticulum
- Maps: Organic Maps / OSM-derived packs
- Radio: SatDump and related receive tooling
- Software vault: source repositories, APKs, package/container mirrors
- Replication: Syncthing / content-addressed archives
- Ledger: Bitcoin Core as an optional archival capability

See `manifests/capabilities.yml`.


## ENDWORLD NANO — implemented

The first runnable profile is now in the repository.

**Target:** 64 GB class  
**Payload policy:** ~48 GB acquisition ceiling + 4 GB derived/container headroom + 12 GB OS/filesystem/runtime reserve.

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld

make builder-deps
make setup
make nano-plan       # resolve sources, download nothing
make nano-acquire    # acquire + hash + freeze
make nano-prepare    # build PMTiles + CycloneDX BOM
make nano-verify     # re-hash the vault
make nano-selftest   # validate profile/runtime wiring
make nano-image      # build 64 GB BIOS+UEFI appliance image

# or test the prepared vault locally:
make nano-run
```

Open `http://NODE-IP:8080` from any device on the LAN.

NANO now wires a local portal, Kiwix, llama.cpp, whisper.cpp transcription, a PMTiles Spain map, Android APK vault, Meshtastic firmware, installed Reticulum tools, frozen Project NOMAD source, local Wi-Fi/DNS, health checks, a capability inventory at `/api/capabilities`, and a guarded bootable-image/flash pipeline. The portal labels each frozen item as a live service, ready download, preserved source, build/runtime dependency, or missing artifact instead of pretending every archived project is already running.

See [docs/NANO.md](docs/NANO.md).

## ENDWORLD FAMILY — implemented

**Target:** 256 GB class  
**Payload policy:** 212 GB acquisition ceiling + 20 GB derived/container headroom + 24 GB OS/filesystem/mutable-state reserve.

FAMILY keeps the NANO lifecycle but expands it into a household appliance:

- Spanish Wikipedia + English Wikipedia without images + Spanish medical/Wikisource.
- Qwen3 8B Q4 local AI and Whisper medium.
- Spain + Portugal PMTiles with runtime map discovery.
- Bitchat, Meshtastic, Organic Maps and Meshtastic firmware.
- Reticulum installed from the frozen source archive.
- Syncthing for trusted household replication.
- Forgejo LTS as a persistent local software forge.
- Frozen source snapshots for Project NOMAD, Syncthing and Forgejo.
- Optional collections such as Wikivoyage, Wikibooks, Gutenberg and Stack Overflow when budget permits.

```bash
make family-plan
make family-acquire
make family-prepare
make family-verify
make family-selftest
make family-image

# local test runtime
make family-run
```

The core runtime, health checks, map discovery and image builder are profile-aware;
FAMILY does not maintain a separate fork of the NANO appliance code.

See [docs/FAMILY.md](docs/FAMILY.md) and [docs/FAMILY_ACCEPTANCE.md](docs/FAMILY_ACCEPTANCE.md).

## ENDWORLD NOMAD — implemented

**Target:** 1 TB decimal. **Role:** rebuild-and-create workstation / offline command center.

NOMAD adds three switchable local AI modes (8B lifeboat, 30B MoE general, 30B MoE coder), Stack Overflow/devdocs/electronics references, iFixit + practical survival/appropriate-technology libraries, Spain/Portugal/France maps, Qdrant, code-server, Forgejo, Syncthing and a frozen Project NOMAD command center. Its rootfs also carries native C/C++, Python, Node.js, Java/Maven, Rust and Go toolchains.

Project NOMAD's updater is intentionally absent from the runtime: new versions flow through ENDWORLD Scout -> quarantine -> verify -> freeze.

```bash
make nomad-plan
make nomad-acquire
make nomad-prepare
make nomad-verify
make nomad-selftest
make nomad-image
make nomad-run
make nomad-ai-coder   # general / lite are also available
```

See [docs/NOMAD.md](docs/NOMAD.md) and [docs/NOMAD_ACCEPTANCE.md](docs/NOMAD_ACCEPTANCE.md).

## Commands (target design)

```bash
endworld scout
endworld acquire --profile family
endworld verify
endworld freeze --profile civilization
endworld export /dev/sdX
endworld status
```

## Profiles

```
nano          64 GB — implemented
family        256 GB — implemented
nomad         1 TB — implemented
civilization  multi-TB — planned
ark           maximum preservation — planned
```

## Principle

> Internet is a build-time dependency, not a run-time dependency.

