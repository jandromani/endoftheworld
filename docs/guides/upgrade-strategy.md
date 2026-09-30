# Upgrade Strategy

THE ARK separates **discovery** from **promotion**.

Recommended lifecycle:

```text
Scout → quarantine → verify → offline test → freeze → build → promote
```

A field node should never replace a trusted dependency merely because an upstream `latest` tag moved.

## Mutable data

Back up and migrate Forgejo, Syncthing, Qdrant, Project NOMAD state and IDE workspaces separately from the immutable vault.

## Rollback

Keep the previous known-good image and matching lock/BOM until the replacement passes offline acceptance.

Scout is an information workflow, not an automatic field updater.
