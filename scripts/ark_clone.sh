#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run: sudo ark-clone /dev/sdX" >&2; exit 2; }
TARGET="${1:-}"
[[ -b "$TARGET" ]] || { echo "Target must be a whole block device, e.g. /dev/sdb" >&2; exit 2; }
[[ "$(lsblk -ndo TYPE "$TARGET" | head -1)" == "disk" ]] || { echo "Target is not a whole disk: $TARGET" >&2; exit 2; }

PROFILE="${ENDWORLD_PROFILE:-}"
if [[ -f /etc/endworld/profile.env ]]; then
  set -a; source /etc/endworld/profile.env; set +a
fi
PROFILE="${ENDWORLD_PROFILE:-nano}"
PROFILE_FILE="/opt/endworld/profiles/$PROFILE.yml"
[[ -f "$PROFILE_FILE" ]] || { echo "Profile contract missing: $PROFILE_FILE" >&2; exit 2; }

ROOT_SRC="$(findmnt -no SOURCE /)"
SOURCE_DISK="$(lsblk -sno PATH,TYPE "$ROOT_SRC" 2>/dev/null | awk '$2=="disk"{print $1;exit}')"
[[ -n "$SOURCE_DISK" ]] || { echo "Cannot determine source system disk." >&2; exit 2; }
[[ "$(readlink -f "$TARGET")" != "$(readlink -f "$SOURCE_DISK")" ]] || { echo "Refusing to overwrite the running Ark disk." >&2; exit 2; }

read_meta(){ python3 - "$PROFILE_FILE" "$1" <<'PY'
import sys,yaml
p=yaml.safe_load(open(sys.argv[1]));print(p["profile"].get(sys.argv[2],""))
PY
}
MIN_BYTES="$(read_meta target_bytes)"
ROOT_END_MIB="$(read_meta root_partition_mib)"
TARGET_BYTES="$(blockdev --getsize64 "$TARGET")"
(( TARGET_BYTES >= MIN_BYTES )) || { echo "Target too small: $TARGET_BYTES < profile minimum $MIN_BYTES" >&2; exit 2; }

echo
echo "THE ARK RECOVERY CLONE"
echo "Source: $SOURCE_DISK ($PROFILE)"
echo "Target: $TARGET ($(numfmt --to=iec "$TARGET_BYTES"))"
echo "ALL DATA ON $TARGET WILL BE DESTROYED."
read -r -p "Type '$TARGET ERASE' to continue: " CONFIRM
[[ "$CONFIRM" == "$TARGET ERASE" ]] || { echo "Cancelled."; exit 2; }

WORK="$(mktemp -d /var/tmp/ark-clone.XXXXXX)"
R="$WORK/root";D="$WORK/data";E="$WORK/efi"
mkdir -p "$R" "$D" "$E"
STACK_WAS_ACTIVE=0
systemctl is-active --quiet endworld-stack.service && STACK_WAS_ACTIVE=1 || true
cleanup(){
  set +e
  for p in "$R/run" "$R/sys" "$R/proc" "$R/dev/pts" "$R/dev" "$E" "$D" "$R"; do mountpoint -q "$p" && umount -lf "$p"; done
  rm -rf "$WORK"
  (( STACK_WAS_ACTIVE )) && systemctl start endworld-stack.service >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "[1/7] Quiescing mutable services..."
systemctl stop endworld-stack.service endworld-power.timer 2>/dev/null || true
sync
while read -r p; do umount "$p" 2>/dev/null || true; done < <(lsblk -lnpo NAME "$TARGET" | tail -n +2 | tac)

echo "[2/7] Partitioning target..."
wipefs -a "$TARGET"
parted -s "$TARGET" mklabel gpt
parted -s "$TARGET" mkpart BIOS 1MiB 3MiB
parted -s "$TARGET" set 1 bios_grub on
parted -s "$TARGET" mkpart EFI fat32 3MiB 515MiB
parted -s "$TARGET" set 2 esp on
parted -s "$TARGET" mkpart ROOT ext4 515MiB "${ROOT_END_MIB}MiB"
parted -s "$TARGET" mkpart DATA ext4 "${ROOT_END_MIB}MiB" 100%
partprobe "$TARGET";udevadm settle
part(){ lsblk -nrpo NAME,PARTN "$TARGET" | awk -v n="$1" '$2==n{print $1;exit}'; }
P2="$(part 2)";P3="$(part 3)";P4="$(part 4)"
[[ -b "$P2" && -b "$P3" && -b "$P4" ]] || { echo "Target partitions did not appear." >&2; exit 2; }

echo "[3/7] Creating filesystems..."
mkfs.vfat -F32 -n ARK_EFI "$P2" >/dev/null
mkfs.ext4 -F -L ARK_ROOT "$P3" >/dev/null
mkfs.ext4 -F -m 0 -L ARK_DATA "$P4" >/dev/null
mount "$P3" "$R";mkdir -p "$R/boot/efi" "$R/srv/endworld";mount "$P2" "$E";mount "$P4" "$D"

echo "[4/7] Copying immutable system..."
rsync -aHAXx --numeric-ids --delete   --exclude='/dev/***' --exclude='/proc/***' --exclude='/sys/***' --exclude='/run/***'   --exclude='/tmp/***' --exclude='/var/tmp/***' --exclude='/mnt/***' --exclude='/media/***'   --exclude='/srv/endworld/***' / "$R/"
mkdir -p "$R/boot/efi" "$R/srv/endworld"

echo "[5/7] Copying Ark vault and mutable state..."
rsync -aHAX --numeric-ids --delete /srv/endworld/ "$D/"

ROOT_UUID="$(blkid -s UUID -o value "$P3")";EFI_UUID="$(blkid -s UUID -o value "$P2")";DATA_UUID="$(blkid -s UUID -o value "$P4")"
cat > "$R/etc/fstab" <<EOF
UUID=$ROOT_UUID / ext4 defaults,noatime 0 1
UUID=$EFI_UUID /boot/efi vfat umask=0077 0 1
UUID=$DATA_UUID /srv/endworld ext4 defaults,noatime 0 2
EOF
mount --bind "$E" "$R/boot/efi";mount --bind "$D" "$R/srv/endworld"
for fs in dev proc sys run; do mkdir -p "$R/$fs"; done
mount --bind /dev "$R/dev";mount --bind /dev/pts "$R/dev/pts";mount -t proc proc "$R/proc";mount -t sysfs sys "$R/sys";mount --bind /run "$R/run"

echo "[6/7] Installing BIOS/UEFI boot chain..."
chroot "$R" grub-install --target=i386-pc --recheck "$TARGET"
chroot "$R" grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ENDWORLD --removable --no-nvram --recheck
chroot "$R" update-grub
if [[ -f "$R/usr/lib/shim/shimx64.efi.signed" && -f "$R/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed" ]]; then
  mkdir -p "$R/boot/efi/EFI/BOOT"
  cp "$R/usr/lib/shim/shimx64.efi.signed" "$R/boot/efi/EFI/BOOT/BOOTX64.EFI"
  cp "$R/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed" "$R/boot/efi/EFI/BOOT/grubx64.efi"
  [[ -f "$R/usr/lib/shim/mmx64.efi.signed" ]] && cp "$R/usr/lib/shim/mmx64.efi.signed" "$R/boot/efi/EFI/BOOT/mmx64.efi" || true
fi

echo "[7/7] Verifying cloned frozen vault..."
python3 "$R/opt/endworld/scripts/verify_vault.py" --vault "$D" --profile-id "$PROFILE"
sync
echo
echo "ARK CLONE READY: $TARGET"
echo "This is a recovery clone and inherits this node's hostname/credentials/state."
echo "Disconnect it before booting if the source Ark remains attached, then perform a disconnected boot drill."
