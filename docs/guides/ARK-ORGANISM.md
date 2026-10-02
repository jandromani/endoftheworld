# THE ARK Organism

THE ARK is no longer only a bootable offline vault. The final software
architecture separates discovery, trust, reasoning, events and replication so
the system can keep operating without giving an LLM unrestricted control.

## Planes

```text
CONNECTED SIDE                         OFFLINE / FIELD SIDE

Scout
  | discovery only
  v
Evolution proposal
  | untrusted metadata
  v
static quarantine -> Ark analysis -> HUMAN APPROVAL -> manifest/CI
  |
  v
Builder / Factory -> signed frozen generation
                         ||
=========================|| trust boundary
                         ||
                     Ark Agent
                         |
              +----------+----------+
              |          |          |
           tools      scheduler   events
              |          |          |
        local evidence   reboot   power state
              |
        +-----+------+----------+
        |            |          |
      field       research   engineer
        \            |          /
         \-----------+---------/
                  coordinator
                         |
                    mutable state
                         |
                    Ark Mesh
                         |
             generations / cold export
                         |
               multi-node redundancy
```

## Agent roles

Roles change **instructions, not permissions**.

- `field`: immediate local operability and resource constraints.
- `research`: source-grounded synthesis and uncertainty.
- `engineer`: reproducible diagnosis and safe implementation planning.
- `coordinator`: reconciles specialist reports.

Every role uses the same allowlisted tool registry. There is still no arbitrary
shell, silent WAN fallback, package installation or disk flashing from the
agent.

## Scheduler and events

`ark-agent-scheduler` stores jobs and events in SQLite under mutable agent
state. It supports:

- recurring interval jobs;
- named local events;
- enable/disable;
- persistent systemd timer execution;
- recovery of tasks left in `running` state after reboot.

Power-policy transitions can emit `low-power` and `power-recovered` events.
Events are persisted even when the local AI is temporarily unavailable.

## Multi-role orchestration

`endworld orchestrate` runs a small set of bounded specialist agents and one
coordinator. This is not a permission-escalating swarm: each specialist is an
ordinary Ark Agent with the same tool policy and separate audit trail.

## Generations and replication

Ark Mesh provides content-addressed chunks and verified capability packs.
Capability packs can be signed and verification can be mandatory before apply.

`ark-generations` adds:

- immutable generation metadata;
- cold-storage exports;
- full integrity verification;
- restore;
- activation metadata and rollback.

`ark-cluster` evaluates multiple inventory files against
`config/ark-cluster.yml`, including copy counts, node roles, state backups,
cold storage and distinct physical sites.

## Evolution

Scout never makes a candidate trusted. The implemented promotion path is:

```text
Scout
 -> PROPOSED_UNTRUSTED
 -> static archive inspection (no execution)
 -> local Ark Agent analysis
 -> explicit human approval
 -> APPROVED_FOR_MANIFEST_REVIEW
 -> normal profile/manifest change
 -> CI
 -> freeze/sign next generation
```

There is intentionally no `auto_execute=true` or silent self-modification.

## What software can and cannot prove

Software/CI can prove the contracts above and no-NIC virtual operation.

It cannot prove:

- a particular physical PC/UEFI/Wi-Fi adapter is reliable;
- a real UPS/solar setup survives an outage;
- a real SDR/radio works with the chosen hardware;
- three sites actually exist in different geographic locations.

Those claims require committed physical evidence. THE ARK keeps those gates
separate so a simulated topology can never become a fake field claim.
