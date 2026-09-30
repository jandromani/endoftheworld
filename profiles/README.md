# Profiles

Profiles are declarative storage/capability envelopes.

NANO is the current reference:

```
profiles/nano.yml
```

Required top-level structure:

```yaml
schema: 1

profile:
  id: nano
  title: ENDWORLD NANO
  target_bytes: 64000000000
  reserve_bytes: 12000000000

runtime:
  portal_port: 8080

artifacts:
  - id: ...
    family: ...
    kind: url | index_latest | github_release_asset | github_snapshot
    required: true | false
    destination: ...
    budget_bytes: ...

containers:
  - id: ...
    image: ...
    required: true | false
```

Future profiles should reuse the same artifact semantics. New resolver kinds
belong in shared builder code rather than one-off shell commands embedded in a
profile.
