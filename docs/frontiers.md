# Frontiers

THE ARK's mission is “the computer at the end of the world”, so the frontier list must include more than software features.

## 1. Usability

### Desktop builder GUI

Goal: choose a profile, destination and storage device without terminal knowledge.

### Signed prebuilt releases

Goal: publish verifiable image releases so ordinary users do not need to reproduce every build.

### First-boot setup

Goal: browser wizard for password, Wi-Fi, hostname, locale, storage and service exposure.

## 2. Platform reach

- Windows builder path.
- macOS builder path.
- ARM64/Raspberry Pi-class image target.
- wider GPU acceleration matrix.

## 3. Trust

- Secure Boot.
- signed release metadata;
- stronger upstream signature verification;
- vulnerability/SBOM policy;
- reproducible-build comparisons for selected critical binaries.

## 4. Unified knowledge

- index non-Kiwix files;
- unified lexical + semantic search;
- automatic ingestion into Qdrant;
- local RAG citations back to exact frozen sources;
- OCR for scanned documents;
- code-aware indexing.

## 5. Software dependency closure

CIVILIZATION begins with APT/PyPI/npm.

Still needed:

- Maven;
- Cargo/crates;
- Go modules;
- OCI registry contents;
- Debian repository metadata/snapshots;
- toolchain-specific dependency closure;
- deterministic restore/install commands.

## 6. Offline updates

A disconnected Ark needs a safe update mechanism:

```text
connected builder
   ↓
signed update pack
   ↓ USB / removable disk / trusted peer
offline Ark
   ↓
verify
   ↓
install alongside previous generation
   ↓
rollback available
```

## 7. Ark-to-Ark replication

- content-addressed chunks;
- deduplication;
- peer inventory exchange;
- verified delta transfer;
- conflict-free mutable-data backup.

## 8. Energy

The best offline server is useless without power.

Future integration could cover:

- UPS state;
- solar/battery telemetry;
- power budgets;
- graceful shutdown;
- low-power service modes;
- “NANO mode” failover.

## 9. Communications beyond normal IP

Current preservation covers Meshtastic/Reticulum/Bitchat and radio tooling sources.

Deeper integration could include:

- configured Reticulum interfaces;
- LoRa service workflows;
- SDR receiving stations;
- satellite weather/data reception;
- packet radio gateways;
- printable frequency/network plans.

## 10. Physical resilience

- supported-hardware matrix;
- BIOS/UEFI regression hardware;
- SSD/NVMe endurance guidance;
- cold-storage copy workflow;
- periodic scrub/hash audits;
- media refresh;
- geographically separate copies.

## 11. Human knowledge

A reconstruction computer should eventually cover:

- medicine and public health;
- water and sanitation;
- agriculture/food preservation;
- power/electrical systems;
- mechanical repair;
- civil construction;
- manufacturing;
- education;
- governance/emergency logistics references where legally redistributable.

## 12. The final ARK profile

The final tier should not be “a 20 TB disk”.

It should be a **multi-node preservation protocol** that can lose a machine and continue.
