#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 2; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-nano}"
VAULT="${ENDWORLD_VAULT:-$ROOT/vault/$PROFILE}"
SUITE="${ENDWORLD_DEBIAN_SUITE:-trixie}"
MIRROR="${ENDWORLD_DEBIAN_MIRROR:-http://deb.debian.org/debian}"
LOCK="$VAULT/lock/$PROFILE.lock.json"
PKG_MANIFEST="$ROOT/manifests/appliance-packages.yml"
[[ -f "$LOCK" ]] || { echo "Acquire $PROFILE first: missing $LOCK" >&2; exit 2; }
for c in debootstrap python3 tar gzip chroot dpkg-scanpackages sha256sum; do command -v "$c" >/dev/null || { echo "Missing factory dependency: $c" >&2; exit 2; }; done
python3 -c 'import yaml' >/dev/null

OUT="$VAULT/factory/$SUITE-amd64"
TMP="$(mktemp -d -p "${ENDWORLD_BUILD_TMP:-/var/tmp}" ark-factory.XXXXXX)"
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
mkdir -p "$OUT"
BOOT="$OUT/debootstrap-$SUITE-amd64.tar.gz"
DEBS="$OUT/appliance-debs-$SUITE-amd64.tar"
META="$OUT/factory-manifest.json"

echo "[1/5] Freezing debootstrap minbase..."
debootstrap --arch=amd64 --variant=minbase --make-tarball="$BOOT" "$SUITE" "$TMP/download" "$MIRROR"

echo "[2/5] Expanding a temporary builder root..."
mkdir -p "$TMP/root"
debootstrap --arch=amd64 --variant=minbase --unpack-tarball="$BOOT" "$SUITE" "$TMP/root" "$MIRROR"
cat > "$TMP/root/etc/apt/sources.list" <<EOF
deb $MIRROR $SUITE main contrib non-free-firmware
deb $MIRROR $SUITE-updates main contrib non-free-firmware
deb http://security.debian.org/debian-security $SUITE-security main contrib non-free-firmware
EOF
cp -L /etc/resolv.conf "$TMP/root/etc/resolv.conf"
mapfile -t PKGS < <(python3 "$ROOT/scripts/appliance_packages.py" --profile "$PROFILE")

echo "[3/5] Freezing additional .deb dependency closure..."
chroot "$TMP/root" apt-get update
chroot "$TMP/root" apt-get install -y --download-only --no-install-recommends "${PKGS[@]}"
mkdir -p "$TMP/repo"
cp "$TMP/root"/var/cache/apt/archives/*.deb "$TMP/repo/" 2>/dev/null || true
(cd "$TMP/repo" && dpkg-scanpackages . /dev/null > Packages && gzip -9c Packages > Packages.gz)
tar -C "$TMP/repo" --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf "$DEBS" .

echo "[4/5] Writing factory manifest..."
python3 - "$BOOT" "$DEBS" "$META" "$PROFILE" "$SUITE" "$MIRROR" "$PKG_MANIFEST" <<'PY'
import datetime as dt,hashlib,json,pathlib,sys,yaml
boot=pathlib.Path(sys.argv[1]);debs=pathlib.Path(sys.argv[2]);meta=pathlib.Path(sys.argv[3])
profile,suite,mirror=sys.argv[4:7];manifest=pathlib.Path(sys.argv[7])
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()
data=yaml.safe_load(manifest.read_text())
groups=["base"]+(["developer"] if profile in ("nomad","civilization") else [])+(["civilization"] if profile=="civilization" else [])
packages=[];seen=set()
for g in groups:
    for p in data.get(g,[]):
        if p not in seen:seen.add(p);packages.append(p)
obj={"schema":1,"kind":"ark-offline-factory-v1","profile":profile,"suite":suite,"architecture":"amd64",
     "mirror_used_while_freezing":mirror,"created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
     "packages":packages,
     "files":[{"name":boot.name,"bytes":boot.stat().st_size,"sha256":sha(boot)},
              {"name":debs.name,"bytes":debs.stat().st_size,"sha256":sha(debs)}]}
meta.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
PY

echo "[5/5] Adding factory artifacts to the frozen lock/BOM..."
python3 - "$LOCK" "$VAULT" "$BOOT" "$DEBS" "$META" <<'PY'
import hashlib,json,os,pathlib,sys
lockp=pathlib.Path(sys.argv[1]);vault=pathlib.Path(sys.argv[2]);paths=[pathlib.Path(x) for x in sys.argv[3:]]
lock=json.loads(lockp.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()
ids=["factory-bootstrap","factory-debs","factory-manifest"]
items=[x for x in lock.get("artifacts",[]) if x.get("id") not in ids]
for rid,p in zip(ids,paths):
    items.append({"id":rid,"family":"factory","kind":"frozen-factory","required":True,
                  "path":str(p.relative_to(vault)),"bytes":p.stat().st_size,"sha256":sha(p),"status":"frozen"})
lock["artifacts"]=items
total=0
for group in ("artifacts","containers"):
    for rec in lock.get(group,[]):
        rel=rec.get("path")
        if rel and (vault/rel).is_file():total+=(vault/rel).stat().st_size
usable=int(lock["target_bytes"])-int(lock["reserve_bytes"])
if total>usable:raise SystemExit(f"Factory pushes payload over profile budget: {total} > {usable}")
lock["payload_bytes"]=total
tmp=lockp.with_suffix(".tmp");tmp.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+"\n");os.replace(tmp,lockp)
print(f"factory locked: {total} / {usable} bytes")
PY
python3 "$ROOT/scripts/generate_bom.py" --vault "$VAULT" --profile-id "$PROFILE"
python3 "$ROOT/scripts/verify_factory.py" --factory "$OUT"
python3 "$ROOT/scripts/verify_vault.py" --vault "$VAULT" --profile-id "$PROFILE"
echo "OFFLINE FACTORY READY: $OUT"
