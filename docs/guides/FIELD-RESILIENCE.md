# Power, radio and beyond-IP resilience

THE ARK treats electricity and communications as part of the computer.

## Power policy

Every image contains `scripts/power_policy.py` and a systemd timer.

Default:

```text
ENDWORLD_POWER_POLICY=monitor
```

Monitor mode writes telemetry but never stops services.

To opt into automatic conservation:

```bash
sudo sed -i 's/ENDWORLD_POWER_POLICY=monitor/ENDWORLD_POWER_POLICY=conserve/' /etc/endworld/profile.env
sudo systemctl restart endworld-power.timer
```

Default thresholds:

```text
20% → enter NANO survival mode
35% → recover stopped services
```

"NANO survival mode" is a service-shedding policy, not a destructive profile conversion. The portal, local maps and Kiwix remain; heavy AI/developer/replication/Project NOMAD containers are stopped to reduce consumption.

If NUT (`upsc`) and `ENDWORLD_UPS_NAME` are available, UPS telemetry is incorporated. Otherwise Linux power-supply sysfs is used.

## Field communications

Generate the human field plan:

```bash
python scripts/field_comms.py render \
  --config config/field-comms.yml \
  --out field-comms.md
```

Generate a conservative Reticulum config:

```bash
python scripts/field_comms.py reticulum-config \
  --config config/field-comms.yml \
  --out reticulum.conf
```

The default uses Reticulum AutoInterface and does **not** enable transport routing automatically.

## Communications ladder

```text
Ethernet
  ↓
Ark Wi-Fi AP
  ↓
Reticulum / Meshtastic
  ↓
receive-only SDR / satellite information
```

Radio operation remains region- and licence-dependent. THE ARK does not hard-code transmit frequencies or power.

## What is software-complete vs field-proven?

The policy engine, plan generator and frozen radio sources can be tested in CI. Real UPS, solar, LoRa, SDR and satellite hardware still require the #14 hardware/drill evidence process.
