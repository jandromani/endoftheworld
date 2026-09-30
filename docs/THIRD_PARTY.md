# Third-party preservation policy

ENDWORLD orchestrates and preserves third-party projects; it does not relicense
them. Upstream copyright, attribution and redistribution conditions remain in
force.

The Builder should preserve upstream LICENSE/NOTICE material whenever it
captures source or release bundles.

## Reticulum

The Reticulum reference implementation is distributed under the project's
custom **Reticulum License**, not a standard OSI identifier. ENDWORLD stores an
unaltered upstream source snapshot and must preserve its license text and
conditions. In particular, ENDWORLD treats that source as runtime/network
software and **not** as material for training an AI/ML/language-model dataset.

## Content packs

Kiwix ZIM files aggregate works with their own content licenses. Inclusion in an
ENDWORLD profile does not imply one uniform license over all content.

## Models and datasets

AI model weights, OpenStreetMap-derived data and other large datasets keep their
own upstream terms. A future profile should not assume that because a downloader
can fetch an artifact it is automatically lawful to redistribute that artifact
as a public binary release.

## Release rule

Before publishing a prebuilt ENDWORLD image to third parties, review the
redistribution terms represented by that image. A locally built personal vault
and a publicly redistributed multi-project image are different licensing
scenarios.
