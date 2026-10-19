# P01c: sealed full-pilot runner readiness

Date: 2026-10-19. **All 30 engineering readiness checks passed. The registered P01 development pilot is ready to run; none of its 512 slots ran in this milestone.** Scientific status remains untested and E01 remains unauthorized.

The [registration](p01c_registration.md) and [source freeze](p01c_freeze.json) precede the sealed [readiness receipt](evidence/p01c-001/readiness_audit.json). The existing P01 protocol, generator, native kernel and detector thresholds are unchanged. P01a's 62 unsupported and two inconclusive development labels remain preserved; P01c does not replace or reinterpret them.

## What is now implemented

The new runner preallocates the entire fixed ledger and runs independent generation, native evolution, Rust detector reporting and Python independent audit in order. It copies sources and release binaries into the campaign bundle and executes those copies. Full mode accepts only the registered protocol and a published readiness receipt bound to the current source freeze; control overrides are forbidden. A slot gets a full-horizon AP label only after the independent audit binds its request, trace and report. Native semantic caps remain audited censored prefixes. Stage time/RSS/output caps and analysis failures remain unmeasured, with explicit reasons and all remaining slots retained.

Each stage has a separate guard. Both stdout and stderr have exact retained-byte ceilings, so a blocked or verbose child cannot bypass a trace-only limit. The guard reports the retained prefix, observed excess and unknown unread suffix rather than accepting a partial report. It polls sampled RSS and elapsed deadlines, kills/reaps on a cap, and detects loss of its campaign parent. The parent records each stage before launch and commits no endpoint while an audit is still pending.

The runner applies the registered aggregate trace/artifact/CPU/time admission checks before each slot and between stages. Source/binary copies, summaries, logs, requests and sealing are charged. Aggregate process CPU includes parent and reaped descendants without adding leaf timings twice. The inventory and fsynced final seal bind the manifest, files and observed resource totals. Existing output paths are never resumed or overwritten; read-only audit does not modify them.

## Readiness evidence

The successful baseline uses **one disclosed seed-0 driven-pair fixture repeated in four engineering slots** for 12 epochs each. It is not four independent law draws or new biological evidence. All four reports matched the independent audit and the fixture's expected AP support. Baseline totals were 239,352 trace bytes, 4,379,363 artifact bytes, 0.929046 aggregate process CPU-seconds and 1.240863 elapsed seconds. No registered baseline ceiling was exceeded. These are host-specific control costs, not projections for the full pilot. Generation-specific fault controls use the already disclosed P01a proposal 2000 with initial states 0..3 for 12 epochs, so they exercise Rust generation and independent reconstruction without evaluating a new full-pilot draw.

| Controls | Result |
| --- | --- |
| Four-slot native/report/audit baseline; generation checked separately | passed |
| Zero event/trace limits | audited censored prefixes, no full-horizon labels |
| Aggregate wall/CPU/trace/artifact exhaustion | all four slots retained as not started |
| Injected budget stops before reporting/audit | completed native work retained; endpoint unmeasured |
| Nonzero failure in each of four stages | affected endpoint withheld; later slots not started |
| Stdout/stderr overflow in each stage | bounded prefixes retained; affected endpoint unmeasured |
| RSS and wall watchdog stops | child killed/reaped; no detector negative substituted |
| Missing/invalid native summary or detector report | infrastructure failure retained |
| Altered sealed manifest or trace | read-only audit rejected tampered copies; original unchanged |
| Existing destination | rejected without changing its seal |
| Guard SIGTERM cancellation | child killed/reaped |
| Abrupt parent exit while a guarded child was active | guard reaped child; unsealed audit accepted zero endpoints |

The abrupt parent-loss control uses `os._exit(91)` so campaign cleanup cannot run. Its original running manifest remains unsealed; a separate [read-only audit](evidence/p01c-001/parent_loss_audit.json) retains all four slots as interrupted/unstarted and accepts no endpoints. It is not resumed or retroactively sealed. A separate unit test simulates RSS-observation failure and verifies child reaping. Unit tests also verify all 512 future slot IDs/order and exact launch-budget boundaries. Rust tests, six Python tests, Clippy and formatting passed.

Forced zero-budget controls necessarily retain minimal failure metadata even when the selected ceiling is zero; their seals expose that overshoot. Source copying is refused when it cannot fit. The successful baseline had no overshoot. Between-stage admission decisions in two controls were deliberately injected, not claims of measured CPU consumption.

## Limits and next step

Sampled RSS is still not a hard instantaneous memory guarantee. Watchdog and OS delays can overshoot wall/CPU budgets. Sealing is charged through inventory/manifest fsync; the final seal's own publication overhead is excluded and explicitly named in the receipt, while its retained byte size is included. Simultaneous guard/OS failure and arbitrary power-loss durability remain unverified. These limits are preserved in the registered development scope.

The next bounded action is the actual **128 × 4 × 1,000-epoch P01 development pilot**, using the existing 8 GiB trace, 12 GiB artifact, one-hour aggregate CPU and two-hour elapsed ceilings. Budget stops, slow tails, analysis failures and all 512 denominators must be reported without rerolls or expansion. Full-pilot data remain development observations; AP support does not establish maintenance, reproduction, adaptation, search superiority or confirmatory prevalence.

Raw controls, source/binary copies, interrupted data and all original receipts remain in ignored `artifacts/p01c-001` (114,884,917 bytes at sealing). Public compact receipts preserve original bytes and reference unpublished raw files through checksum inventories.
