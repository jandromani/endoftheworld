# Zero-touch Ark

Issue: #8

## What ships now

Run:

```bash
bash scripts/ark-gui.sh
```

The launcher opens a local browser builder on `127.0.0.1:8787`.

The GUI lets a non-expert:

1. choose NANO / FAMILY / NOMAD / CIVILIZATION;
2. PLAN;
3. ACQUIRE;
4. create the CIVILIZATION package snapshot when applicable;
5. PREPARE;
6. VERIFY;
7. run SELFTEST;
8. BUILD IMAGE;
9. inspect physical disks and FLASH one.

The browser API has a fixed command allowlist. It does not provide arbitrary shell execution.

## Disk safety

The GUI discovers disks with `lsblk`, identifies the running root disk, blocks it, and requires the exact phrase:

`/dev/<device> ERASE`

before flashing.

The existing low-level flash script still performs its own checks and confirmation.

## First boot

The image contains `endworld-firstboot`.

Before the Wi-Fi access point is enabled, first boot asks for:

- hostname;
- Wi-Fi SSID;
- Wi-Fi password;
- console password;
- country code.

On completion it writes `/var/lib/endworld/firstboot.done`, removes passwordless sudo and removes console autologin for subsequent boots.

## Still open

This is an MVP, not the entire #8 definition of done.

Still needed:

- native desktop packaging;
- Windows builder path;
- macOS builder path;
- signed downloadable prebuilt images;
- fully graphical first boot from another device.
