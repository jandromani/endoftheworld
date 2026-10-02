# THE ARK Frontiers

THE ARK's long-term goal is not “store more files”. It is to preserve enough **capability, trust, usability and redundancy** that the system remains useful when normal infrastructure is unavailable.

The backlog is organized as seven engineering epics. The GitHub issues are the live execution layer; this document explains why each frontier exists and what “done” means.

## 1. 🖱️ Zero-touch Ark — Issue #8\n\n**Status: 🟨 advanced MVP shipped.** Local browser builder + secure first boot + capacity/mount/root disk guards + pre-acquisition estimates are implemented. Packaged Windows/macOS prebuilt-image UX and the first published signed image remain.

**Goal:** a non-technical user can create an Ark without understanding Linux.

- desktop builder GUI;
- signed prebuilt image releases;
- Windows builder path;
- macOS builder path;
- first-boot browser wizard;
- credential rotation on first boot;
- safer disk-selection UX;
- download/space/time estimates;
- recovery-friendly rollback UI.

**Done means:** choose profile → build/download → flash → boot → configure, without reading shell scripts.

Track: https://github.com/jandromani/endoftheworld/issues/8

## 2. 🔐 Trusted Ark — Issue #9\n\n**Status: 🟨 advanced software shipped.** Secure Boot, signed release/update metadata, public release bundle verification, SBOM policy, vulnerability-report blocking, reproducibility comparison and key-recovery guidance are implemented. Curated upstream signature coverage and an actual published signed RC/stable release remain.

**Goal:** strengthen the trust chain from source acquisition to the machine that actually boots.

- Secure Boot;
- signed image metadata;
- signed update bundles;
- stronger upstream signature verification;
- SBOM/vulnerability policy;
- reproducible-build comparison for selected critical binaries;
- key rotation and recovery procedures.

**Done means:** an operator can prove which trusted Ark release produced the bytes being booted.

Track: https://github.com/jandromani/endoftheworld/issues/9

## 3. 🔎 Ask the whole Ark — Issue #10\n\n**Status: 🟨 advanced software shipped.** FTS5 + Kiwix + local vectors/Qdrant cover documents, inventory, PDF/EPUB/DOCX/OCR and code; code symbols are extracted for Python and common systems/application languages, including frozen source archives. Corpus-scale evidence and full multilingual portal/docs parity remain.

**Goal:** one local knowledge surface over everything preserved.

- unified lexical search;
- Qdrant ingestion;
- RAG with citations to exact frozen sources;
- code-aware indexing;
- OCR;
- indexing for non-Kiwix documents;
- multilingual portal and documentation.

**Done means:** one question can search books, code, PDFs and local docs and answer with links back to the exact frozen source.

Track: https://github.com/jandromani/endoftheworld/issues/10

## 4. 📦 Deep software closure & offline updates — Issue #11\n\n**Status: 🟨 MVP shipped.** CIVILIZATION now snapshots APT/PyPI/npm/Maven/Cargo/Go/OCI and supports verified changed-artifact update bundles. Full mirrors, chunk-level dedup and A/B rollback remain.

CIVILIZATION already snapshots selected APT/PyPI/npm dependency closure. The next step is broader rebuildability.

- Maven;
- Cargo/crates;
- Go modules;
- OCI image content;
- Debian repository metadata;
- deterministic restore commands;
- offline update bundle format;
- delta updates;
- rollback;
- content-addressed deduplication.

**Done means:** selected software ecosystems can be rebuilt and upgraded without public registries.

Track: https://github.com/jandromani/endoftheworld/issues/11

## 5. 🤝 Ark-to-Ark replication & the final ARK — Issue #12

**Status: 🟨 MVP shipped.** Content-addressed chunks, peer inventories, missing-chunk packs, verified restore, mutable-state export/import and a reference multi-node replication policy are implemented. Real multi-site deployments and encrypted peer transport remain.

**Goal:** stop thinking of the final ARK as one giant disk.

- peer inventory exchange;
- verified capability-pack transfer;
- content-addressed chunks;
- cross-profile deduplication;
- mutable-state backup;
- offline peer update exchange;
- geographic redundancy;
- cold-storage export sets;
- final multi-node ARK protocol/profile.

**Done means:** losing one node does not mean losing the preserved capability.

Track: https://github.com/jandromani/endoftheworld/issues/12

## 6. 🔌 Energy, radio & beyond-IP resilience — Issue #13

**Status: 🟨 MVP shipped.** Linux/NUT power telemetry, opt-in service shedding, generated Reticulum configuration and a Meshtastic/SDR field plan are implemented. Real UPS/solar/radio hardware evidence remains.

A computer without power or communications is only a box.

- UPS telemetry;
- solar/battery telemetry;
- power budgets;
- low-power mode;
- automatic NANO-mode failover;
- configured Reticulum interfaces;
- deeper Meshtastic workflows;
- SDR receiving;
- satellite weather/data reception;
- packet-radio gateways;
- printable field plans.

**Done means:** THE ARK remains useful when mains power and normal IP networking are unreliable or absent.

Track: https://github.com/jandromani/endoftheworld/issues/13

## 7. 🧪 Physical proof — Issue #14

**Status: 🟨 evidence harness shipped.** The cold-boot/offline field-test protocol and evidence-only hardware matrix are implemented. The matrix deliberately remains UNVERIFIED until real hardware reports are committed.

Repository CI is not field evidence.

- BIOS hardware matrix;
- UEFI hardware matrix;
- Wi-Fi AP matrix;
- GPU/CPU inference matrix;
- SSD/NVMe endurance guidance;
- cold-boot protocol;
- repeated disconnected drills;
- integrity scrub schedule;
- media refresh procedure;
- reproducible field-test reports.

**Done means:** supported combinations have documented real offline boot/recovery evidence.

Track: https://github.com/jandromani/endoftheworld/issues/14

---

## How the layers relate

```text
README
  └── simple public promise + 7 frontier epics

docs/frontiers.md
  └── full technical intent and definitions of done

ROADMAP.md
  └── which product generation unlocks which frontier

GitHub Issues #8–#14
  └── executable engineering backlog
```

## The north star

The final ARK is not a “20 TB apocalypse hard drive”.

It is a **multi-node, verifiable, reproducible preservation system** that can lose a machine, lose the Internet, exchange verified capability with another Ark and still recover.
