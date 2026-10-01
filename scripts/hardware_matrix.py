#!/usr/bin/env python3
"""Aggregate committed THE ARK field reports into a human hardware matrix."""
from __future__ import annotations

import argparse
import json
import pathlib


def human_bytes(n):
    if n is None:
        return "?"
    x = float(n)
    for u in ("B", "GB", "TB"):
        if u == "B" and x >= 1_000_000_000:
            x /= 1_000_000_000
            continue
        if u == "GB" and x >= 1000:
            x /= 1000
            continue
        return f"{x:.0f} {u}"
    return f"{x:.1f} TB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", default="field-reports")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = pathlib.Path(args.reports)
    rows = []
    for p in sorted(root.glob("*.json")) if root.exists() else []:
        try:
            r = json.loads(p.read_text())
        except Exception:
            continue
        if r.get("protocol") != "ark-field-test-v1":
            continue
        h = r.get("hardware") or {}
        rows.append([
            r.get("profile", "?"),
            " ".join(x for x in (h.get("system_vendor"), h.get("product_name")) if x) or "unknown",
            h.get("boot_mode", "?"),
            h.get("cpu", "?"),
            human_bytes(h.get("memory_bytes")),
            str(h.get("wifi_ap_capable")),
            "PASS" if r.get("passed") else "FAIL",
            p.name,
        ])
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    head = """# THE ARK Physical Hardware Matrix

This table contains only committed field reports. **No row means no evidence.**
CI success is not hardware support evidence.

| Profile | Hardware | Boot | CPU | RAM | Wi-Fi AP | Result | Evidence |
|---|---|---|---|---:|---|---|---|
"""
    body = "\n".join("| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |" for row in rows)
    if not rows:
        body = "| — | No physical reports committed yet | — | — | — | — | UNVERIFIED | — |"
    out.write_text(head + body + "\n", encoding="utf-8")
    print(f"{len(rows)} report(s) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
