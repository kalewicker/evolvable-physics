# P01o: v4 keyed sampler and static census registration

2026-10-22. This registers implementation and a future static census after the
[P01n literal-readiness pass](p01n_readiness_findings.md). No keyed sampler is
implemented or executed by this registration. The [protocol](p01o_protocol.json)
is a new contract; all previous panels, criteria, freezes and outcomes remain
unchanged.

## Fixed question and denominator

Do independent implementations produce the specified v4 fields/environments,
and which necessary constructive bodies and type/state/material routes occur?
Fix **32 consecutive, uninspected proposals 6000..6031**, each with initials
**0..3**: 128 environments and **zero epochs**. The range is chosen before any
v4 keyed draw. Retain every proposal, initial, duplicate table and negative,
including failed, censored and unstarted cells. Four initials share a law;
they are not four independent law samples.

This bounded descriptive panel does not estimate prevalence or demonstrate v4
superiority. Namespace `p01-generator-v4` changes all keys, including initial
worlds: there is no paired comparison with P01k and no isolated ablation of
state versus matter changes. The shared role states and positive Structural
matter are authored correlations, not discoveries made by the census.

## Exact source and output contract

Independently serialize UTF-8 compact JSON
`[namespace,proposal,initial,field,index]`, SHA-256 it, interpret the first
sixteen hexadecimal digits as big-endian u64, and reduce modulo the field range.
Keep modulo bias. No rejection, repair, insertion, conditioning, fallback,
reroll or digest-evaluation cache is permitted.

Each complete trace has **119 ordered records**:

1. Three `child_kind_by_donor` reads at initial=0, modulus 3, offset +1.
2. Three `role_state_by_kind` reads at initial=0, modulus 3, offset zero.
3. Eight slots times all eleven raw fields in registered order, at initial=0.
4. Eight nodes, interleaved `node_kind` then `node_state`, requested initial.
5. Eight Structural-edge flags, requested initial.
6. Scheduler index zero, requested initial, modulus `2^64-1`.

That is **15,232 logical records per implementation**, and **6,208 unique
message addresses**: 32 × (94 shared law/map addresses + four × 25 initial
addresses). Repeated evaluations by generators/auditor do not enlarge the law
sample. Retain namespace, proposal, initial, field, index, modulus, exact UTF-8
preimage, full digest, prefix integer and raw reduced value for every record.
All raw values are drawn and logged even when unused or overridden.

Constructive birth uses donor P in state s(P), child f(P) in state s(f(P)).
Structural funding and recycling use ordered kinds [P,f(P)] with exact states
[s(P),s(f(P))]; Structural funding transfers matter=1. Preserve its raw-derived
activation amount, all other forms including Contact transfers, operation
order/costs, eight slots, initial resources/topology, caps and detectors.
No rules are inserted to make a table work.

Require exact complete Rust/Python outputs, both maps and law identity across
four initials, and independent reconstruction from audited raw fields against
the frozen v4 literal contract. The independent auditor recomputes each message,
SHA and reduction during the one admitted future attempt. A later custody audit
uses saved bytes and file hashes only, without new keyed calls.

The [primitive vectors](p01o_primitive_vectors.json) fix six unhashed serialization
strings and six literal prefix/reduction cases, including state-map scope,
endianness and u64 limits. The max-u64 serialization vector is not an admitted
proposal. Before execution admission, do not hash any v4 namespace message,
including tests, examples, preflight or audit helpers.

## Descriptive report and interpretation

Keep ordered body IDs, duplicates, all template/route counts, and canonical table
identity with only rule IDs removed. Report all 32 cells and distinct-table count
separately. Within each table retain every birth/funding, birth/recycling and
birth/next-birth body combination, with separate ordered-kind, donor-state,
newborn-state, transfer-matter and activation predicates.

Join only on the same birth in the same table. Intersect **all donor-state
predicates simultaneously**; two pairwise intersections with a wildcard birth
would not imply a common donor state. Type-compatible v4 joins must also have
matching exact constructive states and positive Structural matter by design.
Check that as an engineering invariant, not a chemistry threshold. Missing
bodies and incompatible type paths remain possible and must be reported.

Follow kind-map paths through present birth donors until a missing donor or
repeated kind. Report unary state writers and initial kind/state/resource/edge
inventories without enumerating bindings or applicable candidates. Birth leaves
newborn resources (1,1), below its own birth requirement (3,2); positive funding
schema does not prove affordability, leaf topology, state persistence, scheduler
access, visibility or repeated events. The nine-body requirement for complete
three-kind B/F/R role coverage is a specific profile limit, not general kernel
impossibility. No matcher, transition interpreter, worker or detector may run.

Behavioral births/recycling/descendants/AP/maintenance/reproduction/heredity/
adaptation are **null, reason `not_executed`**, not static counts converted to
observed zeros. No route-count threshold admits chemistry or trajectories.

## Limits and failure policy

Each Rust/Python cell stage has 5 seconds, 128 MiB sampled RSS and 1 MiB combined
stdout/stderr. Static report and independent audit each have 30 seconds,
512 MiB sampled RSS and 8 MiB combined output. Aggregate limits are 300 seconds
wall, 120 seconds process CPU and 1 GiB artifacts, with 16 MiB metadata reserve
and 0.01-second polling. Include parent checks, both samplers, analysis/audit,
guards, snapshots, partial streams, inventories, seals and failure receipts.
Compilation and mock tests precede the campaign clock. Sampled RSS plus reaped
peak checks do not establish a hard instantaneous bound.

Before launch reserve full stage wall allowance, twice it in CPU, and stage
output plus metadata reserve. Stop at first unavailable reservation, mismatch,
identity failure or capped/failed stage; preserve and seal the prefix and all
128 planned cells. Do not resume, repeat, replace cells or extend budgets after
the sampled attempt starts. A process/RSS capability check may precede attempt
creation without making keyed calls. Engineering defects before sampling can
be repaired against this unchanged contract; a failed sampled attempt is still
consumed and requires read-only diagnosis.

## Next implementation boundary

Commit/push this registration and its freeze before implementing only the new
paths named by the protocol. Keep old adapters, Cargo files, samplers, protocols
and receipts byte-identical. New tests may use unhashed serialization, literal
prefix arithmetic, injected fields, synthetic reports and guard bookkeeping.
No keyed evaluation on any proposal is yet admitted.

After implementation/mock readiness, freeze complete sources, dependencies,
tools, binaries and inputs; separately commit/push an execution admission that
binds one exact fresh output directory. Before any generator or independent
keyed-audit call, create the complete 128-cell planned manifest. The future
static pass admits only census correctness. Any trajectory proposal needs a
separate justification/registration preserving the full denominator and barring
favorable-law selection. E01 is unauthorized; scientific status is **untested**.
