# Causal ALife Evolvable-Physics Experiment — Revised Plan

Date: 2026-10-17  
Status: Proposed research protocol; no implementation or scientific result is claimed.  
Source: `causal_alife_evolvable_physics_experiment_plan.md`  
Source SHA-256: `6db6f20c9b95627aa69c3f802c7d78867271fe9d530f108b9c34401157308243`

## 1. Aim and first decision

Build a small, auditable local-rewrite substrate and test which sampled laws support active organization, causal reproduction, heritable variation, and adaptation. Keep laws fixed within each inner run. Keep organism labels, lineage inference, and scientific scores outside the world dynamics.

The first scientific question is:

> Under a declared rule generator, environment, scheduler, detector, and compute budget, can descriptor-guided search discover more independently validated active persistent structures than random search?

This question is deliberately narrower than finding the smallest general physics of life. A negative answer is a valid outcome. It does not prove that the substrate cannot support evolution, and it does not prohibit a separately registered assisted-reproduction assay.

The first engineering decision is whether a reference interpreter and an optimized implementation agree on complete state transitions, accounting, and continuation. No large search starts before this gate passes.

All numerical settings below are proposed defaults. A development pilot may change them; the confirmatory protocol must then freeze them before held-out evaluation. Unfilled protocol fields mean the confirmatory experiment is not ready to launch.

## 2. Main corrections to the original plan

| Original section | Problem | Revision |
|---|---|---|
| 5, 9 | The example matches two disconnected nodes despite requiring connected local patterns. | Require an existing local contact edge; define how encounters occur. |
| 7, 19 | Event ancestry and same-seed replay are treated as strong causal evidence. | Separate execution provenance from intervention evidence; specify random coupling and matched controls. |
| 8 | Read/write conflicts, absent-edge predicates, resource contention, and batch semantics are underspecified. | Freeze snapshot reads, serializable selection, predicate conflicts, and atomic commit. |
| 10, 11 | Conservation, reservoirs, and execution policy can change together. | Fix one accounting and environmental profile first; vary other profiles in separate strata. |
| 18, 33, 43 | Promotion thresholds and validation metrics may change after seeing outcomes. | Tune on development data, then lock all confirmatory criteria. |
| 20 | Requiring a surviving parent excludes fission; ancestry in the similarity score risks circular heredity evidence. | Model budding and fission; separate structural recognition from causal attribution. |
| 30 | Failure to find a significant loss is taken as permission to remove a rule. | Require a registered noninferiority margin; qualify minimality by tested operations. |
| 37 | Many seeds are requested without defining the independent statistical unit. | Distinguish campaigns, worlds, environments, and within-world replicates. |
| 43 | Candidate truncation may silently change the physics. | Stop and label incomplete enumeration; a truncated sampler is a separate scheduler profile. |
| 48–49 | Intervention support arrives after persistence claims; search superiority gates unrelated research. | Build branching early; make discovery and assisted-capacity tracks explicit. |

## 3. Claims and falsifiable hypotheses

Record each capability independently as `untested`, `supported`, `not_supported`, or `inconclusive`, with assay version, effect estimate, uncertainty, and denominator. Do not collapse these into an automatic ladder or a single life score.

| Question | Evidence required | Limit of conclusion |
|---|---|---|
| How prevalent is active persistence? | Independent draws from a frozen rule generator and initial-state distribution. | Prevalence under this sampling distribution, not all possible laws. |
| Do early descriptors predict later capacity? | Prediction on held-out rule families, using descriptors measured before the outcome window. | Predictive association, not enabling mechanism. |
| Does guided search help? | Repeated matched-budget search campaigns and independent final evaluation. | Algorithmic advantage within the registered budget and domain. |
| Does a structure maintain itself? | Turnover and matched interruption of a proposed maintenance process. | Maintenance of a detector-defined structure in the tested environment. |
| Does it reproduce? | Recurrent descendant production, independent continuation, and controlled parent-process interventions. | Causal reproduction; not automatically heredity or evolution. |
| Is variation inherited and selected? | Native variants, common-environment transmission, and differences in descendant production. | Darwinian evolution within the measured traits and conditions. |
| Does adaptation occur? | Reciprocal assays of ancestors and evolved descendants after controlled environmental histories. | Adaptation to the tested challenge. |
| Are there enabling laws? | Paired law additions/deletions with fixed accounting, environment, and evaluation. | A capability boundary at the tested resolution, not a universal phase transition. |

“Evolvability is sparse” needs a declared prevalence threshold and denominator. Without them, report a prevalence estimate rather than a binary verdict. A failed search bounds what this protocol found; it is not an impossibility proof.

## 4. Freeze a baseline substrate before searching it

### State and locality

Use typed attributed hypergraphs with bounded integer state, node-local resource balances, and explicit contact edges. Distinguish contact edges, which permit encounters, from structural edges, which form candidate organization. Fix contact transport rules outside the outer-search genome in v0 and count their activity separately.

Specify edge endpoint order, permitted arities, repeated endpoints, parallel-edge policy, match injectivity, and dangling-edge deletion behavior. Suggested v0: ordered endpoints, arity 2–4, distinct endpoints, no duplicate identical edges, injective matches, and deletion rejected if incident edges are not explicitly handled.

Patterns must be connected through explicitly matched edges. The original attachment example becomes:

```text
match: a:type1 --contact-- b:type2
condition: no structural_edge(type3, a, b)
consume: local activation and free matter at a
produce: structural_edge(type3, a, b), with matter transferred to its bound inventory
```

Do not interpret disconnected patterns as local collisions. If free mixing is desired, define and test it as a different encounter model. Disconnected micro-environments remain isolated unless explicit transport connects them.

### Accounting and environment

Use a fixed matter inventory in the baseline: free matter plus matter bound in nodes and edges is conserved exactly. Creation reserves and binds matter; deletion releases the same declared amount. Charge edges as well as nodes. Resource insufficiency rejects a transition without side effects.

Use a separate activation channel with a declared source and sink. Record injected and dissipated amounts exactly. This is abstract bookkeeping, not a claim of physical thermodynamics. Supply locations, rates, transport, and reservoir accessibility are part of the environment specification.

Test a driven baseline and a closed comparison separately. Never pool their outcomes. Avoid globally accessible reservoirs in the local baseline because they couple distant structures through resource competition.

Initially mutate rewrite laws only. Fix scheduler, transport, accounting, numeric types, and environment. Later conservation or transport variants receive new profile IDs and separate sampling distributions.

### IR and rule generation

Start with serializable IR; postpone a textual DSL until semantics stabilize. Permit create/delete, bounded integer state updates, edge edits, and resource transfers. Logging annotations are observer output and cannot influence matches or scores directly.

Reject malformed proposals with a recorded reason. Do not silently repair them: repair changes the generator distribution. If repair is studied, version the transformation and retain pre- and post-repair proposals.

Specify rule-count distribution, type frequencies, pattern sizes, operator probabilities, duplicate-rule handling, and invalid-proposal policy. Report both total proposals and valid worlds. Deduplicate alpha-equivalent rule encodings where feasible, but do not call syntactic normalization proof of semantic equivalence.

## 5. Executable scheduler contract

An epoch reads an immutable pre-epoch snapshot.

1. Enumerate every legal match under the fixed limits.
2. Canonically identify matches, including rule instance and variable bindings. Resolve pattern symmetries explicitly so automorphisms do not accidentally multiply firing rates.
3. Derive deterministic priorities from a versioned keyed random function of seed, epoch, rule identity, and match identity. Specify tie-breaking. Do not depend on hash-table iteration or worker completion order.
4. Greedily select matches in priority order using a documented conflict policy.
5. Stage the selected transitions and validate every invariant.
6. Commit the batch atomically in canonical event order. Assign created IDs deterministically.
7. Update indexes and emit state, accounting, and event digests.

The conservative v0 policy rejects write/write and read/write overlap. Read/read overlap is allowed. Existence checks, adjacency scans, and negative predicates are reads too: creating a previously absent edge must conflict with another selected event that relied on its absence. Node deletion conflicts with incident-edge operations. Local resource accounts are explicit conflict keys. Serialize access to a shared account in v0 rather than implementing ambiguous concurrent withdrawals.

No rejected preparation changes graph state, allocator continuation, resources, random state, epoch, or event history. A matching-cap breach stops before committing a partial epoch. Log it as `match_budget_exceeded`; do not keep an arbitrary prefix of matches.

The epoch scheduler defines this model's dynamics. It is not a continuous-time kinetic model. Later rate-based scheduling is a separately versioned experiment.

Incremental matching comes only after brute-force matching passes differential tests. Negative constraints, time-dependent inputs, and supply changes must invalidate the appropriate cached matches even when no nearby entity was edited.

## 6. Provenance, replay, and interventions

### Execution provenance

Call the trace an execution-dependency DAG. Record field-level reads and writes where practical, creation/deletion, predicate witnesses, resource-account versions, and environment events. An entity-wide `last_modified_event` is too coarse to explain every dependency.

Absence predicates need an adjacency/index version or equivalent witness. These are conservative dependency records, not proof that each predecessor was causally necessary. Resource sharing and scheduler exclusion can influence an event without appearing in a simple construction ancestry chain.

Keep observational lineage hypotheses separate from execution dependencies and intervention estimates. Do not use ancestry simultaneously to define parent-child similarity and then count that similarity as evidence of heredity.

### Replay and continuation

A checkpoint must include graph, allocator state, resource ledgers, epoch, random keys/counters, scheduler version, and any semantically relevant cache state. Reconstructed caches must be verified against full enumeration.

Required checks:

- Reference interpreter versus optimized runtime: identical accepted transitions and final state.
- Interrupted run versus uninterrupted run: identical future events after recovery in a fresh process.
- Single worker versus multiple workers: identical semantic output.
- No-op intervention versus baseline: identical continuation.
- Logging enabled versus disabled: identical dynamics.
- Interrupted writes: no partial checkpoint accepted as complete.

### Counterfactual random coupling

A common seed alone does not guarantee matched stochastic conditions after a branch changes the number of random draws. Use keyed random priorities to keep shared candidate identities coupled where possible; document the identity mapping and where it breaks. Repeat effects across independent seeds. Treat coupling as a variance-reduction choice, not a proof of causal validity.

### Intervention controls

Use baseline, sham operation, target intervention, matched unrelated intervention, and rescue where feasible. Match removed material, activation, position/contact degree, and disturbance magnitude. Specify whether removed matter is retained inert, returned to a reservoir, or removed from the system.

Parent deletion can suppress offspring simply by changing resources or collision opportunities. Test narrower process interruption when possible. Whole-rule disabling changes the world laws; report it as a mechanism ablation, distinct from an intervention on one candidate parent.

Build these facilities before making self-maintenance claims.

## 7. Detector contract and adversarial calibration

Use two independent structure proposals initially: connected local subgraphs and interaction-based communities. Freeze extraction frequency, allowed sizes, similarity, overlap resolution, and split/merge tracking on development fixtures. Preserve detector disagreements and uncertain assignments.

For each candidate report duration, structural similarity, matter turnover, internal state-changing events, size trajectory, resource use, and maintenance-intervention effect. Require organization and activity to involve the same candidate; an inert object with an attached oscillator must not pass merely by pooling their scores.

Define the primary active-persistence predicate before search evaluation:

```text
AP = observed for at least L epochs
     AND similarity >= s at the required observation fraction
     AND state-changing activity >= a within the candidate
     AND size remains in the declared interval
     AND no qualifying safety cap is reached
```

`L`, `s`, `a`, observation fraction, size interval, and handling of identity gaps are mandatory registry fields selected on development fixtures. This predicate establishes active persistence only. Turnover plus a controlled interruption effect is a separate maintenance endpoint.

Required held-out fixtures include frozen objects, inert objects with independent oscillators, resource-free growth, noise, irrelevant state-bit diversity, environmental templating, shared-environment parent/child resemblance, fragmentation without renewed construction, self-maintaining turnover, budding, and fission.

Do not automatically reject templating as fake life: parent-mediated copying may genuinely reproduce. Distinguish copying caused by a parent from independent formation caused by the same external template, and test heritable variation separately.

Every named fixture must receive its expected capability labels. Report confusion counts on additional generated fixture families with uncertainty. Passing fixtures validates these assays on known examples, not unrestricted sensitivity to unknown life.

## 8. Small first implementation

Use four modules or crates initially:

```text
core       state, IR, accounting, canonical encoding
runtime    reference matcher, scheduler, commit, checkpoints, branching
analysis   offline descriptors, detectors, intervention summaries
experiments  generators, batch runner, registry, reports, search adapters
```

Keep a slow independent reference interpreter small enough to audit. Parallelize independent runs first. Add a static graph/trace viewer only after artifacts can be independently inspected. Defer elaborate DSL tooling, GPU work, sixteen mutation operators, and separate archive/viewer services.

This is a standalone design review. Reuse decisions for an existing repository require a separate inspection of its current contracts; this document assumes no existing implementation is complete.

## 9. Experiments and stop gates

### P00 — Semantics and assay validation

Deliver the specification, reference interpreter, runtime, accounting checker, continuation verifier, branching engine, and fixture report.

Gate: zero unexplained semantic/replay mismatches; exact accounting; expected fixture classifications. Any failure stops scientific campaigns. Replication fixtures are needed before the replication assay, not as a dependency of the earliest dynamics census.

### P01 — Development and cost pilot

Proposed pilot: 128 rule sets × 4 initial states × 1,000 epochs, plus fixtures. Measure candidate matches, accepted events, memory, trace bytes, and wall time. This is development data and never becomes confirmatory evidence.

Freeze detector thresholds, rule generator, environment profiles, truncation behavior, archive bins, selection rules, and the complete statistical analysis afterward. Estimate total cost from observed workload distributions, including slow tails, rather than epochs alone. Freeze total core-hour, storage, and per-run limits before scaling.

Gate: feasible cost and a detector that distinguishes the registered positive and adversarial fixtures. If not, revise the protocol with a new version and preserve the failed pilot.

### E01 — Random census

Proposed initial census: 512 independent valid world draws × 8 initial states × 2,000 epochs. Expand only through a separately recorded budget decision.

Report active-persistence prevalence, termination distribution, activity, turnover, and uncertainty. The world is the sampling unit; its initial states are nested observations. Keep cap hits, invalid proposals, and incomplete runs visible with separate denominators.

Retain a random sample of rejected candidates for longer evaluation to estimate screening false negatives. Label oscillatory, quiet, and noisy dynamics descriptively; none is an automatic proof of evolutionary incapacity.

### E02 — Search comparison

Compare independent random sampling, mutation-only hill climbing, and MAP-Elites. Give each the same rule representation, validity rules, development evaluator, initial archive budget, run limits, and final selection budget. Charge duplicate and invalid proposals to the budget; report their frequencies.

MAP-Elites is a search hypothesis, not an anti-Goodhart guarantee. Its archive still depends on chosen descriptors and within-cell quality. Start with two dimensions to limit empty cells; freeze bins and normalization on development data. Keep capability vectors for reporting, but define the exact within-cell selection rule.

Proposed design: 20 matched campaign blocks, each containing all three methods, with 256 proposal slots per method and a shared predeclared compute ceiling. Count proposals not evaluated before the ceiling as yielding no discovery for the budgeted endpoint. Report both proposal counts and consumed compute. The pilot must establish whether this design has useful precision; otherwise label it exploratory before launch.

Each campaign selects exactly 8 candidates using a frozen rule; unfilled slots count as zero. Evaluate them on 32 fresh, sequestered initial states. Validation results never return to search. Define each candidate's validation score as its AP success fraction; the primary campaign endpoint is the mean across its 8 slots. This evaluates the yield of the full search-and-selection procedure without pretending all candidates are independent.

Primary contrast: paired MAP-Elites minus random campaign endpoints. Proposed practical margin: 0.10 absolute success fraction. Use a preregistered paired campaign-level bootstrap interval with 10,000 resamples. Declare superiority only if the lower 95% bound exceeds 0.10. If the interval overlaps the margin, report inconclusive; if its upper bound is below the margin, report that the target advantage was not supported. Hill-climbing comparisons and archive coverage are secondary unless multiplicity is planned in advance.

Use development estimates to simulate precision before confirmation. No extra campaigns, replacement seeds, or adjusted thresholds after viewing the held-out results.

### E03 — Persistence and maintenance confirmation

Freeze a shortlist and evaluate longer runs on fresh conditions. Test maintenance interventions with matched controls and registered observation windows. Select intervention targets from discovery traces, then evaluate target-selection procedures on separate trials.

Gate: reproducible maintenance effect with specified minimum size and uncertainty, plus acceptable detector calibration. Report AP without maintenance when only the first criterion is supported.

### E04 — Two reproduction tracks

**Spontaneous-origin track:** random initial states under the frozen distribution; detect and intervene on candidate reproduction.

**Assisted-capacity track:** insert a supplied or searched replicator under a separately fixed synthesis budget. Record every seed structure and its construction cost. Keep laws and environment fixed; changing laws during synthesis is outer search and must be declared.

Reproduction requires two descendant organizations capable of subsequent reproduction under the assay, allowing budding, fission, or other registered split models. A parent need not survive intact. Model uncertain or multiple parents rather than forcing a tree.

Assistance can show that a world supports a behavior. It cannot show spontaneous origin. Exogenous mutation measures a viability neighborhood; it is not native variation.

Neither track requires MAP-Elites to beat random search. Each requires its own validated assay and authorization through the research schedule.

### E05 — Endogenous heredity and differential reproduction

Disable external mutation, external selection, and hidden reseeding during the native-evolution interval. Fix the trait extraction procedure before confirmatory measurements. Separate new variants from re-expression of initial diversity and environmentally induced state changes.

Compare descendant traits under common environments, shuffled parent assignments within time/environment strata, and replicated independent lineages. Resample at the founder/run level; descendants sharing ancestry are not independent replicates.

Count descendants that themselves meet the reproduction criterion over a fixed window as the primary reproductive-success measure. Resource capture and survival are supporting traits. A proposed default is at least three consecutive transmissions for a variant; freeze the actual horizon and effect thresholds during assay calibration.

Gate: transmitted variation and reproducible differences in reproduction under controlled conditions. No claim of adaptation yet.

### E06 — Adaptation

Create replicate ancestral populations; assign histories to baseline and changed environments. After a fixed evolutionary interval, assay ancestors and both descendant groups in both environments under standardized starting conditions. Include an acclimation/washout protocol when justified by fixtures and report its effect on viability.

Measure reproductive success, not just activity. The primary contrast is changed-history descendants versus unchanged-history descendants in the changed environment, alongside each group's ancestral comparison. Estimate the history × assay-environment interaction as evidence of specificity. A cost in the original environment is informative but not required for adaptation.

Separate inherited adaptation, reversible plasticity, ecological sorting, and general improvement. No post-hoc substitution of the challenge environment.

### E07 and later — Ecology, reduction, and expansion

Use factorial presence/absence and environment-transfer tests for ecological interaction and niche construction. Specify density and resource controls before assigning biological labels.

For reduction, preregister a tolerated loss, for example 0.05 absolute success probability. Remove a rule only when the confidence bound supports noninferiority within that margin. Failure to detect a difference is insufficient. Use paired runs, multiple pruning orders, and selected joint deletions. Validate the final reduced candidate on untouched data.

Call the result “locally irreducible under the tested deletion/simplification operations and assay.” Global minimality requires exhaustive bounded search or proof. Rule count alone is not a universal complexity measure; report encoding length, state alphabet, pattern size, resource assumptions, and initial-condition information too.

Test enabling-law additions in matched pairs with fixed initial-condition distributions. Separate origin from capacity: deleting a law may prevent origin while leaving an implanted lineage viable, or vice versa.

## 10. Statistical and data governance

Split development, candidate selection, and final validation. Keep mutated descendants and near-duplicate world families together when testing descriptor generalization. Fresh initial-state seeds test robustness of a chosen world; held-out rule families test generalization across laws. They answer different questions.

Every confirmatory registry must specify:

- Hypothesis, estimand, independent unit, primary endpoint, practical margin, and interval/test method.
- Generator/environment versions, seeds or sealed seed manifest, run lengths, resource and compute limits.
- Detector versions, exact thresholds, promotion/selection rules, and missing-data policy.
- Sample size or a fully specified sequential rule; do not improvise repeated significance checks.
- Primary and secondary contrasts, multiplicity policy, and treatment of correlated lineages.
- Criteria for supported, not supported, inconclusive, and invalid assay outcomes.

For finite-budget discovery, cap hits count as unsuccessful discovery attempts. For claims about persistence duration or biological capability, the same runs may be censored or unmeasured; report bounds and termination reasons. Infrastructure errors invalidate affected evidence rather than becoming silent biological failures. Preserve them; fix-and-rerun under a new recorded campaign version.

Report uncertainty by the correct cluster level. Do not treat thousands of related events or offspring as thousands of independent trials. A validation set becomes development data after its outcomes inform changes; new confirmation then needs new held-out data.

## 11. Artifacts, storage, and verification

For every proposal retain parentage, mutation record, validity decision, canonical encoding/hash, configuration, seeds, termination, and summary. For every run retain initial-state identity, environment schedule, binary/source/dependency versions, final digest, accounting totals, and checkpoint metadata.

Use full traces for the bounded pilot and intervention runs. For a larger census, retain compact checkpoints/digests and predeclared trace samples. Reconstruct a promoted run's full history only through deterministic rerun verified against the original digests; do not imply omitted history was retained. Estimate logging cost explicitly.

Suggested bundle:

```text
protocol.json
campaign_manifest.json
proposal_ledger.jsonl
worlds/<hash>/rules.cir
runs/<id>/manifest.json
runs/<id>/initial_state.bin
runs/<id>/metrics.parquet
runs/<id>/checkpoints/
runs/<id>/events.zst             # when retained
interventions/<id>/branch_manifest.json
verification/accounting.json
verification/reference_replay.json
reports/findings.md
checksums.sha256
```

Separate execution status from scientific acceptance in manifests. An independent checker should recompute conservation, state digests, counts, and registered acceptance predicates without calling the same analysis functions under test. Preserve original failures and every change to the protocol.

Every report states the research question, registered hypothesis, sample flow and exclusions, resource costs, estimates and intervals, failures, intervention results, detector disagreements, exact reproduction commands, artifact hashes, and what remains untested.

## 12. Open-endedness and complexity

Treat increasing organization as a later finite-horizon claim. Declare measurement scales, novelty criteria, and survival windows before observing the confirmatory trajectories. Compare size-matched and activity-matched controls. Causal depth can increase merely because time passes; compression can reflect noise or serialization; motif counts can grow merely because graphs grow.

Require functional interventions for claimed new roles and record innovations that fail to persist. Repeat with larger resource capacities and longer horizons to test whether apparent growth saturates. Finite observations do not establish unbounded future innovation.

The open-ended-evolution literature contains differing definitions and emphasizes scalability and novelty criteria; choose a definition explicitly rather than treating a capability level as proof. See [Taylor et al., Open-Ended Evolution: Perspectives from the OEE Workshop in York](https://doi.org/10.1162/ARTL_A_00210).

## 13. Immediate build order and completion boundary

1. Write executable transition, locality, accounting, and scheduler specifications.
2. Implement the reference interpreter and exact ledger verifier.
3. Implement the production transition path and differential fixtures.
4. Add checkpoint continuation, no-op branching, and controlled interventions.
5. Calibrate active-persistence and maintenance detectors on positive and adversarial fixtures.
6. Run P01, freeze a feasible protocol, then run E01.
7. Run E02 only once its detector, budget, and statistical design are frozen.
8. Publish the result at this boundary, including a negative or inconclusive result, before extending the program.

Do not begin with a 100,000-world search or a full reproduction/ecology stack. First deliver a verified substrate, a calibrated assay, a measured cost model, and one reproducible census. This creates a useful result even if no promising world is found.

## 14. Method references and status

MAP-Elites explicitly uses user-chosen behavior dimensions and performance within those regions; the archive is not objective-free. This motivates specifying both descriptors and selection quality and testing it against equal-budget alternatives. See [Mouret and Clune, Illuminating search spaces by mapping elites](https://arxiv.org/abs/1504.04909).

The controls, defaults, gates, and revised sequence above are proposed design choices for this project, not results demonstrated by those references. The next deliverable is P00's executable specification and fixture matrix; implementation and confirmation remain future work.
