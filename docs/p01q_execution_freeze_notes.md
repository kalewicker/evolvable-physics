# P01q execution freeze and admission

2026-10-23. The [freeze](p01q_execution_freeze.json) and
[admission](p01q_execution_admission.json) prepare the sole bounded dynamical
attempt at `artifacts/p01q-001`: all 32 retained laws, all 128 saved environments,
128 epochs per cell. They must be committed and pushed before any transition.
No worker, candidate enumeration, transition replay or keyed evaluation ran
while preparing this gate. The attempt directory does not exist.

The [read-only review](evidence/p01q-execution-readiness-001/readiness.json)
and [runner's closure check](evidence/p01q-execution-readiness-001/runner_closure.json)
both passed. The closure pins 1,107 project/input/receipt files, 3,846 dependency
files, four tools and 23 complete directory memberships. All 533 preceding
public receipts and the original registered inputs are included. All five
implementation hashes still match the passing 17-test readiness receipt.
The original P01o inventory/seal and P01p closure receipts passed the runner's
custody checks without recomputing generator keys or parsing retained worlds.

The worker and reporter hashes exactly match the previously verified P01g
binaries; no rebuild was needed. Fresh locked/offline Cargo metadata has the
same 21 dependency packages. Every previously frozen dependency/tool byte still
matches. The dependency closure adds 758 files from the complete installed
Python standard-library tree, including existing bytecode caches. Those files
are now hashed and included in exact membership checks alongside crate sources
and Rust target libraries. The Python framework library is also pinned.
Execution must disable bytecode writes so imports cannot change this closure.
This identifies the installed toolchain; it does not make the host OS/hardware
hermetic or establish a hard instantaneous RSS bound.

Six new invented-file closure tests passed normally and with Python optimization.
They reject changed source/dependency/tool/binary bytes, added dependency files,
missing hash coverage, mismatched admission links/readiness, changed output or
scope, and an existing consumed attempt. No test failed. Logs and exact source
snapshots are retained. Neither those tests nor the closure check run dynamics.
The source/input snapshot set totals 25,564,664 bytes, and dependencies total
218,625,102 bytes before binaries, future outputs and closure metadata. These
are measured custody sizes, not a runtime cost forecast.

After this freeze/admission is committed and pushed, the sole admitted command is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/p01q_campaign.py artifacts/p01q-001
```

The runner checks closure and probes process/RSS capability before creating the
attempt directory. A capability failure before creation does not consume a
trajectory attempt or apply transitions. Creation consumes the registration,
even if preparation later fails. All 128 planned slots precede any worker launch.
Preserve negative, censored, failed and unstarted outcomes; no retry, resumption,
completion of missing cells, replacement, repaired input, selection of favorable
laws or enlarged horizon/budget is admitted. The registered 1,200-second wall,
600-second CPU, 2-GiB artifact and 64-MiB terminal-reserve limits remain unchanged.

After the single attempt, audit saved receipts without rerunning worlds or
keyed sampling. Live watchdog behavior, actual cost, trajectory completion and
mechanism outcomes remain untested at this gate. Behavioral outcomes remain
null/not_executed until observed. Preserve all historical negative/inconclusive
results and original criteria; scientific status stays untested and E01 is not
authorized. A passing continuation gate can only justify proposing a new bounded
protocol, never automatic expansion or a claim of reproduction.
