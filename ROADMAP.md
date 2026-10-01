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

## 🚧 ARK — maximum — PRESERVE

Candidate goals:

- multi-node content-addressed replication;
- cold-storage export sets;
- geographic redundancy;
- preservation manifests independent of a single filesystem;
- long-term media refresh procedures;
- source + toolchain + build-dependency closure for selected critical software;
- broader cultural/scientific/educational archives;
- reproducible recovery plans from bare hardware.

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
