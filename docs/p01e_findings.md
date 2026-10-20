# P01e: single-pass independent verifier preflight

Date: 2026-10-19. **The frozen candidate matched the fixed evidence panel and used 50.174% less recorded paired child CPU.** All 11 registered corruptions were rejected by both implementations. The sealed execution passed its original engineering gate without a resource overshoot. The frozen receipt auditor subsequently failed on floating-point summation equality; a disclosed post-hoc read-only correction confirms the receipts and gate arithmetic. That checker failure remains preserved. No benchmark was repeated, no source/input freeze was changed, and no native world was executed.

## Frozen attempt and exactness

The [protocol](p01e_protocol.json), [implementation registration](p01e_registration.md) and [source/input freeze](p01e_freeze.json) were fixed before execution. The freeze binds 63 source files and 39 input files. The original P00/P01 scientific contracts, consumed campaign, detector thresholds and outcomes remain unchanged. The new adapter uses the frozen Python transition/environment interpreter and detector, independently of Rust, and emits activity during its checked event application. It retains candidate enumeration, scheduler, provenance, state/accounting, environment, summary, cap and complete detector-record checks.

One attempt ran in a new `artifacts/p01e-001` directory. Its [manifest](evidence/p01e-001/manifest.json), [inventory](evidence/p01e-001/checksums.json) and [seal](evidence/p01e-001/seal.json) remain immutable. Original input inventory/provenance was verified before paired execution. Source copies, guard outputs, corrupted copies and stage receipts remain in that bundle. The source and validator freeze preceded every candidate call on the fixed panel.

All **112 native fixture cases and 96 primary environment cases** matched on state, activity and/or complete detector records, as applicable. The frozen reference also verified the branch/maintenance fields of those environment cases; candidate equivalence covered their 16 warmups and 80 retained maintenance arms. [Per-case receipts](evidence/p01e-001/fixture_equivalence.json) retain identity and result digests. These are engineering fixtures, not new maintenance evidence.

All eight fixed P01 pairs verified the exact original full detector output and produced identical input/output/endpoint receipts. Seven were complete `not_supported` cases; slot 177 remained a censored prefix with a null full-horizon endpoint. No unstarted law, new trajectory, continued prefix, preferred detector, or replacement slot was introduced. The new adapter was not tested on the other 462 started P01 cells in this registration, including the 33 inconclusive cells; their original frozen-verifier results remain authoritative.

## Registered paired CPU result

There was one pair per input, with alternating reference/candidate order and no warmup timing, retries, outlier removal or repeats. The same pairs served the P01 correctness panel.

| P01 slot | Order | Reference child CPU | Candidate child CPU |
| --- | --- | ---: | ---: |
| 0 | reference, candidate | 2.276284 s | 1.355778 s |
| 64 | candidate, reference | 1.065041 s | 0.682480 s |
| 128 | reference, candidate | 14.462616 s | 7.475691 s |
| 177, censored | candidate, reference | 60.238742 s | 28.376477 s |
| 256 | reference, candidate | 1.332804 s | 0.803269 s |
| 320 | candidate, reference | 1.654554 s | 0.937974 s |
| 384 | reference, candidate | 1.640591 s | 0.978689 s |
| 469 | candidate, reference | 33.174855 s | 17.110240 s |
| **Sum** | | **115.845487 s** | **57.720598 s** |

The candidate/reference CPU ratio was **0.498255**, below the unchanged 0.8 gate. Child CPU includes imports, parsing, verification, detector construction and common receipt hashing. Provenance checks, guard/`ps` and parent overhead are included separately in aggregate accounting. This is a host-specific observation on a selected engineering panel. It is not a representative speed estimate, a runtime-tail bound, a whole-campaign forecast or proof that all 512 original horizons would fit. Slot 177's trace remains censored regardless of replay speed. Cache/load effects were not independently controlled and there is no repeated timing variance estimate.

Both adapters accepted the clean assembled control and rejected every applicable registered corruption: priority, parents, event omission, ledger, prepared ordering, external receipt, native world, summary, detector output, forged cap and partial record. Each rejection was an AssertionError at the relevant check; guard failure/crash did not substitute for rejection. The mutated copies were made from retained records, with no native trajectory generation. All 28 guarded stages exited successfully.

| Sealed aggregate observation | Value | Registered ceiling |
| --- | ---: | ---: |
| Process CPU, including parent/guards/reaped descendants | 227.043987 s | 600 s |
| Elapsed time | 195.128468 s | 900 s |
| Retained bundle bytes, including seal | 1,632,415 | 1,073,741,824 |
| Maximum observed child RSS, sampled/rusage | 361,168,896 bytes | 1,073,741,824 |

No ceiling overshot. Sampled RSS is not a hard instantaneous bound. Sealed usage is observed after inventory publication and before final seal publication overhead, matching the disclosed accounting boundary. Later receipt audits, test logs and publication work are outside that campaign measurement.

## Preserved receipt-auditor failure and correction

The frozen [v1 auditor](../scripts/audit_p01e.py) passed inventory/source/stage/case checks, then failed its exact float equality for summed CPU. Its `+=` accumulation gave candidate CPU `57.720597999999995`; the runner's `sum` gave `57.720598`, a difference of about `7.1e-15` seconds. The [original traceback](evidence/p01e-001/auditor_failure.txt) is retained. This is a reporting-arithmetic failure, not an output mismatch or a failed timing threshold. The original auditor, candidate, harness, freeze, assessment, seal and measured records were not repaired in place.

The separate [v2 receipt auditor](../scripts/audit_p01e_v2.py) was written **after** measurement. It sums the recorded CPU decimal strings and evaluates the original 0.8 gate with Decimal arithmetic. It allows at most `1e-12` seconds and `1e-15` ratio difference solely when comparing recorded floating-point display arithmetic; no such tolerance is used in the cost threshold, source hashes, states, detector records or endpoints. Two regressions retain the actual rounding case and reject a one-microsecond or changed-ratio alteration. The [corrected audit receipt](evidence/p01e-001/receipt_audit_v2.json) verifies the complete retained inventory, fixed denominator/order, all outputs/corruption receipts, censoring, exact gate arithmetic and resource accounting. This correction is post-hoc and does not retroactively make the frozen v1 checker pass.

Sixteen unit tests passed before execution. Nineteen passed after the separate arithmetic correction, including a check that optimized Python cannot disable the corrected auditor's assertions. Their logs, correction source hash, original failure, audit and [admission record](p01e_admission.json) are anchored in [publication context](evidence/p01e-001/publication_context.json), outside the original inventory. No verifier or timing process was rerun to obtain admission.

## Scope and next bounded task

P01e admits the separate adapter only for the disclosed retained evidence and checks, with the receipt-auditor correction explicitly recorded. The frozen P01 campaign pipeline still uses its original verifier. Integrating the adapter into a future campaign requires a new pipeline registration; this result admits no new world execution, generator change, sampling, budget expansion or E01. Scientific status remains untested.

The next bounded task is **designing and registering generator-v2 reachability witnesses**: specify how a funded birth becomes attached, how a created member can later be removed/recycled, and how Contact topology, locality, activity credit and resource accounting constrain those operations. Require a source-level reachability argument and fixed positive/negative witness expectations before any native fixture execution or new sampling. Preserve generator v1 and its consumed pilot. This is a design/registration step, not permission to repair or rerun P01 or optimize this candidate again against its timing panel.
