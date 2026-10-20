# P01g registration and sampler structural review

2026-10-20. **The generator-v2 sampling-feasibility protocol and independent Rust
and Python samplers are implemented and statically reviewed. No hash-keyed law
was constructed and no native transition ran.** This milestone fixes the
development question and input selection before observing any sampled table.
Scientific status remains untested.

The [protocol](p01g_protocol.json) fixes proposal IDs 4000..4015, initial-state IDs
0..3, proposal-major order and 128 epochs per trajectory: 16 law cells, 64
trajectories and 8,192 requested epochs. It preserves the immutable
[v2 distribution design](generator_v2_design.md), including modulo bias, duplicate
rules, initial resource inventories, Contact ring, state draws and kernel limits.
It changes neither v1 nor any consumed P01/P01e/P01f evidence.

The primary development mechanism gate requires two distinct sampled rule tables
with an actual attached funded newborn visible to both estimators, and one of
those tables with a same-child birth/visibility/recycling loop in a single
trajectory. Duplicate tables count once. Four initial states remain nested
conditions, not independent law samples. Additional funding and descendant
construction are secondary endpoints. The complete engineering gate requires all
64 horizons, full independent generation/transition/detector agreement, valid
event-level extraction and resource/provenance checks. A failed or incomplete
panel stops escalation; a positive panel only permits proposing another bounded
development study. These are engineering thresholds, not statistical or life
criteria. [Registration rationale](p01g_registration.md) explains scope and costs.

`generator-v2` is a separate binary, leaving frozen Cargo/library/generator files
unchanged. The Python sampler independently constructs the same declared
distribution. Both CLIs require a future separate execution admission bound to
the exact protocol bytes and fixed slot. Their full sampled-output equivalence
has not yet been measured. The static review does not establish a useful law,
sampler preimage, prevalence, AP, maintenance, reproduction or evolution.

The locked offline release build and Clippy with warnings denied passed. Three
Rust tests and all 40 Python tests passed. New sampler tests injected literal
bounded field values; they exercised all eight templates, transfer routes,
wildcard/concrete states, inventories, draw-index separation and boundary/error
conditions without calling the hash-keyed law path. Synthetic decision tests
reject pooled children, pooled initial states, duplicate-table inflation,
censored positives, unborn IDs, changed law identities and altered cell counts.
Both new Python entry points reject `-O`. No registered witness, generator draw,
candidate matching or dynamical replay was used by the new tests.

The [registration freeze](p01g_registration_freeze.json) binds the prior frozen
source union, consumed reachability prerequisite, new protocol/rationale,
sampler implementations and static checker/tests. The
[static receipt](evidence/p01g-registration-001/static_review.json) and its
[inventory](evidence/p01g-registration-001/checksums.json) were produced in a new
output directory. External build/test logs and later closeout documentation are
bound by [publication context](evidence/p01g-registration-001/publication_context.json).
This is not an execution freeze or simulator seal. All earlier source freezes
and published receipt entries remain unchanged.

**Next implement the fixed campaign and event-level mechanism validator using the
existing worker, reporter, guard and independent interpreters.** Validate its
aggregation/failure handling with synthetic records, then freeze the complete
source/dependency/binary/input closure and separate execution admission before
any hash-keyed law construction or trajectory, including tests/rehearsals. Only
the fixed batch may subsequently run under the registered ceilings; no replaced
law, repaired input, reroll, longer horizon, relaxed gate, consumed-panel repeat
or E01 is admitted. Preserve full detector disagreements and closed activation
limits. No sampling is admitted by this registration-only closeout.
