# Acquisition and update policy

ENDWORLD has two independent loops:

## 1. Known capability update loop

A monthly scout checks pinned upstream projects for new releases or commits. It records metadata only. No new release is automatically promoted into a stable image.

A Builder can subsequently acquire approved versions into quarantine. Acquisition should preserve, where licensing allows:

- source archive and exact commit
- release binaries / APK / firmware
- upstream checksums and signatures
- license and attribution files
- documentation
- container digest or image archive
- SBOM and ENDWORLD-generated hashes

## 2. New capability discovery loop

The scout also searches selected capability families for candidate projects. Candidates are ranked only as leads for review; popularity is never treated as trust.

Before promotion, a capability should pass:

1. identity/provenance check
2. license/redistribution review
3. architecture/support check
4. source and artifact hash capture
5. malware/static checks where applicable
6. SBOM generation
7. offline installation test
8. offline functional smoke test
9. rollback test
10. exact version freeze

## Cadence

Monthly is a good default for discovery because ENDWORLD values stability over novelty.

A stable image should normally be rebuilt quarterly or on demand. Critical security fixes may justify an exceptional rebuild. Data with a different natural cadence (maps, Wikipedia/ZIM, blockchain, package mirrors) should have its own policy rather than inheriting the software cadence.

## Never

- never execute newly discovered binaries during discovery
- never auto-promote unknown software
- never replace the last known-good artifact
- never depend on a floating `latest` tag inside a frozen image
- never store secrets in the manifest
