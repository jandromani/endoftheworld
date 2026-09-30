# Overview

## Mission

THE ARK preserves **operational capability** for disconnected environments.

It is built around the ENDWORLD engine: a manifest-driven pipeline that resolves public upstream sources while online, downloads them into quarantine, records provenance and hashes, prepares derived assets, freezes containers, and assembles a bootable offline appliance.

## The problem

Most modern tools quietly depend on external systems:

- documentation websites;
- search engines;
- package registries;
- app stores;
- container registries;
- SaaS control planes;
- cloud model APIs;
- online maps.

A conventional backup preserves bytes but often leaves the user without the software, indexes, interfaces or dependencies needed to use those bytes.

THE ARK therefore asks a different question:

> What must be preserved so a person can still **do useful work** offline?

## Product ladder

### NANO

The smallest useful Ark: reference knowledge, medicine, maps, local AI, transcription and resilient communications.

### FAMILY

A household node: more knowledge, stronger AI, replication and a local software forge.

### NOMAD

A technical rebuild node: coding AI, developer references, an IDE, vector search, native toolchains, repair/DIY/survival knowledge and Project NOMAD.

### CIVILIZATION

Planned multi-terabyte profile focused on rebuilding broader technical systems: package ecosystems, CAD, engineering, science, infrastructure and larger educational corpora.

### ARK

Planned maximum-preservation tier focused on long-term replication, geographic redundancy, recovery procedures and preservation closure.

## What THE ARK is not

It is not:

- a promise that all Internet content can be preserved;
- a replacement for professional emergency planning;
- a reason to ignore normal backups;
- an automatically self-updating field appliance;
- a single giant Git repository full of binaries.

Git is the control plane. Large assets belong in the vault.

## Design principles

1. Internet is a build dependency, not a runtime dependency.
2. Required capabilities fail closed.
3. Optional content never crowds out required content.
4. Unknown downloads are data until verified and promoted.
5. Runtime state is separate from immutable frozen content.
6. Profiles share one engine.
7. Claims must match the actual acceptance level.
