# NANO-MINI

NANO-MINI is **not a product profile**. It exists only to prove the appliance
boot path in CI with a tiny frozen fixture vault.

The gate builds a real GPT image with the same Debian/systemd/Docker/runtime
stack as NANO, then boots a pristine copy twice:

1. legacy BIOS;
2. UEFI with OVMF.

Both boots use `-nic none`. Inside the guest, a one-shot smoke service proves:

- the portal is alive;
- Kiwix is alive;
- local chat reaches the frozen llama container;
- Ask the Ark retrieves a Kiwix article;
- Whisper transcription reaches port 8083;
- the PMTiles file is byte-range served;
- `/vault/state/` is inaccessible;
- WAN detection reports offline.

A successful guest prints `THE_ARK_OFFLINE_SMOKE=PASS` to its serial console
and powers itself off.


The smoke test also exercises THE ARK Agent end-to-end with no NIC:

1. local Kiwix search;
2. frozen article read;
3. confined field-note write;
4. explicit offline status observation;
5. final answer with a frozen source id;
6. policy self-test rejecting a non-allowlisted shell action.

The additional success marker is:

`THE_ARK_AGENT_OFFLINE_SMOKE=PASS`
