#!/usr/bin/env python3
from __future__ import annotations
import argparse, getpass, os, pathlib, re, shlex, shutil, subprocess

ENV=pathlib.Path("/etc/endworld/profile.env")
MARKER=pathlib.Path("/var/lib/endworld/firstboot.done")
AUTOLOGIN=pathlib.Path("/etc/systemd/system/getty@tty1.service.d/autologin.conf")
SUDOERS=pathlib.Path("/etc/sudoers.d/endworld")
HOSTS=pathlib.Path("/etc/hosts")

def update_env(changes):
    lines=ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out=[];seen=set()
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            k=line.split("=",1)[0]
            if k in changes:
                out.append(k+"="+shlex.quote(changes[k]));seen.add(k);continue
        out.append(line)
    for k,v in changes.items():
        if k not in seen:out.append(k+"="+shlex.quote(v))
    tmp=ENV.with_suffix(".tmp");tmp.write_text("\n".join(out)+"\n",encoding="utf-8");os.chmod(tmp,0o600);os.replace(tmp,ENV);os.chmod(ENV,0o600)

def read_env():
    result={}
    if not ENV.exists():return result
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line:continue
        k,v=line.split("=",1)
        try:
            parts=shlex.split(v);result[k]=parts[0] if parts else ""
        except ValueError:result[k]=v.strip("'\"")
    return result

def ask(label,default):
    value=input(f"{label} [{default}]: ").strip()
    return value or default

def console_password():
    while True:
        a=getpass.getpass("Console password for user endworld (min 12 chars): ")
        b=getpass.getpass("Repeat: ")
        if a!=b:print("Passwords do not match.");continue
        if len(a)<12:print("Use at least 12 characters.");continue
        return a

def secret_password(label,min_len=12,max_len=128):
    while True:
        a=getpass.getpass(f"{label} (min {min_len} chars): ")
        b=getpass.getpass("Repeat: ")
        if a!=b:print("Passwords do not match.");continue
        if not min_len<=len(a)<=max_len:print(f"Use {min_len}-{max_len} characters.");continue
        if any(ord(c)<32 or ord(c)>126 for c in a):print("Use printable ASCII for maximum compatibility.");continue
        return a

def wifi_password():
    while True:
        a=getpass.getpass("Wi-Fi password (8-63 chars): ")
        b=getpass.getpass("Repeat: ")
        if a!=b:print("Passwords do not match.");continue
        if not 8<=len(a)<=63:print("WPA2 passwords must be 8-63 characters.");continue
        if any(ord(c)<32 or ord(c)>126 for c in a):print("Use printable ASCII for maximum Wi-Fi compatibility.");continue
        return a

def update_hosts(host):
    lines=HOSTS.read_text(encoding="utf-8").splitlines() if HOSTS.exists() else []
    out=[];done=False
    for line in lines:
        if line.startswith("127.0.1.1"):
            out.append("127.0.1.1 "+host);done=True
        else:out.append(line)
    if not done:out.append("127.0.1.1 "+host)
    HOSTS.write_text("\n".join(out)+"\n",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");args=ap.parse_args()
    if args.check:print("first-boot wizard: OK");return 0
    if os.geteuid()!=0:raise SystemExit("Run with sudo.")
    if MARKER.exists():print("First-boot setup is already complete.");return 0
    env=read_env();profile=env.get("ENDWORLD_PROFILE","nano")
    print("\nTHE ARK FIRST BOOT\n==================")
    print("Set private credentials before the Wi-Fi access point is enabled.\n")
    keymap=ask("Keyboard layout",env.get("ENDWORLD_KEYMAP","es"))
    if not re.fullmatch(r"[A-Za-z0-9_+.-]{1,32}",keymap):raise SystemExit("Invalid keymap.")
    if shutil.which("loadkeys"):subprocess.run(["loadkeys",keymap],check=False)
    subprocess.run(["localectl","set-keymap",keymap],check=False)
    print(f"Keyboard layout set to {keymap!r} before password entry.")
    host=ask("Hostname",f"endworld-{profile}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,62}",host):raise SystemExit("Invalid hostname.")
    ssid=ask("Wi-Fi name",env.get("ENDWORLD_WIFI_SSID",f"THE-ARK-{profile.upper()}"))
    if not 1<=len(ssid.encode("utf-8"))<=32:raise SystemExit("Wi-Fi SSID must be 1-32 bytes.")
    country=ask("Wi-Fi country code",env.get("ENDWORLD_WIFI_COUNTRY","ES")).upper()
    if not re.fullmatch(r"[A-Z]{2}",country):raise SystemExit("Wi-Fi country must be a two-letter code.")
    wifi=wifi_password();console=console_password()
    changes={"ENDWORLD_WIFI_SSID":ssid,"ENDWORLD_WIFI_PASSWORD":wifi,"ENDWORLD_WIFI_COUNTRY":country,"ENDWORLD_KEYMAP":keymap}
    if env.get("ENDWORLD_ENABLE_CODE_SERVER","0")=="1":
        changes["ENDWORLD_CODE_PASSWORD"]=secret_password("Private code-server password")
    update_env(changes)
    subprocess.run(["chpasswd"],input="endworld:"+console+"\n",text=True,check=True)
    pathlib.Path("/etc/hostname").write_text(host+"\n",encoding="utf-8");update_hosts(host)
    subprocess.run(["hostnamectl","set-hostname",host],check=False)
    SUDOERS.unlink(missing_ok=True);AUTOLOGIN.unlink(missing_ok=True)
    MARKER.parent.mkdir(parents=True,exist_ok=True);MARKER.write_text("configured\n",encoding="utf-8")
    subprocess.run(["systemctl","daemon-reload"],check=False)
    subprocess.run(["systemctl","restart","endworld-network.service"],check=False)
    print("\nSetup complete. Passwordless sudo and console autologin are disabled.")
    print("Reboot is recommended.")
    return 0
if __name__=="__main__":raise SystemExit(main())
