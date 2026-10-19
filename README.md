# Evolvable Physics

First implementation of the [revised research plan](docs/experiment_plan_v2.md). This standalone Rust package implements a bounded closed-resource transition kernel and reproducible validation artifacts. Full P00 and all scientific capability claims remain incomplete/untested.

## Run

From this directory:

```sh
cargo fetch --locked
cargo test --locked --offline
python3 scripts/validate.py artifacts/p00f-new-run
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

## Next boundary

Intervention contracts and controls are documented in [P00b semantics](docs/interventions.md). The environment wrapper is specified in [P00c semantics](docs/environment.md). Environment-aware interventions and tested publication recovery are documented in [P00d semantics](docs/environment_branches.md). Fixed detector calibration is specified in [P00e](docs/detectors.md). The P00 admission requirements and frozen transfer panel are in [P00f registration](docs/p00f_registration.md). Missing logging equivalence and environment-to-detector integration remain admission blockers; broader storage-failure coverage is also limited. Only then freeze and run P01. The current report must not be interpreted as evidence of active persistence, self-maintenance, evolution, or search superiority.

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

Implementation is paused at P00f. P00 remains unadmitted because logging equivalence and complete environment-to-detector integration are pending. Further implementation waits for the user's next instruction.

At the end of future project turns, commit and push any changes to this repository after the appropriate checks. See [AGENTS.md](AGENTS.md).
