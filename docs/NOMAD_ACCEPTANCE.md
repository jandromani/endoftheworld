# ENDWORLD NOMAD acceptance

Software acceptance and physical field acceptance are separate.

## CI/source acceptance
Python/shell validation, NANO+FAMILY+NOMAD selftests, exact 1 TB envelope, live required-source resolution, synthetic acquire/hash/verify, capability routing, and AI-switch wiring must pass.

## Builder acceptance
On a real x86-64 builder: `make nomad-acquire`, `make nomad-prepare`, `make nomad-verify`, `make nomad-selftest`, `make nomad-image`.

## Offline runtime acceptance
With WAN removed verify Kiwix/maps; lite/general/coder switching; Whisper; persistent Forgejo/Syncthing/Qdrant/code-server; Project NOMAD+MySQL+Redis from frozen images without updater; APK/firmware downloads; and Reticulum installation.

## Physical acceptance
Still requires acquiring the real hundreds-of-GB vault, building/flashing a >=1 TB SSD/NVMe, BIOS+UEFI boot tests, Wi-Fi AP test where supported, repeated disconnected reboots, on-node rehash and persistence checks. Until then NOMAD is software/CI-complete, not physically field-proven.
