#!/usr/bin/env python3
"""ENDWORLD command-line entrypoint.

Every profile follows the same operator lifecycle:
plan -> acquire -> prepare -> verify -> selftest -> run/build-image -> flash.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(*cmd: str, sudo: bool = False) -> int:
    args = list(cmd)
    if sudo:
        args.insert(0, "sudo")
    print("+", " ".join(args))
    return subprocess.call(args, cwd=ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(prog="endworld")
    ap.add_argument("--profile", default="nano", help="profile id from profiles/<id>.yml")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("plan", "acquire", "prepare", "verify", "run", "stop", "status", "doctor", "scout", "selftest", "index"):
        sub.add_parser(name)
    agent = sub.add_parser("agent", help="run a bounded offline agent task")
    agent.add_argument("goal")
    agent.add_argument("--task-id")
    agent.add_argument("--max-steps", type=int, default=8)
    ai=sub.add_parser("ai-mode"); ai.add_argument("mode",choices=["lite","general","coder"])
    sp = sub.add_parser("snapshot-packages")
    sp.add_argument("--manifest")
    b = sub.add_parser("build-image")
    b.add_argument("--output")
    fl = sub.add_parser("flash")
    fl.add_argument("device")
    fl.add_argument("--image")
    args = ap.parse_args()

    profile_path = ROOT / "profiles" / f"{args.profile}.yml"
    if not profile_path.exists():
        raise SystemExit(f"Unknown profile: {args.profile}")
    vault = f"vault/{args.profile}"
    py = sys.executable

    if args.command in ("plan", "acquire"):
        return run(py, "scripts/acquire.py", args.command, "--profile", str(profile_path), "--vault", vault)
    if args.command == "prepare":
        rc = run(py, "scripts/prepare_profile.py", "--profile", str(profile_path), "--vault", vault)
        if rc:
            return rc
        rc = run(py, "scripts/generate_bom.py", "--vault", vault, "--profile-id", args.profile)
        if rc:
            return rc
        return run(py, "scripts/build_search_index.py", "--vault", vault, "--repo", str(ROOT))
    if args.command == "verify":
        return run(py, "scripts/verify_vault.py", "--vault", vault, "--profile-id", args.profile)
    if args.command == "index":
        return run(py, "scripts/build_search_index.py", "--vault", vault, "--repo", str(ROOT))
    if args.command == "run":
        return run("bash", "runtime/start-profile.sh", args.profile)
    if args.command == "stop":
        return run("bash", "runtime/stop-profile.sh", args.profile)
    if args.command == "status":
        return run(py, "scripts/healthcheck.py", "--local", "--profile-id", args.profile)
    if args.command == "doctor":
        return run("bash", "scripts/doctor.sh")
    if args.command == "scout":
        return run(py, "scripts/scout.py")
    if args.command == "selftest":
        cmd = [py, "scripts/selftest.py", "--profile", str(profile_path)]
        if (ROOT / vault / "lock" / f"{args.profile}.lock.json").exists():
            cmd += ["--vault", vault]
        return run(*cmd)
    if args.command == "agent":
        vault_path = pathlib.Path("/srv/endworld") if pathlib.Path("/srv/endworld/lock").exists() else ROOT / vault
        cmd = [py, "scripts/agent_runner.py", "--vault", str(vault_path), "--profile", args.profile,
               "--max-steps", str(args.max_steps)]
        if args.task_id:
            cmd += ["--task-id", args.task_id]
        cmd.append(args.goal)
        return run(*cmd)
    if args.command == "ai-mode":
        return run("bash","runtime/switch-ai.sh",args.mode)
    if args.command == "snapshot-packages":
        manifest = args.manifest or f"manifests/{args.profile}-packages.yml"
        return run(py, "scripts/snapshot_packages.py", "--profile", str(profile_path), "--vault", vault, "--manifest", manifest)
    if args.command == "build-image":
        output = args.output or f"dist/endworld-{args.profile}-amd64.img"
        return run("bash", "scripts/build_disk_image.sh", args.profile, output, sudo=True)
    if args.command == "flash":
        image = args.image or f"dist/endworld-{args.profile}-amd64.img"
        return run("bash", "scripts/flash_image.sh", image, args.device, sudo=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
