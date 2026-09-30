# Build a Bootable Image

## Requirements

The current image builder expects:

- x86-64 Linux host;
- root/sudo;
- debootstrap;
- GRUB BIOS + EFI tooling;
- partition/filesystem utilities;
- rsync;
- Python + PyYAML;
- enough local scratch and output storage.

Install project prerequisites with:

```bash
make builder-deps
```

## Prerequisites in the vault

Before image build, the selected profile must have:

- frozen lock;
- CycloneDX BOM;
- verified artifacts;
- at least one prepared PMTiles map.

Typical lifecycle:

```bash
make nomad-acquire
make nomad-prepare
make nomad-verify
make nomad-selftest
make nomad-image
```

## Image layout

The builder creates GPT with:

1. BIOS_GRUB;
2. EFI FAT32;
3. root ext4;
4. ENDWORLD_DATA ext4.

The profile controls exact image bytes and root boundary.

## Debian bootstrap

The root filesystem is created with debootstrap and receives:

- kernel;
- GRUB;
- systemd;
- Docker;
- networking/AP packages;
- Python/runtime dependencies;
- profile-specific extras.

NOMAD additionally installs developer toolchains.

## Vault copy

The prepared vault is copied to:

`/srv/endworld`

The profile runtime environment is copied to:

`/etc/endworld/profile.env`

## Reticulum

The builder installs Reticulum from the frozen source archive when present rather than downloading it during first boot.

## Output integrity

After teardown/unmount, the raw image receives a SHA-256 sidecar.

## Practical warning

A sparse 1 TB image still requires careful handling. Flashing, copying and hashing the final raw image can be expensive even when the logical filesystem contains less data.
