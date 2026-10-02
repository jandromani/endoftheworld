# Trust & Verification

## Threat model

THE ARK assumes upstream content can be:

- unavailable;
- replaced;
- corrupted;
- unexpectedly larger;
- republished under a moving alias;
- malicious;
- incompatible with the profile.

The project therefore does not treat “download succeeded” as “trusted”.

## Resolution

Sources are resolved into concrete metadata before acquisition whenever possible.

For GitHub snapshots, `default` resolves to the repository's actual default branch. `latest-release` resolves to a release tag when available.

## Budgets

Each artifact has `budget_bytes`.

A required artifact that exceeds its declared budget fails planning.

Optional artifacts may be skipped.

The planner first reserves space for all required items, preventing an early optional artifact from crowding out a later required item.

## Integrity

Every acquired artifact receives a locally computed SHA-256.

When a supported upstream checksum file is available, ENDWORLD extracts and verifies the upstream SHA-256 as well.

The lock records whether upstream checksum verification occurred.

## Containers

Containers are pulled during acquisition and exported into the vault as TAR archives.

At runtime ENDWORLD loads the frozen TAR before starting the service. A mutable local tag is therefore not silently trusted over the frozen profile artifact.

## Source preservation

Source snapshots are often preserved even when a component is not started as a service. This creates a distinction between:

- SERVICE;
- READY/installable artifact;
- PRESERVED source;
- RUNTIME/build dependency.

The portal exposes that distinction rather than pretending every archived project is running.

## Promotion

Scout metadata does not automatically mutate a stable field node.

Recommended lifecycle:

```text
discover → quarantine → verify → test → freeze → promote → replicate
```

## Remaining limitations

SHA-256 proves identity, not benign behavior.

A fully mature supply-chain pipeline could additionally include:

- signature verification;
- SBOM enrichment;
- vulnerability scans;
- malware analysis;
- reproducible-build comparisons;
- license policy;
- maintainer/repository reputation metadata.

Those controls should complement, not replace, offline functional testing.


## Boot-chain trust

Built amd64 images install Debian's signed Secure Boot chain when the signed
packages are available:

```text
UEFI firmware trust store
  -> Debian/Microsoft-trusted shim
  -> Debian-signed GRUB
  -> Debian-signed kernel
  -> THE ARK runtime + frozen vault
```

The removable-media fallback path is `EFI/BOOT/BOOTX64.EFI`. BIOS boot remains
available separately for older hardware.

Secure Boot establishes boot-code provenance; it does not authenticate the
multi-gigabyte vault by itself. Vault identity remains bound by the lock/BOM and
release metadata.

## Signed release material

`release_trust.py` can:

- generate an offline signing key pair;
- create release metadata binding image + lock + CycloneDX BOM + Git revision;
- sign and verify the metadata;
- publish a SHA-256 fingerprint of the public key;
- verify that supplied image/lock/BOM bytes exactly match the signed manifest.

The private release key must not live on a field Ark.

## Signed offline updates

`update_bundle.py` creates changed-artifact bundles tied to an exact base lock.
Bundles can be signed and application can require a valid detached signature
before staging any payload.

Recommended promotion path:

```text
Scout -> review -> acquire -> tests -> frozen generation
      -> signed update/release -> offline verification -> apply
```

## Key rotation and recovery

Keep at least two offline copies of the release public key fingerprint outside
the Ark media. A replacement signing key is a new trust epoch: publish the new
fingerprint through an already trusted channel and never silently overwrite a
field node's trust root.
