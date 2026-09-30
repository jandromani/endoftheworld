# Ports & Services

| Port | Service | Profiles |
|---:|---|---|
| 8080 | ENDWORLD portal | all |
| 8081 | Kiwix | all |
| 8082 | llama.cpp | all |
| 8083 | whisper.cpp | all |
| 3000 | Forgejo HTTP | FAMILY, NOMAD |
| 2222 | Forgejo SSH | FAMILY, NOMAD |
| 8384 | Syncthing GUI | FAMILY, NOMAD |
| 22000 TCP/UDP | Syncthing transfer | FAMILY, NOMAD |
| 21027 UDP | Syncthing discovery | FAMILY, NOMAD |
| 6333 | Qdrant HTTP | NOMAD |
| 6334 | Qdrant gRPC | NOMAD |
| 8443 | code-server | NOMAD |
| 8090 | Project NOMAD | NOMAD |

These defaults assume a trusted local network or isolated AP. Do not expose them directly to the public Internet without additional security controls.
