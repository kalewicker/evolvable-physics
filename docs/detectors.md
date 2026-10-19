# P00e bounded structure and maintenance calibration

Status: fixed engineering calibration protocol. The machine-readable thresholds and expected fixture labels are in `detector_protocol.json`; its canonical SHA-256 is embedded in every output. These are operational definitions for a small substrate, not a universal definition of life.

## Proposals and identity

Two post-hoc estimators operate on independently replayable native traces:

1. Connected components of Structural edges. Contact edges do not define organizational membership. Isolated nodes and components outside 2–6 nodes are excluded; oversized components are counted rather than silently split.
2. Components of a rolling three-epoch coactivity graph. Each native event links the nodes whose type/state/existence or structural incidence actually changed. Reads, resource transfers, burns, provenance, and event markers alone do not create activity credit. Old/deleted nodes are filtered from current proposals. Single active nodes are excluded by the same minimum size.

A slow exact event replay first verifies every trace. Activity is then measured from sequential event-level physical changes, not from rule matches or ancestry labels. The Rust extractor shares transition execution; Python independently replays both transitions and analysis.

Consecutive proposals link when ID-set Jaccard overlap is at least 1/2. A link is accepted only if it is unique in both directions. A split/merge with multiple eligible links is marked ambiguous; old tracks and newly started ambiguous tracks cannot pass. Gaps are not bridged. Identity is a detector hypothesis, and retention of IDs is a deliberate restriction. Complete replacement of a genuinely persistent organization may therefore be missed.

For each proposal, record a multiset of node types and structural edge kinds plus ordered endpoint types. Its multiset Jaccard similarity to the track's first observation must be at least 1/2 at every sample. This descriptor is not a graph-isomorphism proof. Separately, physical maintenance endpoints use an exact canonical topology/type fingerprint computed over all permutations of at most six nodes. Both representations exclude IDs, node state, resource quantities, and provenance.

## Active-persistence predicate

A passing track must have:

- At least eight consecutive epochs and a proposal at every observation.
- Size 2–6 at every observation and feature similarity at least 1/2 throughout.
- State/topology activity in at least half its elapsed epochs.
- Every member observed during its life credited with at least one physical state/topology change. This prevents a stable inert component from borrowing activity from one attached oscillator.
- No ambiguous identity link.

Record each estimator's tracks and raw counts. Support requires a pair of passing tracks with overlapping terminal membership (Jaccard at least 1/2) at the same time. This prevents agreement from pooling unrelated structures. If one estimator passes and the other does not, or their passing tracks cannot be paired, the run is inconclusive. Both negative yields not_supported under this detector's scope. Preserve all disagreements.

Stable topology with monotonically changing irrelevant state bits can satisfy this predicate. It must not be described as functional innovation, heredity, or maintenance. AP detects active persistence as defined; the separate maintenance intervention gate provides the additional evidence.

## Turnover and maintenance

Turnover counts births and deaths of members in an accepted track using physical node creation/deletion, not mere membership reassignment. Require at least two matched birth/death counts in both paired estimator tracks. For the maintenance claim, those same paired tracks must include the focal root. Unrelated active or turning-over components cannot supply its evidence.

The maintenance endpoint is physical motif occupancy: in a twelve-epoch continuation, count samples where the structural component containing the focal root has the exact topology/type fingerprint of its discovery exemplar. Endpoint matching ignores activity, node IDs, and state bits. This prevents stopping an oscillator from masquerading as loss of its maintained physical organization.

A maintenance-supported fixture requires focal AP/turnover, a target-induced occupancy drop of at least 6/12 relative to baseline, and equal baseline/sham/unrelated/rescue occupancy counts. The zero tolerance and horizon are fixture-specific registered choices; they cannot be carried into a stochastic scientific assay without a new protocol and uncertainty analysis.

Controls use a native checkpoint after two warmup epochs. Baseline is an empty request. Sham explicitly retains the repair anchor's current state. Target sets it to 9, preventing the registered repair rule. Unrelated performs the same edit on the matched anchor in a disconnected duplicate structure. Rescue immediately reverses the target edit before continuation. Every branch retains its request/receipt and trace. The focal root is ID 0, and its exemplar is the initial component {0,1,2}; selection is fixed for these disclosed fixtures.

## Registered fixture expectations

Nine families × seeds 0–15 = 144 primary runs, each twelve epochs. Seeds 0–3 are development replicates (36 runs); 4–15 are preassigned validation replicates (108 runs). All fixture designs are disclosed; validation seeds are not a blinded or unseen-family benchmark. Thresholds were fixed before the validation runner; no result-dependent retuning or seed replacement is allowed.

| Family | AP | Maintenance | Reason/limit |
|---|---|---|---|
| frozen_pair | not_supported | not_supported | No physical activity |
| active_pair | supported | not_supported | Both nodes oscillate; no material turnover |
| inert_with_oscillator | not_supported | not_supported | Whole component cannot borrow one node's activity |
| attached_inert | inconclusive | not_supported | Interaction estimator finds active pair; connectivity includes inert third node |
| irrelevant_bits | supported | not_supported | AP is not evidence of useful function or maintenance |
| wholesale_replacement | not_supported | not_supported | Consecutive ID overlap below the detector's identity threshold |
| noise_replacement | not_supported | not_supported | Competing rules yield seed-dependent new-node states; no persistent detected identity |
| renewal | supported | supported | Independent aging/removal creates a hole; repair reconstructs a component |
| passive_turnover | supported | not_supported | Components replace unnecessarily; stopping turnover preserves physical motif |

The noise fixture tests transient replacement noise; it does not establish rejection of all random processes. Full replacement is an explicit sensitivity limit rather than proof that no organization exists.

Renewal and passive_turnover each use two matched components and five arms, for 160 additional twelve-epoch continuations (1,920 epochs). In renewal, the expected occupancy vector is [8,8,0,8,8]. Passive turnover expects [12,12,12,12,12], preserving a registered negative intervention result. Renewal cycles through leaf aging, removal, and repair; matter is conserved and no external mutation or hidden reseeding is used.

## Admission and limits

The independent Python analysis must match every proposal, track, activity/turnover count, agreement pair, fingerprint, branch endpoint, and label, after validating all underlying native traces. Altered labels, summaries, membership, turnover, intervention requests, fingerprints, and endpoint counts must be rejected.

Passing these disclosed examples establishes fixed-fixture calibration only. It does not establish sensitivity/specificity over arbitrary worlds. Generated, separately frozen fixture families, false-negative screening audits, multiscale identity, and broader ecological/adversarial cases remain further validation work. Reproduction/heritability detectors are outside this stage.

This result does not on its own pass full P00 or admit the P01 pilot. The next boundary is an admission audit of P00 requirements and a separately frozen detector-generalization panel, including missing extraction/coverage limits, before broad sampling.
