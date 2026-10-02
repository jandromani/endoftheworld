#!/usr/bin/env python3
"""Power/field policy for THE ARK.

Default policy is monitor-only. If ENDWORLD_POWER_POLICY=conserve, a node on
battery can automatically shed heavy services below a configured threshold,
leaving the portal, static maps and Kiwix available as a low-power survival
surface. This is called "NANO survival mode"; it does not rewrite the profile.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import time

HEAVY_STOP = [
    "endworld-nomad-admin",
    "endworld-code-server",
    "endworld-qdrant",
    "endworld-forgejo",
    "endworld-syncthing",
    "endworld-ai",
    "endworld-whisper",
    "endworld-nomad-redis",
    "endworld-nomad-mysql",
]
RECOVER_ORDER = [
    "endworld-nomad-mysql",
    "endworld-nomad-redis",
    "endworld-syncthing",
    "endworld-forgejo",
    "endworld-qdrant",
    "endworld-code-server",
    "endworld-ai",
    "endworld-whisper",
    "endworld-nomad-admin",
]


def read_text(path: pathlib.Path):
    try:
        return path.read_text().strip()
    except OSError:
        return None


def read_int(path: pathlib.Path):
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def sysfs_status(root: pathlib.Path) -> dict:
    result = {
        "battery_present": False,
        "battery_percent": None,
        "battery_status": None,
        "ac_online": None,
        "power_watts": None,
        "energy_wh": None,
        "runtime_hours_estimate": None,
    }
    if not root.exists():
        return result

    for dev in root.iterdir():
        typ = (read_text(dev / "type") or "").lower()
        if typ == "battery" and not result["battery_present"]:
            result["battery_present"] = True
            result["battery_percent"] = read_int(dev / "capacity")
            result["battery_status"] = read_text(dev / "status")
            p = read_int(dev / "power_now")
            e = read_int(dev / "energy_now")
            if p is None:
                current = read_int(dev / "current_now")
                voltage = read_int(dev / "voltage_now")
                if current is not None and voltage is not None:
                    p = (current * voltage) / 1_000_000
            if p is not None:
                result["power_watts"] = round(float(p) / 1_000_000, 2) if p > 10000 else round(float(p), 2)
            if e is not None:
                result["energy_wh"] = round(float(e) / 1_000_000, 2)
            if result["energy_wh"] and result["power_watts"] and result["power_watts"] > 0:
                result["runtime_hours_estimate"] = round(result["energy_wh"] / result["power_watts"], 2)
        elif typ in ("mains", "usb", "usb_c", "ac"):
            online = read_int(dev / "online")
            if online is not None:
                result["ac_online"] = bool(online) if result["ac_online"] is None else bool(result["ac_online"] or online)
    return result


def nut_status() -> dict:
    name = os.getenv("ENDWORLD_UPS_NAME", "").strip()
    if not name or not shutil.which("upsc"):
        return {"available": False}
    try:
        out = subprocess.check_output(["upsc", name], text=True, stderr=subprocess.DEVNULL, timeout=3)
    except Exception:
        return {"available": False}
    rows = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            rows[k.strip()] = v.strip()
    charge = None
    try:
        charge = float(rows.get("battery.charge", ""))
    except ValueError:
        pass
    status = rows.get("ups.status")
    return {
        "available": True,
        "name": name,
        "status": status,
        "battery_percent": charge,
        "on_battery": bool(status and "OB" in status.split()),
        "low_battery": bool(status and "LB" in status.split()),
        "runtime_seconds": float(rows["battery.runtime"]) if rows.get("battery.runtime", "").replace(".", "", 1).isdigit() else None,
        "load_percent": float(rows["ups.load"]) if rows.get("ups.load", "").replace(".", "", 1).isdigit() else None,
    }


def docker_exists(name: str) -> bool:
    try:
        return subprocess.call(["docker", "inspect", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except OSError:
        return False


def docker_running(name: str) -> bool:
    try:
        out = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", name], text=True, stderr=subprocess.DEVNULL)
        return out.strip().lower() == "true"
    except Exception:
        return False


def transition(mode: str, state_dir: pathlib.Path) -> list[str]:
    actions = []
    state_dir.mkdir(parents=True, exist_ok=True)
    stopped_path = state_dir / "power-stopped.json"

    if mode == "survival":
        stopped = []
        for name in HEAVY_STOP:
            if docker_exists(name) and docker_running(name):
                subprocess.run(["docker", "stop", "-t", "8", name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                stopped.append(name)
                actions.append("stopped:" + name)
        stopped_path.write_text(json.dumps(stopped, indent=2) + "\n")
    elif mode == "normal":
        try:
            wanted = set(json.loads(stopped_path.read_text()))
        except Exception:
            wanted = set()
        for name in RECOVER_ORDER:
            if name in wanted and docker_exists(name) and not docker_running(name):
                subprocess.run(["docker", "start", name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                actions.append("started:" + name)
        stopped_path.unlink(missing_ok=True)
    return actions


def decide(status: dict, policy: str, threshold: float, recover: float, previous: str) -> str:
    if policy != "conserve":
        return "monitor"
    ups = status.get("ups") or {}
    percent = status.get("battery_percent")
    on_battery = status.get("ac_online") is False or bool(ups.get("on_battery"))
    if ups.get("low_battery"):
        return "survival"
    ups_percent = ups.get("battery_percent")
    effective = ups_percent if ups_percent is not None else percent
    if on_battery and effective is not None and effective <= threshold:
        return "survival"
    if previous == "survival":
        if status.get("ac_online") is True:
            return "normal"
        if effective is not None and effective >= recover:
            return "normal"
        return "survival"
    return "normal"


def emit_agent_event(state_path: pathlib.Path, name: str, payload: dict) -> None:
    scheduler = pathlib.Path(__file__).with_name("agent_scheduler.py")
    try:
        vault = state_path.resolve().parents[2]
    except IndexError:
        return
    if not scheduler.is_file() or not (vault / "state").exists():
        return
    subprocess.run([
        __import__("sys").executable, str(scheduler), "--vault", str(vault),
        "emit", name, "--payload", json.dumps(payload, separators=(",", ":"))
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sysfs", default="/sys/class/power_supply")
    ap.add_argument("--fixture")
    ap.add_argument("--state", default="/srv/endworld/state/field/power.json")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--policy", choices=["monitor", "conserve"], default=os.getenv("ENDWORLD_POWER_POLICY", "monitor"))
    ap.add_argument("--threshold", type=float, default=float(os.getenv("ENDWORLD_POWER_THRESHOLD", "20")))
    ap.add_argument("--recover", type=float, default=float(os.getenv("ENDWORLD_POWER_RECOVER", "35")))
    ap.add_argument("--emit-events", action="store_true")
    args = ap.parse_args()

    if args.threshold >= args.recover:
        raise SystemExit("threshold must be below recover percentage")

    state_path = pathlib.Path(args.state)
    state_dir = state_path.parent
    if args.fixture:
        status = json.loads(pathlib.Path(args.fixture).read_text())
    else:
        status = sysfs_status(pathlib.Path(args.sysfs))
        status["ups"] = nut_status()

    try:
        old = json.loads(state_path.read_text())
        previous = old.get("mode", "normal")
    except Exception:
        previous = "normal"

    mode = decide(status, args.policy, args.threshold, args.recover, previous)
    actions = []
    if args.apply and args.policy == "conserve" and mode != previous:
        actions = transition(mode, state_dir)

    out = {
        "schema": 1,
        "timestamp_unix": int(time.time()),
        "policy": args.policy,
        "threshold_percent": args.threshold,
        "recover_percent": args.recover,
        "mode": mode,
        "previous_mode": previous,
        "actions": actions,
        **status,
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, state_path)
    if args.emit_events and args.policy == "conserve" and mode != previous:
        event = "low-power" if mode == "survival" else "power-recovered"
        emit_agent_event(state_path, event, {
            "mode": mode,
            "previous_mode": previous,
            "battery_percent": out.get("battery_percent"),
            "ac_online": out.get("ac_online"),
            "power_watts": out.get("power_watts"),
            "runtime_hours_estimate": out.get("runtime_hours_estimate"),
        })
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
