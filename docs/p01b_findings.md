# P01b: full-pilot registration and detector reporting

Date: 2026-10-19. **Reporting fidelity passed on all 64 retained P01a runs, seven fixed fixtures, and the cap/corruption controls.** Full P01 has not started. Scientific status remains untested.

The [full development protocol](p01_protocol.json) and [registration](p01b_registration.md) fix the next pilot's 128 rule sets × four initial states × 1,000 epochs. Proposal IDs 3000..3127 are disjoint from P01a. Budgets are 8 GiB of traces, 12 GiB total artifacts, one hour of aggregate process CPU and two hours elapsed. Native runs retain the 10-second and sampled 128 MiB RSS watchdogs; analysis stages have separate ceilings. The memory policy explicitly accepts sampling for this development scope, with missed peaks and overshoot possible. No hard instantaneous memory bound is established.

These are registered ceilings for a future runner, not claims that the old P01a runner enforces the new multi-stage campaign. Cap hits and unstarted slots must remain in the 512-slot denominator. No budget expansion, replacement draw, continuation of capped runs or threshold adjustment is admitted. The registration describes CPU/storage accounting, conservative launch reservations, cost-tail summaries, nested initial states and censored/unmeasured cells. E01 remains unauthorized.

## Observed detector outputs

The [readiness receipt](evidence/p01b-001/readiness_audit.json) records independent Python/Rust agreement over the existing 4,096 generated epochs. No P01a trajectory was regenerated or extended, and no full-P01 world was evaluated.

| Full 64-epoch operational AP label | Retained P01a states |
| --- | ---: |
| supported | 0 |
| not_supported | 62 |
| inconclusive | 2 |
| Total | 64 |

These are descriptive results on 16 development law draws with four nested initial states each, not confirmatory prevalence estimates. The frozen detector's lack of support is preserved. No selection or search occurred. Thresholds, connected/coactivity estimators, ambiguous tracks and excluded-large counts remain unchanged. Turnover is exported descriptively; maintenance is always `not_assessed` because no matched maintenance interventions ran on these generated worlds.

Six seed-0 environment fixtures exactly matched their original full detector records: driven pair, driven renewal and mixed islands supported AP; external flux, no-op pair and unfunded pair did not. The seed-0 attached-inert fixture retained `inconclusive`. This verifies reporting compatibility on disclosed controls; it does not establish detector accuracy for arbitrary generated laws.

## Cap and integrity handling

The new `pilot-report` executable reads the worker request, canonical newline-terminated epochs and separate worker summary. It verifies accounting and final identity, replays the whole environment through the frozen reference adapter, and checks the next rejected epoch before accepting a cap reason. The independent Python checker reconstructs the next epoch and matching-budget counts separately and compares every detector field.

Existing zero-event/zero-trace and exact-boundary controls exported `coverage: censored_prefix` and `full_horizon_ap: null`. Binding, match and world-size caps did likewise. Seven corruptions were rejected: missing summary, partial record, forged completion, dishonest cap reason, changed event count, altered world and altered detector output. A separate regression test added after sealing confirms the harder case: a driven-pair prefix that **supports AP at epoch 12** hits its event ceiling before the requested 13th epoch and still exports no full-horizon endpoint. Its [test log](evidence/p01b-001/supported_prefix_tests.txt) and [supplemental receipt](evidence/p01b-001/supplemental_verification.json) are separate from the original bundle inventory.

Rust tests, Python tests, Clippy and formatting passed. P00f, P00g, P01a and P01b frozen files still match their hashes. The sealed [manifest](evidence/p01b-001/manifest.json) identifies input bundles, binary hashes, source snapshot and each of the 64 outputs. Full reports, fixture inputs and rejection logs remain in ignored `artifacts/p01b-001`; compact receipts are public. Later documentation, the positive-prefix test and supplemental verification do not alter the frozen reporting code or prior evidence.

## Next execution gate

Registration and reporting are ready. **Full P01 execution readiness remains false** until a new sealed campaign runner enforces the registered native, Rust-analysis and independent-audit stages; total CPU/storage/output ceilings; complete fixed denominator; and per-stage failure outcomes. P01a's frozen runner cannot be repurposed by changing its panel. The next bounded task is that runner with forced-limit and crash/failure accounting tests, before spending the registered full-pilot budget.
