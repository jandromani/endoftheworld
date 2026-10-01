# Ask the whole Ark

Issue: #10

`prepare` now creates:

`vault/<profile>/state/search/ark-search.sqlite`

using SQLite FTS5.

## Indexed today

The bounded local index covers:

- THE ARK documentation;
- profiles and manifests;
- project scripts/runtime code;
- frozen lock metadata;
- plain-text vault artifacts;
- text/code files inside preserved source TAR/ZIP archives;
- metadata for Kiwix collections.

## Search API

`GET /api/search?q=reticulum`

returns ranked local results.

## Grounded ask API

`POST /api/ask`

```json
{"question":"How does THE ARK preserve source code?"}
```

The portal retrieves local evidence first, labels it `[S1]`, `[S2]`, etc., then asks the local llama.cpp endpoint to answer only from that evidence.

The response includes the sources separately.

## Kiwix limitation

This MVP does not unpack and index every article body from every ZIM. Kiwix remains the full-text engine for those collections and the UI provides a Kiwix search handoff.

Still open:

- federated ZIM article results;
- OCR;
- Qdrant/embedding semantic ingestion;
- multilingual ranking;
- deeper document anchors.
