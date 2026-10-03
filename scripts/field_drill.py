#!/usr/bin/env python3
"""Collect reproducible physical field evidence for THE ARK.

A report records hardware identity, boot mode, Wi-Fi AP capability, local service
health, WAN reachability and optional vault verification. CI can test the report
format with fixtures, but only a real operator can assert a physical cold boot.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import socket
import subprocess
import urllib.request


def text(path: pathlib.Path):
    try:
        return path.read_text(errors="replace").strip()
    except OSError:
        return None


def command(args, timeout=5):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=timeout).strip()
    except Exception:
        return None


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            return 200 <= r.status < 500
    except Exception:
        return False


def wan_reachable() -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=0.7):
            return True
    except OSError:
        return False


def cpu_model():
    try:
        for line in pathlib.Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def memory_bytes():
    try:
        for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except Exception:
        pass
    return None


def wifi_ap_capable():
    out = command(["iw", "list"])
    if not out:
        return None
    in_modes = False
    for line in out.splitlines():
        s = line.strip()
        if s == "Supported interface modes:":
            in_modes = True
            continue
        if in_modes and s.startswith("* AP"):
            return True
        if in_modes and line and not line.startswith("\t"):
            break
    return False


def disks():
    out = command(["lsblk", "--json", "-b", "-o", "NAME,SIZE,MODEL,TRAN,ROTA,TYPE"])
    if not out:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    return [
        {
            "name": x.get("name"), "bytes": x.get("size"), "model": (x.get("model") or "").strip(),
            "transport": x.get("tran"), "rotational": bool(x.get("rota")),
        }
        for x in data.get("blockdevices", []) if x.get("type") == "disk"
    ]


def gpus():
    out = command(["lspci"])
    if not out:
        return []
    return [line for line in out.splitlines() if any(k in line.lower() for k in ("vga compatible", "3d controller", "display controller"))]


def collect(profile: str) -> dict:
    dmi = pathlib.Path("/sys/class/dmi/id")
    return {
        "profile": profile,
        "hardware": {
            "system_vendor": text(dmi / "sys_vendor"),
            "product_name": text(dmi / "product_name"),
            "product_version": text(dmi / "product_version"),
            "board_name": text(dmi / "board_name"),
            "bios_vendor": text(dmi / "bios_vendor"),
            "bios_version": text(dmi / "bios_version"),
            "boot_mode": "UEFI" if pathlib.Path("/sys/firmware/efi").exists() else "BIOS",
            "cpu": cpu_model(),
            "memory_bytes": memory_bytes(),
            "disks": disks(),
            "gpus": gpus(),
            "wifi_ap_capable": wifi_ap_capable(),
        },
        "runtime": {
            "kernel": command(["uname", "-srmo"]),
            "boot_id": text(pathlib.Path("/proc/sys/kernel/random/boot_id")),
            "uptime_seconds": float((text(pathlib.Path("/proc/uptime")) or "0").split()[0]),
            "docker": command(["docker", "--version"]),
            "reticulum": command(["rnstatus", "--version"]) or ("installed" if shutil.which("rnstatus") else None),
        },
        "checks": {
            "portal": http_ok("http://127.0.0.1/health"),
            "kiwix": http_ok("http://127.0.0.1:8081/"),
            "ai": http_ok("http://127.0.0.1:8082/health"),
            "voice": http_ok("http://127.0.0.1:8083/"),
            "wan_reachable": wan_reachable(),
        },
    }


def agent_smoke(profile: str, vault: pathlib.Path) -> dict:
    script = pathlib.Path(__file__).with_name("agent_runner.py")
    goal = "Find local burn-treatment guidance, cite the frozen source, write a field note, and confirm offline status."
    p = subprocess.run(
        [__import__("sys").executable, str(script), "--vault", str(vault), "--profile", profile,
         "--task-id", "field-agent-smoke", "--json", goal],
        text=True, capture_output=True, timeout=300,
    )
    try:
        data = json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {}
    except Exception:
        data = {}
    return {"ok": p.returncode == 0 and bool(data.get("ok")), "returncode": p.returncode,
            "result": data, "output": (p.stdout + p.stderr)[-4000:]}


def vault_verify(profile: str, vault: pathlib.Path) -> dict:
    script = pathlib.Path(__file__).with_name("verify_vault.py")
    p = subprocess.run(
        [__import__("sys").executable, str(script), "--vault", str(vault), "--profile-id", profile],
        text=True, capture_output=True,
    )
    return {"ok": p.returncode == 0, "returncode": p.returncode, "output": (p.stdout + p.stderr)[-4000:]}


def assess(report: dict, expect_offline: bool, require_cold: bool, require_agent: bool) -> list[str]:
    failures = []
    checks = report.get("checks") or {}
    if not checks.get("portal"):
        failures.append("portal not reachable")
    if not checks.get("kiwix"):
        failures.append("Kiwix not reachable")
    if expect_offline and checks.get("wan_reachable"):
        failures.append("WAN is still reachable during offline drill")
    if require_cold and not report.get("operator_assertions", {}).get("cold_boot"):
        failures.append("cold boot was not asserted by the operator")
    if require_agent and not (report.get("agent_smoke") or {}).get("ok"):
        failures.append("offline agent smoke failed")
    vv = report.get("vault_verification")
    if vv is not None and not vv.get("ok"):
        failures.append("vault verification failed")
    return failures


def markdown(report: dict) -> str:
    h = report["hardware"]
    c = report["checks"]
    a = report["operator_assertions"]
    failures = report.get("failures", [])
    status = "PASS" if report["passed"] else "FAIL"
    return f"""# THE ARK Field Test — {status}

- Report ID: `{report['report_id']}`
- UTC: {report['created_utc']}
- Profile: **{report['profile']}**
- System: {h.get('system_vendor') or 'unknown'} {h.get('product_name') or ''}
- Firmware: {h.get('bios_vendor') or 'unknown'} {h.get('bios_version') or ''}
- Boot: **{h.get('boot_mode')}**
- CPU: {h.get('cpu') or 'unknown'}
- Memory: {h.get('memory_bytes') or 'unknown'} bytes
- Wi-Fi AP capable: {h.get('wifi_ap_capable')}
- Cold boot asserted: {a.get('cold_boot')}
- WAN expected offline: {a.get('expect_offline')}
- WAN reachable: {c.get('wan_reachable')}
- Portal: {c.get('portal')}
- Kiwix: {c.get('kiwix')}
- AI: {c.get('ai')}
- Voice: {c.get('voice')}
- Agent smoke: {(report.get('agent_smoke') or {}).get('ok', 'not requested')}

## Failures

{chr(10).join('- ' + x for x in failures) if failures else '- none'}

This report is evidence from one hardware/run combination, not a universal compatibility claim.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.getenv("ENDWORLD_PROFILE", "nano"))
    ap.add_argument("--vault", default="/srv/endworld")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    ap.add_argument("--expect-offline", action="store_true")
    ap.add_argument("--cold-boot-asserted", action="store_true")
    ap.add_argument("--require-cold-boot", action="store_true")
    ap.add_argument("--verify-vault", action="store_true")
    ap.add_argument("--agent-smoke", action="store_true")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    if args.fixture:
        report = json.loads(pathlib.Path(args.fixture).read_text())
        report.setdefault("profile", args.profile)
    else:
        report = collect(args.profile)

    report["schema"] = 1
    report["protocol"] = "ark-field-test-v1"
    report["evidence_origin"] = "fixture" if args.fixture else "physical"
    report["created_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["report_id"] = report.get("runtime", {}).get("boot_id") or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report["operator_assertions"] = {
        "cold_boot": bool(args.cold_boot_asserted),
        "expect_offline": bool(args.expect_offline),
    }
    if args.verify_vault and not args.fixture:
        report["vault_verification"] = vault_verify(args.profile, pathlib.Path(args.vault))
    if args.agent_smoke and not args.fixture:
        report["agent_smoke"] = agent_smoke(args.profile, pathlib.Path(args.vault))
    failures = assess(report, args.expect_offline, args.require_cold_boot, args.agent_smoke)
    report["failures"] = failures
    report["passed"] = not failures

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        md = pathlib.Path(args.markdown)
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"report": str(out), "passed": report["passed"], "failures": failures}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
