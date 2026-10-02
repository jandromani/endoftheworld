# THE ARK Agent

THE ARK Agent is the offline reasoning/execution plane of a field node. It is
deliberately smaller than a general-purpose computer-control agent.

## Trust model

The frozen vault is read-only. The agent may write only under:

`/srv/endworld/state/agent/workspace/`

The first version has no arbitrary shell, package installation, disk flashing,
trust-root changes, or silent WAN fallback. Every model action and tool result
is appended to a human-readable JSONL audit trail.

## Loop

```text
goal
  -> model emits one JSON action
  -> allowlist policy
  -> local tool
  -> observation
  -> persisted task state
  -> repeat or final answer
```

Tools:

- `ark.search` — local FTS + Kiwix.
- `ark.read_source` — read only a source returned by search.
- `ark.status` — node/services/offline state.
- `ark.maps` — list frozen PMTiles.
- `ark.write_note` — agent workspace only.
- `ark.mesh_status` — Ark Mesh / Reticulum readiness.
- `ark.playbook` — explicitly allowlisted non-destructive playbooks.

## CLI

```bash
endworld --profile nano agent "Find the local burn guidance, cite it, and write a field note."
```

## Portal/API

The portal exposes a local task panel backed by `POST /api/agent/run`.
Task summaries are available at `GET /api/agent/tasks`.

## Offline gate

NANO-MINI boots with QEMU `-nic none` and forces the agent through a real
search → source read → note write → status → final sequence. The gate also
executes a policy self-test that attempts a non-allowlisted shell tool.

Success marker:

`THE_ARK_AGENT_OFFLINE_SMOKE=PASS`

This proves bounded tool use in the virtual offline appliance. It does not
replace physical hardware field proof.
