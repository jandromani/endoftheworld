# Contributing to THE ARK

THE ARK is a capability-preservation project. A good contribution makes the offline node more useful **without weakening reproducibility, trust or storage discipline**.

## Before opening a PR

1. Run the existing profile self-tests.
2. Keep NANO/FAMILY/NOMAD backward compatible unless the PR explicitly changes a contract.
3. Never replace a pinned/frozen dependency with an unbounded runtime download.
4. Document provenance, expected size and license considerations for new artifacts.
5. Prefer maintained upstreams and stable machine-readable sources.
6. Explain the offline use case.

## Adding a capability

A capability proposal should answer:

- **What problem remains offline?**
- **Which profile needs it?**
- **What is the upstream source?**
- **How is the version resolved?**
- **How large can it become?**
- **Is it required or optional?**
- **How is integrity verified?**
- **Is it runnable, preserved source, firmware, an APK, knowledge or a build dependency?**
- **What acceptance test proves it is useful?**

Do not add software merely because it is interesting.

## Adding an artifact

Artifacts live in a profile YAML and must have:

- a unique `id`;
- `family`;
- supported `kind`;
- explicit `required` policy;
- safe relative destination;
- non-zero `budget_bytes`;
- enough source metadata for reproducible resolution.

Downloaded artifacts are quarantined data. Acquisition must never execute them.

## Adding a container

Containers must use explicit repositories and tags. At acquisition time ENDWORLD freezes the pulled image into the vault and records its hash/digest metadata.

A new service also needs:

- start/stop wiring;
- health/status reporting;
- capability-plane action;
- documented port;
- mutable-state location;
- CI coverage.

## Adding a profile

A profile is a product contract, not a loose preset. Define:

- exact target bytes;
- reserve bytes;
- acquisition headroom;
- root partition size;
- mission statement;
- required capabilities;
- optional capability ordering;
- preparation steps;
- runtime services;
- acceptance criteria;
- `profiles/<name>/README.md`.

## Documentation standard

Update docs in the same PR when behavior changes. User-facing commands must be copy-pasteable. Clearly distinguish:

- implemented;
- CI-tested;
- source-resolved;
- acquired;
- image-built;
- physically field-tested.

## Pull request checklist

- [ ] Python compiles.
- [ ] Shell scripts parse.
- [ ] Existing profile self-tests pass.
- [ ] New profile/capability has deterministic validation.
- [ ] Required live sources resolve.
- [ ] Storage budgets remain valid.
- [ ] Runtime ports do not collide.
- [ ] Mutable state is not put under immutable hashes.
- [ ] Documentation is updated.
- [ ] No secret or credential is committed.

## Commit style

Use short imperative subjects such as:

`Add NOMAD developer plane`

`Harden checksum resolution`

`Document offline recovery workflow`

## Scope

Defensive, resilient, educational and reconstruction-oriented tooling is welcome. Contributions that primarily enable harm, unauthorized access or evasion are outside the purpose of THE ARK.
