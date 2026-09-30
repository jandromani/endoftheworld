# Storage Model

## Why profiles use exact sizes

A profile is intended to become a raw disk image. Its target size is therefore an explicit byte contract.

Current targets:

| Profile | Raw target | Reserve | Acquisition headroom |
|---|---:|---:|---:|
| NANO | 64 GB | 12 GB | 4 GB |
| FAMILY | 256 GB | 24 GB | 20 GB |
| NOMAD | 1 TB | 150 GB | 100 GB |
| CIVILIZATION | 4 TB | 700 GB | 400 GB |

## Terms

### Target

Exact raw-image size.

### Reserve

Space intentionally unavailable to the immutable payload envelope. It protects room for the root filesystem, operational overhead and profile policy.

### Acquisition headroom

Space reserved during acquisition for frozen containers and derived outputs.

### Artifact ceiling

`target - reserve - acquisition_headroom`

Required artifacts must fit beneath this ceiling before acquisition begins.

## Why NOMAD leaves free space

A rebuild workstation needs working room after installation.

Mutable consumers include:

- Forgejo repositories;
- Syncthing replicas;
- Qdrant indexes;
- code-server workspaces;
- Project NOMAD databases/storage;
- generated documents;
- future operator data.

Filling a 1 TB profile to 99% with read-only archives would make the node less useful.

## Vault layout

Typical paths:

```text
knowledge/zim/
ai/models/
maps/raw/
maps/tiles/
apps/android/
firmware/
source/
tools/
web/vendor/
containers/
lock/
state/
```

Everything except `state/` belongs conceptually to the frozen profile.

## Mutable state

Mutable state is deliberately not included in frozen artifact hashes because legitimate operation changes it continuously.

Back it up separately.

## Filesystem model

The image uses:

- GPT;
- BIOS_GRUB;
- EFI;
- ext4 root;
- ext4 ENDWORLD_DATA.

The data filesystem is mounted at `/srv/endworld`.
