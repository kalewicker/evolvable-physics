# P00a fixture and verification matrix

All seven trace fixtures run seeds 0–15 for exactly 12 epochs. Rust reference/indexed outputs must match completely. Python separately enumerates matches, applies operations, reconstructs conflict selection, dependencies, accounting, canonical hashes, and every final state. No candidate/seed replacement is used.

| Fixture | Engineering expectation | Scientific classification |
|---|---|---|
| frozen | Zero events; only epoch advances | Untested; no persistence detector |
| oscillator | Two independent nodes alternate 0/1; 24 events; return to initial node values | Known state oscillation only |
| attach_detach | Local edge creation/deletion and activation dissipation; exact balances | Untested |
| growth_recycling | Funded node/edge creation and deletion; allocator continuation | Untested; no reproduction inference |
| transfer | Shared recipient serializes competing transfers; balances exact | Untested |
| absence_conflict | Edge creation excludes a competing absence-dependent rewrite | Untested |
| resource_exhaustion | Compound operation is inapplicable; no partially changed state | Untested |

Additional Rust regression tests exercise match/binding/node/edge caps with full rollback, disconnected patterns, corrupted balances, duplicate edges, compound operation overflow, dangling deletion, shared-account conflicts, prior-event provenance, no-op branching, rule-storage order, independent thread execution, 3/4-endpoint ordered hyperedges, and epoch/event-counter overflow.

Python tamper tests must reject altered priorities, final states, parent records, omitted events, and changed rules. Fresh-process checks must match seven resumed epochs to uninterrupted continuation; zero-epoch continuation must match the checkpoint exactly. Truncated/tampered checkpoints and attempts to overwrite an existing checkpoint must fail.

Independent threads run separate complete worlds; this is not a test of parallel matching inside one world. There is no separate logging-disabled mode. The Python audit does not independently certify grammar rejection or budget exhaustion. Those limits must remain explicit in the findings report.
