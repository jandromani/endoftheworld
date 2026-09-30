# FAQ

## Is THE ARK an apocalypse project?

It can be used for emergency preparedness, but the architecture is equally relevant to remote sites, education, field labs, homelabs and long-lived offline deployments.

## Why is the repository still called `endoftheworld`?

THE ARK is the public identity. ENDWORLD is retained as the engine/CLI name and repository legacy identifier to avoid breaking automation and links.

## Why not put all binaries in Git?

Large datasets and container archives do not belong in ordinary Git history. Git stores the reproducible control plane; the vault stores payloads.

## Why not just mirror everything?

Because storage, validation time and operator attention are finite. Curation is a feature.

## Why Kiwix?

ZIM is a mature format for self-contained offline content and Kiwix provides a practical local server.

## Why PMTiles?

It packages vector tile data into a single range-addressable archive, making offline map serving simple.

## Why not Ollama?

The current implementation standardizes directly on llama.cpp for a small, explicit runtime surface. Other engines could become profile capabilities later.

## Does NOMAD have RAG?

It has Qdrant and local AI, but a fully automated ingestion/RAG layer over all Ark content is still roadmap work.

## Why is Project NOMAD inside ENDWORLD NOMAD?

Project NOMAD contributes an excellent local command-center/application model. ENDWORLD remains the outer acquisition and trust boundary.

## Why disable its updater?

A field node should not mutate its trusted baseline merely because an Internet tag changed. Updates should be rebuilt through the Ark pipeline.

## Does CI prove the appliance works on hardware?

No. CI proves repository contracts and software paths. Hardware/offline acceptance requires a real image, real storage and a disconnected boot test.

## Does this replace normal backups?

No. Back up mutable state and important personal data separately.
