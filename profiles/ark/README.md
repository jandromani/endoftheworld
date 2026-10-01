# 🛶 THE ARK · ARK

**multi-node preservation protocol · PRESERVE · software MVP implemented**

ARK is not defined as “the biggest disk”. Its first working layer is a protocol
between independent nodes: compare what each node has, transfer only verified
missing content, and reconstruct a lost immutable vault.

## Implemented

- peer inventory exchange;
- 8 MiB SHA-256 content-addressed chunks;
- verified missing-chunk capability packs;
- cross-profile/object-store deduplication;
- full-file verification after reconstruction;
- mutable-state export/import kept separate from the immutable vault;
- offline generation update bundles;
- cold-storage/geographic redundancy policy;
- power/communications field policy;
- physical evidence/report format and hardware matrix.

## Start here

- [Ark Mesh](../../docs/guides/ARK-MESH.md)
- [Field resilience](../../docs/guides/FIELD-RESILIENCE.md)
- [Physical field tests](../../docs/guides/FIELD-TEST.md)
- [Hardware evidence matrix](../../docs/hardware-matrix.md)

## Reference redundancy policy

`config/ark-cluster.yml` starts with:

- 3 immutable copies;
- 2 mutable-state copies;
- 1 powered-off cold copy;
- geographic separation.

These values are an operational starting point, not evidence that a real
distributed deployment already exists.

## What remains

Real multi-site peer deployments, encrypted peer transport UX, automatic peer
discovery, solar/UPS/radio hardware integrations and repeated disaster drills
still require field evidence.

## Principle

The final Ark is not one device. It assumes any single node can disappear.
