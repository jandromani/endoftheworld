# Trusted Ark Releases

Issue: #9

Every image build now produces:

```text
dist/endworld-<profile>-amd64.img
dist/endworld-<profile>-amd64.img.sha256
dist/endworld-<profile>-amd64.img.release.json
```

The release manifest binds:

- image SHA-256 and byte size;
- frozen lock SHA-256 and byte size;
- CycloneDX BOM SHA-256 and byte size;
- profile;
- Git commit;
- UTC creation time.

## Generate an offline signing key

Keep the private key outside the repository.

```bash
python scripts/release_trust.py keygen \
  --private /secure/ark-private.pem \
  --public trust/ark-release-public.pem
```

## Sign a release manifest

```bash
python scripts/release_trust.py sign \
  --file dist/endworld-nano-amd64.img.release.json \
  --key /secure/ark-private.pem \
  --signature dist/endworld-nano-amd64.img.release.sig
```

If `ENDWORLD_SIGNING_KEY` is set during image build, the signature is created automatically.

## Verify

```bash
python scripts/release_trust.py verify \
  --file dist/endworld-nano-amd64.img.release.json \
  --public-key trust/ark-release-public.pem \
  --signature dist/endworld-nano-amd64.img.release.sig
```

The same detached-signature primitive can sign offline update bundles.

## Still open

- Secure Boot;
- hardware-backed release keys;
- published signed prebuilt GitHub releases;
- stronger upstream signature coverage;
- formal vulnerability/promotion policy.
