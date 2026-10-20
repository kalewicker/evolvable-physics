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

That registration is consumed and [closed](docs/p01_closure.json). [P01d diagnosis](docs/p01d_findings.md) checked every retained epoch: generator v1 leaves newborns isolated/unfunded and makes node deletion unreachable; all 33 disagreements remain inconclusive. Independent Python verification used 80.073% of recorded leaf CPU. The separate verifier passed [P01e's fixed offline panel](docs/p01e_findings.md) with 50.174% lower paired child CPU; the frozen receipt auditor's float-sum failure and post-hoc arithmetic correction are preserved. [P01f execution](docs/p01f_execution_findings.md) verified all 48 registered authored reachability witnesses with exact agreement across both Rust matchers and independent Python replay. The next task is registering a small generator-v2 sampling-feasibility preflight. No law sampling or repeated witness batch is admitted. Scientific status remains untested and E01 remains unauthorized.

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

Implementation resumed at the user’s request after publication. P01 is sealed and closed; P01d diagnosis and P01e offline verifier preflight are complete. P01f reachability execution is complete and consumed. All 48 authored cases passed; the v2 sampler remains unimplemented. Next register the bounded sampling-feasibility preflight before any law draws.

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

[Generator-v2 design](docs/generator_v2_design.md) specifies attached funded birth, Structural resource transfer and recoverable leaf deletion using existing operations. The [protocol](docs/p01f_protocol.json) and [literal witness registry](docs/p01f_witnesses.json) fix 12 authored families across four seeds, with explicit positive/negative predictions and future execution ceilings. The fixed witness runner is implemented and its single registered batch passed; the law sampler remains unimplemented.

```sh
python3 scripts/check_p01f_registration.py artifacts/p01f-registration-new
```

This static review requires a new output directory and byte-matching [registration freeze](docs/p01f_registration_freeze.json). It checks schemas, case census and declared inventory arithmetic; it does not match or execute a rule or establish a predicted trajectory. [Registration findings](docs/p01f_findings.md) preserve that distinction. The subsequent [execution findings](docs/p01f_execution_findings.md) report all 48 cases passing under the separately frozen implementation. The batch is consumed; do not repeat it. No law search or E01 is admitted.

For a retained complete local bundle, the receipt-only audit performs no transitions:

```sh
python3 scripts/audit_p01f_receipts.py artifacts/p01f-001
```

The public receipts omit raw traces and dependency snapshots, so this audit requires the full local bundle. See [implementation](docs/p01f_implementation.md), [execution freeze](docs/p01f_execution_freeze.json) and [reachability admission](docs/p01f_reachability_admission.json).
