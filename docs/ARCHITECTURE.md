# ENDWORLD architecture

ENDWORLD separates **control plane**, **vault**, **derived artifacts** and
**runtime** so the project can scale without turning Git into a multi-terabyte
binary dump.

## Control plane

The Git repository contains:

- profiles and capability policy;
- source resolvers;
- acquisition code;
- integrity verification;
- deterministic post-processing;
- image construction;
- runtime services;
- CI and discovery automation.

## Vault

The vault is generated content:

```
vault/<profile>/
  knowledge/
  ai/
  maps/
  apps/
  firmware/
  source/
  containers/
  web/
  tools/
  lock/
```

It is not committed to Git.

## Frozen lock

`lock/<profile>.lock.json` is the boundary between the online Builder and
offline node. Anything expected to survive without Internet must be represented
there with its provenance and integrity metadata.

## Derived artifacts

Some Internet source material is archival but not directly consumable. ENDWORLD
turns it into runtime-friendly artifacts before freezing the appliance.

NANO example:

```
Spain OSM PBF
    +
Planetiler
    ↓
spain.pmtiles
    ↓
MapLibre + PMTiles browser
```

Planetiler supports generating PMTiles directly from OSM inputs; ENDWORLD keeps
the original PBF as well as the derived map so the capability can be rebuilt.

## Runtime

The runtime does not need an upstream network:

```
                       ┌───────────────┐
phone / laptop ───────►│ ENDWORLD HTTP │
                       └──────┬────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
         Kiwix             llama.cpp          PMTiles
         :8081               :8082             Range
            │
            └──────── APK / firmware / frozen source
```

## Network

The appliance has two access paths.

**Deterministic fallback:** normal Ethernet with DHCP and mDNS,
`endworld-nano.local`.

**Off-grid path:** when Linux reports an AP-capable wireless adapter, NANO
creates an isolated Wi-Fi network, runs DHCP/DNS locally, and resolves
`end.world` to itself.

No Internet routing is required.

## Immutable field nodes

A field node should not silently replace known-good artifacts. Updates belong
on the Builder:

```
monthly scout → human review → acquire → prepare → verify → new image
```

This also makes recovery simple: the immutable image remains the recovery
object.

## Scale axis

The code path stays the same while profiles change:

```
NANO          capacity constrained, portable
FAMILY        broader family knowledge/media
NOMAD         ~1 TB class
CIVILIZATION  multi-TB technical/cultural preservation
ARK           maximum preservation and redundancy
```

The profile, not ad-hoc runtime code, should express those differences.
