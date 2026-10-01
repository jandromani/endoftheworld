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
- `ai-mode lite|general|coder` — NOMAD/CIVILIZATION model switch\n- `index` — rebuild the local FTS5 search index

Each implemented profile also has Make aliases such as `nomad-plan`, `nomad-acquire`, `nomad-run` and `nomad-image`.

## Additional operator tools

- `bash scripts/ark-gui.sh` — local browser builder
- `python scripts/release_trust.py ...` — release manifests and detached signatures
- `python scripts/update_bundle.py ...` — create, verify and apply offline update bundles
