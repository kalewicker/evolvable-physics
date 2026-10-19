# P01: registered development and cost pilot

Date: 2026-10-19. **The first registered pilot finished at its CPU launch-reserve check: 469 complete horizons, one audited censored prefix, and 42 unstarted slots out of 512.** There were no infrastructure failures, rerolls, replacements or budget expansions. Scientific status remains untested; E01 is not admitted.

The [protocol](p01_protocol.json) registered 128 rule sets × four initial states × 1,000 epochs, IDs 3000..3127 in proposal-major order. The [launch context](evidence/p01-001/launch_context.json) identifies source commit `06bd4e9`, frozen protocol, admitted readiness receipt and binary hashes. Sources and binaries were copied before execution. All original protocols, thresholds and limits stayed unchanged.

## Outcomes and denominator

The [sealed campaign audit](evidence/p01-001/campaign_audit.json) verifies the inventory, source/binary identities, stage receipts and request/trace/report bindings. Every started slot passed independent generation, native replay, detector reporting and independent Python audit. The [slot table](evidence/p01-001/slot_outcomes.csv) retains all 512 registered cells.

| Outcome | States out of 512 |
| --- | ---: |
| Full-horizon operational AP supported | 0 |
| Full-horizon operational AP not supported | 436 |
| Full-horizon operational AP inconclusive | 33 |
| Audited censored prefix; no full-horizon label | 1 |
| Started but unmeasured | 0 |
| Not started before campaign budget stop | 42 |

There were **469,935 independently verified epochs, 1,655,754 committed native events and 1,878,032 applicable candidates**. All generated environments were closed; no external channels ran. Applicable-candidate counts exclude operation-inapplicable pattern matches and partial binding work. All declared native work was independently verified, including the censored prefix; no failed analysis was substituted with a negative label.

Initial states are nested within law draws. Across all 128 registered laws: 94 had four `not_supported` states; 22 had complete state tables containing inconclusive results and no supported state; 12 had at least one censored or unstarted state and no verified support. None had a verified supported state. Only 118 law draws were generated before the stop, with zero duplicate complete law sets among them. These are development descriptions, not independent-state prevalence estimates or evidence that support is impossible in the generator distribution.

The 33 disagreements remain `inconclusive`. The frozen detector was not retuned. A `not_supported` label means its operational criteria were not supported over the supplied trajectory; it does not establish absence of organization or biological capability. Maintenance was **not assessed**: descriptive turnover does not replace matched interventions.

## Censoring and budget stop

Slot 177, proposal 3044 / initial state 1, reached the 32 MiB trace ceiling after 935 epochs. Its 33,540,866-byte prefix passed both detector replay and independent audit. The staged next epoch was not published, and the full-horizon label remains null. It was not continued or replaced.

The last evaluated slot was 469: proposal 3117 / state 1. Slots 470..511 were not launched, beginning with proposal 3117 / state 2. The pre-seal aggregate CPU observation was 3,502.116951 seconds. Adding the registered 100-second next-slot reservation would exceed the 3,600-second ceiling; the wall, trace and artifact reservations still fit. This explains the generic `campaign_budget` stop without relaxing the reservation to fill cheap-looking slots. Unstarted and censored cells are not AP negatives and cannot be discarded from the denominator.

| Sealed resource observation | Value | Registered ceiling |
| --- | ---: | ---: |
| Aggregate process CPU, including parent/guards/reaped descendants/sealing | 3,506.036956 s | 3,600 s |
| Elapsed time | 3,021.936799 s | 7,200 s |
| Epoch traces | 4,865,221,216 bytes | 8,589,934,592 bytes |
| Total retained campaign file bytes | 4,953,302,088 bytes | 12,884,901,888 bytes |

The [seal](evidence/p01-001/seal.json) reports **no overshoot** of any registered ceiling. Its measurement boundary is after manifest/inventory fsync and before final seal publication overhead. Final seal byte size is included in artifact accounting. Build/readiness checks and subsequent read-only publication/reporting work are outside the campaign measurement; their outputs remain separate. File bytes are not filesystem allocated blocks.

## Observed cost tail

Across 470 started slots, the sum of child-stage elapsed times had mean **5.889159 s**, median **2.783846 s**, nearest-rank p95 **25.709551 s**, and observed maximum **68.612614 s**. These per-slot sums exclude parent/guard-startup gaps; use the sealed totals for campaign accounting. The censored slot's cost is a lower observation for its requested 1,000-epoch horizon, not a completed runtime. The maximum is not a tail bound.

Independent Python audit dominated: mean **4.689941 s**, p95 **21.831854 s**, maximum **59.664188 s**, against its 60-second watchdog. Native processing peaked at 2.728883 s and Rust reporting at 6.215340 s. Observed child peak RSS maxima were 6,258,688 bytes native, 182,435,840 bytes Rust reporting and 367,722,496 bytes Python audit. RSS remains sampled: missed instantaneous peaks and overshoot are possible. No hard memory bound is established.

Full stage distributions, declared-versus-verified work and provenance are in [machine-readable findings](evidence/p01-001/findings.json). The observed CPU tail and reserved launch rule prevented completion of every horizon within this budget; the pilot does not demonstrate feasibility of evaluating all 512 horizons under the same ceiling. It demonstrates bounded execution with explicit missing/censored cells.

## Verification, limits and next work

All frozen P00/P01a/P01b/P01c files still match their hashes. The sealed audit passed every retained file/hash and all completed audit bindings. Nine Python tests passed, including three reporting regressions covering the full denominator, refusal of unaudited positives, and malformed worker summaries. The source/binary build and readiness identities were checked before launch. The descriptive summarizer was added after launch and reads the immutable bundle; its hash is recorded in the report. It neither reruns worlds nor changes detector output. Original raw evidence remains in ignored `artifacts/p01-001`, with report and preflight/context files stored separately.

This remains a narrow generator-v1 development result. It does not measure calibrated detector sensitivity/specificity on arbitrary worlds, reproduction, heredity, adaptation, maintenance or search superiority. The compute stop and trace censoring are informative outcomes rather than grounds for expansion. The disclosed Contact-ring/template biases remain intact; no proposal was repaired after observation.

The next bounded milestone is **read-only pilot diagnosis and protocol closure**: inspect generator reachability and detector disagreements, attribute the verification cost tail, and register any subsequent implementation or sampling change before new world runs. Do not resume the 42 unstarted slots, extend the capped run, repeat this consumed campaign, or launch E01 under the original pilot registration.
