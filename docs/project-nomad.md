# Project NOMAD inside THE ARK

[Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad) is an offline-first knowledge/education and application-management platform.

Its upstream Command Center orchestrates Dockerized resources through a browser UI and includes concepts such as local AI/RAG, Kiwix, Kolibri education, offline maps, CyberChef, notes and a Supply Depot app catalog.

## Why include it?

THE ARK had two different problems:

1. **How do we create a reproducible, trusted, bootable preservation appliance?**
2. **How does a human manage a rich collection of offline applications?**

ENDWORLD solves #1.

Project NOMAD is extremely useful for #2.

## Layering

```text
physical disk / Debian
        │
THE ARK / ENDWORLD
        │
        ├── profile contract
        ├── source resolution
        ├── integrity + provenance
        ├── frozen containers
        ├── frozen knowledge/models/maps
        └── image builder
                 │
                 └── NOMAD/CIVILIZATION runtime
                         │
                         └── Project NOMAD Command Center
```

## What is frozen today?

For ENDWORLD NOMAD/CIVILIZATION the profile freezes:

- Project NOMAD admin image;
- MySQL;
- Redis;
- Project NOMAD source snapshot.

Its state is kept outside immutable vault hashing under `state/project-nomad/`.

## Why not let Project NOMAD update itself?

Upstream supports opt-in updates.

That is useful for a normal connected install.

A frozen Ark has a different trust promise: a field node should remain exactly the version we tested.

Therefore the updater sidecar is deliberately excluded. A newer Project NOMAD release should be discovered by Scout, acquired, tested and frozen into a new Ark build.

## Security note

Project NOMAD's application-management architecture requires Docker socket access.

That is a high-trust permission. The README/security docs call it out explicitly, and code-server does not receive the Docker socket by default.

Project NOMAD itself is designed for trusted/offline/local networks and upstream currently does not provide application authentication. Do not expose it directly to the public Internet.
