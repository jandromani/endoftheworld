#!/usr/bin/env bash
set -euo pipefail
MARKER=/var/lib/endworld/data-expanded
[[ -f "$MARKER" ]] && exit 0
src="$(findmnt -no SOURCE /srv/endworld 2>/dev/null || true)"
[[ "$src" == /dev/* ]] || { echo "DATA is not a block partition; skip expansion."; exit 0; }
part="$(lsblk -no PARTN "$src" 2>/dev/null | tr -d ' ')"
parent="$(lsblk -no PKNAME "$src" 2>/dev/null | tr -d ' ')"
[[ -n "$part" && -n "$parent" ]] || { echo "Cannot identify DATA parent; skip."; exit 0; }
disk="/dev/$parent"
echo "Expanding ENDWORLD DATA partition $src on $disk to available device capacity."
parted -s "$disk" resizepart "$part" 100%
partprobe "$disk" || true
udevadm settle || true
resize2fs "$src"
mkdir -p "$(dirname "$MARKER")"
printf 'expanded %s\n' "$(date -u +%FT%TZ)" > "$MARKER"
