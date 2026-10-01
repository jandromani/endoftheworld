# Physical field-test protocol

THE ARK never treats a green GitHub Action as proof that a random PC, Wi-Fi chip,
GPU and SSD will survive a real disconnected boot.

## One real test

1. Build and flash a verified Ark image.
2. Power the target machine fully off.
3. Remove/disable normal WAN connectivity.
4. Power it on from cold state.
5. Confirm the portal and Kiwix work locally.
6. Run vault verification.
7. Generate a signed/committable field report.

Example:

```bash
sudo python3 /opt/endworld/scripts/field_drill.py \
  --profile nomad \
  --vault /srv/endworld \
  --expect-offline \
  --cold-boot-asserted \
  --require-cold-boot \
  --verify-vault \
  --out /srv/endworld/state/field/nomad-test.json \
  --markdown /srv/endworld/state/field/nomad-test.md
```

The operator assertion is explicit because software cannot prove that you
physically removed power before the current boot.

## Promote evidence into the repository

Copy the JSON report into `field-reports/` after reviewing it for information
you are comfortable publishing.

Then regenerate:

```bash
python scripts/hardware_matrix.py \
  --reports field-reports \
  --out docs/hardware-matrix.md
```

## Support rule

A hardware combination is:

- **UNVERIFIED** until there is a field report;
- **PASS** only for the tested combination represented by that report;
- never promoted merely because a similar laptop/chipset worked.

## Repeated recovery

Reference cadence in `hardware/matrix.yml`:

- monthly integrity scrub;
- quarterly disconnected recovery drill;
- storage-media review every two years.

These are starting operational defaults, not guarantees of media lifespan.

## SSD/NVMe guidance

Prefer reputable SSD/NVMe devices with published endurance specifications,
monitor SMART/NVMe health where supported, keep independent copies, and replace
media proactively when health indicators or error history deteriorate.

The final ARK design assumes that **storage devices fail** and relies on
replication rather than faith in one drive.
