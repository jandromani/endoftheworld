# Field radio and beyond-IP operations

THE ARK treats radio as a field capability, not as a reason to silently
transmit.

## Receive-only baseline

`ark-radio inventory` reports available RTL-SDR/SatDump/Reticulum pieces.

`ark-radio plan` writes a receive-only field plan.

`ark-radio capture` uses `rtl_sdr` to record IQ samples for a frequency,
sample rate and bounded duration selected by the operator. It contains no
transmit path.

NOMAD/CIVILIZATION preserve SatDump and RTL-SDR source so receive workflows can
be rebuilt from frozen source/dependencies.

## Beyond IP

The field stack is layered:

1. Ethernet / local Wi-Fi;
2. Reticulum;
3. LXMF / Sideband;
4. Meshtastic hardware where available;
5. receive-only SDR / satellite data.

Actual frequencies, transmit power, licensing and radio configuration remain
operator decisions subject to local rules and hardware.

## Power coupling

`power_policy.py` observes Linux batteries and optional NUT UPS telemetry.
With `conserve` policy it can shed heavy services and enter NANO survival
mode. Transitions can emit persistent local events for later agent handling.

## Evidence

Presence of source code or a firmware bundle is not radio hardware proof.
A supported field combination needs a real hardware report and disconnected
drill before it is marked field-proven.
