# 🚀 THE ARK Beginner Guide

This guide assumes you have **never built a bootable Linux appliance before**.

If a term is unfamiliar, keep going: the steps explain what it means.

## What are we making?

A spare SSD that contains its own operating system plus offline knowledge, AI, maps and tools.

When finished, the SSD can boot a compatible x86-64 PC.

You do **not** copy THE ARK onto your everyday Windows desktop and magically make Windows offline. You build a separate bootable appliance.

## The safest first project: NANO

NANO is 64 GB and contains the same core architecture as the bigger profiles.

Start there.

## What you need

- one x86-64 PC running Debian/Ubuntu Linux for the build;
- Internet while downloading;
- a spare SSD/USB device of at least 64 GB for NANO;
- enough free builder storage for both the downloaded vault and a raw disk image;
- administrator (`sudo`) access.

A useful rule: have **roughly twice the profile size plus temporary space** available on the builder.

## I use Windows or macOS

Direct building is not yet the beginner path.

The current image builder needs Linux features such as loop devices, debootstrap, GRUB and Linux filesystems.

Best current options:

1. use a spare Linux machine;
2. dual-boot or install Debian/Ubuntu on a spare PC;
3. use an experienced Linux host.

A supported Windows/macOS builder is on the frontier list.

## One-command guided setup

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld
bash scripts/ark-wizard.sh
```

The wizard explains each destructive/large step before it happens.

## What the wizard does

### PLAN

Checks what NANO currently resolves to and how large the required payload is.

Nothing large is downloaded yet.

### ACQUIRE

Downloads the actual offline content into:

`vault/nano/`

It also freezes container images and writes:

`vault/nano/lock/nano.lock.json`

That file is your exact receipt.

### PREPARE

Transforms raw assets that need preparation.

Example:

`Spain OSM PBF → Spain PMTiles`

It then writes a CycloneDX bill of materials.

### VERIFY

Re-hashes everything and compares it to the lock.

### RUN

Optional. Starts the Ark services on your current Linux machine so you can test before making a boot disk.

Open:

`http://localhost:8080`

### BUILD IMAGE

Creates a raw bootable disk image:

`dist/endworld-nano-amd64.img`

### FLASH

Writes that image to your spare physical drive.

**Everything previously on that drive is destroyed.**

The project refuses the running root disk and asks you to type the exact target path.

## How do I find the correct drive?

Before inserting the spare disk:

```bash
lsblk -o NAME,SIZE,MODEL,TRAN,MOUNTPOINTS
```

Insert it and run the same command again.

Look for the new device.

Typical examples:

- `/dev/sdb`
- `/dev/sdc`
- `/dev/nvme1n1`

Never guess.

## Boot it

1. Shut down the target computer.
2. Connect the Ark drive.
3. Power on.
4. Enter the machine's boot menu (often F12/F11/Esc/Del; manufacturer-dependent).
5. Select the Ark drive.
6. Wait for Linux and Ark services to start.

## How do I open it?

### From the Ark computer itself

The console automatically logs into the development user.

Current default:

`endworld / endworld`

Change the password:

```bash
passwd
```

### From another computer/phone on Ethernet/LAN

Try:

`http://endworld-nano.local/`

or the Ark machine's IP address.

### Using the Ark's Wi-Fi

If the Wi-Fi chipset supports Linux AP mode, the node creates its profile network.

NANO defaults:

`ENDWORLD-NANO`

The development password is stored in `config/nano.env`. Change it before using the node on an untrusted network.

## What will I see?

The portal links to:

- offline library;
- maps;
- local AI;
- transcription;
- APK vault;
- frozen capability inventory;
- integrity/status.

Bigger profiles add more cards/services.

## I want FAMILY/NOMAD/CIVILIZATION instead

Run the wizard again and select another profile.

Be aware of storage:

- FAMILY: 256 GB
- NOMAD: 1 TB
- CIVILIZATION: 4 TB

CIVILIZATION also snapshots selected APT/PyPI/npm dependencies, so its build stage is significantly heavier.

## Important reality check

GitHub CI proves the source code and profile wiring.

It does not magically perform a complete 4 TB physical build.

For disaster-readiness, perform your own disconnected boot drill and keep more than one copy.
