#!/usr/bin/env bash
set -euo pipefail
IMAGE="$1"
MODE="${2:-bios}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
COPY="$WORK/nano-mini-$MODE.img"
cp --sparse=always "$IMAGE" "$COPY"
LOG="$WORK/serial.log"

COMMON=(-m 3072 -smp 2 -display none -serial stdio -monitor none -no-reboot -nic none
        -drive "file=$COPY,format=raw,if=virtio,cache=unsafe")
EXTRA=()
if [[ "$MODE" == "uefi" ]]; then
  CODE=""
  VARS=""
  for p in /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd; do [[ -f "$p" ]] && { CODE="$p"; break; }; done
  for p in /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd; do [[ -f "$p" ]] && { VARS="$p"; break; }; done
  [[ -n "$CODE" && -n "$VARS" ]] || { echo "OVMF firmware not found" >&2; exit 2; }
  cp "$VARS" "$WORK/vars.fd"
  EXTRA=(-machine q35 -drive "if=pflash,format=raw,readonly=on,file=$CODE" -drive "if=pflash,format=raw,file=$WORK/vars.fd")
elif [[ "$MODE" != "bios" ]]; then
  echo "mode must be bios or uefi" >&2; exit 2
fi

set +e
timeout 360 qemu-system-x86_64 "${EXTRA[@]}" "${COMMON[@]}" 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}
set -e
if ! grep -q 'THE_ARK_OFFLINE_SMOKE=PASS' "$LOG"; then
  echo "Offline smoke marker missing (qemu rc=$rc)" >&2
  tail -200 "$LOG" >&2
  exit 1
fi
echo "QEMU $MODE OFFLINE PASS"
