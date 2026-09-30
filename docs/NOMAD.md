# ENDWORLD NOMAD

NOMAD is the 1 TB rebuild-and-create profile. Internet is a build dependency, not a runtime dependency.

## Storage
Exact image: 1,000,000,000,000 bytes. Protected reserve: 150 GB. Acquisition headroom: 100 GB. Artifact ceiling: 750 GB. Root partition ends at 32,768 MiB. The profile intentionally leaves working space for repositories, Qdrant indexes, Project NOMAD state, Syncthing replicas and newly-created data.

## AI modes
One stable llama.cpp API on :8082 can switch between:
- lite — Qwen3 8B Q4_K_M;
- general — Qwen3 30B-A3B Q4_K_M;
- coder — Qwen3-Coder 30B-A3B Instruct Q4_K_S.

Only one 30B-class model runs at once. Use `endworld --profile nomad ai-mode coder|general|lite`.

## Developer plane
The appliance rootfs installs Git, build-essential, CMake/Ninja, Clang/GDB, Python+venv, Node/npm, Java/Maven, Rust/Cargo, Go, SQLite, ripgrep, tmux and Vim. Frozen services add Forgejo (:3000/SSH :2222), code-server (:8443), Qdrant (:6333/:6334), llama.cpp (:8082) and Kiwix (:8081). The vault preserves source for llama.cpp, Qdrant, code-server, PlatformIO, Arduino CLI, ESP32, CyberChef, SatDump, Reticulum, mirror engines and maker projects.

## Survival / DIY / repair
Required knowledge includes water treatment, food preservation, knots, post-disaster recovery, Ready.gov EN+ES, CD3WD appropriate technology, Hundred Rabbits off-grid notes, iFixit EN+ES, home and vehicle repair, gardening, outdoors, ham radio, electronics, Arduino and Raspberry Pi. WikiHow is intentionally absent because ENDWORLD does not pin a provider-removed archive.

## Project NOMAD
The Project NOMAD admin runs at :8090 with frozen MySQL and Redis dependencies. ENDWORLD remains the outer trust boundary. The upstream updater sidecar is intentionally disabled: field nodes do not self-mutate outside Scout -> quarantine -> verify -> freeze -> promote. The admin receives Docker socket access because Supply Depot needs container control; code-server does not receive that socket.

## Mutable state
`state/dev`, `state/qdrant`, `state/syncthing`, `state/forgejo`, `state/project-nomad` and `state/runtime/ai-mode` remain outside immutable vault hashes.

## Hardware
32 GB RAM is the practical floor; 64 GB is preferred for the 30B modes plus services. GPU acceleration is optional; CPU operation remains the portability baseline.
