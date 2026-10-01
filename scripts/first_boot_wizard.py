#!/usr/bin/env python3
from __future__ import annotations
import argparse, getpass, os, pathlib, re, subprocess

ENV=pathlib.Path("/etc/endworld/profile.env")
MARKER=pathlib.Path("/var/lib/endworld/firstboot.done")
AUTOLOGIN=pathlib.Path("/etc/systemd/system/getty@tty1.service.d/autologin.conf")
SUDOERS=pathlib.Path("/etc/sudoers.d/endworld")

def update_env(changes):
    lines=ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out=[]; seen=set()
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            k=line.split("=",1)[0]
            if k in changes:
                out.append(k+"="+changes[k]);seen.add(k);continue
        out.append(line)
    for k,v in changes.items():
        if k not in seen:out.append(k+"="+v)
    tmp=ENV.with_suffix(".tmp");tmp.write_text("\n".join(out)+"\n",encoding="utf-8");os.replace(tmp,ENV)

def ask(label,default):
    v=input(f"{label} [{default}]: ").strip()
    return v or default

def new_password(label):
    while True:
        a=getpass.getpass(label+" (min 12 chars): ")
        b=getpass.getpass("Repeat: ")
        if a!=b:print("Passwords do not match.");continue
        if len(a)<12:print("Use at least 12 characters.");continue
        return a

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");args=ap.parse_args()
    if args.check:print("first-boot wizard: OK");return 0
    if os.geteuid()!=0:raise SystemExit("Run with sudo.")
    if MARKER.exists():print("First-boot setup is already complete.");return 0
    env={}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k,v=line.split("=",1);env[k]=v
    profile=env.get("ENDWORLD_PROFILE","nano")
    print("\nTHE ARK FIRST BOOT\n==================")
    print("Set private credentials before the Wi-Fi access point is enabled.\n")
    host=ask("Hostname",f"endworld-{profile}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,62}",host):raise SystemExit("Invalid hostname.")
    ssid=ask("Wi-Fi name",env.get("ENDWORLD_WIFI_SSID",f"THE-ARK-{profile.upper()}"))
    country=ask("Wi-Fi country code",env.get("ENDWORLD_WIFI_COUNTRY","ES")).upper()
    wifi=new_password("Wi-Fi password")
    console=new_password("Console password for user endworld")
    update_env({"ENDWORLD_WIFI_SSID":ssid,"ENDWORLD_WIFI_PASSWORD":wifi,"ENDWORLD_WIFI_COUNTRY":country})
    subprocess.run(["chpasswd"],input="endworld:"+console+"\n",text=True,check=True)
    pathlib.Path("/etc/hostname").write_text(host+"\n",encoding="utf-8")
    subprocess.run(["hostnamectl","set-hostname",host],check=False)
    SUDOERS.unlink(missing_ok=True);AUTOLOGIN.unlink(missing_ok=True)
    MARKER.parent.mkdir(parents=True,exist_ok=True);MARKER.write_text("configured\n",encoding="utf-8")
    subprocess.run(["systemctl","daemon-reload"],check=False)
    subprocess.run(["systemctl","restart","endworld-network.service"],check=False)
    print("\nSetup complete. Passwordless sudo and console autologin are disabled.")
    print("Reboot is recommended.")
    return 0
if __name__=="__main__":raise SystemExit(main())
