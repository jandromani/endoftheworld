# Environment Variables

Profile defaults live in `config/<profile>.env`.

## Common

| Variable | Meaning |
|---|---|
| `ENDWORLD_PROFILE` | active profile |
| `ENDWORLD_VAULT` | vault path override |
| `ENDWORLD_WIFI_SSID` | AP SSID |
| `ENDWORLD_WIFI_PASSWORD` | AP password |
| `ENDWORLD_WIFI_COUNTRY` | regulatory country |
| `ENDWORLD_WIFI_ADDRESS` | AP address/CIDR |
| `ENDWORLD_AI_THREADS` | llama.cpp threads |
| `ENDWORLD_AI_CONTEXT` | context size |
| `ENDWORLD_AI_MODEL_ID` | selected model |
| `ENDWORLD_WHISPER_MODEL_ID` | selected Whisper model |

## FAMILY / NOMAD

`ENDWORLD_ENABLE_SYNCTHING` · `ENDWORLD_ENABLE_FORGEJO`

## NOMAD

`ENDWORLD_AI_MODE` · `ENDWORLD_AI_LITE_MODEL_ID` · `ENDWORLD_AI_GENERAL_MODEL_ID` · `ENDWORLD_AI_CODER_MODEL_ID` · `ENDWORLD_ENABLE_QDRANT` · `ENDWORLD_ENABLE_CODE_SERVER` · `ENDWORLD_ENABLE_NOMAD` · `ENDWORLD_CODE_PASSWORD` · `ENDWORLD_PROJECT_NOMAD_PORT`

Project NOMAD DB/application secrets are generated into persistent state on first launch rather than committed.

## Builder

`ENDWORLD_IMAGE_BYTES` · `ENDWORLD_DEBIAN_SUITE` · `ENDWORLD_DEBIAN_MIRROR` · `ENDWORLD_BUILD_TMP` · `ENDWORLD_PLANETILER_MEMORY`

Do not commit real credentials into profile env files.
