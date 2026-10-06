# Security Policy

THE ARK intentionally ingests third-party software and data, so the acquisition boundary is treated as hostile until content is verified and frozen.

## Trust model

```text
untrusted Internet
      ↓
   Scout
      ↓
 Quarantine
      ↓
 Verify
      ↓
  Freeze
      ↓
 trusted profile
```

The acquisition script downloads artifacts but does not execute them.

## Security invariants

- Required artifacts must resolve or acquisition fails.
- Every acquired file receives a local SHA-256.
- Upstream SHA-256 is checked when a source publishes one in a supported form.
- Container images are frozen into local TAR archives.
- Runtime loads the frozen image archive rather than trusting a same-tag local image.
- Paths are constrained to the vault.
- Mutable application state is separated from immutable frozen content.
- Field nodes do not automatically promote new upstream versions.
- Project NOMAD's updater sidecar is disabled in the ENDWORLD NOMAD profile.

## Docker socket

Project NOMAD receives Docker socket access because its application-management model requires it. This is a high-trust boundary: control of that service can imply control of the host Docker daemon. It is therefore limited to the dedicated NOMAD profile and documented as such.

code-server does **not** receive the Docker socket by default.

## First-boot credentials

Build-time templates contain bootstrap credentials, but the supported field flow
keeps the Wi-Fi AP disabled until the console first-boot wizard requires a new
private console password and Wi-Fi password. The resulting profile environment
file is root-only (`0600`), and passwordless sudo/autologin are removed after
setup.

A device that has not completed first boot should be treated as unprovisioned
and must not be left with untrusted physical access.

## Reporting a vulnerability

Please open a GitHub security advisory/private vulnerability report if the repository supports it. If private reporting is unavailable, open a minimal issue asking for a private contact channel without publishing exploit details.

Useful reports include:

- path traversal;
- integrity bypass;
- arbitrary artifact execution;
- malicious source promotion;
- credential exposure;
- unsafe container privilege;
- unauthenticated network control;
- image-builder privilege issues.

## Dependency updates

Security updates are not applied directly to a field node. They should be:

1. discovered;
2. reviewed;
3. acquired in quarantine;
4. verified;
5. tested offline;
6. frozen into a new profile build;
7. deliberately promoted.

This makes update latency a conscious trade-off for reproducibility and supply-chain control.


## Current tamper/confidentiality limits

Secure Boot authenticates the signed firmware-facing boot chain. THE ARK also
hashes frozen vault artifacts and periodically scrubs them against the lock.
Those controls do **not** currently provide full-disk confidentiality or
dm-verity protection for the root filesystem.

Therefore:

- data at rest is not encrypted by default;
- an attacker with prolonged physical media access can read unencrypted data;
- root filesystem mutation is not cryptographically prevented after boot;
- a passing vault scrub detects frozen-content changes but is not a TPM-backed
  measured-boot attestation.

Optional LUKS/TPM/dm-verity hardening is a future security profile, not a
prerequisite for the portable offline NANO field mission.
