# Philosophy

## Preserve capability, not nostalgia

THE ARK does not try to mirror the Internet for its own sake. Storage is finite. Every byte competes with another capability.

The project values material that lets people:

- understand;
- diagnose;
- communicate;
- repair;
- navigate;
- learn;
- program;
- fabricate;
- reproduce knowledge;
- recover systems.

## The Ark metaphor

The product ladder intentionally uses the Ark metaphor.

A NANO device carries only the smallest viable set of “animals”: a compact library, a small model, a map and communications tooling.

FAMILY carries more species and supports a household.

NOMAD adds a workshop: development, search, repair, radio and reconstruction tooling.

CIVILIZATION and ARK expand from individual/household continuity toward preservation of larger technical ecosystems.

The metaphor is useful because it forces curation. The question is not “can we download this?” but “does this deserve a place on the boat?”

## Reproducibility over convenience

A live `latest` tag is convenient until it changes.

A remote web UI is convenient until DNS, authentication or the provider disappears.

THE ARK prefers explicit versions, manifests, hashes and rebuilds.

## Graceful degradation

Profiles should remain useful when some hardware capabilities are absent.

Examples:

- no GPU → CPU inference still works, slower;
- no Wi-Fi AP support → Ethernet/mDNS fallback;
- insufficient RAM for a NOMAD 30B mode → switch to lite;
- optional knowledge source grows beyond budget → skip it while preserving required artifacts.

## Human control

Scout may discover. Automation may download into quarantine. Stable profiles should not silently promote unknown code.

The final trust transition remains deliberate.
