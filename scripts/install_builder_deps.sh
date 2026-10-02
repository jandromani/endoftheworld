#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 2; }
apt-get update
apt-get install -y   python3 python3-venv python3-pip python3-yaml docker.io default-jre-headless   debootstrap parted dosfstools e2fsprogs util-linux rsync   grub-pc-bin grub-efi-amd64-bin grub2-common efibootmgr   jq curl ca-certificates shellcheck openssl maven rustc cargo golang-go dpkg-dev poppler-utils tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
systemctl enable --now docker
echo "Builder dependencies installed."
java -version
