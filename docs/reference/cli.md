# CLI Reference

Primary entrypoint:

`python scripts/endworld.py --profile <profile> <command>`

The appliance installs `endworld` as a wrapper around the same CLI.

## Profiles

`nano` · `family` · `nomad`

## Commands

- `plan` — resolve sources and storage envelope without downloading
- `acquire` — download, verify and freeze artifacts/containers
- `prepare` — create derived artifacts and BOM
- `verify` — re-hash the vault against the lock
- `selftest` — validate profile/runtime contracts
- `run` — start local runtime
- `stop` — stop runtime
- `status` — health checks
- `build-image` — build raw bootable image
- `flash <device>` — write image to target device
- `doctor` — builder/runtime prerequisites
- `scout` — capability scouting
- `ai-mode lite|general|coder` — NOMAD model switch

Each implemented profile also has Make aliases such as `nomad-plan`, `nomad-acquire`, `nomad-run` and `nomad-image`.
