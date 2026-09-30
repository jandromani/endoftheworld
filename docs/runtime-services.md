# Runtime Services

The service set depends on profile.

| Service | NANO | FAMILY | NOMAD | CIVILIZATION | Default port |
|---|:---:|:---:|:---:|---:|
| Portal | ✅ | ✅ | ✅ | ✅ | 8080 |
| Kiwix | ✅ | ✅ | ✅ | ✅ | 8081 |
| llama.cpp | ✅ | ✅ | ✅ | ✅ | 8082 |
| whisper.cpp | ✅ | ✅ | ✅ | ✅ | 8083 |
| Forgejo | — | ✅ | ✅ | ✅ | 3000 |
| Syncthing | — | ✅ | ✅ | ✅ | 8384 |
| Qdrant | — | — | ✅ | ✅ | 6333/6334 |
| code-server | — | — | ✅ | ✅ | 8443 |
| Project NOMAD | — | — | ✅ | ✅ | 8090 |

## Portal

The stdlib Python portal:

- serves the UI;
- exposes status/health;
- lists APKs;
- discovers PMTiles;
- exposes the capability inventory;
- proxies local chat;
- proxies transcription;
- supports HTTP Range for large local assets.

## Kiwix

All frozen ZIM files in the knowledge directory are passed to the Kiwix server.

## AI

One llama.cpp service is exposed on port 8082.

NANO/FAMILY use their profile model.

NOMAD stores several models but starts one at a time.

## Voice

whisper.cpp serves the selected frozen model.

## Syncthing / Forgejo

These are persistent household/developer services and therefore store state under `state/`.

## Qdrant

NOMAD uses persistent Qdrant storage for vector collections and future local RAG/indexing.

## code-server

NOMAD exposes a browser IDE with a persistent workspace. It intentionally does not receive the host Docker socket by default.

## Project NOMAD

NOMAD freezes and starts:

- Project NOMAD admin;
- MySQL;
- Redis.

The upstream updater sidecar is intentionally absent. Project NOMAD admin receives Docker-socket access because its application-management architecture requires it; this is documented as a high-trust boundary.


## CIVILIZATION package vault

CIVILIZATION adds immutable APT, PyPI and npm snapshot TARs. These are not daemon services: the portal exposes them as frozen vault artifacts and they are covered by the same lock/BOM integrity model.
