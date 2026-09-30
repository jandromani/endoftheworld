#!/usr/bin/env python3
"""ENDWORLD command-line entrypoint.

The CLI is deliberately profile-oriented so NANO becomes the template for
larger profiles without changing the operator workflow.
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
    ap.add_argument("--profile", default="nano", choices=["nano"])
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("plan", "acquire", "prepare", "verify", "run", "stop", "status", "doctor", "scout"):
        sub.add_parser(name)
    b = sub.add_parser("build-image")
    b.add_argument("--output", default="dist/endworld-nano-amd64.img")
    f = sub.add_parser("flash")
    f.add_argument("device")
    f.add_argument("--image", default="dist/endworld-nano-amd64.img")
    args = ap.parse_args()

    if args.profile != "nano":
        raise SystemExit("Only NANO is implemented in v0.1")

    py = sys.executable
    if args.command in ("plan", "acquire"):
        return run(py, "scripts/build_nano.py", args.command)
    if args.command == "prepare":
        rc = run(py, "scripts/prepare_nano.py")
        if rc:
            return rc
        return run(py, "scripts/generate_bom.py", "--vault", "vault/nano")
    if args.command == "verify":
        return run(py, "scripts/verify_vault.py", "--vault", "vault/nano")
    if args.command == "run":
        return run("bash", "runtime/start-nano.sh")
    if args.command == "stop":
        return run("bash", "runtime/stop-nano.sh")
    if args.command == "status":
        return run(py, "scripts/healthcheck.py", "--local")
    if args.command == "doctor":
        return run("bash", "scripts/doctor.sh")
    if args.command == "scout":
        return run(py, "scripts/scout.py")
    if args.command == "build-image":
        return run("bash", "scripts/build_disk_image.sh", args.output, sudo=True)
    if args.command == "flash":
        return run("bash", "scripts/flash_image.sh", args.image, args.device, sudo=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
