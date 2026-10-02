# Offline factory

The connected builder can freeze the Debian bootstrap and every appliance OS
package before deployment. This closes the gap where the vault was frozen but
the operating-system rebuild still depended on Debian mirrors.

## Create while connected

```bash
sudo python3 scripts/offline_factory.py create \
  --profile nano \
  --suite trixie \
  --out /media/archive/ark-factory
```

The factory contains:

- a `debootstrap --make-tarball` bootstrap set;
- a profile-specific recursive APT package cache;
- `Packages` / `Packages.gz` metadata for a local APT repository;
- a SHA-256 `factory-manifest.json`.

Verify later with:

```bash
python3 scripts/offline_factory.py verify --factory /media/archive/ark-factory
```

## Build with WAN absent

```bash
sudo ENDWORLD_FACTORY_DIR=/media/archive/ark-factory \
  bash scripts/build_disk_image.sh nano dist/endworld-nano-amd64.img
```

The image builder unpacks the frozen bootstrap tarball and bind-mounts the
local APT repository into the chroot for package installation. It restores
normal Debian source definitions in the finished field image, but they are not
used to build it.

## Offline map derivation

Planetiler auxiliary inputs are also frozen artifacts in every profile:
water polygons, Natural Earth and lake centerlines. `prepare_profile.py`
passes their local paths and no longer uses Planetiler's `--download` path.

Package ecosystems beyond the appliance OS remain governed by
`snapshot_packages.py`, including APT, PyPI, npm, Maven, Cargo, Go and OCI
for CIVILIZATION.
