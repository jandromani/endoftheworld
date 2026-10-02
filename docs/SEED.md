# THE ARK Seed / Clone

A running Ark can create another bootable Ark without using the public Internet.

## Command

```bash
sudo ark-clone /dev/sdX
```

The target must be a whole unmounted disk. The operator must type the exact
device path before destructive work begins.

## What the clone does

1. refuses to target the running Ark disk when it can identify it;
2. creates a fresh GPT layout with BIOS, EFI, ROOT and DATA partitions;
3. formats each target filesystem with new UUIDs;
4. copies the appliance root and `/srv/endworld` vault/state;
5. writes a target-specific `/etc/fstab`;
6. installs BIOS GRUB and removable-path UEFI GRUB;
7. installs the Debian signed shim → signed GRUB fallback chain;
8. verifies the copied frozen vault before declaring success.

The clone retains mutable state. Rotate credentials when ownership/trust changes.

## Expand-to-fill

Distributed NANO images are intentionally smaller than nominal 64 GB media.
On first boot, `endworld-expand-data.service` expands the DATA partition and
ext4 filesystem to consume remaining device capacity.

This avoids assuming every product sold as “64 GB” exposes the exact same
number of bytes.

## Security boundary

`ark-clone` is intentionally destructive and therefore is **not** exposed as
an autonomous agent tool. The human operator remains the approval boundary.

## Physical proof

The clone path is software-ready, but a clone is not considered field-proven
until the source and target have both completed disconnected physical recovery
drills and their reports are committed.
