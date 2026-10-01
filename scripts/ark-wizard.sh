#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say(){ printf '\n%s\n' "$*"; }
die(){ printf '\nERROR: %s\n' "$*" >&2; exit 2; }
ask_yes(){
  local prompt="$1" answer
  read -r -p "$prompt [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]]
}
run(){ printf '\n+ %s\n' "$*"; "$@"; }

[[ "$(uname -s)" == "Linux" ]] || die "The current builder supports Linux only. See docs/guides/BEGINNER.md."
[[ "$(uname -m)" == "x86_64" ]] || die "The current image builder targets x86-64/amd64."

cat <<'EOF'

╔══════════════════════════════════════════════════════╗
║                    THE ARK WIZARD                    ║
║  Build an offline knowledge / AI / recovery node.   ║
╚══════════════════════════════════════════════════════╝

Choose a profile:

  1) NANO           64 GB   SURVIVE
  2) FAMILY        256 GB   LIVE + SHARE
  3) NOMAD           1 TB   REBUILD + CREATE
  4) CIVILIZATION    4 TB   RECONSTRUCT

If this is your first Ark, choose 1.
EOF

read -r -p "Choose 1-4: " choice
case "$choice" in
  1) PROFILE=nano; SIZE="64 GB" ;;
  2) PROFILE=family; SIZE="256 GB" ;;
  3) PROFILE=nomad; SIZE="1 TB" ;;
  4) PROFILE=civilization; SIZE="4 TB" ;;
  *) die "Choose 1, 2, 3 or 4." ;;
esac

say "Selected: ${PROFILE^^} ($SIZE)"
say "The builder may need roughly the profile size for the vault PLUS the final raw image, plus temporary space."

if ! command -v apt-get >/dev/null; then
  die "The beginner dependency installer currently expects Debian/Ubuntu (apt-get)."
fi

if ask_yes "Install/refresh Linux builder dependencies now? This uses sudo."; then
  run sudo bash scripts/install_builder_deps.sh
fi

if [[ ! -x .venv/bin/python ]]; then
  say "Creating the project Python environment..."
  run make setup
fi

run .venv/bin/python scripts/endworld.py --profile "$PROFILE" doctor

say "PLAN resolves current sources and sizes. It does not download the full payload."
run .venv/bin/python scripts/endworld.py --profile "$PROFILE" plan

if ! ask_yes "Acquire the full $PROFILE payload now? This can download a lot of data."; then
  say "Stopped after PLAN. Re-run this wizard when you are ready."
  exit 0
fi

run .venv/bin/python scripts/endworld.py --profile "$PROFILE" acquire

if [[ "$PROFILE" == "civilization" ]]; then
  say "CIVILIZATION also freezes selected APT/PyPI/npm dependency closure."
  if ask_yes "Create package snapshots now?"; then
    run .venv/bin/python scripts/endworld.py --profile civilization snapshot-packages
  else
    say "CIVILIZATION is not complete until package snapshots are created."
  fi
fi

run .venv/bin/python scripts/endworld.py --profile "$PROFILE" prepare
run .venv/bin/python scripts/endworld.py --profile "$PROFILE" verify
run .venv/bin/python scripts/endworld.py --profile "$PROFILE" selftest

say "The frozen vault is ready."

if ask_yes "Start it locally first, without erasing a disk?"; then
  run .venv/bin/python scripts/endworld.py --profile "$PROFILE" run
  say "Open http://localhost:8080 (or this machine's LAN IP on port 8080)."
  say "When finished: make ${PROFILE}-stop"
fi

if ! ask_yes "Build the full bootable raw image now?"; then
  say "Done. You can later run: make ${PROFILE}-image"
  exit 0
fi

run .venv/bin/python scripts/endworld.py --profile "$PROFILE" build-image

IMAGE="dist/endworld-$PROFILE-amd64.img"
say "Image built: $IMAGE"

if ! ask_yes "Do you want to flash a physical disk now?"; then
  say "Later: make ${PROFILE}-flash DEVICE=/dev/sdX"
  exit 0
fi

say "Available disks:"
lsblk -o NAME,SIZE,MODEL,TRAN,MOUNTPOINTS
printf '\n'
read -r -p "Type the target device path (example /dev/sdb): " DEVICE
[[ "$DEVICE" == /dev/* ]] || die "That does not look like a /dev device."

say "The flash script will show the disk again and require the exact path before erasing it."
run .venv/bin/python scripts/endworld.py --profile "$PROFILE" flash "$DEVICE"

say "Done. Boot a compatible PC from the Ark disk."
say "First-boot guide: docs/guides/FIRST-BOOT.md"
