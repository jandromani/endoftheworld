# THE ARK Roadmap

The roadmap grows capability density rather than simply filling larger disks.

## ✅ NANO — 64 GB — SURVIVE

Mission: a portable offline reference node.

Implemented:

- bootable Debian appliance;
- BIOS + UEFI;
- Spanish knowledge and medicine;
- local AI;
- Whisper;
- Spain PMTiles;
- Bitchat / Meshtastic / Reticulum;
- integrity lock + BOM;
- local portal and Wi-Fi/LAN access.

## ✅ FAMILY — 256 GB — LIVE + SHARE

Mission: household continuity.

Adds:

- bilingual knowledge;
- stronger local AI;
- Iberian maps;
- Organic Maps;
- Syncthing;
- Forgejo;
- persistent household mutable state.

## ✅ NOMAD — 1 TB — REBUILD + CREATE

Mission: retain technical creation capability.

Adds:

- switchable lite/general/coder AI;
- Stack Overflow + devdocs;
- electronics, Arduino and Raspberry Pi references;
- repair, survival and appropriate-technology corpus;
- Qdrant;
- code-server;
- native developer toolchains;
- Project NOMAD admin with frozen DB/cache dependencies;
- Spain + Portugal + France maps;
- expanded source preservation.

## ✅ CIVILIZATION — 4 TB — RECONSTRUCT

Implemented foundation:

- immutable APT package snapshot seeded from reconstruction toolchains;
- immutable PyPI wheel and npm cache snapshots;
- OCI Distribution registry source plus existing frozen container TARs;
- KiCad, FreeCAD, OpenSCAD and Blender source preservation;
- electronics datasheets and component knowledge;
- NumPy, SciPy, SymPy, scikit-learn and JupyterLab source preservation;
- engineering and OpenFOAM source preservation;
- agriculture and food systems;
- water, sanitation and energy;
- medical/clinical reference expansion;
- full Europe OSM → PMTiles continental map;
- offline education curricula;
- larger multimodal local models;
- local OCR/vision;
- search/RAG across curated documents and code.

The design goal is **rebuild practical infrastructure**, not preserve every byte on the Internet.

## ✅ ARK software architecture — DISTRIBUTE + EVOLVE

Implemented software foundation:

- bounded offline Agent with audited allowlisted tool use;
- persistent scheduler, local event queue and reboot recovery;
- specialist roles plus coordinator without permission escalation;
- signed content-addressed Ark Mesh capability packs;
- immutable generation metadata, cold-storage exports and rollback metadata;
- multi-node redundancy planner with copy/site/role requirements;
- receive-only RTL-SDR field workflow and radio inventory;
- power-policy events feeding the offline scheduler;
- Scout → untrusted proposal → static inspection → local Agent analysis → explicit human approval;
- verified offline factory and dependency closure;
- universal lexical/vector/Kiwix knowledge federation.

The remaining ARK gap is **physical deployment evidence**, not a missing software
control plane: multiple real nodes, distinct sites, storage/media refresh and
real power/radio hardware must still be exercised and documented.

## Roadmap R2–R4 milestone

Software shipped on the roadmap branch:

- evidence-only multi-hardware physical campaign gate;
- Debian signed shim → signed GRUB Secure Boot fallback path;
- release material verification and public-key fingerprints;
- signed offline update bundles with enforced verification;
- `ark-clone` for human-approved offline Ark-to-Ark disk replication;
- NANO distribution image reduced to 58 GB while preserving the previous 52 GB usable payload envelope;
- first-boot DATA expand-to-fill.

These are software gates. **Physical field proof remains unclaimed** until real
reports from actual machines are committed.

## Roadmap R5–R6 milestone

Software on the factory/knowledge branch adds:

- a hashed offline Debian factory containing a debootstrap seed and local APT closure;
- image rebuild through `ENDWORLD_FACTORY_DIR` without public package mirrors;
- frozen Planetiler auxiliary datasets so PMTiles preparation does not fetch hidden inputs;
- universal lexical indexing for text/code, PDF, EPUB, DOCX and OCR images;
- Poppler + Spanish/English Tesseract in NOMAD/CIVILIZATION and in factory closure;
- a frozen local embedding model, local embedding endpoint and Qdrant ingestion for rich profiles;
- portal and agent retrieval federated across lexical, vector and Kiwix evidence.

## Roadmap R7–R10 milestone

Software adds:

- **R7 FIELD:** receive-only RTL-SDR inventory/capture plan, retained SatDump/Reticulum/Meshtastic layers and power transitions as local events;
- **R8 MESH:** optionally mandatory signed capability packs, generations, cold export/restore and geographic redundancy planning;
- **R9 EVOLUTION:** discovery remains untrusted; static inspection + local Agent analysis + explicit human approval are required before manifest review;
- **R10 ARK:** persistent offline scheduler, event queue, reboot recovery, bounded specialist roles, coordinator and a read-only organism status surface.

No software test may convert simulated hardware/sites into a physical
field-proof claim.

## Roadmap R11–R13 pre-hardware closure

Before the first physical NANO field drive, software now additionally provides:

- safer local Builder flash selection: running root, mounted disks and undersized targets are blocked;
- pre-acquisition storage and transfer-time estimates;
- signed public release bundle creation/verification with a release manifest, SBOM, SHA-256 set and key fingerprint;
- an explicit trust policy with vulnerability-report enforcement and reproducibility comparison;
- code-aware symbol indexing for Python and common systems/application languages, including frozen source archives;
- a public release runbook that keeps cryptographic promotion separate from physical field proof.

Remaining R11–R13 work is deliberately narrower: packaged Windows/macOS prebuilt-image UX,
curated upstream signature coverage, full bilingual portal/docs parity and corpus-scale/reconstruction
evidence from real complete profile builds.

## Cross-cutting work

- stronger first-boot provisioning;
- signed release metadata;
- offline package mirror tooling;
- hardware compatibility matrix;
- automated image smoke tests where practical;
- RAG/index builders;
- storage deduplication;
- per-capability license metadata;
- field-test reports;
- recovery drills.

## Definition of “done”

No profile is considered physically field-proven until a real full-size payload has been acquired, built, flashed and repeatedly operated with WAN removed.


### CIVILIZATION storage contract

- 4 TB decimal raw image
- 700 GB protected reserve
- 400 GB acquisition/derived headroom
- 64 GiB root boundary
- package snapshots are generated before prepare/BOM and become normal hashed lock artifacts

The package layer deliberately snapshots **downloaded dependency closure**, not merely mirror software source.


---

## Frontier epics

The product ladder and frontier backlog are related but not identical. Profiles define **what an Ark carries**; frontier epics define **what the platform must learn to do next**.

| Epic | Primary unlock |
|---|---|
| [#8 Zero-touch builder](https://github.com/jandromani/endoftheworld/issues/8) | adoption across every profile |
| [#9 Boot-chain trust](https://github.com/jandromani/endoftheworld/issues/9) | trusted releases / field promotion |
| [#10 Universal search & RAG](https://github.com/jandromani/endoftheworld/issues/10) | NOMAD → CIVILIZATION knowledge plane |
| [#11 Software closure & updates](https://github.com/jandromani/endoftheworld/issues/11) | CIVILIZATION |
| [#12 Ark-to-Ark replication](https://github.com/jandromani/endoftheworld/issues/12) | final ARK |
| [#13 Power/radio resilience](https://github.com/jandromani/endoftheworld/issues/13) | field-ready NANO/FAMILY/NOMAD |
| [#14 Physical proof](https://github.com/jandromani/endoftheworld/issues/14) | every profile before “field-proven” |

The final ARK tier should emerge from #9 + #11 + #12 + #13 + #14, not from simply allocating a larger disk.

---

## ARK Mesh / field-resilience milestone

The software MVP for frontier epics #12–#14 now adds:

- content-addressed Ark-to-Ark inventories and capability packs;
- verified reconstruction and separate mutable-state backup;
- power telemetry with opt-in low-power service shedding;
- generated Reticulum/field communications plans;
- reproducible physical field reports and an evidence-only hardware matrix.

This does **not** promote the project to “field-proven”. That requires committed
reports from real BIOS/UEFI, storage, Wi-Fi and power/radio hardware under
disconnected recovery drills.
