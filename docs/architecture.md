# Architecture

## System model

```text
                    PUBLIC INTERNET
                          │
                      [ Scout ]
                          │
                      [ Plan ]
                          │
                   [ Quarantine ]
                          │
                    [ Verification ]
                          │
                      [ Freeze ]
                          │
                     Frozen Vault
                          │
           ┌──────────────┼───────────────┐
           │              │               │
        prepare         runtime          image
        PMTiles         services         builder
           │              │               │
           └──────────────┴───────────────┘
                          │
                     OFFLINE NODE
```

## Control plane

The Git repository contains:

- profile manifests;
- capability metadata;
- acquisition and verification logic;
- preparation logic;
- runtime orchestration;
- portal code;
- image-building logic;
- CI;
- documentation.

It deliberately does **not** contain multi-gigabyte payloads.

## Profiles

A profile YAML is a storage and capability contract.

Key metadata includes:

- exact image target size;
- protected reserve;
- acquisition headroom;
- root filesystem boundary;
- artifacts;
- containers;
- map derivations;
- policy.

The shared engine reads the profile rather than maintaining separate implementations for NANO/FAMILY/NOMAD.

## Acquisition engine

`scripts/acquire.py` supports several source forms:

- direct URL;
- latest matching item in an HTTP index;
- GitHub release asset;
- GitHub source snapshot.

It resolves source metadata first, calculates required and optional envelopes, then downloads only if the required set fits.

## Lock

Acquisition writes a profile lock containing:

- resolved URL;
- version/release/ref metadata;
- local vault path;
- byte size;
- SHA-256;
- upstream checksum result when available;
- frozen container metadata.

The lock becomes the source of truth for runtime loading.

## Preparation

`scripts/prepare_profile.py` creates derived assets after acquisition.

Today the principal derived artifact is PMTiles generated from frozen OSM PBF data using frozen Planetiler.

Derived output is inserted back into the lock and budget-checked.

## Runtime

The runtime is composed of:

- profile environment;
- frozen lock;
- frozen container TARs;
- local portal;
- service launcher;
- health checks;
- network/AP setup;
- mutable state directories.

Services are loaded from frozen TAR files before start.

## Image builder

`scripts/build_disk_image.sh` creates a GPT disk image containing:

- BIOS boot partition;
- EFI partition;
- Debian root filesystem;
- ENDWORLD data partition;
- runtime code;
- frozen vault.

The builder is intentionally Linux/x86-64 oriented today.

## Trust boundaries

The main boundaries are:

1. Internet → quarantine.
2. Quarantine → frozen vault.
3. Frozen vault → runtime.
4. Immutable vault → mutable state.
5. Docker-socket-capable services → host.

See [trust-and-verification.md](trust-and-verification.md).
