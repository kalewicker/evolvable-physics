# P01k: keyed v3 sampler and static census registration

2026-10-20. This registers the next implementation and a future **static-only**
sampled panel. It makes no keyed draw now. The
[protocol](p01k_protocol.json) binds the [v3 design](generator_v3_design.md)
after [literal-field readiness](p01j_readiness_findings.md); it does not amend
P01g's consumed protocol, negative continuation gate or inconclusive labels.

## Question and fixed denominator

Do independent v3 samplers produce exactly the specified fields/environments,
and which necessary constructive routes occur in 32 consecutive, uninspected
law cells? Fix proposal IDs **5000..5031**, each with initial IDs **0..3**:
128 initial environments, zero requested epochs. No proposal has been evaluated
to choose this range. The panel is a bounded descriptive census, not a powered
prevalence estimate or comparison demonstrating v3 superiority.

Retain all 32 proposal cells and all 128 environments, including duplicates,
missing templates, negative routes, failures and unstarted cells. Four initial
states share a law and are nested observations. A new namespace changes all
keys; matching a v2 proposal number would not pair identical laws or worlds.

## Key contract and independent checks

Both samplers independently serialize the exact UTF-8 compact JSON array
`["p01-generator-v3", proposal, initial, field, index]`, hash with SHA-256,
take the first sixteen hex digits as big-endian u64, then reduce modulo range.
Do not reject modulo-biased results, repair kinds/states/resources, force body
presence or cache digest evaluations. The three map fields and all 88 rule
fields use initial=0. Twenty-five initial-world fields use the requested initial
ID. Evaluate all eleven fields for all eight rule slots, including unused
fields, matching the readiness adapter's complete field access policy.

There are **116 logical field records per environment** and **14,848 per
implementation**, but only **6,112 unique message addresses** across the panel:
32 × (91 shared law/map keys + four × 25 initial-world keys). The Rust/Python
and audit computations revisit these same addresses; none are independent law
samples. Retain exact preimage bytes, full digest, u64 prefix, modulus and raw
result for each logical draw. An independent auditor reconstructs every message
and digest from the fixed contract, rather than trusting either sampler's log.

Require exact full JSON equality, map/rule identity across initial IDs, field
scope/ranges and all operation/accounting/profile/limit invariants. Independent
construction checks must not merely compare the two samplers: rebuild outputs
from audited raw fields against the frozen contract. Use new sampler/runner/
report/audit paths; leave the frozen literal adapters, Cargo files, historical
samplers, detectors and protocols intact.

The [primitive vectors](p01k_primitive_vectors.json) exercise serialization and
literal u64-prefix reduction, including an endianness-sensitive case and large
integer boundaries. **Do not hash these namespace-bearing messages before the
execution admission.** The max-u64 proposal vector tests serialization only;
it adds no proposal to the panel. Before freezing execution, only serialization,
literal prefix arithmetic, injected-field construction, literal descriptor and
watchdog/bookkeeping tests are admitted. Sampler code may be written after this
registration is committed/pushed; no keyed call on any proposal is admitted yet,
including from tests, examples, audit helpers or preflight commands.

## Static census and its limits

Report all eight rule slots, ordered duplicate bodies and template/route
counts. Identify tables by the canonical ordered rule list after removing only
rule IDs, preserving body multiplicity and order. Report both 32 law cells and
distinct tables, not just favorable distinct tables.

For every same-table birth/funding pair, birth/recycle pair and birth/next-birth
pair, retain body IDs and separate these predicates:

- Ordered donor/child kinds agree. For incoming pairs, birth P→C must match
  pair slots [P,C] exactly; the next birth's donor must match C.
- Birth donor and pair donor states intersect: equal, or at least one wildcard.
  Birth leaves the donor state unchanged. This is schema intersection, not proof
  that an initial node can reach that state.
- The child's state at creation equals the relevant target/donor predicate,
  or that predicate is wildcard. Failure means immediate state misalignment;
  unary state writes might later change it. Do not infer permanent exclusion.
- Funding carries positive matter. This is separate from kind/state alignment.
  The newborn begins at (1 matter, 1 activation), below birth's (3,2) requirement;
  two unit-matter transfers would be needed before its own birth. Do not simulate
  those transfers or assert they occur.

Join motifs only on the same birth body within the same law. Retain type-only,
immediate-state-aligned and material-bearing joins separately; never pool bodies
across laws. Follow the total kind map through the present birth-donor kind set
to record missing donors or repeated kinds. A closed type graph is not a paid
lifecycle. Report state-write bodies and unresolved resource/topology barriers.

Each initial cell retains kind/state histograms and resource/edge inventories.
Do not enumerate pattern bindings, candidates or applicable operations. No
matcher, transition interpreter, worker or detector may run. Birth/recycling/
descendant/AP/maintenance/reproduction/heredity/adaptation outcomes are **null,
reason `not_executed`**, not zero. Original Contact nodes, orphan/nonleaf
restrictions and the conservative closed-resource bound of 64 births remain
part of the source contract, not observations from this census.

## Budget, failure policy and decision

The protocol fixes 5-second/128-MiB-sampled-RSS/1-MiB-output ceilings for each
generator cell stage, followed by separate 30-second/512-MiB/8-MiB static-report
and independent-audit stages. Aggregate ceilings are 300 seconds wall, 120
seconds process CPU and 1 GiB artifacts, with 16 MiB metadata reserve. Include
both samplers, parent checks, guards, snapshots, analyses, inventories and seals.
Compilation and mock tests precede the campaign clock. Sampled RSS is not a
hard instantaneous memory bound.

Before every stage, reserve its full wall allowance, twice that allowance in
CPU, and its output allowance plus metadata reserve. On failed identity,
mismatch, guard violation or unavailable reservation, stop, seal the prefix and
retain all 128 planned cells with explicit status/reason. Do not resume missing
cells, retry the sampled batch, extend budgets or replace a proposal/state.
Engineering defects found before sampling may be fixed against the unchanged
registration. A failed sampled attempt remains consumed even if the defect is
later understood; read-only diagnosis precedes any separately justified work.

The engineering gate requires complete independent verification and custody,
not a motif count. **There is no chemistry or trajectory continuation gate in
this static census.** Zeros must be published, never rerolled into positives.
Positive paths establish schema availability only. Any future dynamical
question requires separate registration and justification, preserving the full
census denominator and forbidding a favorable-law subset or longer runs chosen
from these outcomes. A static pass does not admit that future experiment.

## Implementation and execution boundary

The [registration freeze](p01k_registration_freeze.json) binds inputs, vectors,
this specification, checker/tests and historical source contracts. After it is
committed/pushed, implement the registered new sampler/runner/report/audit paths
and test with literal/mock sources only. Then freeze the full source/dependency/
tool/binary/input closure and publish a separate admission binding an exact new
output directory. Commit/push that freeze/admission **before the first keyed
hash evaluation**. The future runner writes all 128 planned cells before any
sampler or independent hash-audit call.

This turn registers and statically checks the plan only. Actual sampler and
census implementations, keyed draws and all world execution remain undone.
E01 is unauthorized; scientific status remains **untested**.
