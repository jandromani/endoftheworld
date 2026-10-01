# Deep Software Closure & Offline Updates

Issue: #11

CIVILIZATION now defines seven package ecosystems:

- APT;
- PyPI;
- npm;
- Maven;
- Cargo/crates;
- Go modules;
- OCI images.

Run:

```bash
make civilization-snapshot-packages
```

Each ecosystem becomes:

`vault/civilization/packages/<ecosystem>.snapshot.tar`

Each TAR is hashed and inserted into the profile lock. A `RESTORE.txt` inside each snapshot describes the intended offline restore path.

## Execution policy

APT, PyPI, npm, Cargo, Go and OCI snapshotting download/package content without executing target package code.

Maven is the documented exception: THE ARK invokes a pinned Apache Maven dependency plugin in a disposable builder directory to resolve closure. Target application libraries are not executed.

## Offline update bundles

Given two complete vault generations:

```bash
python scripts/update_bundle.py create \
  --base-vault /ark-old \
  --new-vault /ark-new \
  --profile civilization \
  --out civilization-update.tar
```

Verify:

```bash
python scripts/update_bundle.py verify civilization-update.tar
```

Apply:

```bash
python scripts/update_bundle.py apply civilization-update.tar \
  --target-vault /srv/endworld
```

Application is refused unless the target lock SHA-256 exactly matches the declared base generation.

Changed payload files are staged and verified before promotion. The new lock is written last.

Old orphaned payloads are not automatically deleted.

Sign the update TAR with `scripts/release_trust.py sign` before carrying it to another Ark.

## Still open

- broader ecosystem seed sets;
- full Debian repository snapshots;
- content-addressed chunk-level deduplication;
- binary delta compression;
- automatic A/B image rollback.
