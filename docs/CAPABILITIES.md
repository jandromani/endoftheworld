# THE ARK capability status

This document separates four different meanings of "works":

- **WIRED** — code/configuration exists and is connected to the appliance.
- **CI PROVEN** — the behavior has an automated executable gate.
- **REAL CORE PROVEN** — upstream binaries/models/formats are exercised, not stubs.
- **PHYSICAL PENDING** — USB/SSD/firmware/radio/power behavior still requires real hardware.

## NANO capability matrix

| Plane | Capability | Current software state | Remaining proof |
|---|---|---|---|
| Boot | Hybrid GPT, BIOS + UEFI | WIRED + QEMU proven | external SSD/real firmware |
| Boot trust | Debian shim → signed GRUB → signed kernel | WIRED; enforced Secure Boot QEMU gate | real firmware Secure Boot |
| Storage | ROOT + DATA, expand-to-fill | WIRED; larger virtual-disk gate | real SSD/controller |
| First boot | keyboard, hostname, private console/Wi-Fi credentials | WIRED | interactive physical console + Wi-Fi |
| Network | Ethernet DHCP/mDNS + optional local Wi-Fi AP | WIRED | chipset/AP-mode matrix |
| Knowledge | Wikipedia ES + medicine Kiwix | WIRED; Kiwix API/small-real-ZIM gate | full 40+ GB corpus acquisition |
| Retrieval | FTS5, code symbols, Kiwix-grounded RAG | WIRED + CI | full corpus latency/quality |
| AI | Qwen3-4B Q4 via llama.cpp | WIRED; exact-model real-runtime gate | target-PC speed/RAM |
| Agent | bounded planner/tool loop + audit/workspace | WIRED + no-NIC QEMU | real-model/full-vault tasks |
| Voice | Whisper-small local transcription | WIRED; exact-model + format-conversion gate | microphone/device UX |
| Maps | Spain OSM → PMTiles viewer + labels | WIRED; real Planetiler small-extract gate | full Spain build/runtime measurement |
| Navigation | route planning / geocoder / turn-by-turn | NOT IMPLEMENTED | optional future capability |
| Comms | Reticulum AutoInterface shared daemon | WIRED + boot-service gate | real LAN/radio peer |
| Mobile comms | Bitchat/Meshtastic/Sideband APKs + firmware | PRESERVED/READY | real Android/radio pairing |
| SDR | RTL-SDR receive-only workflow, SatDump source on richer profiles | WIRED | real dongle/antenna |
| Power | Linux/NUT telemetry, survival policy/events | WIRED + fixture CI | real UPS/battery/solar |
| Integrity | SHA-256 lock + CycloneDX SBOM | WIRED + CI | full real lock/BOM |
| Release | signed public release + vulnerability policy | WIRED + CI | first signed NANO RC |
| Flash | Linux/Windows/macOS signed release flasher | packaged CI + write/readback logic | destructive real-device test |
| Clone | Ark-to-Ark whole-disk clone | WIRED after audit fix | SSD A → SSD B |
| Mesh | signed content-addressed packs/generations/cold restore | WIRED + CI | physical peer transfer |
| Evolution | Scout → quarantine → Agent review → human approval → CI | WIRED + CI | operational release cycle |
| GPU | CUDA/ROCm/Vulkan acceleration | NOT WIRED | optional post-NANO optimization |
| Encryption | at-rest full-disk/state encryption | NOT WIRED | optional security trade-off |

## What NANO is intentionally not

NANO is a portable CPU-baseline field node. It is not intended to contain every
reconstruction package or every map on Earth. FAMILY/NOMAD/CIVILIZATION add
sharing, stronger AI, developer stacks, semantic vectors and dependency closure.

## Gate for calling NANO "field proven"

The label is reserved until all of these are real evidence, not fixtures:

1. complete NANO acquisition + prepare + verify;
2. signed RC image created;
3. release flashed and reread successfully on physical SSD;
4. cold boot on at least two distinct x86-64 machines;
5. BIOS and UEFI evidence across the campaign;
6. Secure Boot evidence on compatible firmware;
7. WAN physically removed;
8. portal, Kiwix, Qwen, Agent, Whisper and PMTiles pass;
9. first-boot credentials and Wi-Fi AP tested on real hardware;
10. repeated reboot/integrity checks;
11. Ark A → Ark B clone and boot;
12. recovery from the second Ark.

Until then, use **software-proven** rather than **field-proven**.
