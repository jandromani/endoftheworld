# ENDWORLD FAMILY acceptance

FAMILY is considered source-complete when every deterministic check below is
green. Physical acceptance additionally requires a real acquisition, image build
and boot on target hardware.

## CI acceptance

The `Validate ENDWORLD FAMILY` workflow must prove:

- all Python entrypoints compile;
- all shell entrypoints parse;
- NANO and FAMILY source self-tests pass;
- FAMILY remains exactly 256,000,000,000 bytes;
- FAMILY keeps 24 GB reserve and 20 GB acquisition headroom;
- required capability ids are present;
- both Spain and Portugal derived PMTiles are declared;
- the portal starts as profile `family`;
- `/api/maps` discovers multiple map archives;
- HTTP byte-range serving works;
- Syncthing and Forgejo appear as service capabilities;
- every required Internet source resolves during the plan stage;
- the generic CLI exposes FAMILY build/flash commands.

NANO validation must remain green in the same pull request.

## Builder acceptance

Run:

```bash
make family-plan
make family-acquire
make family-prepare
make family-verify
make family-selftest
```

Acceptance conditions:

- `vault/family/lock/family.lock.json` exists;
- `vault/family/lock/family.cdx.json` exists;
- no required acquisition failure is recorded;
- every represented frozen file re-hashes successfully;
- payload bytes remain below the 232 GB usable envelope;
- `spain.pmtiles` and `portugal.pmtiles` exist;
- frozen container TARs exist for Kiwix, llama.cpp, whisper.cpp, Syncthing and Forgejo.

## Local runtime acceptance

Run:

```bash
make family-run
make family-status
```

Required health:

- portal UP;
- Kiwix UP;
- AI UP;
- Whisper UP;
- at least one PMTiles map READY;
- Reticulum source/installation available;
- Syncthing UP;
- Forgejo UP.

Then verify manually:

- Kiwix opens both Spanish and English reference content.
- A local AI prompt completes with the 8B model while disconnected.
- An audio file transcribes locally.
- Spain and Portugal can both be selected in the map UI.
- An Android APK downloads from the portal.
- Syncthing can pair a second trusted device and replicate a test file.
- Forgejo completes first-instance setup and can create/clone/push a local test repository.

## Image acceptance

Run:

```bash
make family-image
sha256sum -c dist/endworld-family-amd64.img.sha256
```

Verify:

- GPT contains BIOS_GRUB, EFI, ROOT and DATA partitions;
- image virtual size is exactly 256,000,000,000 bytes;
- root partition ends at 12,288 MiB;
- vault fits in the data partition;
- BIOS GRUB installation succeeds;
- removable UEFI GRUB installation succeeds.

## Physical acceptance

Flash a disposable 256 GB-or-larger SSD and boot one BIOS-capable system and one
UEFI-capable system when practical.

With upstream Internet disconnected:

1. boot to the ENDWORLD console;
2. connect over Ethernet/mDNS;
3. verify `http://endworld-family.local/`;
4. verify the ENDWORLD-FAMILY AP when the Wi-Fi adapter supports AP mode;
5. verify Kiwix, AI, transcription, both maps, Syncthing and Forgejo;
6. reboot and verify Syncthing/Forgejo state persists;
7. run the on-node health check;
8. verify the frozen vault still passes SHA-256 validation.

GitHub-hosted CI cannot replace this physical boot/radio/storage test.
