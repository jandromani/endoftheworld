# Public release runbook

This runbook is for a release candidate built from a fully acquired and verified
profile. Release packaging is a cryptographic/distribution gate; it is not a
substitute for physical field proof.

## 1. Build and verify

```bash
python scripts/endworld.py --profile nano acquire
python scripts/endworld.py --profile nano prepare
python scripts/endworld.py --profile nano verify
python scripts/endworld.py --profile nano selftest
python scripts/endworld.py --profile nano build-image
```

## 2. Trust audit

```bash
python scripts/trust_audit.py lock vault/nano/lock/nano.lock.json
```

If a Trivy or Grype JSON report is available:

```bash
python scripts/trust_audit.py vulnerabilities scan.json
```

Unallowlisted CRITICAL findings fail policy. Exceptions belong in
`config/vulnerability-allowlist.yml` and should be time-bounded and justified.

## 3. Signing key boundary

Keep the private release key on offline/removable signing media. Do not put it
in Git, GitHub Actions, the field Ark, or the release directory.

Verify the public-key fingerprint independently:

```bash
python scripts/release_trust.py fingerprint --public-key keys/release-public.pem
```

## 4. Create the release

```bash
python scripts/endworld.py --profile nano release-create \
  --version 1.0.0-rc1 \
  --private-key /offline-signing/release-private.pem \
  --public-key keys/release-public.pem
```

The default output is:

`dist/releases/nano-1.0.0-rc1/`

and contains the compressed disk image, frozen lock, CycloneDX SBOM, public
key, signed release manifest, detached signature, SHA256SUMS and verification
instructions.

## 5. Verify as a recipient

On a separate machine/copy of the release:

```bash
python scripts/endworld.py release-verify dist/releases/nano-1.0.0-rc1
```

Expected marker:

`THE_ARK_PUBLIC_RELEASE=VERIFIED`

## 6. Physical promotion

Only after cryptographic verification:

1. flash a dedicated SSD;
2. boot with WAN physically removed;
3. complete first boot;
4. run the field test with cold-boot and Agent smoke;
5. repeat on additional supported hardware;
6. commit the field reports;
7. promote RC → stable only when the physical campaign gate passes.

## Reproducibility spot check

For critical selected outputs built twice:

```bash
python scripts/trust_audit.py compare build-a.bin build-b.bin --label bootloader
```

A PASS means byte-for-byte identity only. It does not replace source review,
signature validation, SBOM policy or offline functional testing.
