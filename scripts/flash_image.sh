#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 2; }
IMAGE="${1:-}"
DEVICE="${2:-}"
[[ -f "$IMAGE" ]] || { echo "Image not found: $IMAGE" >&2; exit 2; }
[[ -b "$DEVICE" ]] || { echo "Not a block device: $DEVICE" >&2; exit 2; }
[[ "$DEVICE" != /dev/loop* ]] || { echo "Refusing loop device." >&2; exit 2; }

root_src="$(findmnt -n -o SOURCE / || true)"
if [[ "$root_src" == "$DEVICE"* ]]; then echo "REFUSING: $DEVICE contains the running root filesystem." >&2; exit 3; fi

image_bytes="$(stat -c %s "$IMAGE")"
device_bytes="$(blockdev --getsize64 "$DEVICE")"
(( device_bytes >= image_bytes )) || { echo "Device is too small." >&2; exit 2; }

echo "DANGER: this will erase ALL data on $DEVICE"
lsblk -o NAME,SIZE,MODEL,FSTYPE,MOUNTPOINTS "$DEVICE"
if [[ "${ENDWORLD_FLASH_CONFIRM:-}" != "YES" ]]; then
  read -r -p "Type the exact device path ($DEVICE) to continue: " confirm
  [[ "$confirm" == "$DEVICE" ]] || { echo "Cancelled."; exit 1; }
fi

while read -r m; do [[ -n "$m" ]] && umount "$m"; done < <(lsblk -nrpo MOUNTPOINTS "$DEVICE" | grep '^/' || true)

if [[ -f "$IMAGE.sha256" ]]; then
  (cd "$(dirname "$IMAGE")" && sha256sum -c "$(basename "$IMAGE.sha256")")
fi

echo "Flashing THE ARK image..."
dd if="$IMAGE" of="$DEVICE" bs=16M iflag=fullblock oflag=direct status=progress conv=fsync
sync
partprobe "$DEVICE" 2>/dev/null || true
echo "Flash complete. Boot the target machine from $DEVICE."
