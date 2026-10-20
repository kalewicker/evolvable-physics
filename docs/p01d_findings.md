# P01d: generator scope, detector disagreements and protocol closure

Date: 2026-10-19. **Generator v1 cannot connect, fund or delete its newborn nodes, and cannot execute node deletion.** This restriction is specific to the frozen initial distribution and templates, not the kernel. The read-only analysis checked all 470 started slots, 469,935 retained epochs and 1,655,754 events, including the censored prefix. It evolved no worlds and changed no labels. All 33 disagreements remain inconclusive; scientific status remains untested and E01 is not admitted.

The [analysis plan](p01d_analysis_plan.md) discloses the post-hoc source/report inspection. The [completed manifest](evidence/p01d-001/manifest.json), [input audit](evidence/p01d-001/input_campaign_audit.json) and [checksum inventory](evidence/p01d-001/checksums.json) bind the scan to the original sealed P01 bundle. All frozen sources and the original inventory passed verification. The 42 unstarted slots were neither generated nor dropped from the original denominator.

## Generator reachability

The [source-level inductive argument](generator_v1_reachability.md) explains the restriction. All Contact edges form an immutable ring on the original eight nodes. Structural-edge creation requires an existing Contact pair. New nodes therefore remain isolated and cannot bind the pair templates for transfer, attachment or deletion. The sole node-deletion template targets an original Structural pair, but its target retains Contact edges, so the entire atomic operation is inapplicable. The kernel supports node deletion in other fixtures; this generator cannot reach it.

Across the retained corpus, the scan found **4,183 births, zero deaths and a maximum of 72 live nodes**. Every observed world preserved the Contact ring, restricted Structural endpoints to original ring pairs, kept newborn matter/activation at zero, and satisfied the allocator/matter bound. All detector proposals contained only original nodes; all tracks had zero node births/deaths and no node turnover. Births were resource-funded by original nodes; the new nodes themselves were unfunded. Unary state changes on newborns remain possible.

| Generator template | Committed events |
| --- | ---: |
| SetState | 731,282 |
| AddState | 914,099 |
| Burn | 3,472 |
| Contact-pair Transfer | 620 |
| CreateNode | 4,183 |
| Contact-pair CreateEdge | 1,051 |
| DeleteEdge | 1,047 |
| DeleteEdge + DeleteNode | 0 |

All eight templates occur among the 118 generated laws, including 121 deletion-template rule slots. Zero committed node deletions therefore has a source-level explanation beyond simply not drawing that template. Structural-edge recycling among original nodes remains reachable and observed. These counts do not establish maintenance.

The frozen activity definition excludes resource-only changes. A birth credits its newborn singleton, not the funding account; subsequent unary changes remain singleton activity. With a minimum proposal size of two, neither estimator can include a newborn. This confines detected organization to the original eight nodes. It does **not** prove active persistence impossible on their state/edge dynamics. The finite scan corroborates the source argument; it is not formal universal verification, and changing templates or activity credit requires a new versioned contract.

## All detector disagreements retained

Saved Boolean track gates were recomputed from the original metrics at unchanged thresholds. All matched. Full per-slot summaries and every supported track in a disagreement are published in [slot diagnoses](evidence/p01d-001/slot_diagnoses.json) and [inconclusive cases](evidence/p01d-001/inconclusive_cases.json).

| Complete-horizon estimator outcome | States |
| --- | ---: |
| Neither supported | 436 |
| Connected supported, interaction unsupported | 31 |
| Interaction supported, connected unsupported | 2 |
| Both supported | 0 |

The one censored prefix had neither estimator supported, but retains no full-horizon AP endpoint. The complete-horizon labels remain 436 `not_supported`, 33 `inconclusive`, zero `supported`.

For the 31 connected-only cells, 23 had no eligible interaction proposals in any sample. The remaining eight had ten interaction tracks in total, each spanning only two epochs against the registered eight-epoch minimum. Four of these tracks also failed the active-fraction gate. These are overlapping failed conditions, not separate causal attributions. There were 35 connected supported tracks across these 31 cells; track counts are not state counts.

The two opposite-direction cells share law 3025:

- Slot 102 / state 2: the interaction track on nodes 5 and 6 persisted from sample 5 to 1,000 with 995 active epochs. The connected track lasted 1,000 epochs, but node 0 in its accumulated members never became active; its only failed gate was `inactive_members`.
- Slot 103 / state 3: the interaction track on nodes 0 and 7 lasted from sample 1 to 1,000 with 999 active epochs. The connected estimator had 1,000 tracks, each with zero duration and inactive members, 501 empty samples, and 501 excluded-large component observations. These counts describe structural fragmentation and size exclusions; they do not authorize accepting the interaction estimate alone.

No disagreement was resolved by selecting a preferred estimator. The audit also retained empty samples and excluded components throughout the corpus. It does not calibrate detector sensitivity or specificity, infer causal necessity, or assess maintenance.

## Verification cost from existing receipts

| Leaf stage | Summed recorded process CPU |
| --- | ---: |
| Generator | 0.976079 s |
| Native worker | 196.430159 s |
| Rust report | 347.382660 s |
| Independent Python audit | 2,189.183567 s |
| All leaf stages | 2,733.972465 s |

Python audit used **80.073% of recorded leaf CPU**. Guard self CPU summed to 232.146499 s. Guard-plus-reaped-child observations summed to 3,305.076605 s; subtracting guard self and leaf CPU gives 338.957641 s of inferred reaped nonleaf CPU at those boundaries. A further 200.960351 s separates that sum from the authoritative sealed aggregate of 3,506.036956 s. These differences are not an exact exclusive parent or `ps` profile: boundaries and cleanup differ. Original ceilings, censoring and launch-reserve accounting remain authoritative.

Inspection of the frozen Python call graph identifies repeated work: `pilot_reporting.verify` calls `pilot.verify_trace`, which checks every native epoch via `audit.verify_case`; it then calls `audit_integration.analyze_environment`, whose `activity` path repeats `audit.verify_case` and applies committed events once more to recover activity. Thus the source implies two checked candidate/scheduler replays and three committed-event applications per retained epoch, in addition to candidate-preparation work. This is a call-graph inference, not sampled runtime profiling or a measured speedup. The next candidate must preserve every independent check while producing activity during the checked replay.

## Closure and next gate

The [closure receipt](p01_closure.json) marks P01 consumed and closed. Execution/accounting/replay passed; feasibility of completing all 512 horizons within its budget was not demonstrated, and no full-horizon AP support was established. The original 469 complete horizons, one censored prefix, 42 unstarted slots, negative labels and inconclusive labels remain immutable. Do not resume, reroll, repeat or enlarge that registration. No new world run or E01 is admitted.

The next bounded task is [P01e: offline verifier equivalence/cost preflight](p01e_protocol.json). Implement a separate Python verifier that emits activity during its independent checked replay. Before execution, freeze its implementation, validator and input hashes. Use the fixed 112 native and 96 environment integration cases plus eight named existing P01 slots, including censored slot 177. Require exact full records/endpoints, applicable corruption rejection and at least 20% lower summed leaf CPU on the fixed paired panel, under the registered resource limits. The panel is post-hoc engineering evidence, not a representative speed estimate. The candidate and benchmark have not been implemented or run in P01d.

Thirteen Python regression tests passed, including four malformed-record/gate tests for this diagnostic. Their [test log](evidence/p01d-001/tests.txt) was produced outside the completed diagnostic bundle. [Publication context](evidence/p01d-001/publication_context.json) binds that log and these later closure/protocol documents without changing the original diagnostic inventory. No Rust, generator or detector semantics changed.
