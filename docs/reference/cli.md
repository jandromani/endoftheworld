# CLI Reference

Primary entrypoint:

`python scripts/endworld.py --profile <profile> <command>`

The appliance installs `endworld` as a wrapper around the same CLI.

## Profiles

`nano` · `family` · `nomad` · `civilization`

## Commands

- `plan` — resolve sources and storage envelope without downloading
- `acquire` — download, verify and freeze artifacts/containers
- `prepare` — create derived artifacts, BOM and local search index
- `verify` — re-hash the vault against the lock
- `selftest` — validate profile/runtime contracts
- `run` — start local runtime
- `stop` — stop runtime
- `status` — health checks
- `build-image` — build raw bootable image
- `flash <device>` — write image to target device
- `doctor` — builder/runtime prerequisites
- `scout` — capability scouting
- `ai-mode lite|general|coder` — NOMAD/CIVILIZATION model switch
- `index` — rebuild the local FTS5 search index
- `vector-index` — rebuild semantic vectors on rich profiles
- `agent "<goal>" [--role field|research|engineer|coordinator]` — bounded local tool-using task
- `orchestrate "<goal>"` — run bounded specialist roles and a coordinator
- `scheduler ...` — persistent recurring/event-driven agent jobs
- `radio ...` — receive-only field radio inventory/plan/capture
- `mesh ...` — content-addressed Ark-to-Ark exchange and signed packs
- `generations ...` — cold generations, restore, activation and rollback metadata
- `evolution ...` — untrusted capability proposal/inspection/analysis/approval workflow
- `cluster ...` — evaluate multi-node copy/site/role redundancy

Each implemented profile also has Make aliases such as `nomad-plan`, `nomad-acquire`, `nomad-run` and `nomad-image`.

## Additional operator tools

- `bash scripts/ark-gui.sh` — local browser builder
- `python scripts/release_trust.py ...` — release manifests and detached signatures
- `python scripts/update_bundle.py ...` — create, sign, verify and apply offline update bundles
- `ark-clone /dev/<disk>` — human-approved destructive offline clone to another disk
- `ark-field-test ...` — collect real hardware/offline evidence
- `ark-radio ...` — receive-only SDR operations
- `ark-agent-scheduler ...` — direct scheduler/event queue interface
- `ark-orchestrator ...` — direct multi-role orchestration interface

Destructive actions such as flashing/cloning are deliberately not exposed as
autonomous Agent tools.
