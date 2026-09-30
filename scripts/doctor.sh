#!/usr/bin/env bash
set -euo pipefail

fail=0
warn=0

ok(){ printf 'OK   %s\n' "$*"; }
bad(){ printf 'FAIL %s\n' "$*"; fail=$((fail+1)); }
warning(){ printf 'WARN %s\n' "$*"; warn=$((warn+1)); }

command -v python3 >/dev/null && ok "python3" || bad "python3 missing"
python3 -c 'import yaml' >/dev/null 2>&1 && ok "PyYAML" || bad "PyYAML missing (make setup)"
command -v docker >/dev/null && ok "docker" || bad "docker missing"
docker info >/dev/null 2>&1 && ok "docker daemon" || warning "docker daemon unavailable to current user"
command -v java >/dev/null && ok "java" || warning "Java 21+ needed for nano-prepare"
if command -v java >/dev/null; then
  major="$(java -version 2>&1 | awk -F'[ ".]' '/version/{print $3; exit}')"
  [[ "$major" =~ ^[0-9]+$ ]] && (( major >= 21 )) && ok "Java $major" || warning "Java 21+ recommended"
fi

for cmd in parted losetup mkfs.vfat mkfs.ext4 debootstrap grub-install rsync; do
  command -v "$cmd" >/dev/null && ok "$cmd" || warning "$cmd missing (required only for build-image)"
done

if [[ -f vault/nano/lock/nano.lock.json ]]; then
  ok "NANO lock exists"
else
  warning "NANO vault not acquired yet"
fi

printf '\nDoctor complete: %d failure(s), %d warning(s)\n' "$fail" "$warn"
(( fail == 0 ))
