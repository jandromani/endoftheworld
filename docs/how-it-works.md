# How THE ARK Works

This is the literal build path from Git repository to offline computer.

## 1. Git is the control plane

The repository stores small reproducibility material:

```text
profiles/
manifests/
scripts/
runtime/
config/
docs/
```

It does not attempt to commit Wikipedia/models/maps into Git.

## 2. Capability catalog: what are we watching?

`manifests/capabilities.yml`

This is the scouting radar.

An entry here means: “this project may be useful; track it”.

It does **not** mean the capability ships in a product.

## 3. Profile manifest: what must this Ark carry?

Examples:

`profiles/nano.yml`

`profiles/nomad.yml`

A profile defines:

- exact disk target;
- reserve/headroom;
- artifacts;
- required vs optional policy;
- source resolver;
- maximum expected size;
- destination;
- containers;
- maps to derive;
- policy.

This is the product contract.

## 4. Plan: resolve before downloading

`scripts/acquire.py plan`

Resolvers turn moving upstreams into concrete candidates.

Supported source types include:

- direct URL;
- latest matching item in an index;
- GitHub release asset;
- GitHub source snapshot.

Planning checks the storage envelope first.

Required content gets priority over optional content.

## 5. Acquire: fill the warehouse

`scripts/acquire.py acquire`

Content lands under:

`vault/<profile>/`

Typical layout:

```text
knowledge/zim/
ai/models/
maps/raw/
apps/android/
firmware/
source/
tools/
web/vendor/
containers/
lock/
state/
```

Acquisition treats downloads as data and does not execute downloaded artifacts.

## 6. Lock: write the receipt

`vault/<profile>/lock/<profile>.lock.json`

Records concrete facts such as:

- artifact ID;
- resolved source;
- release/ref/version metadata;
- local path;
- bytes;
- SHA-256;
- upstream checksum result;
- frozen container image/path.

If upstream changes later, the old lock still describes the old frozen Ark.

## 7. Prepare: make raw content useful

`scripts/prepare_profile.py`

Example:

```text
spain-YYMMDD.osm.pbf
          ↓ Planetiler
spain.pmtiles
```

Prepared output is added to the lock and budget-checked.

CIVILIZATION also has a package snapshot stage that materializes selected APT/PyPI/npm dependencies while connected.

## 8. BOM: machine-readable inventory

`scripts/generate_bom.py`

writes a CycloneDX inventory:

`<profile>.cdx.json`

The lock is the runtime truth; the BOM is a standard inventory/export view.

## 9. Verify

`scripts/verify_vault.py`

recomputes hashes and ensures local bytes still match the frozen lock.

## 10. Runtime

`runtime/start-stack.sh`

loads frozen container TARs and starts profile services.

The local portal provides discovery and a simple UI.

Mutable service data lives under `state/` so normal operation does not invalidate the frozen vault.

## 11. Image build

`scripts/build_disk_image.sh`

creates:

- GPT partition table;
- BIOS boot support;
- EFI boot support;
- Debian root filesystem;
- ENDWORLD data filesystem;
- runtime;
- frozen vault.

## 12. Flash and boot

`scripts/flash_image.sh`

writes the raw image to a real block device.

After boot, systemd starts networking, the portal, the frozen stack and health checks.

## The most important rule

The public Internet can change.

The field node should not silently change with it.

So the update model is:

```text
discover → review → acquire → verify → freeze → build → promote
```

not:

```text
field node → pull latest from Internet forever
```
