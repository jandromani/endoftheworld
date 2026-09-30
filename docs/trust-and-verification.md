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
