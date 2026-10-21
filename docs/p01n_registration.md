# P01n: fixed literal-field readiness for proposed v4

2026-10-20. Register the independent Rust/Python literal adapters and fixed
readiness checks **before implementing them**. The [protocol](p01n_protocol.json)
and [literal registry](p01n_literal_fields.json) fix inputs, order, expected
semantics, traces, negative controls, limits and failure handling. This is an
engineering registration, with no proposal IDs or sampled experiment panel.

## Fixed factored panel

| Panel | Expansion | Cases |
| --- | --- | ---: |
| Constructive rules | 27 type maps × 27 state maps × 3 donors × 3 constructive variants | 6,561 |
| Unchanged rules | 27 type maps × 3 donors × 6 other variants × 16 raw state pairs | 7,776 |
| Assemblies | 27 type maps × 27 state maps × 4 initial records | 2,916 |
| Ignored fields | 37 groups, values fixed in registry | 395 |
| Invalid input | 79 named mutations | 79 |
| Validator-only local conditions | 13 fixed Boolean vectors | 13 |

There are **17,727 adapter requests**; the 13 local-condition descriptors are
checked by the future validator, not sent to either adapter. This is a factored
panel rather than every possible field combination. All 729 map-pair groups
have four initial IDs, identical rules and identical shared maps. Assembly
rotation depends only on map indices, never the initial ID. Nine rotations
cover all forms/routes across the panel; each assembly still has eight slots.

The constructive panel deliberately supplies raw wildcard states, a newborn
value different from its mapped state, wrong raw target/newborn kinds and
matter=0. Effective v4 roles must nevertheless use the declared maps and
Structural matter=1. The unchanged panel covers SetState, AddState, Burn,
Contact Transfer, Contact-pattern edge creation and Structural edge-only
deletion, retaining raw state/wildcard and amount/material boundaries.

Ignored-field probes require complete rule output to remain equal while the
full raw trace changes as appropriate. All nine irrelevant raw fields of birth
and recycling, seven of Structural funding, and all type/state maps for each
unchanged variant are covered. These probes do not hide raw fields from
recording or validation. They are finite equality groups, not a sampled prior.

## Exact interface, semantics and gates

Requests use `mode=rule` or `mode=assembly`, `case_id`, `map` (kinds 1..3) and
`state_map` (states 0..2). Rule requests also have `rule_id` and all eleven raw
`fields`; assemblies have `initial_id`, its literal `initial_fields`, and eight
`rule_fields`. The protocol fixes success/error JSON exactly. Reject invalid
values, including booleans, before callback use; do not coerce, reduce modulo,
fall back to a draw, or skip validation of ignored fields. Dotted invalid
targets are mutations of this interface, not input keys.

Both adapters use literal callbacks, not hash sources. Each valid rule records
**17 reads**: three type fields, three state fields, then eleven slot fields.
Each assembly records **119**: six map fields, 88 slot fields and 25 initial
fields. The protocol fixes read order, address/initial routing, domains and raw
values, including ineffective fields. Cross-initial reuse is an exact identity
check, not an assertion that initial environments are the same.

Compare complete decoded outputs and traces, not selected keys or only two
implementations agreeing. The future validator needs its own declarative
operation/accounting oracle. Birth/funding/recycling effective substitutions
must follow [v4's contract](generator_v4_design.json); all other operation
operands/order, edge pattern classes, absence tests, initial resources, ledgers,
allocators, counters, limits and closed channels follow frozen v3 semantics.
CreateEdge/DeleteEdge act on Structural edges even when the edge-creation
template matches a Contact edge. Do not reinterpret a Contact pattern as a
Contact-producing operation.

The local-condition descriptors separate body/type presence, states, material,
construction resources, leaf condition, creation edge and slot cap. They are
independent necessary-condition flags, not applicability verdicts. State-only
and material-only controls are counterfactual descriptors, not effective v4
rules. Drift/resource/nonleaf/orphan cases are hypothetical local conditions;
the nine-body profile is explicitly not an eight-slot table. No rule binding,
world transition, scheduler or detector is evaluated. Native reachability,
sampling prevalence, chemistry, reproduction and adaptation remain untested.

All four protocol gates must pass. Future validation has 60 seconds and 256 MiB
combined retained stdout/stderr per adapter, plus a 300-second aggregate wall
deadline for preparation/guards/audit. Builds and ordinary tests precede that
deadline. Enforce process-group kill/reap and preserve partial outputs and
limit/not-started receipts. These are development limits, not a campaign budget
or performance claim; no instantaneous RSS bound is asserted.

## Freeze, admission and stopping boundary

The [registration freeze](p01n_registration_freeze.json) binds every tracked
source/protocol outside the mutable guidance/status/public index and public
receipt directory, plus the new registration/checker/tests. The preceding 402
public receipts are separately pinned. Preserve all original experiment seals,
consumed panels, failed gates and inconclusive classifications. Publication
context binds final guidance/findings added after the freeze.

After this registration is committed/pushed, implement only the new literal
adapters, fixed validator and tests at the registered paths. Rust's automatic
bin discovery avoids changing frozen Cargo files. No hash sampler implementation
or namespace-keyed evaluation is admitted, even in tests. Record every readiness
attempt's full source/input/binary identities and logs. An engineering defect
may be repaired against the same panel in a new output directory; never change
the inputs/criteria to obtain a pass and retain all failures.

This turn stops at static registration verification. It constructs and executes
no adapter, native law or world. Actual sampler implementation, sampling,
trajectories, new environment/detector criteria and E01 require separate future
decisions. Scientific status remains **untested**.
