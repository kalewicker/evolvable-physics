# P01f execution: attached birth, descendant growth and leaf recycling

2026-10-20. **All 48 registered authored cases passed, with exact agreement across
both Rust matchers and independent Python verification.** This confirms the
registered bounded reachability predictions. The v2 law sampler has not been
implemented or drawn from. Scientific status remains untested.

The [immutable registration](p01f_protocol.json) and [literal inputs](p01f_witnesses.json)
were unchanged. The new [implementation](p01f_implementation.md),
[execution freeze](p01f_execution_freeze.json) and
[execution admission](p01f_execution_admission.json) were committed and pushed as
`7f7edf2` before the single native batch. The freeze bound 94 source/input/build
receipt files, 3,088 dependency files, tool identities and the release binary.
No registered witness transition ran before this freeze. The locked offline
release build, Clippy with warnings denied and 29 Python tests passed before
execution; the tests used structural checks and mocked records, not witness
trajectories. An initial manual optimized-Python probe expected a local error
message, but the frozen imported interpreter rejected `-O` earlier; the final
regression checks that upstream assertion guard directly. This occurred before
the freeze and did not execute a witness.

One attempt ran in the new local `artifacts/p01f-001` directory. Its
[manifest](evidence/p01f-001/manifest.json), [inventory](evidence/p01f-001/checksums.json),
[seal](evidence/p01f-001/seal.json), [panel audit](evidence/p01f-001/panel_audit.json)
and later [read-only receipt audit](evidence/p01f-001/receipt_audit.json) all passed.
No case, seed, prediction, threshold, horizon or resource ceiling was changed or
replaced. The registration is consumed; do not repeat the panel to obtain a new
outcome. All prior P01 negative/inconclusive results and the P01e auditor failure
remain preserved.

| Measured result | Reference matcher | Indexed matcher |
| --- | ---: | ---: |
| Fixed cases | 48 | 48 |
| Complete horizons | 44 | 44 |
| Expected whole-epoch size rejections | 4 | 4 |
| Attempted epochs | 92 | 92 |
| Committed epochs | 88 | 88 |
| Committed events | 60 | 60 |
| Node births | 28 | 28 |
| Node deaths | 16 | 16 |

The two matcher columns are repeated engineering checks on the same 48 inputs,
not 96 independent scientific samples. Frozen Rust observers perform additional
validation replays inside the measured native stage. Their work is included in
costs, not counted as additional experimental cases.

All four attached-birth seeds created a funded node 8 with a Structural edge to
its donor, and both estimators included the pair `[0,8]` at sample 1. All four
cycle cases committed four births and four recycles in eight epochs, restoring
root matter and exhausting its activation. All four descendant cases followed
the declared birth, two funding transfers and child-funded birth sequence.

Every negative control matched: insufficient resources, original Contact
incidence, nonleaf incidence and the wrong transfer route produced empty
committed epochs with no leaked staged edits. Size rejection preserved the
entire environment, including its epoch and counters. Structural resource-only
funding received no physical activity credit. Edge-only detachment left the
registered live, funded orphan. These retained restrictions matter when defining
future sampled-law endpoints.

The independent audit checked complete candidate lists and priorities, conflict
selection, event order/IDs/parents, resource and writer accounting, states and
environment receipts. The original Python activity/detection path and separate
single-pass adapter agreed with every full native detector/activity record. A
second read-only auditor checked source/input/dependency snapshots, the complete
3,208-file inventory, fixed slots, stage outputs, admission and resource receipts.
The later audit was outside the sealed bundle and did not rerun transitions.

| Resource observation | Measured | Registered ceiling |
| --- | ---: | ---: |
| Native process wall | 0.419504 s | 30 s |
| Python audit process wall | 0.545260 s | 90 s |
| Native observed peak RSS | 11,501,568 bytes | 268,435,456 bytes |
| Python audit observed peak RSS | 37,748,736 bytes | 536,870,912 bytes |
| Native retained output | 1,604,638 bytes | 33,554,432 bytes |
| Python audit retained output | 8,456 bytes | 2,097,152 bytes |
| Aggregate process CPU | 2.316850 s | 300 s |
| Sealed wall | 2.484261 s | 240 s |
| Sealed artifact bytes | 195,977,865 | 536,870,912 |

No ceiling overshot. RSS enforcement is sampled, with reaped-process peak also
checked; it is not a hard instantaneous bound. Dependency snapshots account for
190,473,641 bytes of the bundle. Build/tests preceded campaign measurement; the
sealed accounting includes snapshotting, guards, both stages and inventory work,
plus final seal bytes. The last timing observation precedes final seal publication.
Later receipt auditing and public packaging are outside those measurements.

This gate establishes expressivity at authored resource/topology boundaries.
It does not establish a finite-sampler preimage of these rule tables, generated-
law prevalence, AP, maintenance, reproduction, heredity or adaptation. Several
initial states intentionally differ from the proposed generator distribution.

**Next register a small generator-v2 sampling-feasibility preflight.** Specify
fixed law IDs and nested initial-state seeds, horizons, resource/output ceilings,
and go/no-go criteria before drawing laws. Check the sampler statically against
the distribution contract first. Report attached funded birth, funding of created
members, descendant construction and recycling per sampled law, retaining zeros
and clarifying which behaviors coexist within one law. Keep those mechanistic
observations separate from frozen detector labels and preserve disagreements.
Measure the complete pipeline's cost without extrapolating the tiny witness run
to campaign feasibility. The closed activation bound precludes indefinite
constructive turnover; a driven-maintenance assay requires a separate future
environment protocol. Reuse the existing guard, accounting and independent
interpreters rather than starting another general validation framework. No law
draw or E01 is admitted by this closeout.
