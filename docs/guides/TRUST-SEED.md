# Release trust, Secure Boot and Ark cloning

## Boot trust

AMD64 images install Debian's signed shim and signed GRUB fallback chain:

```text
UEFI firmware
  -> EFI/BOOT/BOOTX64.EFI   (Debian/Microsoft-signed shim)
  -> EFI/BOOT/grubx64.efi   (Debian-signed GRUB)
  -> signed Debian kernel
```

The NANO-MINI offline gate verifies that both EFI binaries contain signatures.
Physical Secure Boot behavior still belongs in the hardware campaign.

## Release key

Generate the project/release key on an offline machine and keep the private key
off GitHub:

```bash
python3 scripts/release_trust.py keygen \
  --private ark-release-private.pem \
  --public ark-release-public.pem
python3 scripts/release_trust.py fingerprint \
  --public-key ark-release-public.pem
```

Publish the public key and fingerprint independently (README/release page,
printed kit sheet, and another trusted channel). A public key stored only on
the same removable medium does not protect against replacement of that medium.

The builder can include the public-key fingerprint in release metadata through
`ENDWORLD_SIGNING_PUBLIC_KEY`, and sign through `ENDWORLD_SIGNING_KEY`.

Verify both signature and payload bytes:

```bash
python3 scripts/release_trust.py verify --file release.json \
  --public-key ark-release-public.pem --signature release.sig

python3 scripts/release_trust.py verify-materials --manifest release.json \
  --image endworld-nano-amd64.img \
  --lock nano.lock.json --bom nano.cdx.json
```

## Signed update bundles

`update_bundle.py` can sign the whole offline update TAR. Applying with
`--require-signature` refuses unsigned or incorrectly signed media.

## Ark creates another Ark

On a running physical Ark:

```bash
sudo ark-clone /dev/sdX
```

The command:

1. refuses the running source disk and mounted targets;
2. requires typing the exact target path;
3. recreates BIOS/EFI/ROOT/DATA partitions;
4. copies the appliance root and frozen/mutable data;
5. installs BIOS, UEFI and signed shim/GRUB boot chains;
6. verifies the copied frozen vault.

The clone keeps mutable state and credentials. Rotate them when the clone
belongs to a different trust owner.

The DATA partition expands to the real target capacity on boot. NANO uses a
58 GB image while retaining the same 52 GB usable payload envelope as the
previous 64,000,000,000-byte layout, so common 64 GB-class media are less
likely to be rejected solely because their actual capacity is smaller.
