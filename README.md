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
**Payload policy:** up to 56 GB frozen payload + 8 GB runtime/filesystem reserve.

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld

make setup
make nano-plan       # resolve sources, download nothing
make nano-acquire    # acquire + hash + freeze
make nano-verify     # re-hash the vault

# disconnect Internet here
make nano-run
```

Open `http://NODE-IP:8080` from any device on the LAN.

NANO currently provides a local portal, Kiwix knowledge service, llama.cpp local AI service, an Android APK vault, OSM Spain data, Meshtastic firmware, and frozen source for critical communication/core components.

See [docs/NANO.md](docs/NANO.md).

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
nano          tens of GB
family        hundreds of GB
nomad         ~1 TB class
civilization  multi-TB
ark           maximum preservation
```

## Principle

> Internet is a build-time dependency, not a run-time dependency.

