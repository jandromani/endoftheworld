#!/usr/bin/env python3
"""Receive-only radio/SDR operations for THE ARK field node."""
from __future__ import annotations
import argparse, json, pathlib, shutil, subprocess, time, os

def inventory(vault):
    src=vault/"source/radio"; firmware=vault/"firmware/meshtastic"
    return {
        "schema":1,"receive_only":True,
        "rtl_sdr":shutil.which("rtl_sdr"),"rtl_test":shutil.which("rtl_test"),"rtl_fm":shutil.which("rtl_fm"),
        "satdump":shutil.which("satdump"),
        "satdump_source":next((str(x) for x in src.glob("satdump-source-*")),None) if src.is_dir() else None,
        "rtl_sdr_source":next((str(x) for x in src.glob("rtl-sdr-source-*")),None) if src.is_dir() else None,
        "meshtastic_bundles":[str(x) for x in sorted(firmware.glob("*"))] if firmware.is_dir() else [],
        "reticulum":shutil.which("rnstatus"),
    }

def plan(vault,out):
    inv=inventory(vault)
    text=f"""# THE ARK receive-only field radio plan

This playbook never transmits. The operator must select frequencies and comply
with local rules before using any transmitter.

## Hardware discovery

- rtl_sdr: {inv['rtl_sdr'] or 'not installed'}
- rtl_test: {inv['rtl_test'] or 'not installed'}
- rtl_fm: {inv['rtl_fm'] or 'not installed'}
- SatDump binary: {inv['satdump'] or 'not installed'}
- SatDump frozen source: {inv['satdump_source'] or 'not preserved in this profile'}
- Reticulum: {inv['reticulum'] or 'not installed'}

Run field_radio.py inventory and rtl_test -t before capture.

## Generic IQ capture

Choose a lawful receive frequency and sample rate, then run field_radio.py
capture with --frequency-hz, --sample-rate, --seconds and --out. The command
calls rtl_sdr only and cannot transmit.

## Satellite/weather decode

If a compatible SatDump binary is installed, process a previously captured
file locally. NOMAD/CIVILIZATION preserve SatDump source so the decoder can be
rebuilt from frozen sources/dependencies.

## Mesh communications

Meshtastic firmware bundles preserved: {len(inv['meshtastic_bundles'])}
Reticulum status command: rnstatus
LXMF/Sideband are the preferred message layer over Reticulum.
"""
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding="utf-8")
    return {"out":str(out),**inv}

def capture(freq,rate,seconds,out,gain):
    exe=shutil.which("rtl_sdr")
    if not exe:raise SystemExit("rtl_sdr is not installed")
    if freq<=0 or rate<225000 or rate>3200000:raise SystemExit("invalid receive frequency/sample rate")
    if seconds<1 or seconds>3600:raise SystemExit("capture duration must be 1..3600 seconds")
    out.parent.mkdir(parents=True,exist_ok=True)
    cmd=[exe,"-f",str(freq),"-s",str(rate)]
    if gain is not None:cmd+=["-g",str(gain)]
    cmd.append(str(out));started=time.time();p=subprocess.Popen(cmd)
    try:p.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    return {"path":str(out),"bytes":out.stat().st_size if out.exists() else 0,
            "seconds":round(time.time()-started,2),"frequency_hz":freq,"sample_rate":rate,"receive_only":True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--vault",default=os.getenv("ENDWORLD_VAULT","/srv/endworld"))
    sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("inventory")
    p=sub.add_parser("plan");p.add_argument("--out",default="/srv/endworld/state/field/radio-plan.md")
    c=sub.add_parser("capture");c.add_argument("--frequency-hz",type=int,required=True);c.add_argument("--sample-rate",type=int,default=2048000)
    c.add_argument("--seconds",type=int,default=60);c.add_argument("--gain",type=float);c.add_argument("--out",required=True)
    a=ap.parse_args();vault=pathlib.Path(a.vault)
    if a.cmd=="inventory":result=inventory(vault)
    elif a.cmd=="plan":result=plan(vault,pathlib.Path(a.out))
    else:result=capture(a.frequency_hz,a.sample_rate,a.seconds,pathlib.Path(a.out),a.gain)
    print(json.dumps(result,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
