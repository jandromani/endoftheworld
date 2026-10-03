#!/usr/bin/env bash
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Run ark-clone with sudo/root." >&2; exit 2; }
TARGET="${1:-}"
[[ -b "$TARGET" ]] || { echo "Usage: ark-clone /dev/DEVICE" >&2; exit 2; }
[[ "$(lsblk -ndo TYPE "$TARGET")" == "disk" ]] || { echo "Target must be a whole disk." >&2; exit 2; }

source_dev="$(findmnt -no SOURCE / 2>/dev/null || true)"
source_parent=""
if [[ "$source_dev" == /dev/* ]]; then source_parent="$(lsblk -no PKNAME "$source_dev" 2>/dev/null | tr -d ' ')"; fi
[[ "/dev/$source_parent" != "$TARGET" ]] || { echo "Refusing to overwrite the running Ark disk." >&2; exit 2; }

if lsblk -nrpo MOUNTPOINT "$TARGET" | grep -q '[^[:space:]]'; then
  echo "Target or one of its partitions is mounted. Unmount it first." >&2; exit 2
fi

echo "DANGER: this will erase $TARGET"
echo "Model: $(lsblk -ndo MODEL,SIZE "$TARGET")"
read -r -p "Type the exact device path to continue: " answer
[[ "$answer" == "$TARGET" ]] || { echo "Cancelled."; exit 2; }

PROFILE=nano
if [[ -f /etc/endworld/profile.env ]]; then
  set -a; source /etc/endworld/profile.env; set +a
  PROFILE="${ENDWORLD_PROFILE:-nano}"
else
  PROFILE=nano
fi
profile_file="/opt/endworld/profiles/$PROFILE.yml"
ROOT_END_MIB=8192
if [[ -f "$profile_file" ]]; then
  ROOT_END_MIB="$(python3 - "$profile_file" <<'PY'
import sys,yaml
p=yaml.safe_load(open(sys.argv[1],encoding="utf-8"))
print((p.get("profile") or {}).get("root_partition_mib") or 8192)
PY
)"
fi

partdev(){ if [[ "$TARGET" =~ [0-9]$ ]]; then printf '%sp%s\n' "$TARGET" "$1"; else printf '%s%s\n' "$TARGET" "$1"; fi; }
P1="$(partdev 1)"; P2="$(partdev 2)"; P3="$(partdev 3)"; P4="$(partdev 4)"
work="$(mktemp -d /var/tmp/ark-clone.XXXXXX)"; ROOTM="$work/root"
cleanup(){
  set +e
  for p in run sys proc dev/pts dev; do mountpoint -q "$ROOTM/$p" && umount -lf "$ROOTM/$p"; done
  mountpoint -q "$ROOTM/boot/efi" && umount -lf "$ROOTM/boot/efi"
  mountpoint -q "$ROOTM/srv/endworld" && umount -lf "$ROOTM/srv/endworld"
  mountpoint -q "$ROOTM" && umount -lf "$ROOTM"
  rm -rf "$work"
}
trap cleanup EXIT INT TERM

wipefs -a "$TARGET"
parted -s "$TARGET" mklabel gpt
parted -s "$TARGET" mkpart BIOS 1MiB 3MiB
parted -s "$TARGET" set 1 bios_grub on
parted -s "$TARGET" mkpart EFI fat32 3MiB 515MiB
parted -s "$TARGET" set 2 esp on
parted -s "$TARGET" mkpart ROOT ext4 515MiB "${ROOT_END_MIB}MiB"
parted -s "$TARGET" mkpart DATA ext4 "\${ROOT_END_MIB}MiB" 100%
partprobe "$TARGET"; udevadm settle
for p in "$P1" "$P2" "$P3" "$P4"; do [[ -b "$p" ]] || { echo "Partition missing: $p" >&2; exit 2; }; done

mkfs.vfat -F32 -n ARK_EFI "$P2" >/dev/null
mkfs.ext4 -F -L ENDWORLD_ROOT "$P3" >/dev/null
mkfs.ext4 -F -m 0 -L ENDWORLD_DATA "$P4" >/dev/null

mkdir -p "$ROOTM"; mount "$P3" "$ROOTM"
mkdir -p "$ROOTM/boot/efi" "$ROOTM/srv/endworld"
mount "$P2" "$ROOTM/boot/efi"; mount "$P4" "$ROOTM/srv/endworld"

vault_bytes="$(du -sb /srv/endworld | awk '{print $1}')"
data_free="$(df -B1 --output=avail "$ROOTM/srv/endworld" | tail -1 | tr -d ' ')"
(( vault_bytes < data_free )) || { echo "Target DATA partition is too small for current Ark state." >&2; exit 2; }

echo "[1/4] Copying appliance root..."
rsync -aHAX --numeric-ids --one-file-system \
  --exclude='/dev/*' --exclude='/proc/*' --exclude='/sys/*' --exclude='/run/*' \
  --exclude='/tmp/*' --exclude='/mnt/*' --exclude='/media/*' \
  --exclude='/boot/efi/*' --exclude='/srv/endworld/*' / "$ROOTM/"

echo "[2/4] Copying frozen vault + mutable state..."
rsync -aHAX --numeric-ids /srv/endworld/ "$ROOTM/srv/endworld/"

root_uuid="$(blkid -s UUID -o value "$P3")"
data_uuid="$(blkid -s UUID -o value "$P4")"
efi_uuid="$(blkid -s UUID -o value "$P2")"
cat > "$ROOTM/etc/fstab" <<EOF
UUID=$root_uuid / ext4 defaults,noatime 0 1
UUID=$efi_uuid /boot/efi vfat umask=0077 0 1
UUID=$data_uuid /srv/endworld ext4 defaults,noatime 0 2
EOF

echo "[3/4] Installing BIOS + UEFI + Secure Boot chain..."
for p in dev dev/pts proc sys run; do mkdir -p "$ROOTM/$p"; done
mount --bind /dev "$ROOTM/dev"; mount --bind /dev/pts "$ROOTM/dev/pts"
mount -t proc proc "$ROOTM/proc"; mount -t sysfs sys "$ROOTM/sys"; mount --bind /run "$ROOTM/run"
chroot "$ROOTM" grub-install --target=i386-pc --recheck "$TARGET"
chroot "$ROOTM" grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ENDWORLD --removable --no-nvram --recheck
chroot "$ROOTM" update-grub
chroot "$ROOTM" /opt/endworld/scripts/install_secure_boot.sh / "$root_uuid"
rm -f "$ROOTM/var/lib/endworld/data-expanded"

echo "[4/4] Verifying copied frozen vault..."
chroot "$ROOTM" python3 /opt/endworld/scripts/verify_vault.py --vault /srv/endworld --profile-id "$PROFILE"
sync
echo "ARK CLONE COMPLETE: $TARGET"
echo "The clone keeps mutable state. Rotate credentials if the new node will have a different trust owner."
