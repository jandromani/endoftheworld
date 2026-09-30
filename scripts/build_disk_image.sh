#!/usr/bin/env bash
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Run as root (the CLI uses sudo)." >&2; exit 2; }

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-nano}"
PROFILE_FILE="$REPO/profiles/$PROFILE.yml"
[[ -f "$PROFILE_FILE" ]] || { echo "Unknown profile: $PROFILE" >&2; exit 2; }
OUTPUT="${2:-$REPO/dist/endworld-$PROFILE-amd64.img}"
VAULT="${ENDWORLD_VAULT:-$REPO/vault/$PROFILE}"
SUITE="${ENDWORLD_DEBIAN_SUITE:-trixie}"
MIRROR="${ENDWORLD_DEBIAN_MIRROR:-http://deb.debian.org/debian}"

read_profile(){
  python3 - "$PROFILE_FILE" "$1" <<'PY'
import sys,yaml
p=yaml.safe_load(open(sys.argv[1],encoding="utf-8"))
meta=p["profile"]
key=sys.argv[2]
print(meta.get(key,""))
PY
}
PROFILE_ID="$(read_profile id)"
IMAGE_BYTES="${ENDWORLD_IMAGE_BYTES:-$(read_profile target_bytes)}"
ROOT_END_MIB="$(read_profile root_partition_mib)"
ROOT_END_MIB="${ROOT_END_MIB:-8192}"
TITLE="$(read_profile title)"
[[ "$PROFILE_ID" == "$PROFILE" ]] || { echo "Profile id mismatch: $PROFILE_ID" >&2; exit 2; }

need(){ command -v "$1" >/dev/null || { echo "Missing build dependency: $1" >&2; exit 2; }; }
for c in parted losetup mkfs.vfat mkfs.ext4 mount umount debootstrap grub-install rsync chroot sha256sum python3; do need "$c"; done
python3 -c 'import yaml' >/dev/null 2>&1 || { echo "python3-yaml missing; run make builder-deps" >&2; exit 2; }
[[ "$(uname -m)" == "x86_64" ]] || { echo "amd64 image builder requires an x86_64 Linux host." >&2; exit 2; }
[[ -f "$VAULT/lock/$PROFILE.lock.json" ]] || { echo "Acquire and prepare $PROFILE first: missing lock." >&2; exit 2; }
[[ -f "$VAULT/lock/$PROFILE.cdx.json" ]] || { echo "Run endworld prepare first: CycloneDX BOM missing." >&2; exit 2; }
find "$VAULT/maps/tiles" -maxdepth 1 -type f -name '*.pmtiles' -print -quit 2>/dev/null | grep -q . || {
  echo "Run endworld prepare first: no PMTiles map found." >&2; exit 2;
}

python3 "$REPO/scripts/verify_vault.py" --vault "$VAULT" --profile-id "$PROFILE"

BUILD="$(mktemp -d -p "${ENDWORLD_BUILD_TMP:-/var/tmp}" endworld-image.XXXXXX)"
ROOTFS="$BUILD/root"
LOOP=""
cleanup(){
  set +e
  mountpoint -q "$ROOTFS/run" && umount -lf "$ROOTFS/run"
  mountpoint -q "$ROOTFS/sys" && umount -lf "$ROOTFS/sys"
  mountpoint -q "$ROOTFS/proc" && umount -lf "$ROOTFS/proc"
  mountpoint -q "$ROOTFS/dev/pts" && umount -lf "$ROOTFS/dev/pts"
  mountpoint -q "$ROOTFS/dev" && umount -lf "$ROOTFS/dev"
  mountpoint -q "$ROOTFS/boot/efi" && umount -lf "$ROOTFS/boot/efi"
  mountpoint -q "$ROOTFS/srv/endworld" && umount -lf "$ROOTFS/srv/endworld"
  mountpoint -q "$ROOTFS" && umount -lf "$ROOTFS"
  [[ -n "$LOOP" ]] && losetup -d "$LOOP" 2>/dev/null || true
  rm -rf "$BUILD"
}
trap cleanup EXIT INT TERM

mkdir -p "$(dirname "$OUTPUT")" "$ROOTFS"
rm -f "$OUTPUT" "$OUTPUT.sha256"
truncate -s "$IMAGE_BYTES" "$OUTPUT"

echo "[1/9] Partitioning sparse $PROFILE image..."
parted -s "$OUTPUT" mklabel gpt
parted -s "$OUTPUT" mkpart BIOS 1MiB 3MiB
parted -s "$OUTPUT" set 1 bios_grub on
parted -s "$OUTPUT" mkpart EFI fat32 3MiB 515MiB
parted -s "$OUTPUT" set 2 esp on
parted -s "$OUTPUT" mkpart ROOT ext4 515MiB "${ROOT_END_MIB}MiB"
parted -s "$OUTPUT" mkpart DATA ext4 "${ROOT_END_MIB}MiB" 100%

LOOP="$(losetup --find --show --partscan "$OUTPUT")"
udevadm settle
for n in 1 2 3 4; do
  for _ in {1..20}; do [[ -b "${LOOP}p$n" ]] && break; sleep .2; done
  [[ -b "${LOOP}p$n" ]] || { echo "Loop partition ${LOOP}p$n missing" >&2; exit 2; }
done

echo "[2/9] Creating filesystems..."
mkfs.vfat -F32 -n ENDWORLD_EFI "${LOOP}p2" >/dev/null
mkfs.ext4 -F -L ENDWORLD_ROOT "${LOOP}p3" >/dev/null
mkfs.ext4 -F -m 0 -L ENDWORLD_DATA "${LOOP}p4" >/dev/null

mount "${LOOP}p3" "$ROOTFS"
mkdir -p "$ROOTFS/boot/efi" "$ROOTFS/srv/endworld"
mount "${LOOP}p2" "$ROOTFS/boot/efi"
mount "${LOOP}p4" "$ROOTFS/srv/endworld"

DATA_FREE="$(df -B1 --output=avail "$ROOTFS/srv/endworld" | tail -1 | tr -d ' ')"
VAULT_BYTES="$(du -sb "$VAULT" | awk '{print $1}')"
(( VAULT_BYTES < DATA_FREE )) || { echo "Vault $(numfmt --to=iec "$VAULT_BYTES") does not fit data partition $(numfmt --to=iec "$DATA_FREE")" >&2; exit 2; }

echo "[3/9] Bootstrapping Debian $SUITE..."
debootstrap --arch=amd64 --variant=minbase "$SUITE" "$ROOTFS" "$MIRROR"

cat > "$ROOTFS/etc/apt/sources.list" <<EOF
deb $MIRROR $SUITE main contrib non-free-firmware
deb $MIRROR $SUITE-updates main contrib non-free-firmware
deb http://security.debian.org/debian-security $SUITE-security main contrib non-free-firmware
EOF
cp -L /etc/resolv.conf "$ROOTFS/etc/resolv.conf"

for fs in dev proc sys run; do mkdir -p "$ROOTFS/$fs"; done
mount --bind /dev "$ROOTFS/dev"
mount --bind /dev/pts "$ROOTFS/dev/pts"
mount -t proc proc "$ROOTFS/proc"
mount -t sysfs sys "$ROOTFS/sys"
mount --bind /run "$ROOTFS/run"

echo "[4/9] Installing appliance OS packages..."
export DEBIAN_FRONTEND=noninteractive
chroot "$ROOTFS" apt-get update
chroot "$ROOTFS" apt-get install -y --no-install-recommends   linux-image-amd64 grub-pc-bin grub-efi-amd64-bin grub2-common efibootmgr   systemd-sysv systemd-resolved sudo ca-certificates curl jq python3 python3-pip python3-yaml python3-setuptools python3-wheel python3-cryptography python3-serial   docker.io hostapd dnsmasq iw rfkill avahi-daemon   iproute2 iputils-ping net-tools rsync less nano   firmware-linux-free firmware-iwlwifi firmware-realtek firmware-atheros

if [[ "$PROFILE" == "nomad" || "$PROFILE" == "civilization" ]]; then
  echo "Installing rebuild-and-create developer toolchain..."
  chroot "$ROOTFS" apt-get install -y --no-install-recommends git build-essential cmake ninja-build pkg-config clang gdb python3-dev python3-venv nodejs npm default-jdk-headless maven rustc cargo golang-go sqlite3 ripgrep tmux vim
fi
if [[ "$PROFILE" == "civilization" ]]; then
  echo "Installing CIVILIZATION science/reconstruction baseline..."
  chroot "$ROOTFS" apt-get install -y --no-install-recommends python3-numpy python3-scipy python3-pandas python3-matplotlib python3-sympy ffmpeg imagemagick graphviz pandoc
fi

HOSTNAME="endworld-$PROFILE"
echo "$HOSTNAME" > "$ROOTFS/etc/hostname"
cat > "$ROOTFS/etc/hosts" <<EOF
127.0.0.1 localhost
127.0.1.1 $HOSTNAME
::1 localhost ip6-localhost ip6-loopback
EOF
cat > "$ROOTFS/etc/fstab" <<'EOF'
LABEL=ENDWORLD_ROOT / ext4 defaults,noatime 0 1
LABEL=ENDWORLD_EFI /boot/efi vfat umask=0077 0 1
LABEL=ENDWORLD_DATA /srv/endworld ext4 defaults,noatime 0 2
EOF

chroot "$ROOTFS" useradd -m -s /bin/bash endworld
echo "endworld:endworld" | chroot "$ROOTFS" chpasswd
chroot "$ROOTFS" usermod -aG sudo,docker endworld
echo 'endworld ALL=(ALL) NOPASSWD:ALL' > "$ROOTFS/etc/sudoers.d/endworld"
chmod 0440 "$ROOTFS/etc/sudoers.d/endworld"

echo "[5/9] Copying ENDWORLD runtime and frozen vault..."
mkdir -p "$ROOTFS/opt/endworld" "$ROOTFS/etc/endworld"
rsync -a --delete --exclude '.git/' --exclude '.venv/' --exclude 'vault/' --exclude 'dist/' "$REPO/" "$ROOTFS/opt/endworld/"
install -m 0644 "$REPO/config/$PROFILE.env" "$ROOTFS/etc/endworld/profile.env"
rsync -aH --info=progress2 "$VAULT/" "$ROOTFS/srv/endworld/"

chmod +x "$ROOTFS"/opt/endworld/runtime/*.sh "$ROOTFS"/opt/endworld/runtime/network/*.sh "$ROOTFS"/opt/endworld/scripts/*.sh 2>/dev/null || true
cat > "$ROOTFS/usr/local/bin/endworld" <<'EOF'
#!/bin/sh
exec python3 /opt/endworld/scripts/endworld.py "$@"
EOF
chmod 0755 "$ROOTFS/usr/local/bin/endworld"

RETICULUM_TAR="$(find "$ROOTFS/srv/endworld/source/comms" -maxdepth 1 -type f -name 'reticulum-source-*.tar.gz' | head -1 || true)"
if [[ -n "$RETICULUM_TAR" ]]; then
  RETICULUM_CHROOT="${RETICULUM_TAR#"$ROOTFS"}"
  chroot "$ROOTFS" python3 -m pip install --break-system-packages --no-build-isolation --no-deps "$RETICULUM_CHROOT"
else
  echo "Frozen Reticulum source archive not found" >&2
  exit 2
fi

echo "[6/9] Configuring networking and services..."
mkdir -p "$ROOTFS/etc/systemd/network"
cat > "$ROOTFS/etc/systemd/network/20-wired.network" <<'EOF'
[Match]
Name=en* eth*

[Network]
DHCP=yes
MulticastDNS=yes
EOF
mkdir -p "$ROOTFS/etc/systemd/resolved.conf.d"
cat > "$ROOTFS/etc/systemd/resolved.conf.d/endworld.conf" <<'EOF'
[Resolve]
MulticastDNS=yes
LLMNR=yes
EOF

cp "$REPO"/runtime/systemd/* "$ROOTFS/etc/systemd/system/"
chroot "$ROOTFS" systemctl disable hostapd.service dnsmasq.service 2>/dev/null || true
chroot "$ROOTFS" systemctl enable docker.service avahi-daemon.service systemd-networkd.service systemd-resolved.service
chroot "$ROOTFS" systemctl enable endworld-network.service endworld-portal.service endworld-stack.service endworld-health.timer

mkdir -p "$ROOTFS/etc/systemd/system/getty@tty1.service.d"
cat > "$ROOTFS/etc/systemd/system/getty@tty1.service.d/autologin.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin endworld --noclear %I $TERM
EOF

source "$REPO/config/$PROFILE.env"
cat >> "$ROOTFS/home/endworld/.bashrc" <<EOF

if [[ -t 1 ]]; then
  echo
  echo "$TITLE"
  echo "Portal: http://$HOSTNAME.local/  |  Wi-Fi: ${ENDWORLD_WIFI_SSID}"
  echo "Default Wi-Fi password: ${ENDWORLD_WIFI_PASSWORD} (change /etc/endworld/profile.env)"
  echo "Status: sudo python3 /opt/endworld/scripts/healthcheck.py --vault /srv/endworld --profile-id $PROFILE"
  echo
fi
EOF
chroot "$ROOTFS" chown -R endworld:endworld /home/endworld

echo "[7/9] Installing bootloader..."
cat > "$ROOTFS/etc/default/grub" <<EOF
GRUB_DEFAULT=0
GRUB_TIMEOUT=2
GRUB_DISTRIBUTOR="$TITLE"
GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3"
GRUB_CMDLINE_LINUX=""
EOF
chroot "$ROOTFS" grub-install --target=i386-pc --recheck "$LOOP"
chroot "$ROOTFS" grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ENDWORLD --removable --no-nvram --recheck
chroot "$ROOTFS" update-grub

echo "[8/9] Cleaning image..."
chroot "$ROOTFS" apt-get clean
rm -rf "$ROOTFS/var/lib/apt/lists/"* "$ROOTFS/tmp/"* "$ROOTFS/var/tmp/"*
sync

echo "[9/9] Final integrity metadata..."
cleanup
set -e
trap - EXIT INT TERM
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
echo "Built: $OUTPUT"
echo "SHA256: $(cat "$OUTPUT.sha256")"
echo "Profile: $PROFILE ($IMAGE_BYTES bytes)"
echo "Default console user: endworld / endworld"
echo "Default Wi-Fi: $ENDWORLD_WIFI_SSID / $ENDWORLD_WIFI_PASSWORD"
