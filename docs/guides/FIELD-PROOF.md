# Physical field proof

CI can prove software contracts; it cannot prove a Wi-Fi chipset, SSD, firmware,
battery or motherboard.

A physical campaign is valid only when its JSON reports were created on real
hardware with WAN deliberately removed.

## Per-machine run

Boot the flashed Ark, disconnect WAN, then run:

```bash
sudo ark-field-test \
  --profile nano \
  --vault /srv/endworld \
  --expect-offline \
  --cold-boot-asserted \
  --require-cold-boot \
  --verify-vault \
  --agent-smoke \
  --out field-reports/<machine>-<boot>.json \
  --markdown field-reports/<machine>-<boot>.md
```

Repeat cold boots and keep each report. Do not edit a failed report into a pass.

## Campaign gate

With reports from at least two genuinely different machines:

```bash
python3 scripts/field_campaign.py \
  --reports field-reports \
  --min-hardware 2 \
  --require-bios-and-uefi \
  --require-agent \
  --out field-reports/campaign.json
```

Only a successful real campaign may emit:

`THE_ARK_PHYSICAL_CAMPAIGN=PASS`

Fixture reports used by CI validate the schema only. They are not field
evidence and must never be committed as hardware support evidence.
