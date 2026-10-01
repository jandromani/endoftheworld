#!/usr/bin/env bash
set -euo pipefail
MOUNT="${ENDWORLD_DATA_MOUNT:-/srv/endworld}"
[[ $EUID -eq 0 ]] || { echo "grow-data must run as root" >&2; exit 2; }
PART="$(findmnt -no SOURCE "$MOUNT" 2>/dev/null || true)"
[[ "$PART" == /dev/* ]] || { echo "ARK data mount is not a block partition: $PART"; exit 0; }
PK="$(lsblk -no PKNAME "$PART" 2>/dev/null | head -1 | tr -d ' ')"
NUM="$(lsblk -no PARTN "$PART" 2>/dev/null | head -1 | tr -d ' ')"
[[ -n "$PK" && -n "$NUM" ]] || { echo "Cannot determine parent disk for $PART" >&2; exit 2; }
DISK="/dev/$PK"
DISK_BYTES="$(blockdev --getsize64 "$DISK")"
LAST_END="$(parted -m "$DISK" unit B print 2>/dev/null | awk -F: -v n="$NUM" '$1==n{gsub("B","",$3);print $3}')"
[[ "$LAST_END" =~ ^[0-9]+$ ]] || { echo "Cannot read partition end for $PART"; exit 0; }
FREE=$(( DISK_BYTES - LAST_END ))
if (( FREE < 134217728 )); then echo "ARK data partition already uses the disk."; exit 0; fi
echo "Growing ARK data partition $PART to fill $DISK ($FREE bytes available)"
sgdisk -e "$DISK"
parted -s "$DISK" resizepart "$NUM" 100%
partprobe "$DISK" || true
udevadm settle || true
resize2fs "$PART"
echo "ARK data partition expanded."
