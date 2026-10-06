#!/usr/bin/env bash
set -euo pipefail
ROOTFS="${1:-/}"
ROOT_UUID="${2:-}"
ESP="$ROOTFS/boot/efi"
shim="$ROOTFS/usr/lib/shim/shimx64.efi.signed"
mm="$ROOTFS/usr/lib/shim/mmx64.efi.signed"
grub="$ROOTFS/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed"
for p in "$shim" "$mm" "$grub"; do
  [[ -f "$p" ]] || { echo "Secure Boot asset missing: $p" >&2; exit 2; }
done
dest="$ESP/EFI/BOOT"
mkdir -p "$dest"
install -m 0644 "$shim" "$dest/BOOTX64.EFI"
install -m 0644 "$grub" "$dest/grubx64.efi"
install -m 0644 "$mm" "$dest/mmx64.efi"
if [[ -n "$ROOT_UUID" ]]; then
  cat > "$dest/grub.cfg" <<EOF
search --no-floppy --fs-uuid --set=root $ROOT_UUID
set prefix=(\$root)/boot/grub
configfile \$prefix/grub.cfg
EOF
else
  cat > "$dest/grub.cfg" <<'EOF'
search --no-floppy --label ENDWORLD_ROOT --set=root
set prefix=($root)/boot/grub
configfile $prefix/grub.cfg
EOF
fi
echo "Installed Debian-signed shim -> signed GRUB fallback chain."
