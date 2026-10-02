#!/usr/bin/env python3
"""Deterministic source/vault self-test for ENDWORLD profiles.

No network access and no downloads. Validates profile contracts, path safety,
profile-specific wiring, generic runtime routing and (optionally) a frozen vault.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Frontier integration: every profile must retain the common mesh/field/evidence wiring.


class SelfTestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def safe_rel(value: str, label: str) -> pathlib.PurePosixPath:
    p = pathlib.PurePosixPath(value)
    require(bool(value), f"{label} is empty")
    require(not p.is_absolute(), f"{label} must be relative: {value}")
    require(".." not in p.parts, f"{label} contains traversal: {value}")
    return p


def load_server():
    path = ROOT / "runtime" / "server.py"
    spec = importlib.util.spec_from_file_location("endworld_runtime_server", path)
    require(spec is not None and spec.loader is not None, "cannot import runtime/server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_profile(profile_path: pathlib.Path) -> dict:
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "profile must be a mapping")
    require(data.get("schema") == 1, "unsupported profile schema")
    meta = data.get("profile") or {}
    pid = str(meta.get("id") or "")
    require(pid, "profile.id missing")
    target = int(meta.get("target_bytes") or 0)
    reserve = int(meta.get("reserve_bytes") or 0)
    headroom = int(meta.get("acquisition_headroom_bytes") or 0)
    root_mib = int(meta.get("root_partition_mib") or 8192)
    require(target > 0, "target_bytes must be positive")
    require(0 <= reserve < target, "reserve_bytes must fit target")
    require(0 <= headroom < target - reserve, "acquisition headroom must fit usable payload")
    require(4096 <= root_mib <= 65536, "root_partition_mib outside supported envelope")
    ceiling = target - reserve - headroom

    ids: set[str] = set()
    artifact_ids: set[str] = set()
    artifacts = data.get("artifacts") or []
    require(isinstance(artifacts, list) and artifacts, "profile has no artifacts")
    kind_fields = {
        "url": ("url",),
        "index_latest": ("index_url", "href_regex"),
        "github_release_asset": ("repo", "asset_regex"),
        "github_snapshot": ("repo",),
    }
    for i, rec in enumerate(artifacts):
        require(isinstance(rec, dict), f"artifact #{i} must be a mapping")
        rid = str(rec.get("id") or "")
        require(rid and rid not in ids, f"duplicate or missing artifact id: {rid!r}")
        ids.add(rid)
        artifact_ids.add(rid)
        kind = str(rec.get("kind") or "")
        require(kind in kind_fields, f"{rid}: unsupported artifact kind {kind!r}")
        for field in kind_fields[kind]:
            require(bool(rec.get(field)), f"{rid}: missing {field}")
        safe_rel(str(rec.get("destination") or "misc"), f"{rid}.destination")
        budget = int(rec.get("budget_bytes") or 0)
        require(budget > 0, f"{rid}: budget_bytes must be positive")
        require(budget <= target - reserve, f"{rid}: item budget exceeds usable profile")

    for rec in data.get("containers") or []:
        rid = str(rec.get("id") or "")
        require(rid and rid not in ids, f"duplicate or missing component id: {rid!r}")
        ids.add(rid)
        image = str(rec.get("image") or "")
        require("/" in image and ":" in image, f"{rid}: container image must include repository and tag")

    for spec in (data.get("prepare") or {}).get("maps", []):
        require(spec.get("id"), "prepare map id missing")
        require(spec.get("source_artifact") in artifact_ids,
                f"{spec.get('id')}: source artifact not declared")
        require(str(spec.get("filename") or "").endswith(".pmtiles"),
                f"{spec.get('id')}: PMTiles filename required")

    for rel in (
        "runtime/server.py", "runtime/kiwix_client.py", "runtime/start-stack.sh", "runtime/start-profile.sh",
        "runtime/portal/index.html", "scripts/acquire.py", "scripts/verify_vault.py",
        "scripts/prepare_profile.py", "scripts/build_disk_image.sh",
        "scripts/build_search_index.py", "scripts/release_trust.py", "scripts/update_bundle.py",
        "scripts/first_boot_wizard.py", "builder/ark_builder.py",
        "scripts/ark_mesh.py", "scripts/power_policy.py", "scripts/field_comms.py",
        "scripts/field_drill.py", "scripts/field_campaign.py", "scripts/hardware_matrix.py",
        "scripts/agent_runner.py", "scripts/ark_clone.sh", "scripts/install_secure_boot.sh",
        "scripts/offline_factory.py", "scripts/vector_index.py",
        "runtime/vector_client.py", "runtime/vector-index.sh", "runtime/systemd/endworld-vector-index.service",
        "manifests/appliance-os-packages.yml",
        "runtime/expand-data.sh", "runtime/systemd/endworld-expand-data.service",
        "config/ark-cluster.yml", "config/field-comms.yml",
    ):
        require((ROOT / rel).is_file(), f"missing wired runtime file: {rel}")

    expected_common = {
        "wikipedia-es", "wikipedia-medicine-es", "spain-osm", "planetiler",
        "maplibre-js", "maplibre-css", "pmtiles-js", "bitchat-android",
        "meshtastic-android", "reticulum-source", "project-nomad-source",
        "planetiler-water-polygons", "planetiler-natural-earth", "planetiler-lake-centerlines",
        "kiwix", "llama-server", "whisper-server",
    }
    require(expected_common.issubset(ids), f"{pid}: common wiring missing {sorted(expected_common - ids)}")

    if pid == "nano":
        expected = {"qwen3-4b-q4", "whisper-small","sideband-android","lxmf-source",
                    "meshtastic-firmware-esp32s3","meshtastic-firmware-nrf52840",
                    "meshtastic-firmware-rp2040","meshtastic-firmware-rp2350"}
        require(expected.issubset(ids), f"NANO wiring missing ids: {sorted(expected - ids)}")
        require(target == 58_000_000_000, "NANO distribution image target must stay 58,000,000,000 bytes")
        require(reserve == 6_000_000_000, "NANO reserve must preserve a 52 GB usable envelope")
    elif pid == "nano-mini":
        expected={"qwen3-4b-q4","whisper-small"}
        require(expected.issubset(ids), f"NANO-MINI wiring missing ids: {sorted(expected-ids)}")
        require(6_000_000_000 <= target <= 8_000_000_000, "NANO-MINI target outside CI envelope")
        require((ROOT/"config/nano-mini.env").is_file(),"NANO-MINI runtime env missing")
        require((ROOT/"runtime/offline-smoke.sh").is_file(),"NANO-MINI offline smoke missing")
    elif pid == "family":
        expected = {
            "wikipedia-en-nopic", "wikisource-es", "qwen3-8b-q4", "whisper-medium",
            "portugal-osm", "organicmaps-android", "meshtastic-firmware",
            "syncthing-source", "forgejo-source", "syncthing", "forgejo",
        }
        require(expected.issubset(ids), f"FAMILY wiring missing ids: {sorted(expected - ids)}")
        require(target == 256_000_000_000, "FAMILY target must stay exactly 256,000,000,000 bytes")
        require((ROOT / "config" / "family.env").is_file(), "FAMILY runtime env missing")
    elif pid == "nomad":
        expected={"wikipedia-en-nopic","wikipedia-medicine-en","wikibooks-en","stackoverflow-en","qwen3-8b-q4","qwen3-30b-a3b-q4","qwen3-coder-30b-a3b-q4s","whisper-medium","france-osm","ifixit-en","ifixit-es","appropriate-tech-cd3wd","electronics-stackexchange","arduino-stackexchange","raspberrypi-stackexchange","project-nomad-source","llama-cpp-source","qdrant-source","code-server-source","platformio-source","arduino-cli-source","esp32-source","satdump-source","syncthing","forgejo","qdrant","code-server","project-nomad-admin","project-nomad-mysql","project-nomad-redis"}
        require(expected.issubset(ids), f"NOMAD wiring missing ids: {sorted(expected-ids)}")
        require(target==1_000_000_000_000,"NOMAD target must stay exactly 1 TB decimal")
        require("nomic-embed-text-v1.5-q4" in ids, "NOMAD embedding model missing")
        require((ROOT/"config/nomad.env").is_file(),"NOMAD runtime env missing")
        require((ROOT/"runtime/switch-ai.sh").is_file(),"NOMAD AI switcher missing")
        require({m["id"] for m in (data.get("prepare") or {}).get("maps",[])}=={"spain-pmtiles","portugal-pmtiles","france-pmtiles"},"NOMAD map contract changed")
    elif pid == "civilization":
        expected={"wikipedia-en-nopic","stackoverflow-en","qwen3-8b-q4","qwen3-30b-a3b-q4","qwen3-coder-30b-a3b-q4s","europe-osm","freecad-source","kicad-source","openscad-source","jupyterlab-source","numpy-source","scipy-source","sympy-source","opencv-source","gdal-source","qgis-source","registry-source","pypiserver-source","syncthing","forgejo","qdrant","code-server","project-nomad-admin","project-nomad-mysql","project-nomad-redis"}
        require(expected.issubset(ids), f"CIVILIZATION wiring missing ids: {sorted(expected-ids)}")
        require(target==4_000_000_000_000,"CIVILIZATION target must stay exactly 4 TB decimal")
        require(reserve==700_000_000_000,"CIVILIZATION reserve contract changed")
        require(headroom==400_000_000_000,"CIVILIZATION acquisition headroom changed")
        require(root_mib==65536,"CIVILIZATION root boundary must stay 65536 MiB")
        require("nomic-embed-text-v1.5-q4" in ids, "CIVILIZATION embedding model missing")
        require((ROOT/"config/civilization.env").is_file(),"CIVILIZATION runtime env missing")
        require((ROOT/"manifests/civilization-packages.yml").is_file(),"CIVILIZATION package snapshot manifest missing")
        require((ROOT/"scripts/snapshot_packages.py").is_file(),"CIVILIZATION package snapshot engine missing")
        require("europe-pmtiles" in {m["id"] for m in (data.get("prepare") or {}).get("maps",[])},"CIVILIZATION Europe map contract missing")

    require(ceiling > 0, f"{pid}: acquisition ceiling invalid")
    return {"id": pid, "target": target, "reserve": reserve, "headroom": headroom, "ceiling": ceiling}


def validate_runtime(profile: dict) -> None:
    server = load_server()
    base = pathlib.Path("/tmp/endworld-selftest-root")
    require(server.safe_join(base, "ok/file.bin") == (base / "ok/file.bin").resolve(), "safe_join rejected safe path")
    require(server.safe_join(base, "../escape") is None, "safe_join allowed parent traversal")
    require(server.safe_join(base, "%2e%2e/escape") is None, "safe_join allowed encoded traversal")
    start_stack=(ROOT/"runtime/start-stack.sh").read_text(encoding="utf-8")
    require("--entrypoint whisper-server" in start_stack and "ENDWORLD_WHISPER_LANGUAGE" in start_stack,
            "whisper server entrypoint/language is not pinned")
    require('docker image inspect "$image"' in start_stack,"container boot cache is not wired")
    server_text=(ROOT/"runtime/server.py").read_text(encoding="utf-8")
    require('path=="/vault/state"' in server_text,"mutable state is not blocked from /vault")
    require("kiwix_hits" in server_text and "ENDWORLD_RAG_MAX_CHARS" in server_text,
            "Kiwix federation/RAG budget is not wired")
    mapjs=(ROOT/"runtime/portal/map.js").read_text(encoding="utf-8")
    require('type:"symbol"' in mapjs and '"text-field"' in mapjs,"offline map labels are not wired")

    samples = {
        "wikipedia-es": ("knowledge", "knowledge/zim/wiki.zim", "service"),
        "qwen3-8b-q4": ("ai", "ai/models/model.gguf", "anchor"),
        "whisper-medium": ("ai", "ai/models/whisper.bin", "anchor"),
        "bitchat-android": ("comms", "apps/android/bitchat.apk", "link"),
        "meshtastic-firmware": ("comms", "firmware/meshtastic/fw.zip", "link"),
        "reticulum-source": ("comms", "source/comms/reticulum.tar.gz", "link"),
        "project-nomad-source": ("core", "source/core/nomad.tar.gz", "link"),
        "syncthing": ("replication", "containers/syncthing.tar", "service"),
        "forgejo": ("software-vault", "containers/forgejo.tar", "service"),
        "qdrant": ("ai", "containers/qdrant.tar", "service"),
        "code-server": ("developer", "containers/code-server.tar", "service"),
        "project-nomad-admin": ("core", "containers/project-nomad-admin.tar", "service"),
    }
    for rid, (family, path, action_kind) in samples.items():
        f = base / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")
        rec = {"id": rid, "family": family, "path": path, "required": True, "bytes": 1}
        item = server.describe_capability(rec, base, reticulum_available=False)
        require(item.get("action") and item["action"].get("kind") == action_kind,
                f"{rid}: no operator action wired")

    builder = (ROOT / "scripts" / "build_disk_image.sh").read_text(encoding="utf-8")
    require("exec python3 /opt/endworld/scripts/endworld.py" in builder,
            "appliance endworld CLI wrapper is not installed")
    require("grub-efi-amd64-signed" in builder and "shim-signed" in builder,
            "Debian Secure Boot packages are not wired")
    require("endworld-expand-data.service" in builder and "ark-clone" in builder,
            "clone/expand-to-fill wiring missing")
    require("ENDWORLD_FACTORY_DIR" in builder and "offline_factory.py" in builder,
            "offline factory rebuild path missing")
    manifest=(ROOT/"manifests/appliance-os-packages.yml").read_text(encoding="utf-8")
    require("poppler-utils" in manifest and "tesseract-ocr-spa" in manifest,
            "PDF/OCR runtime closure missing")


def validate_vault(vault: pathlib.Path, profile: dict) -> dict:
    lock_path = vault / "lock" / f"{profile['id']}.lock.json"
    require(lock_path.is_file(), f"vault lock missing: {lock_path}")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    require(lock.get("profile") == profile["id"], "lock profile mismatch")
    require(int(lock.get("target_bytes") or 0) == profile["target"], "lock target mismatch")
    require(int(lock.get("reserve_bytes") or 0) == profile["reserve"], "lock reserve mismatch")
    for group in ("artifacts", "containers"):
        for rec in lock.get(group, []):
            rel = rec.get("path")
            if rel:
                safe_rel(str(rel), f"lock {rec.get('id')}.path")
    payload = int(lock.get("payload_bytes") or 0)
    usable = profile["target"] - profile["reserve"]
    require(payload <= usable, f"locked payload {payload} exceeds usable envelope {usable}")
    return {"lock": str(lock_path), "payload_bytes": payload, "prepared": bool(lock.get("prepared"))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=str(ROOT / "profiles" / "nano.yml"))
    ap.add_argument("--vault")
    args = ap.parse_args()
    try:
        profile = validate_profile(pathlib.Path(args.profile).resolve())
        validate_runtime(profile)
        result = {
            "profile": profile["id"], "source": "OK", "target_bytes": profile["target"],
            "acquisition_ceiling_bytes": profile["ceiling"],
        }
        if args.vault:
            result["vault"] = validate_vault(pathlib.Path(args.vault).resolve(), profile)
        print(json.dumps(result, indent=2))
        return 0
    except (SelfTestError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SELFTEST FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
