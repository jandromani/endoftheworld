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

## Default credentials

The current appliance templates include initial local credentials for convenience during development. They must be changed before use on an untrusted network. See `docs/reference/environment-variables.md`.

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
