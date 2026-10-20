# P01g: sampled births are reachable, recycling gate failed

2026-10-20. **All 64 registered trajectories completed and passed independent
verification, but the mechanism continuation gate failed.** Ten of the 16
distinct sampled rule tables produced detector-visible funded births. None
produced newborn recycling, additional Structural funding of an actual newborn,
or child-funded descendant construction in the retained horizons. The registered
decision is `engineering_pass_mechanism_fail`: stop escalation of this
distribution and diagnose the existing evidence before considering any redesign.
Scientific status remains untested; no E01 or sampling expansion is admitted.

## Immutable attempt and verification

The [protocol](p01g_protocol.json) and [sampler registration](p01g_registration.md)
fixed proposal IDs 4000..4015, four nested initial states and 128 epochs per
trajectory before any law construction. The new
[implementation](p01g_implementation.md), [execution freeze](p01g_execution_freeze.json)
and [execution admission](p01g_execution_admission.json) were committed and pushed
as `17b5b1e` before execution. The freeze bound 116 source/input/build-receipt
identities, 3,088 dependency files, tool identities and all three release binaries.
The original protocol, sampler sources and every earlier source freeze were
unchanged. The locked offline build, Clippy and 52 Python tests passed; new tests
used invented event records/synthetic bookkeeping without sampler draws or
transition application.

One attempt ran in the new `artifacts/p01g-001` directory. All 64 pending cells
were recorded before the first law construction. There were no failed stages,
censored prefixes, unstarted cells, retries, replacements, repaired laws or
changed criteria. The [manifest](evidence/p01g-001/manifest.json),
[assessment](evidence/p01g-001/assessment.json), [inventory](evidence/p01g-001/checksums.json)
and [seal](evidence/p01g-001/seal.json) remain immutable.

The Rust and independently implemented Python samplers agreed on every complete
initial environment. All four initial states for each proposal retained exactly
the same ordered rule table. There were 16 distinct tables, with duplicate rule
bodies/multiplicity retained. The native worker and original Rust reporter,
original independent Python transition/environment/detector verifier and separate
single-pass adapter all agreed. Checked committed-event applications emitted the
physical observations and retained event IDs, actual created node IDs, complete
eligibility proposals, funding/refund details and source hashes. Pattern/binding
caps were independently counted for every retained frame. Validation
reconstructions/replays are included in campaign cost and are not additional
law samples.

The later [read-only receipt audit](evidence/p01g-001/receipt_audit.json) passed
all 4,568 inventory entries, 256 stage receipts, 64 trajectory audit receipts,
source/dependency/binary/input bindings, complete denominator, observation proof
links, resource accounting and both gate decisions. It made no sampler call or
transition replay and was outside the measured campaign. Public cell receipts
are byte-identical copies; context records their renamed original paths. Raw
trajectories, source/dependency snapshots and binaries remain local.

## Fixed-panel outcomes

| Endpoint | Observation |
| --- | ---: |
| Law cells / distinct tables | 16 / 16 |
| Complete trajectories | 64 / 64 |
| Committed epochs / native events | 8,192 / 7,453 |
| Attached funded births | 142, across 29 trajectories |
| Detector-visible actual newborns | 104, across 26 trajectories / 10 tables |
| Later Structural funding events to actual newborns | 0 |
| Child-funded descendant construction | 0 |
| Actual newborn recycling / visible birth-recycle loops | 0 / 0 |
| Observed orphaned actual newborns | 0 |
| Full-horizon AP labels | 62 `not_supported`, 2 `inconclusive`, 0 `supported` |

Births/newborn counts are instances within trajectories, not globally unique
biological individuals. Four initial conditions are nested under each law;
there are 16 sampled law cells, not 64 independent law samples. These are
descriptive results for a fixed deterministic panel, not an unbiased prevalence
estimate or a matched comparison against v1.

Both inconclusive cases use proposal 4007: slots 29 (initial state 1) and 31
(initial state 3). Their connected estimator supported AP while the interaction
estimator did not. The complete original detector records are retained in
[slot 29](evidence/p01g-001/inconclusive/29_detector_report.json) and
[slot 31](evidence/p01g-001/inconclusive/31_detector_report.json). The labels and
thresholds remain unchanged; connected support alone is not accepted as joint
AP support.

The first mechanism threshold passed: 10 distinct tables with visible birth
against a minimum of two. The second failed: zero tables with a same-newborn,
same-trajectory visibility/recycling loop against a minimum of one. Secondary
endpoints were not substituted. Thus a feasible, correctly verified pipeline
does not admit continuation on the registered mechanism criterion. Zero observed
recycling does not prove that the distribution cannot produce it. P01f's authored
positive witnesses remain valid; this panel tests discoverability under the
declared sampler and initial distribution.

## Measured resource cost

| Quantity | Observed | Registered ceiling |
| --- | ---: | ---: |
| Aggregate process CPU | 63.495392 s | 300 s |
| Sealed wall | 59.822481 s | 600 s |
| Retained artifact bytes | 270,142,422 | 1,073,741,824 |
| Maximum observed child RSS | 43,073,536 bytes | Stage-specific 128–512 MiB |

Summed leaf CPU was 0.142150 s for generation, 2.592139 s for native workers,
3.887542 s for Rust reporting and 30.120711 s for Python auditing. The aggregate
also includes parent work, guards/ps, validation reconstructions, snapshots,
extraction, summarization and inventory publication. Stage and per-run
median/nearest-rank-p95/maximum costs remain in the original assessment. No
per-process or aggregate ceiling overshot. RSS enforcement is sampled with reaped
peak checked, not an instantaneous hard bound.

Build/tests preceded the campaign. Final seal bytes are included; the last
timing observation precedes final seal publication. Later receipt auditing and
public packaging are outside measured usage. These measurements establish
feasibility only for this panel, horizon, host and pipeline, not a larger campaign
forecast. Closed activation remains 64 per initial world and does not establish
sustained constructive turnover or thermodynamics.

## Closure and next question

The [closure record](p01g_closure.json) consumes this registration and preserves
the negative gate. Do not rerun, replace seeds, extend horizons, select the ten
favorable tables for escalation or relax the recycling criterion under it.

Next perform a disclosed read-only diagnosis of the existing initial states,
rule bodies, candidates, events and mechanism/detector receipts. Reconcile which
transfer/recycling bodies were present, whether observed newborn edges and
kind/state/resource conditions could enable them, and where eligible operations
failed to occur or lost scheduler conflicts. Distinguish limitations proved from
source from absences in this finite panel. Do not construct new laws or evolve
worlds for that diagnosis. Any later redesign or driven environment needs a
separate justification and registration; no such experiment is admitted here.
