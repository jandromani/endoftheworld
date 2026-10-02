#!/usr/bin/env python3
"""Aggregate physical field reports without turning CI into fake hardware proof."""
from __future__ import annotations
import argparse, json, pathlib, sys

def identity(report):
    h=report.get("hardware") or {}
    return "|".join(str(h.get(k) or "") for k in ("system_vendor","product_name","board_name","bios_version"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reports",default="field-reports")
    ap.add_argument("--min-hardware",type=int,default=2)
    ap.add_argument("--require-bios-and-uefi",action="store_true")
    ap.add_argument("--require-agent",action="store_true")
    ap.add_argument("--out")
    a=ap.parse_args()
    root=pathlib.Path(a.reports); rows=[]
    for p in sorted(root.glob("*.json")) if root.exists() else []:
        try:r=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        if r.get("protocol")!="ark-field-test-v1":continue
        rows.append((p,r))
    passed=[(p,r) for p,r in rows if r.get("passed") is True]
    hardware={identity(r) for _,r in passed if identity(r).strip("|")}
    modes={str((r.get("hardware") or {}).get("boot_mode") or "") for _,r in passed}
    boot_ids={str((r.get("runtime") or {}).get("boot_id") or "") for _,r in passed if (r.get("runtime") or {}).get("boot_id")}
    failures=[]
    if len(hardware)<a.min_hardware:failures.append(f"need {a.min_hardware} unique physical hardware identities, have {len(hardware)}")
    if a.require_bios_and_uefi and not {"BIOS","UEFI"}.issubset(modes):failures.append("need both BIOS and UEFI evidence")
    if a.require_agent and any(not (r.get("agent_smoke") or {}).get("ok") for _,r in passed):failures.append("one or more passing reports lack agent smoke")
    if any((r.get("checks") or {}).get("wan_reachable") for _,r in passed):failures.append("a passing report has WAN reachable")
    result={"schema":1,"protocol":"ark-field-campaign-v1","reports":len(rows),"passing_reports":len(passed),
            "unique_hardware":len(hardware),"boot_modes":sorted(modes),"unique_boot_ids":len(boot_ids),
            "field_proven":not failures,"failures":failures,
            "evidence":[p.name for p,_ in passed]}
    if a.out:
        p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if not failures:print("THE_ARK_PHYSICAL_CAMPAIGN=PASS")
    return 0 if not failures else 2
if __name__=="__main__":raise SystemExit(main())
