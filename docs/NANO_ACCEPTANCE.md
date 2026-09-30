# ENDWORLD NANO acceptance test

This checklist is the physical Definition of Done for a release candidate.

## A. Builder

- [ ] `make builder-deps` completes on a clean supported x86_64 Debian/Ubuntu host.
- [ ] `make setup` completes.
- [ ] `make doctor` reports no failures.
- [ ] `make nano-plan` resolves all required artifacts.
- [ ] `make nano-acquire` completes after interruption/resume.
- [ ] `make nano-prepare` creates `maps/tiles/spain.pmtiles`.
- [ ] `make nano-verify` passes.
- [ ] Corrupting one frozen byte makes `nano-verify` fail.
- [ ] Restoring the file makes verification pass again.

## B. Local runtime before imaging

- [ ] `make nano-run` starts portal, Kiwix and llama.cpp.
- [ ] Portal status shows Kiwix UP.
- [ ] Portal status shows AI UP.
- [ ] Local AI returns an answer with WAN disconnected.
- [ ] Kiwix opens an article with WAN disconnected.
- [ ] Spain map pans/zooms with WAN disconnected.
- [ ] Browser downloads Bitchat APK from the local vault.
- [ ] HTTP Range request against `spain.pmtiles` returns 206.

## C. Image

- [ ] `make nano-image` creates a 64,000,000,000-byte raw image.
- [ ] Image SHA-256 file verifies.
- [ ] The image contains four GPT partitions with the expected labels.
- [ ] Vault fits with free headroom.

## D. Physical UEFI boot

- [ ] Flash to a sacrificial 64 GB+ device.
- [ ] Boot on an x86_64 UEFI machine with Secure Boot disabled.
- [ ] System reaches ENDWORLD console without WAN.
- [ ] `http://endworld-nano.local/` opens from another LAN device.
- [ ] Reboot twice and confirm services recover automatically.

## E. Physical legacy BIOS boot

- [ ] Boot the same image on one legacy BIOS-capable x86_64 test machine.
- [ ] Portal and vault remain healthy.

## F. Off-grid Wi-Fi

With an adapter whose Linux driver advertises AP mode:

- [ ] SSID `ENDWORLD-NANO` appears.
- [ ] Android/iOS/laptop receives a 10.42.0.x lease.
- [ ] `http://end.world/` opens.
- [ ] captive-portal probe redirects to ENDWORLD.
- [ ] Kiwix, AI, map and APK download work with Ethernet physically unplugged.

If the test adapter lacks AP mode, record the adapter and driver; this is a
hardware compatibility result, not a portal failure.

## G. Failure/recovery

- [ ] Stop Kiwix container; status reports degradation.
- [ ] Restart `endworld-stack.service`; Kiwix recovers.
- [ ] Stop AI container; status reports degradation.
- [ ] Reboot; AI recovers.
- [ ] Disconnect WAN before boot; boot behavior is unchanged.
- [ ] Remove Wi-Fi adapter; Ethernet/mDNS path still works.

## Release sign-off

Record:

```
release:
git_sha:
vault_lock_sha256:
image_sha256:
builder_os:
builder_cpu:
uefi_test_machine:
bios_test_machine:
wifi_adapter:
wifi_driver:
result:
notes:
```
