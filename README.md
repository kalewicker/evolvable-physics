# Evolvable Physics

First implementation of the [revised research plan](docs/experiment_plan_v2.md). This standalone Rust package implements a bounded closed-resource transition kernel and reproducible validation artifacts. P00 is admitted for the bounded engineering profiles and disclosed fixture panels. The first bounded P01 development pilot is complete at its registered CPU reserve stop. Scientific capability claims remain untested.

## Run

From this directory:

```sh
cargo fetch --locked
cargo test --locked --offline
python3 scripts/validate.py artifacts/p00g-new-run
```

The validation command requires a **new** output directory. It preserves failures, copies source files, records source/binary hashes, runs tests and Clippy, compares two Rust matchers across 112 cases / 1,344 epochs, independently replays all transitions in Python, tests corrupted evidence, and verifies fresh-process checkpoint continuation. It also checks 160 controlled intervention arms across two fixture families with an independent external-operation interpreter. Dependencies are pinned in Cargo.lock; omit `--offline` in an environment without cached crates when fetching dependencies initially.

For direct execution:

```sh
cargo run --locked --offline -- fixtures artifacts/manual-fixtures
cargo run --locked --offline -- resume artifacts/manual-fixtures/checkpoint.json 7 artifacts/manual-resumed.json
python3 scripts/audit.py artifacts/manual-fixtures/suite.json
```

## Implemented

- Typed ordered hypergraphs; connected bounded patterns; explicit negative edge predicates.
- Integer resources and exact matter/activation accounting.
- State, node, structural-edge, transfer, and dissipation operations.
- Deterministic priorities, conservative read/write conflict selection, atomic epochs.
- Reference and type-indexed matching; full event/dependency traces.
- Validated, non-overwriting checkpoints; source-bound state/resource interventions with explicit external-event receipts.
- Baseline, sham, target, unrelated-target, and immediate-rescue control fixtures.
- Independent standard-library Python transition replay and tamper rejection checks.
- Offline structural/coactivity proposals, temporal tracking, active-persistence criteria, and physically grounded maintenance controls; see [detector protocol](docs/detectors.md).
- A versioned environment wrapper with scheduled activation supply/extraction and directed contact-local transport; independent replay across 64 fixed control runs.

See [executable semantics](docs/semantics.md) and [fixture matrix](docs/fixtures.md) for limits. This has no life score, reproduction detector, scientific search, or graphical interface.

## Branch a checkpoint

```sh
cargo run --locked --offline -- intervention-fixtures artifacts/branch-fixtures
cargo run --locked --offline -- branch artifacts/branch-fixtures/state_arrest-source.json artifacts/branch-fixtures/state_arrest-request.json artifacts/target-branch
```

The branch bundle preserves the source, request, receipt, and resulting checkpoint. Keep it with subsequent continuation artifacts.

## Current gate and next work

[P00g findings](docs/p00g_findings.md) close the logging-equivalence and complete-environment detector blockers. The [current admission receipt](docs/evidence/p00g-001/p00g_admission_audit.json) admits P00 for bounded engineering profiles and the disclosed fixtures. Historical P00f assessments remain preserved.

[P01a findings](docs/p01a_findings.md) report the registered development preflight: 64/64 generated runs completed and independently replayed across 4,096 epochs. A separate worker streams bounded traces; event/output ceilings preserve whole-epoch state, and the supervisor enforces wall and sampled RSS watchdogs. RSS sampling is not a hard instantaneous memory bound. The initial sandbox failure is retained.

The [first P01 development pilot](docs/p01_findings.md) stopped at its CPU launch reserve: 469 complete horizons, one censored prefix and 42 unstarted slots. Its 469 complete-run AP labels were 436 `not_supported`, 33 `inconclusive` and zero `supported`. All 512 registered cells remain in the report, and the sealed audit passed without a resource overshoot.

That registration is consumed and [closed](docs/p01_closure.json). [P01d diagnosis](docs/p01d_findings.md) checked every retained epoch: generator v1 leaves newborns isolated/unfunded and makes node deletion unreachable; all 33 disagreements remain inconclusive. Independent Python verification used 80.073% of recorded leaf CPU. The separate verifier passed [P01e's fixed offline panel](docs/p01e_findings.md) with 50.174% lower paired child CPU; the frozen receipt auditor's float-sum failure and post-hoc arithmetic correction are preserved. [P01f execution](docs/p01f_execution_findings.md) verified all 48 registered authored reachability witnesses with exact agreement across both Rust matchers and independent Python replay. [P01g execution](docs/p01g_execution_findings.md) completed all 64 sampled trajectories and passed the engineering gate, but failed its recycling continuation criterion. [P01h diagnosis](docs/p01h_findings.md) found no compatible birth/funding or birth/recycling kind pairs in those tables. Next review type-coherent rule generation as a design-only task. No law sampling or repeated witness batch is admitted. Scientific status remains untested and E01 remains unauthorized.

## Environment fixtures and continuation

```sh
cargo run --locked --offline -- environment-fixtures artifacts/environment-fixtures
cargo run --locked --offline -- environment-resume artifacts/environment-fixtures/driven-checkpoint.json 5 artifacts/driven-resumed.json
```

Environment checkpoints contain both the schedule/ledgers and embedded native world; use `environment-resume`, not the old native-only command.

## Environment-aware branch bundles

```sh
cargo run --locked --offline -- environment-branch-fixtures artifacts/integrated-fixtures
cargo run --locked --offline -- environment-branch artifacts/integrated-fixtures/state_arrest-source.json artifacts/integrated-fixtures/state_arrest-request.json artifacts/integrated-target
cargo run --locked --offline -- environment-branch-resume artifacts/integrated-target 6 artifacts/integrated-target-resumed.json
```

Bundle resume validates completion, full source identity, and receipts before continuing the environment schedule.

## Detector fixtures

```sh
cargo run --locked --offline -- detector-fixtures artifacts/detector-fixtures
python3 scripts/audit_detectors.py artifacts/detector-fixtures/suite.json
```

Analysis outputs retain both estimators, identity ambiguity, raw activity/turnover counts, and controlled physical occupancy endpoints.

## Frozen detector transfer panel

```sh
cargo run --locked --offline -- generalization-panel artifacts/generalization-new
python3 scripts/audit_generalization.py artifacts/generalization-new/suite.json
```

The detector thresholds stay frozen. The full validation command also emits a P00 admission audit, preserving exclusions, disagreements, and any failed panel prediction.

## Public repository and workflow

Published at [kalewicker/evolvable-physics](https://github.com/kalewicker/evolvable-physics). The crate and executable retain the name `causal-alife`.

The public snapshot includes source, locked dependencies, protocols, reports, the revised experiment plan, and [compact validation receipts](docs/evidence/README.md). Raw `artifacts/`, `target/`, caches, and machine-local settings stay outside Git. Run the validation command above to generate full evidence from source.

Implementation resumed at the user’s request after publication. P01 is sealed and closed; P01d diagnosis and P01e offline verifier preflight are complete. P01f reachability execution is complete and consumed. All 48 authored cases passed. P01g completed the bounded sampling-feasibility preflight: ten tables produced visible birth, none produced a newborn recycling loop. Its registration is consumed. P01h diagnosed incompatible donor/child kinds; next is a design-only review of type-coherent constructive rules.

At the end of future project turns, commit and push any changes to this repository after the appropriate checks. See [AGENTS.md](AGENTS.md).

## Logging modes and environment analysis

Full output remains the default. `resume-quiet` and `environment-resume-quiet` retain semantic state and checkpoint identity while suppressing exported step records. Quiet intervals need verified replay to supply event histories for analysis.

```sh
cargo run --locked --offline -- integration-fixtures artifacts/integration-new
python3 scripts/audit_integration.py artifacts/integration-new/suite.json
```

The environment adapter verifies full phases and credits native physical changes only. [P00g semantics](docs/p00g_semantics.md) describe the fixed controls and limits.

## P01a development preflight

```sh
python3 scripts/pilot.py artifacts/p01a-new-run
python3 scripts/audit_pilot.py artifacts/p01a-new-run artifacts/p01a-new-audit.json
```

The registered runner requires macOS or Linux and permission to query child RSS with `ps`; a sandbox can block that query. Output directories and audit destinations must be new. It runs checks, builds the release worker, tests forced guards, and evaluates the fixed panel without replacements. [Registration](docs/p01a_registration.md), [limits](docs/p01a_protocol.json), and [source freeze](docs/p01a_freeze.json) distinguish this engineering preflight from the full P01 pilot. The extra executable is `pilot-worker`; `cargo run` still defaults to `causal-alife`.

## P01b detector reporting and registration

```sh
cargo build --release --locked --offline --bin pilot-report
./target/release/pilot-report artifacts/p01a-002/runs/2000-0-request.json artifacts/p01a-002/runs/2000-0
python3 scripts/validate_p01b.py artifacts/p01b-new-run artifacts/p01a-002 artifacts/p00g-001
```

Use your own complete P01a/P00 validation bundles in the last two arguments when reproducing. Validation requires a new output directory; it reads existing trajectories and runs only disclosed control fixtures. [Full pilot budgets](docs/p01_protocol.json) are registered; this command does not launch the full pilot. The reporter retains all detector details and marks capped prefixes separately from full-horizon endpoints. [P01b findings](docs/p01b_findings.md) preserve the observed negative/inconclusive results and remaining execution gate.

## Sealed P01 campaign

```sh
cargo build --release --locked --offline --bin pilot-worker --bin pilot-report
python3 scripts/campaign.py artifacts/p01-new-run
python3 scripts/audit_campaign.py artifacts/p01-new-run artifacts/p01-new-audit.json
```

The campaign command reproduces the historical runner entry point and requires a new output path, current frozen sources, and the published P01c readiness receipt. **The original P01 registration is consumed: do not launch it again, resume its unstarted slots, or extend its capped run without a newly registered protocol.** It queries child RSS with `ps`, which can require permission outside a desktop sandbox. Sources/binaries, bounded stage outputs, all slot outcomes and the final seal are retained. A full pilot can stop at its budget without completing all horizons; no slot is replaced. An unsealed interrupted bundle is never resumed, and its read-only audit accepts no endpoints.

To rerun only the engineering controls, use `python3 scripts/validate_p01c.py artifacts/p01c-new-run`. See [registration](docs/p01c_registration.md), [findings](docs/p01c_findings.md) and [full pilot ceilings](docs/p01_protocol.json). Neither command authorizes E01.

## P01 findings and read-only report

```sh
python3 scripts/summarize_p01.py artifacts/p01-001 artifacts/p01-new-report
```

Use an existing complete sealed bundle and a new report directory. This verifies inventory/audit bindings and computes descriptive tables; it never evolves a world or resumes a campaign. The [first pilot findings](docs/p01_findings.md) preserve 436 unsupported and 33 inconclusive complete-run labels, one censored prefix and 42 unstarted cells. No AP support was established, and E01 remains unauthorized.

## P01d read-only diagnosis

```sh
python3 scripts/diagnose_p01.py artifacts/p01-001 artifacts/p01d-new-analysis
```

Use an existing sealed campaign and a new analysis directory. This verifies the original inventory, scans existing traces and saved detector fields, and attributes cost from retained receipts; it does not evolve worlds or change labels. [Findings](docs/p01d_findings.md) separate the finite scan from the [source-level reachability argument](docs/generator_v1_reachability.md). Public receipts do not contain raw trajectories, so this command requires the complete local bundle. The [P01e findings](docs/p01e_findings.md) report the subsequent offline verifier preflight.

## P01e offline verifier preflight

The [P01e protocol](docs/p01e_protocol.json) and [implementation registration](docs/p01e_registration.md) specify a separate Python verifier that emits physical activity during checked replay. It preserves the frozen reference pipeline. Its fixed source/input identities are in [the freeze](docs/p01e_freeze.json). This is an engineering comparison on existing evidence, with no native world execution.

```sh
python3 scripts/validate_p01e.py artifacts/p01e-new-run
python3 scripts/audit_p01e_v2.py artifacts/p01e-new-run artifacts/p01e-new-audit.json
```

These are the historical entry points, not authorization to repeat the single registered timing attempt. Execution requires the full byte-matching P00g/P01 bundles, a new output directory and permission for `ps` memory sampling. Receipts alone do not contain those inputs. The audit reads a completed bundle and requires a new destination outside it. RSS is sampled; no hard instantaneous memory bound is established.

[P01e findings](docs/p01e_findings.md) preserve the single sealed attempt, 112 native and 96 environment fixture comparisons, eight exact P01 pairs, and all 11 corruption rejections. The candidate used 57.720598 versus 115.845487 seconds of paired child CPU on this host/panel. The frozen v1 receipt auditor failed on float-sum equality; the separate post-hoc v2 auditor verifies Decimal gate arithmetic without changing the original candidate, harness, freeze or measurements. The [admission record](docs/p01e_admission.json) records that qualification. The original campaign pipeline and scientific status remain unchanged.

## P01f reachability registration

[Generator-v2 design](docs/generator_v2_design.md) specifies attached funded birth, Structural resource transfer and recoverable leaf deletion using existing operations. The [protocol](docs/p01f_protocol.json) and [literal witness registry](docs/p01f_witnesses.json) fix 12 authored families across four seeds, with explicit positive/negative predictions and future execution ceilings. The fixed witness runner is implemented and its single registered batch passed; the law sampler subsequently ran in [P01g](docs/p01g_execution_findings.md), whose engineering gate passed and mechanism gate failed.

```sh
python3 scripts/check_p01f_registration.py artifacts/p01f-registration-new
```

This static review requires a new output directory and byte-matching [registration freeze](docs/p01f_registration_freeze.json). It checks schemas, case census and declared inventory arithmetic; it does not match or execute a rule or establish a predicted trajectory. [Registration findings](docs/p01f_findings.md) preserve that distinction. The subsequent [execution findings](docs/p01f_execution_findings.md) report all 48 cases passing under the separately frozen implementation. The batch is consumed; do not repeat it. No law search or E01 is admitted.

For a retained complete local bundle, the receipt-only audit performs no transitions:

```sh
python3 scripts/audit_p01f_receipts.py artifacts/p01f-001
```

The public receipts omit raw traces and dependency snapshots, so this audit requires the full local bundle. See [implementation](docs/p01f_implementation.md), [execution freeze](docs/p01f_execution_freeze.json) and [reachability admission](docs/p01f_reachability_admission.json).

## P01g sampling-feasibility registration

The [fixed protocol](docs/p01g_protocol.json) and [rationale](docs/p01g_registration.md)
register 16 law IDs × four initial states × 128 epochs. The engineering gate
requires all 64 complete horizons and independent full checks. The separate
mechanism gate requires two distinct tables with detector-visible funded birth,
one with same-child recycling in the same trajectory. Duplicate tables and
nested initial states do not inflate that gate. Negative/inconclusive and
censored/unstarted results retain their denominators.

```sh
python3 scripts/check_p01g_registration.py artifacts/p01g-registration-new
```

This performs static registration checks only, into a new output directory.
The [registration findings](docs/p01g_findings.md) preserve the original static
review. The subsequent [execution findings](docs/p01g_execution_findings.md) report
64/64 complete trajectories with independent verification, ten distinct tables
with visible birth and zero with newborn recycling. The engineering gate passed;
the mechanism continuation gate failed. The registration is consumed and
[closed](docs/p01g_closure.json); no repeated or expanded sampling or E01 is admitted.
[P01h diagnosis](docs/p01h_findings.md) now explains the failure through incompatible ordered kind pairs; the [source argument](docs/p01h_source_argument.md) is scoped to these exact tables.

The receipt audit reads a complete retained local bundle without sampler calls
or transitions:

```sh
python3 scripts/audit_p01g_receipts.py artifacts/p01g-001
```

Public compact receipts omit raw trajectories, dependency snapshots and binaries.
The complete local bundle is required for this audit.

## P01h read-only mechanism diagnosis

The [analysis plan](docs/p01h_analysis_plan.md) and [findings](docs/p01h_findings.md)
cover all 16 laws / 64 trajectories. None of the nine birth/Structural-funding
pairs or 15 birth/recycling pairs has compatible ordered kinds. Every observed
newborn-mechanism exposure was inapplicable; no scheduler loss explains those
zeros. The [conditional source argument](docs/p01h_source_argument.md) explains
why longer horizons or different seeds cannot enable those typed routes in the
same tables. This does not prove a limitation of all possible v2 laws or the kernel.

```sh
python3 scripts/diagnose_p01g.py artifacts/p01g-001 artifacts/p01h-new-analysis
python3 scripts/audit_p01h.py artifacts/p01g-001 artifacts/p01h-new-analysis
```

These commands require the complete retained local bundle and a new analysis
directory; they read records without law construction or transition application.
Public compact receipts omit raw trajectories. Next is a design-only type-
coherence review that accounts for the changed prior and child-as-donor path.
No new generator, law draw, dynamics or E01 is admitted.

## P01i type-coherent design review

The [proposed v3 design](docs/generator_v3_design.md) shares a per-law map from
donor kind to child kind across birth, Structural funding and leaf recycling.
It explicitly checks whether children can match another birth donor; matching
incoming funding/recycling kinds alone is insufficient. Forms, donor kinds,
states and routes remain independently keyed. The changed correlation is
authored sampling bias, not an evolved mechanism.

[Static findings](docs/p01i_findings.md) cover all 27 maps and eight donor
subsets, with independent graph checks and explicit failure examples. No laws
were sampled or worlds advanced. Next is a separate registration for literal-
field adapter readiness checks; generator implementation and a new experiment
are not yet admitted. The P01g negative gate and scientific status are unchanged.

## P01j literal-field readiness registration

The [fixed readiness protocol](docs/p01j_protocol.json) and
[registration notes](docs/p01j_registration.md) now register 11,664 individual
rule-field cases and 972 environment assemblies, plus missing-body/state/
material barriers, invalid inputs and ignored-field probes. The
[static findings](docs/p01j_findings.md) verify descriptor coverage and frozen
identities; the adapters have not run.

Next implement the separate Rust/Python literal-field adapters and fixed
validator under this registration. No hash sampler, candidate enumeration,
world transitions, new sampling panel or E01 is admitted. The input registry
and criteria remain frozen even if an implementation needs repair.

## P01j literal-field implementation

The separate Rust/Python adapters and bounded validator now pass the fixed
panel: 11,664 rules, 972 environment assemblies and all negative/invalid/
ignored-field checks, with complete output equality and independent operation/
accounting invariants. [Readiness findings](docs/p01j_readiness_findings.md)
include the retained initial compilation failure, tests and read-only receipt
audit. Neither adapter contains a hash sampler or executes world transitions.

```sh
cargo build --release --locked --offline --bin generator-v3-fields
python3 scripts/validate_p01j.py artifacts/p01j-readiness-new
python3 scripts/audit_p01j_readiness.py artifacts/p01j-readiness-001 artifacts/p01j-readiness-new-audit.json
```

Validation requires a new directory and the intact frozen local inputs; the
read-only audit requires the complete retained bundle. Engineering repairs may
repeat the same fixed readiness panel while preserving every attempt. Next is
a separate registration for the actual keyed sampler and an unfiltered static
census. No law sampling, world execution or E01 is currently admitted.

## P01k keyed-sampler/static-census registration

The [new registration](docs/p01k_registration.md) fixes 32 proposal IDs × four
initial states for a future static census, with zero world epochs. The
[static findings](docs/p01k_findings.md) verify the 128-cell plan, field-address
counts and unhashed primitive vectors. All laws and negative routes remain in
the denominator; there is no motif-count success gate or favorable-law filter.

Next implement the independent samplers, runner, static report and auditor using
mock/literal inputs only. Actual keyed calls require a separate complete
execution freeze and admission committed/pushed first. No sampled law, world
trajectory or E01 has been admitted by this registration.

## P01k implementation and mock readiness

The keyed samplers, census runner, static report and independent auditor are
implemented. [Implementation findings](docs/p01k_implementation_findings.md)
record 12,671 matching literal responses plus 972 matching recorded mock
assemblies, with independent field/output checks. All tests, Clippy and release
build passed. The mock digests are literal formatting fixtures, not SHA results.

```sh
python3 scripts/validate_p01k_implementation.py artifacts/p01k-implementation-new
```

This development preflight requires a new directory and evaluates no keyed
sampler message. The actual census remains unrun. Next freeze and commit/push
the full execution closure/admission before any keyed call, then execute only
the registered single static attempt. No world trajectories or E01 are admitted.

## P01k sampled static census

The [single sampled census](docs/p01k_execution_findings.md) is complete and
consumed. All 32 laws / 128 initial environments and 258 stages passed independent
sampler, census, custody and cost checks. Kind-compatible funding, recycling and
child-donor routes occur, while complete joined motifs have zero immediate state
alignments. These local predicates are not dynamical reachability or life claims.

No worlds advanced; behavioral endpoints remain null/not_executed. The full
panel and negative history are retained. Next is a read-only review of remaining
state/resource constraints across all 32 tables, before any separately registered
trajectory question. Do not rerun or extend this census or select favorable laws.

## P01l state and resource review

The [read-only review](docs/p01l_findings.md) is complete across all 32 retained
tables and 128 initial records. Later unary state changes permit some routes
that fail the immediate-state test, but no material-funded newborn-to-next-birth
path survives all necessary conditions. The [conditional source argument](docs/p01l_source_argument.md)
excludes that mechanism for these exact tables under their frozen topology;
it makes no sampler-wide or life-impossibility claim. All 163 body combinations
passed independent state/premise checks, and eight tests passed. No worlds ran.

```sh
python3 -m unittest discover -s scripts -p test_p01l.py -v
python3 scripts/review_p01l.py artifacts/p01k-001 artifacts/p01l-new
python3 scripts/audit_p01l.py artifacts/p01k-001 artifacts/p01l-new artifacts/p01l-new-audit.json
```

These commands read saved evidence and require a new analysis output path;
they do not repeat the consumed census. Next is design-only review of a minimal
state/resource-coherent lifecycle prior and its authored bias. Implementation,
fresh sampling, favorable-law evolution and E01 remain unadmitted.

## P01m proposed v4 design

The [design review](docs/p01m_findings.md) recommends shared per-kind constructive
states plus matter-bearing Structural funding. It keeps independently sampled
body presence and eight slots, so missing roles remain possible. These are
explicit authored correlations; no generator or sampled law was implemented.

Finite checks passed across 59,049 kind/state cases and all 13,824 abstract
body-presence profiles. A fully covered three-kind birth/funding/recycling
cycle needs nine bodies and does not fit eight slots. These counts concern
labels and role coverage, not chemistry success or sampler frequencies.

```sh
python3 -m unittest discover -s scripts -p test_generator_v4_design.py -v
python3 scripts/review_generator_v4_design.py artifacts/p01m-design-new
python3 scripts/audit_generator_v4_design.py artifacts/p01m-design-new artifacts/p01m-design-new-audit.json
```

Next separately register literal-field readiness for independent Rust/Python
adapters before implementation. New sampling, world execution and E01 remain
unadmitted. Historical panels, criteria and negative/inconclusive outcomes stay
intact.

## P01n v4 literal-readiness registration

The [fixed registration](docs/p01n_registration.md) defines 17,727 future adapter
requests plus 13 validator-only condition cases. It covers constructive map
coherence, unchanged forms, all four initial records per map pair, ignored raw
fields and invalid boundaries. Complete output equality and 17/119-record traces
are required; no hash draws or world execution are part of this panel.

[Static findings](docs/p01n_findings.md) record ten passing registration tests
both normally and with Python optimization. No adapter was implemented or run.
After this registration is committed/pushed, next implement only its separate
Rust/Python literal adapters and fixed validator, preserving every attempt and
all frozen sources. Actual sampler implementation or new experiments require
separate registration and admission.

## P01n v4 literal readiness complete

The separate v4 literal adapters passed all **17,727 fixed requests**, exact
Rust/Python JSON and ordered traces, and an independent operation/accounting
oracle. All 597,448 field reads per adapter, 729 four-initial groups, 37 ignored
field groups, 79 invalid rejections and 13 validator-only conditions passed.
The read-only custody audit and build/regression checks passed; the initial
test-filter failure is retained. See [findings](docs/p01n_readiness_findings.md)
and [admission](docs/p01n_readiness_admission.json).

This is authored literal construction only; scientific status remains untested.
Next separately register v4 keyed implementation and an unfiltered static
census before implementing or evaluating the actual sampler. No world runs or
E01 are admitted. The original registration, frozen sources and prior results
remain unchanged.

## P01o v4 static-census registration

The [new registration](docs/p01o_registration.md) fixes 32 fresh proposals
(6000..6031) × four initial states, 128 environments and **zero epochs**. It
requires independent field/output checks and an unfiltered descriptive census;
no route-count threshold admits chemistry or trajectories. The new namespace
makes this an unpaired panel, not a test of v4 superiority.

[Static review](docs/p01o_findings.md) and thirteen tests passed normally and
with Python optimization; 235 frozen files and 438 prior receipts matched.
No keyed sampler was implemented or run. Next implement the new paths using
literal/mock tests, then commit/push a separate execution freeze before any
keyed evaluation. Scientific status remains untested.

## P01o sampler implementation readiness complete

Separate v4 samplers, census runner, static report and auditors now pass
literal/mock readiness: all 17,727 frozen responses and 2,916 recorded mock
assemblies matched, with independent operation/static checks. Ten Python and
four Rust tests, Clippy, release build and read-only integrity checks passed.
Both development attempts are retained. See
[findings](docs/p01o_implementation_findings.md) and
[readiness](docs/p01o_implementation_readiness.json).

No v4 keyed draw or sampled census has run. Next prepare and commit/push the
full execution closure and exact-output admission before the single registered
static attempt. Scientific status remains untested; no world runs or E01 are
admitted.

## P01o execution freeze prepared

The [freeze and admission](docs/p01o_execution_freeze_notes.md) bind one static
census to `artifacts/p01o-001`. Pre-execution checks verified 740 source/input/
receipt files, 3,088 dependencies, four tools and the unchanged tested binary.
Six closure tests passed normally and optimized; the initial temporary-path
fixture failure is retained. No keyed evaluation or sampled attempt occurred.

After this gate is committed/pushed, next run only the registered 32-law/128-cell
zero-epoch census, with the original budgets and stop/no-retry policy. All
behavioral endpoints remain unexecuted; scientific status remains untested.

## P01o sampled static census complete

All 32 laws / 128 environments and 258 stages passed independent engineering
and custody/cost checks. The census retains 32 distinct tables, including every
negative. One joined motif has aligned type/state/material predicates; those
local correlations do not establish a resource-feasible lifecycle. No world
epochs ran. See [findings](docs/p01o_execution_findings.md),
[complete summary](docs/evidence/p01o-001/summary.json) and
[closure](docs/p01o_closure.json).

The registration is consumed. Next preregister a read-only resource/state/
topology review across all retained tables before diagnosis. No sampled retry,
repair, favorable-law trajectories or E01 are admitted; scientific status
remains untested.

## P01p read-only diagnosis plan registered

The [post-hoc review plan](docs/p01p_analysis_plan.md) fixes resource/state/
topology questions across every P01o table and initial record. It separates
edge-only cleanup with a surviving orphan from leaf recycling, and tests
conditional balances without executing worlds.

Eight registration tests passed normally and optimized; 264 analysis inputs,
the original inventory/seal and prior receipts matched. See
[registration findings](docs/p01p_registration_findings.md). No new diagnosis ran.
After commit/push, next implement the new read-only helpers and execute this
fixed review. Scientific status remains untested; no sampled or trajectory
reruns are admitted.

## P01p read-only review complete

The registered review and independent audit passed for all 32 laws, 128 initial
records and 170 body combinations. One cleanup-by-recycling branch passes the
conditional state/resource/topology abstraction, including its four founder
state checks. Its ledger restores matter but spends four activation; no
trajectory or reproduction was observed. See [findings](docs/p01p_findings.md)
and [closure](docs/p01p_closure.json).

Thirteen tests passed normally and optimized, including 924 independent state
comparisons. All inputs and original seals remain intact. Next separately
register an unfiltered bounded dynamical mechanism assay across all saved
initial environments. No favorable-law run, new sampling or E01 is admitted.


P01q now registers the first bounded dynamical assay over all 32 retained v4
laws and 128 saved environments, with a fixed 128-epoch horizon and unchanged
P01g continuation criteria. No trajectories have run. Eight registration tests
and complete source/input custody checks passed. Next is implementation and
invented-control readiness, then a separate execution freeze/admission.
See [registration findings](docs/p01q_findings.md) and
[protocol rationale](docs/p01q_registration.md).

P01q implementation readiness is complete: 17 invented/mock tests cover the
registered controls, including all 128 cells and 384 mocked stages. Separate
event auditors preserve cleanup/orphan distinctions and actual phase balances.
No world has run; next is the separately committed execution closure/admission.
See [implementation findings](docs/p01q_implementation_findings.md).
