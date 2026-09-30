# Scaling ENDWORLD profiles

NANO is the golden template.

A new profile should avoid forking runtime logic unless the hardware or service
model truly changes. Prefer extending the manifest.

## Stable interfaces

Every profile should support:

```
endworld plan
endworld acquire
endworld prepare
endworld verify
endworld build-image
endworld flash
endworld run
endworld status
endworld scout
```

## What belongs in a profile

- target image capacity;
- reserve/headroom;
- required and optional artifacts;
- artifact budget ceilings;
- service/container set;
- post-processing jobs;
- architecture targets;
- hardware expectations.

## What belongs in shared code

- URL/release resolution;
- resumable downloads;
- hashing;
- provenance locks;
- budget enforcement;
- HTTP Range serving;
- health/status API;
- AP/DNS setup;
- image safety checks;
- flashing safety;
- capability discovery.

## Promotion rule

A capability can move:

```
candidate → quarantined → verified → frozen → profile
```

but never directly:

```
candidate → runtime
```

## Suggested next profiles

**FAMILY:** 256–512 GB, more languages, education, ebooks, richer maps, media,
password/file tools.

**NOMAD:** ~1 TB, Project NOMAD runtime, broader ZIM collections, stronger local
AI and RAG.

**CIVILIZATION:** 4 TB class, software/package mirrors, engineering, science,
medical, fabrication and large map coverage.

**ARK:** 8–16 TB+, redundant copies, large source mirrors, multiple model
families, broader cultural preservation and cross-node replication.
