# Developer Mode

NOMAD is intended to preserve the ability to build software, not only read source code.

## Native toolchain

The NOMAD image builder installs:

- Git;
- build-essential;
- CMake;
- Ninja;
- Clang;
- GDB;
- Python + venv/dev tooling;
- Node.js + npm;
- Java + Maven;
- Rust + Cargo;
- Go;
- SQLite;
- ripgrep;
- tmux;
- Vim.

## Browser IDE

code-server runs on port 8443 with persistent state under:

`state/dev/`

## Local source forge

Forgejo provides local Git hosting and SSH access.

## Developer knowledge

The NOMAD manifest includes or plans space for:

- Stack Overflow;
- Python docs;
- JavaScript docs;
- Node docs;
- Git docs;
- Docker docs;
- Bash/Linux docs;
- freeCodeCamp;
- electronics;
- Arduino;
- Raspberry Pi;
- robotics;
- optional Unix/ServerFault material.

## Preserved build ecosystems

The source vault preserves selected upstream projects such as:

- llama.cpp;
- Qdrant;
- code-server;
- PlatformIO;
- Arduino CLI;
- ESP32 Arduino core;
- CyberChef;
- SatDump;
- rtl-sdr;
- Marlin;
- Klipper;
- Verdaccio;
- Bandersnatch.

Preserved source is not the same as dependency closure. A future CIVILIZATION profile should preserve package ecosystems and selected build dependency graphs more deeply.

## Recommended workflow offline

1. Create/import a project into Forgejo.
2. Work in code-server or over SSH/local console.
3. Consult Kiwix references.
4. Use coder AI for code assistance.
5. Store embeddings/search indexes in Qdrant when an ingestion workflow is available.
6. Replicate important source through Syncthing or cold-storage export.
