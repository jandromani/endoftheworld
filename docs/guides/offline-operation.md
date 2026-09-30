# Offline Operation

## Objective

An offline acceptance test should prove the node remains useful with all WAN access removed.

## Before disconnecting

Confirm:

- lock exists;
- BOM exists;
- vault verification passes;
- services start;
- maps are prepared;
- mutable-state directories are writable.

## Disconnect WAN

Use a genuinely disconnected test:

- unplug WAN;
- disable upstream Wi-Fi;
- block router Internet if necessary.

Do not confuse “DNS failure” with actual isolation.

## Core checks

### Portal

Open the node by LAN IP or mDNS.

### Knowledge

Open multiple Kiwix collections and search them.

### AI

Ask a question that does not require current Internet information.

### Voice

Upload/record a sample audio file and confirm transcription.

### Maps

Pan/zoom prepared regions.

### Apps

Download an APK from the local vault to a client device.

## FAMILY checks

- create a Forgejo repo;
- restart the stack;
- verify repo persistence;
- pair a Syncthing device/folder;
- replicate a small file.

## NOMAD checks

- switch AI modes;
- edit a project in code-server;
- create a Qdrant collection;
- open Project NOMAD;
- reboot and verify persistence;
- compile a small program in several installed toolchains.

## Reboot drill

A field appliance should survive repeated cold boots.

After each reboot:

```bash
sudo python3 /opt/endworld/scripts/healthcheck.py --vault /srv/endworld --profile-id <profile>
```

## Integrity drill

Periodically re-run vault verification.

Mutable `state/` data should be backed up separately and is expected to change.
