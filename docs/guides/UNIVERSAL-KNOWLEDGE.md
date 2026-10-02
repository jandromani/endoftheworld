# Universal offline knowledge plane

THE ARK search plane combines three local retrieval systems.

## Lexical / document index

`build_search_index.py` creates SQLite FTS5 under
`state/search/ark-search.sqlite`. It indexes:

- Markdown and plain text;
- source code and configuration;
- frozen source archives;
- PDF text, with OCR fallback for scanned PDFs;
- EPUB;
- DOCX;
- images through local Tesseract OCR;
- lock/BOM inventory metadata.

Kiwix ZIM archives remain queried through Kiwix itself rather than being
expanded into the SQLite database.

## Vector index

NOMAD and CIVILIZATION freeze
`nomic-embed-text-v1.5.Q4_K_M.gguf` and run a second local llama.cpp server
on loopback port 8084 in embedding-only mode.

`vector_index.py` embeds the universal SQLite corpus and writes the vectors
to the local Qdrant `ark_knowledge` collection. No embedding API leaves the
machine.

The service is generated after the normal runtime stack is ready:

```bash
endworld --profile nomad vector-index
```

## Unified retrieval

Portal search, grounded RAG and THE ARK Agent federate:

```text
SQLite FTS5 + Qdrant vectors + Kiwix
```

Results preserve their frozen source path/title/kind/URL so final answers can
cite the evidence rather than relying on model memory.

NANO and FAMILY keep the smaller lexical + Kiwix path; vector/Qdrant is an
intentional richer-profile capability.
