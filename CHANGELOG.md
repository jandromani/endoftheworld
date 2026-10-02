# Changelog

Notable changes to THE ARK / ENDWORLD are documented here.

## Unreleased

### Pre-hardware release closure
- Hardened local Builder disk selection by blocking root, mounted and undersized targets.
- Added builder storage/download-envelope estimates before acquisition.
- Added signed public release bundles binding image, lock, CycloneDX SBOM, Git revision and release-key fingerprint.
- Added release verification and main-CLI release-create/release-verify commands.
- Added static trust policy, vulnerability-report enforcement and byte-for-byte reproducibility comparison.
- Added code-aware symbol extraction/search for Python plus common JS/TS/Java/Rust/Go/C/C++/shell sources, including frozen source archives.
- Corrected beginner documentation to match secure first-boot credential behavior.


### Field, mesh, evolution and distributed ARK
- Added receive-only RTL-SDR inventory/plan/capture tooling and appliance package closure.
- Added signed Ark Mesh capability packs with optional mandatory signature verification.
- Added immutable generation metadata, cold-storage export/verify/restore and rollback metadata.
- Added multi-node redundancy planning across content copies, node roles and distinct physical sites.
- Added persistent offline Agent scheduling, named local events and interrupted-task recovery.
- Added bounded field/research/engineer/coordinator roles and multi-role orchestration without permission escalation.
- Connected power-mode transitions to persistent local agent events.
- Added approval-gated evolution: Scout proposal → static inspection → local Agent analysis → explicit human approval.
- Added portal/API organism status for roles, scheduler, tasks, mesh generation, evolution and field state.


### Factory and universal knowledge
- Added a verified offline Debian factory with debootstrap seed + local APT package closure.
- Removed hidden Planetiler network dependencies by freezing auxiliary map datasets.
- Added PDF, EPUB, DOCX and image OCR ingestion to the universal search index.
- Added Poppler and Spanish/English Tesseract to rich profiles and factory closure.
- Added frozen local embeddings, Qdrant semantic ingestion and lexical/vector/Kiwix federation.
- Let THE ARK Agent use local semantic retrieval when available.


### Body, trust and seed
- Added an evidence-only multi-hardware physical campaign gate; CI fixtures cannot by themselves claim field proof.
- Added Debian signed shim → signed GRUB Secure Boot fallback installation.
- Added release material binding verification and public-key fingerprints.
- Added signed offline update bundles with optional mandatory signature enforcement.
- Added `ark-clone` to reproduce an Ark onto another local disk without public Internet.
- Added target UUID regeneration and capacity checks during cloning.
- Changed NANO's distribution image target to 58 GB while preserving its 52 GB usable payload envelope.
- Added first-boot DATA expand-to-fill.


### Agent runtime
- Added a bounded offline planner/executor using the existing local llama.cpp service.
- Added allowlisted local tools for search, frozen-source reading, node/maps/mesh status, field notes and safe playbooks.
- Added persistent task state and JSONL audit trails under mutable `state/agent/`.
- Added CLI, local API and portal interfaces.
- Extended the NANO-MINI no-NIC QEMU gate with a real multi-step agent task and permission-denial self-test.

### Trust and repository hygiene
- Added the Apache-2.0 project license for THE ARK control-plane code.
- Consolidated the case-colliding architecture documentation into `docs/ARCHITECTURE.md`.
- Corrected README first-boot credential guidance.


### CIVILIZATION
- Added the 4 TB CIVILIZATION reconstruction profile.
- Added full-Europe PMTiles preparation.
- Added build-time APT, PyPI and npm dependency snapshotting.
- Added CAD/PCB, scientific-computing, GIS/vision and engineering source preservation.
- Promoted CIVILIZATION from roadmap concept to software/CI implementation.
- Switched the README hero to the actual generated Ark illustration.

### Documentation
- Introduced **THE ARK** as the public project identity.
- Added project-wide documentation, governance, profile sheets and operating guides.
- Added a visual product ladder for NANO → FAMILY → NOMAD → CIVILIZATION → ARK.

## 0.3 — 2026-09-30

### Added
- ENDWORLD NOMAD 1 TB profile.
- Switchable lite/general/coder local AI.
- Stack Overflow, devdocs and maker/electronics knowledge.
- Qdrant.
- code-server.
- Native offline developer toolchains.
- Frozen Project NOMAD admin, MySQL and Redis.
- Expanded survival/DIY/repair corpus.
- France map.
- NOMAD CI and acceptance documentation.

### Changed
- Shared runtime extended for NOMAD services.
- Project NOMAD updater deliberately excluded from field runtime.

## 0.2 — 2026-09-30

### Added
- ENDWORLD FAMILY 256 GB profile.
- Syncthing.
- Forgejo.
- Bilingual knowledge expansion.
- Portugal map.
- Generic profile preparation/runtime/image pipeline.
- Full acquisition-path CI fixture.

### Fixed
- SHA-256 parser for standard checksum files.
- GitHub snapshot default-branch resolution.

## 0.1 — 2026-09-30

### Added
- ENDWORLD NANO 64 GB profile.
- Acquisition, verification and frozen lock model.
- Kiwix, llama.cpp and whisper.cpp.
- Spain PMTiles.
- communications APK/firmware vault.
- Reticulum installation.
- bootable BIOS + UEFI image pipeline.
