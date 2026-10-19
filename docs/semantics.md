# P00a executable semantics

Profile: `p00a-local-closed-v1`. This is a bounded engineering subset of revised-plan P00, not the full baseline experimental substrate.

## State and grammar

Nodes have a u16 type, i32 state, and u64 free matter/activation. Every node and every edge binds exactly one matter unit. IDs and monotone allocators are u64. Edges have a class (Contact or Structural), u16 type, and 2–4 ordered, distinct existing endpoints. Duplicate class/type/endpoint tuples are invalid. IDs are never reused. Arithmetic is checked in both development and release builds.

The initial environment is closed with fixed contact edges. Only structural edges can be created/deleted. There is no supply, transport, geometry, external mutation, or global reservoir. Contact edges are charged matter at initialization. Node deletion returns its bound/free matter and activation to a distinct specified recipient and rejects while any incident edge remains. A rule may delete structural edges before deleting a node. Initial contact-connected nodes therefore cannot be deleted under this profile; this is an explicit limitation, not a general chemistry assumption.

Patterns have 1–6 labelled node slots, at most 8 positive edges, at most 8 absent edges, and 1–8 operations. Positive edges must connect all matched slots. A one-node pattern is connected. Bindings are injective; endpoint order is semantic. Each distinct ordered role binding is one candidate: no implicit symmetry quotient or random deduplication. Rule IDs denote distinct rule instances; exact duplicate bodies under different IDs contribute distinct candidates. This multiplicity is part of the profile and must be controlled by a future generator.

Rules read a pre-epoch snapshot. Conditions match types, optional exact states, positive edges, and absent edges. Operations execute in listed order against a private copy. Created nodes append new slots, addressable by subsequent operations. References to deleted slots, insufficient resources, overflow, duplicate edges, or dangling deletion make a candidate inapplicable. Grammar-invalid rules reject the experiment. No silent repair occurs.

## Accounting

At every transition:

```
sum(free matter) + node count + edge count = initial matter_total
sum(activation) + cumulative dissipated = initial activation_total
```

Creation withdraws one matter unit from a specified matched/local account. Edge/node deletion returns its bound inventory exactly once. Transfer has a distinct source/destination. Burn reduces local activation and adds to the dissipation ledger. The ledger is diagnostic accumulated bookkeeping; it is not read by rules or a globally contested resource. These balances are not thermodynamic claims.

## Scheduling and conflicts

Rules are enumerated by ascending ID. Both matchers traverse the same type/state-compatible injective partial assignments. The reference scans nodes for each pattern slot; the indexed variant builds a type index. Every pushed partial binding counts toward max_bindings; every full pattern match counts toward max_candidates even when the operation sequence is unaffordable. Breaching either cap aborts the epoch unchanged. The indexed matcher is a modest optimization, not an independent transition engine.

Priority is the SHA-256 hex digest of canonical JSON:

```
["priority-v1", seed, epoch, rule_id, [bound_node_ids...]]
```

Sort ascending by (priority, rule ID, binding). SHA-256 is used as deterministic pseudo-random priority, with this versioned encoding; no mutable PRNG stream is consumed. Distinct candidate identities are not promised to couple after graph-changing interventions.

Read footprints conservatively contain both `node:id` and `adj:id` for every matched node, whether or not every field is examined. State/resource updates write `node:id`. Edge edits write endpoint adjacency keys; node deletion writes node and adjacency keys. Thus both positive and negative edge predicates conflict with relevant topology changes. New IDs are omitted from candidate conflict footprints because they do not yet exist; actual event writes include them after allocation during commit.

Greedy selection rejects write/read, read/write, and write/write overlap. Read/read sharing is permitted. This conservative footprint may serialize compatible operations; no claim of maximally parallel or kinetic scheduling is made. Shared local accounts serialize. Selected candidates execute in (rule ID, binding) order with canonical allocations. Their footprint disjointness makes their snapshot requirements safe under this execution order.

All transitions are staged into a cloned world. Node/edge caps apply to the resulting epoch state. Any batch error, invariant failure, counter overflow, or size-cap breach leaves the entire original Experiment unchanged. Even an epoch with no events increments the epoch; quiescent runs do not terminate automatically. No partial candidate list is executed.

## Dependency records

The world tracks the last writer for each node/adjacency key, including deletion tombstones. Event parents are the sorted unique last writers of the candidate's read/write keys. Initial-state reads have no event parent. Events are numbered monotonically in commit order. This conservative dependency DAG does not establish causal necessity; it does not capture all scheduler exclusion alternatives. Fine field-level witnesses and scientific lineage inference are deferred.

## Canonical encoding and checkpoints

JSON object keys are recursively sorted lexicographically (including stringified numeric map keys); arrays retain order; UTF-8 compact JSON has no spaces. Digests use SHA-256. Checkpoints include the entire Experiment: profile, seed, rules, limits, graph, allocators, ledgers, epoch, event counter, and writer map. They include an envelope schema and payload digest. Unknown fields, unknown profiles, invalid balances, bad allocators, and digest mismatches reject loading. Hashes detect accidental alteration; they are not authentication.

The writer creates a new `.pending` file exclusively, writes/syncs complete bytes, then hard-links the final name without overwriting it. Failed/incomplete pending files remain for inspection; only a requested final checkpoint name is loaded. Final files are validated completely before continuation. Power-loss durability on every filesystem is not yet certified. Loading does not change semantic state. Resume runs in a fresh process in the validation script; no-op branches use the exact copied checkpoint.

## Scope exclusions

No asynchronous within-world workers, durable event-store recovery, configurable logging modes, resource injections, match-rate kinetics, transport, active-persistence detector, maintenance detector, random-law generator, or evolutionary search is implemented. Running fixtures does not pass the full P00 gate and does not authorize P01/E01 scientific admission. The independent Python interpreter verifies the fixed fixture corpus; Rust tests separately exercise invalid/capped cases.

## P00b extension

Host state/resource interventions now have a separate [request and receipt contract](interventions.md). Native profile semantics above are unchanged; the extension explicitly records external event IDs rather than attributing host edits to native rules.
