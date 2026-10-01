# Ark-to-Ark replication

THE ARK final tier is a **protocol between nodes**, not simply a larger disk.

## What the mesh does

`scripts/ark_mesh.py` gives two disconnected Arks a deterministic exchange format:

```text
Ark A vault
  ↓ inventory
8 MiB content-addressed chunks
  ↓ compare with Ark B inventory
only missing hashes
  ↓
verified .tar capability pack
  ↓ USB / SSD / trusted LAN transfer
Ark B chunk store
  ↓ restore
frozen vault bytes + original lock/BOM
```

Every chunk is addressed by SHA-256. Identical chunks across different files or profiles are stored once in the shared object store, so NANO/FAMILY/NOMAD/CIVILIZATION can deduplicate common content.

## Create an inventory and local object store

```bash
python scripts/ark_mesh.py inventory \
  --vault vault/nomad \
  --profile nomad \
  --store ark-store \
  --out nomad.inventory.json
```

## Compare two Arks

```bash
python scripts/ark_mesh.py diff \
  --source nomad.inventory.json \
  --target peer.inventory.json
```

## Create a pack containing only missing chunks

```bash
python scripts/ark_mesh.py pack \
  --source-inventory nomad.inventory.json \
  --target-inventory peer.inventory.json \
  --store ark-store \
  --out nomad-to-peer.arkpack.tar
```

## Verify and ingest it on the peer

```bash
python scripts/ark_mesh.py verify-pack nomad-to-peer.arkpack.tar

python scripts/ark_mesh.py apply-pack nomad-to-peer.arkpack.tar \
  --store ark-store \
  --inventory-out received.inventory.json
```

## Reconstruct a lost vault

```bash
python scripts/ark_mesh.py restore \
  --inventory received.inventory.json \
  --store ark-store \
  --target-vault recovered-vault
```

The reconstructed files are checked against their full-file SHA-256 after chunk assembly.

## Mutable state is deliberately separate

Forgejo repositories, Syncthing state, Project NOMAD databases, IDE workspaces and other live data change after boot. They are not part of the immutable lock.

Export them separately:

```bash
python scripts/ark_mesh.py state-export \
  --vault /srv/endworld \
  --profile nomad \
  --out nomad-state.tar
```

The state archive can contain passwords, private repositories or personal files. Encrypt/protect it in transit.

## Offline updates

`scripts/update_bundle.py` remains the generation-to-generation update mechanism. Ark Mesh moves capability chunks between peers; update bundles move one trusted locked generation to the next.

## Geographic redundancy

`config/ark-cluster.yml` defines the reference policy:

- at least 3 immutable copies;
- at least 2 mutable-state copies;
- at least 1 powered-off cold copy;
- geographic separation for the final ARK.

Do not count three disks in the same room as three disaster domains.

## Security boundary

Ark packs are data. Applying a pack never executes transferred payloads. The target should still verify release/update signatures when those are available.
