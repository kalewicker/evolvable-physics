# Evolvable Physics

First implementation of the [revised research plan](docs/experiment_plan_v2.md). This standalone Rust package implements a bounded closed-resource transition kernel and reproducible validation artifacts. P00 is admitted for the bounded engineering profiles and disclosed fixture panels. The registered bounded P01 development pilot is ready to run. Scientific capability claims remain untested.

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

The full 128 × 4 × 1,000-epoch P01 pilot has not started. The [P01b registration and reporting checks](docs/p01b_findings.md) now fix those ceilings and the sampled RSS policy, and independently match frozen detector outputs on all 64 retained trajectories (62 not supported, 2 inconclusive). [P01c](docs/p01c_findings.md) now verifies that runner with 30 control expectations. The registered development pilot is ready to launch into a new sealed directory. Mean linear trace scaling is about 5.9 GB and is not a long-run bound. Scientific status remains untested; no reproduction, adaptation or search-superiority claim is established.

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

Implementation resumed at the user’s request after publication. The current milestone is P01c; the registered bounded P01 development pilot is ready, and has not started.

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

The campaign command launches the registered 512-slot development pilot and requires a new output path, current frozen sources, and the published P01c readiness receipt. It queries child RSS with `ps`, which can require permission outside a desktop sandbox. Sources/binaries, bounded stage outputs, all slot outcomes and the final seal are retained. A full pilot can stop at its budget without completing all horizons; no slot is replaced. An unsealed interrupted bundle is never resumed, and its read-only audit accepts no endpoints.

To rerun only the engineering controls, use `python3 scripts/validate_p01c.py artifacts/p01c-new-run`. See [registration](docs/p01c_registration.md), [findings](docs/p01c_findings.md) and [full pilot ceilings](docs/p01_protocol.json). Neither command authorizes E01.
