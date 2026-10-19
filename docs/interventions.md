# P00b: recorded interventions and matched engineering controls

Status: implementation-stage protocol, not a biological assay. The native profile remains `p00a-local-closed-v1`. External interventions are host actions between epochs; they do not add native rewrite rules. Environment supply/transport is deferred so this boundary can be checked against the existing closed-world semantics first.

## Contract

A request has schema `intervention-v1`, the SHA-256 canonical digest of the **entire source Experiment**, and zero to eight ordered operations. The source identity binds laws, limits, seed, profile, state, epoch, allocators, accounting, and writer provenance. A changed source rejects a stale request. Requests and operations reject unknown JSON fields.

Supported host operations:

- `SetState { node, expected, value }`: require an existing node with the stated current i32 value, then set its state. Later operations in the same request see earlier staged changes.
- `MoveResources { from, to, matter, activation }`: require distinct existing nodes and sufficient source balances; transfer u64 amounts with checked arithmetic. No matter/activation enters or leaves the world. This is an explicit external relocation, not native transport or a rule with a hidden global resource access path.

Apply operations to a private branch. Any invalid schema, source mismatch, missing node, state mismatch, insufficient resource, operation-limit violation, overflow, or invalid final invariant returns an error. The immutable source and source checkpoint remain unchanged. There is no partially accepted request.

An empty request is an exact no-op: no event allocated, no writer metadata changed. A nonempty request allocates one external event ID even when the physical edit is a sham. Its receipt records request digest, before/after Experiment digests, source epoch, read/write node keys, and prior writer IDs. It updates the touched node writers; subsequent native events can depend on the intervention event. Event IDs share the world's monotonic counter, but receipts are explicitly external rather than native-rule events. The epoch, rules, seed, allocators, and resource-total constants remain unchanged.

The conservative footprint records entire node keys for state and balance operations. Adjacency is untouched. A compound request's parents come from the original source snapshot; intermediate steps are part of the same atomic external event.

The branch artifact contains the source checkpoint, request plus receipt plus resulting Experiment, final checkpoint, and completion manifest binding all payload digests. CLI publication uses a newly created directory and refuses existing destinations. The manifest is complete only after payload writes return successfully. A consumer must verify hashes and require completion; full crash/power-loss durability is not claimed. Validation errors occur before directory creation; storage errors may leave an explicitly incomplete/failed directory.

A checkpoint alone retains writer IDs but not the full intervening receipt history. Keep the branch bundle and ancestor bundles with any subsequent continuation. This is the same provenance-retention obligation as retaining native traces. Resuming a checkpoint is not proof that all referenced historical events were retained.

## Frozen engineering matrix

Two fixture families × seeds 0–15 × five arms × eight continuation epochs. Each source has two warmup epochs. There are 32 matched cases, 160 arms, 1,280 continuation epochs, and 64 warmup epochs. The two manipulated nodes (IDs 0 and 2) have identical type, state, resources, and contact degree. Both contact the inert node 1. They have no native rule interaction in these fixtures. Node 0 is the focal target; node 2 is the unrelated control; node 1 holds externally relocated resources.

Each family uses the existing two-rule oscillator (0 → 1 → 0). In the activation family, each firing also burns one activation unit. Initial resources: nodes 0/2 each have 8 free matter and 8 activation; node 1 has 0 free matter and 8 activation. Each node and each of two contact edges binds one matter unit. Total matter is 21; activation is 24. Warmup leaves both active nodes at state 0; their activation is 8 in state-arrest and 6 in activation-relocation.

| Arm | State-arrest family | Activation-relocation family |
|---|---|---|
| baseline | Empty request | Empty request |
| sham | Explicitly set focal state 0 → 0 | Move zero resources from focal node to holder |
| target | Set focal state 0 → 9 | Move all 6 focal activation units to holder |
| unrelated | Set control state 0 → 9 | Move all 6 control activation units to holder |
| rescue | Target operation, then a separately recorded 9 → 0 restoration before continuation | Target operation, then separately return the same 6 units before continuation |

The state-arrest fixture expects 8 firings per unaffected node; activation-relocation expects 6. Target treatment expects 0 focal firings; unrelated treatment expects 0 control firings. Baseline/sham/rescue should agree on physical world trajectories and native candidate priorities. They need not agree on event IDs, dependency parents, or full checkpoint hashes: the intervention history is retained. Rescue is an immediate reversibility/control check, not recovery following extended damage.

These deliberately engineered effects validate causal branching machinery. They do not validate self-maintenance, reproduction, adaptation, ecological isolation in arbitrary worlds, or a structure detector. Matching degree/type/resources is sufficient for this known fixture, not a general guarantee of exchangeability.

## Independent verification and failure controls

Python separately reconstructs external operations, identity checks, exact balances, event allocation, writer updates, receipt digests, and each native continuation through the existing independent interpreter. It checks source warmup and fixture law definitions, exact arm inventory, prescribed operations, matched source properties, intended firing counts, and sham/rescue trajectories.

Tamper cases alter receipts, source identity, operation payload, rescue chain length, arm labels, writer metadata, warmup state, or world laws. All must be rejected. CLI checks reapply target and rescue in fresh processes, resume their checkpoints, compare full expected payloads, verify original source bytes remain unchanged, reject malformed/stale/partially failing requests before publication, and reject output-directory overwrite.

No statistical effect claim is made; seeds probe machinery while expected outcomes are fixed by construction. This completes only the intervention component of P00, not P00 itself.

## Usage

Generate fixed fixtures with `causal-alife intervention-fixtures NEW_DIRECTORY`. Apply a request with `causal-alife branch SOURCE_CHECKPOINT REQUEST_JSON NEW_DIRECTORY`. Use `resume NEW_DIRECTORY/checkpoint.json EPOCHS NEW_CHECKPOINT` to continue. The full validation runner covers these commands and preserves evidence; see the README.
