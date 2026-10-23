# Project instructions

## Repository scope

Work in this standalone `evolvable-physics` repository. The local directory may be named `causal-alife`; its parent Playground repository contains unrelated projects and must never be staged or pushed as part of this project.

## End-of-turn workflow

The user explicitly requested on 2026-10-19: at the end of every future project turn, commit and push the changes.

Before the final response for a turn that changes project files:

1. Run the checks appropriate to those changes; preserve failed scientific gates and their original criteria.
2. Inspect Git status and the staged diff. Include all intended source, documentation, protocol, and test changes; exclude secrets, machine-local settings, build products, caches, and raw generated evidence.
3. Commit with a descriptive message and push the current project branch to its configured GitHub upstream.
4. Verify a clean project working tree and that the remote branch points to the committed HEAD. Mention the commit/push outcome in the final response.

Do not create empty commits for a read-only turn. If push fails or requires user action, report that explicitly; do not claim synchronization. Never force-push or rewrite published history unless the user specifically authorizes it.

## Research status

Implementation resumed on 2026-10-19 at the user’s request after publication. Current P00g admission is recorded in `docs/p00g_findings.md` and `docs/evidence/p00g-001/p00g_admission_audit.json`. P00 is admitted only for bounded engineering profiles and disclosed fixture panels. P01a has completed a registered 64-run generator/cost preflight; see `docs/p01a_findings.md`. P01b registers the full pilot budgets and sampled memory policy and verifies frozen detector reporting; see `docs/p01b_findings.md`. P01c implements and validates the sealed campaign runner; `docs/evidence/p01c-001/readiness_audit.json` admits the registered bounded P01 development pilot. The first full P01 development pilot has finished at its CPU launch-reserve check: 469 complete horizons, one censored prefix and 42 unstarted slots out of 512; see `docs/p01_findings.md` and `docs/evidence/p01-001/campaign_audit.json`. It found 436 not_supported and 33 inconclusive full-horizon AP labels, zero supported. This registration is consumed: do not resume unstarted slots, extend the capped run, reroll, repeat it or expand budgets. P01d has completed read-only diagnosis and closed the consumed protocol; see `docs/p01d_findings.md` and `docs/p01_closure.json`. Generator v1 cannot attach/fund/delete newborns or execute node deletion; this is not a kernel limitation or an AP impossibility proof. All 33 disagreements remain inconclusive. P01e is complete and consumed: the fixed panel matched exactly, all 11 corruptions were rejected, and paired child CPU fell 50.174%. The frozen receipt auditor failed float-sum equality; preserve that failure and the disclosed post-hoc Decimal audit, which confirms gate arithmetic without a rerun. See `docs/p01e_findings.md` and `docs/p01e_admission.json`. The new adapter is separate; the original frozen campaign pipeline is unchanged. Do not repeat timing, tune against the consumed panel or revise its freeze. P01f is complete and consumed: all 48 fixed authored witness cases passed with exact Reference/Indexed agreement and full independent Python replay/activity/detection checks. Per matcher, 44 horizons completed and four expected whole-epoch size rejections preserved full state; 28 births and 16 deaths were verified. See `docs/p01f_execution_findings.md` and `docs/p01f_reachability_admission.json`. The implementation/execution freeze and admission were committed/pushed before the single batch; preserve both it and the original registration, all cases and receipts. No retry, input/threshold repair, replacement or repeated panel is admitted. This is authored-fixture reachability only. P01g execution is complete and consumed. All 64 registered trajectories (16 laws × four states × 128 epochs) and all 256 stages passed independent generation/replay/detector/receipt checks with no overshoot. The engineering gate passed, but the mechanism continuation gate failed: 10 distinct tables produced visible funded births, zero produced same-newborn recycling loops (minimum one). There were 142 births, 104 visible newborns, zero additional Structural funding/descendant construction/recycling, and AP labels 62 not_supported / two inconclusive / zero supported. Both inconclusive cases are law 4007, states 1 and 3; preserve their disagreement. See `docs/p01g_execution_findings.md` and `docs/p01g_closure.json`. The execution freeze/admission was committed and pushed before the single batch; keep it, the original registration, samplers, gate criteria and all receipts unchanged. Do not rerun, select favorable laws for longer runs, change thresholds or expand sampling. P01h read-only diagnosis is complete: all 64 cases, 8,192 pre-epoch worlds and 7,453 events were reconciled without sampler calls, transition application or subprocesses. None of the nine same-law birth/Structural-funding pairs or 15 birth/recycling pairs has compatible ordered donor/child kinds. All 16,598 funding and 18,610 recycling exposures failed kind checks; all 22,797 descendant-birth exposures lacked matter and activation. Zero applicable candidates for these mechanisms rules out scheduler loss as their observed barrier. See `docs/p01h_findings.md`, `docs/p01h_source_argument.md` and the independent record audit. The conditional source argument excludes those mechanisms for these exact tables under the frozen initial contract, not for the whole v2 sampler or kernel. Keep all P01g criteria/negative results and both inconclusive labels unchanged. Next is design-only review of type-coherent constructive rule generation, explicitly preserving child-as-donor reachability and disclosing changed sampling priors/authored bias. No new generator implementation, law repair/filter/reroll, sampled law, witness execution, new environment, threshold change or E01 is admitted by the diagnosis. Any later experiment requires a separately justified registration. P01i design review is complete: the proposed v3 contract uses an unrestricted shared per-law donor-to-child kind map, retaining independently keyed forms/donor kinds/states/routes. All 27 maps and eight birth-donor subsets passed finite-algebra checks, including child-as-donor counterexamples and independent graph closure checks; no law was constructed or world advanced. See `docs/generator_v3_design.md` and `docs/p01i_findings.md`. This is an intentionally altered prior, not an implemented/admitted sampler. Next register literal-field implementation-readiness checks for separate Rust/Python adapters before implementation, including all forms/routes, cross-slot/state map reuse, missing-body/state/material negatives. No hash sampler calls, candidates, dynamics, witness runs or new sampling panel are admitted by that step. Preserve the consumed panels and all original outcomes. P01j implementation-readiness registration is complete: `docs/p01j_protocol.json`, `docs/p01j_literal_fields.json` and `docs/p01j_registration_freeze.json` fix 11,664 rule-field cases, 972 assembly cases, eight local barrier cases, twelve invalid inputs and six ignored-field groups. Static review passed; nine registration tests passed both normally and with Python optimization. No adapter or world was executed. Next implement only the registered separate literal-field Rust/Python adapters and fixed validator, without editing frozen source paths or Cargo files. Literal field construction/testing is admitted after this registration is committed/pushed; actual hash sampler implementation/calls, candidate enumeration, transitions, witnesses and new sampling remain unadmitted. Retain every engineering validation attempt; fix implementation defects against the same frozen panel rather than changing inputs/criteria. See `docs/p01j_findings.md`. P01j literal-field implementation/readiness is now complete: separate Rust/Python adapters passed all 12,671 fixed records, with exact output/trace equality, independent operation/accounting invariants and map reuse across all 243 four-initial groups. Two Rust, nine Python readiness and two receipt-audit regressions passed, as did Clippy/release build. Preserve the initial Rust compilation failure and source snapshot; its callback lifetime fix preceded the successful full panel. The later read-only receipt audit verified all registered inputs and custody without adapter execution. See `docs/p01j_readiness_findings.md` and `docs/p01j_readiness_admission.json`. The actual hash sampler remains unimplemented and unadmitted. Next separately register its bounded implementation and unfiltered static census/equivalence panel, including source/field-key checks, per-table necessary paths, budgets/failure policy and execution freeze before any hash draw. No filtering/repair, world trajectories, changed environment/detector gates or E01 is admitted. Literal-field engineering repairs may repeat only the same frozen panel into a new directory with all failures retained. P01k keyed-sampler/static-census registration is complete: `docs/p01k_protocol.json` fixes 32 uninspected proposals 5000..5031 × four initial IDs, 128 environments and zero world epochs. Static review and nine tests passed; 149 registration file identities and all 363 preceding public receipts matched. No actual keyed sampler or call was implemented/executed this turn. See `docs/p01k_registration.md` and `docs/p01k_findings.md`. After this registration is committed/pushed, next implement the registered new sampler/runner/static-report/auditor paths, without editing frozen adapters, Cargo files or old source paths. Before a separately committed/pushed execution freeze/admission, tests may use unhashed serialization, literal digest-prefix arithmetic, injected fields and synthetic records only; no v3 namespace-keyed hash evaluation on any proposal is admitted, including tests or audit helpers. Freeze the full source/dependency/tool/binary/input closure and exact output path before the future single sampled static attempt. Keep every one of the 32 law cells and 128 environments, all negatives/duplicates and explicit missingness; no repair/filter/reroll, chemistry-count admission threshold, favorable-law subset, resumed/extended sample, world transitions, new environment/detector gates or E01. Behavioral metrics are null/not_executed, never inferred from static paths. P01k sampler/runner/static-report/auditor implementation is complete with literal/mock readiness: four Rust and ten Python tests, Clippy/release build, all 12,671 frozen literal responses and 972 additional recorded mock assemblies passed. The 112,752 recorded fields per implementation use fake prefix metadata, not SHA results. Tests include the full 128-cell pipeline through injected stages and prohibit SHA evaluation of v3 message bytes. Preserve joint donor-state intersection: two pairwise wildcard intersections do not prove a common state for a joined motif. All 149 frozen identities and 366 previous public receipts matched. See `docs/p01k_implementation_findings.md` and `docs/p01k_implementation_readiness.json`. No keyed source, sampled census, live RSS-watchdog integration or world execution has run. Next prepare/verify the full execution closure and exact output admission, commit/push it before any keyed call, then execute and audit only the one registered static attempt. Do not infer actual sampler equality or favorable route counts from mock metadata. All original budgets, failure/no-retry/no-filter rules and scientific limits remain intact. P01k execution freeze/admission is prepared and identity-checked: 172 project/input/build-receipt files, 3,088 dependencies, four tools and the byte-identical tested generator-v3 binary. See `docs/p01k_execution_freeze_notes.md`. Commit/push that freeze/admission before the first keyed evaluation. Only the exact single static census command/output `python3 scripts/p01k_census.py artifacts/p01k-001` is admitted after that gate; all 128 planned cells must exist before any draw. Probe memory-sampling capability before creating the attempt directory; a capability failure before directory creation makes no keyed call. Once the sampled attempt starts, preserve and seal its outcomes with no retry, resumption, extension, repaired input or law selection. Post-seal receipt audit must use file hashes only. No world transitions, detectors, new environment or E01 are admitted. P01k sampled static execution is complete and consumed. Freeze/admission commit `bd8e97d` was pushed before any keyed evaluation. A sandbox ps probe failed before directory creation/draws and is retained; the approved single attempt completed all 128 initial environments (32 distinct tables) and all 258 stages. Independent output/static, post-seal inventory and Decimal cost audits passed, with 29.301340 s wall, 26.407958 s CPU, 204,951,841 bytes and no overshoot. There are kind-compatible birth/funding pairs in four tables, birth/recycling in nine, and child-donor matches in fifteen. Joined type-only motifs occur in two tables, material-bearing in one; none has all immediate state predicates aligned. This is descriptive static evidence, not a chemistry gate failure or a dynamical impossibility result. State writers/phase sequencing remain unresolved. See `docs/p01k_execution_findings.md` and `docs/p01k_closure.json`. The original registration/freeze/admission, seal, all cells and old P01g gate/labels remain immutable; do not retry/resume/extend/replace/repair or select favorable laws for evolution. P01l read-only state/resource review is complete. Plan/freeze commit 0561c90 was pushed before diagnosis. All 32 tables and 128 initial records, 163 body combinations and original seal identities passed independent state/topology/resource checks; eight tests passed, including 924 invented interval/graph comparisons. Sequential unary states recover one joined motif but its funding moves zero matter. No material/state-permitted funded descendant triple exists. The conditional source argument excludes newborn-as-parent first birth for these exact tables under frozen initial/topology/templates, not for the v3 sampler or kernel. See docs/p01l_findings.md, docs/p01l_source_argument.md and docs/p01l_closure.json. Keep original behavioral outcomes null/not_executed, not observed zero. P01m design-only review is complete. Recommend the proposed v4 shared per-kind exact constructive-state map plus matter=1 Structural funding, retaining the unrestricted type map, independent form/donor/route fields, eight slots, initial contract and all operation costs. This authors correlations and removes constructive wildcards; no bodies are inserted and no table success is guaranteed. All 59,049 type/state cases, 78,732 relabeling comparisons and 13,824 body-presence profiles passed; an independent saved-profile audit and three contract tests (six malformed cases) passed. Full per-kind birth/funding/recycling coverage of a three-kind cycle needs nine bodies and does not fit eight slots; this is a role-coverage limit, not general chemistry impossibility. See docs/generator_v4_design.md, docs/p01m_findings.md and docs/p01m_closure.json. No v4 generator, sampled law or world was constructed. P01n fixed literal-readiness registration is complete: docs/p01n_protocol.json and docs/p01n_literal_fields.json fix 6,561 constructive rules, 7,776 unchanged rules, 2,916 assemblies (729 map pairs times four initials), 395 ignored-field evaluations in 37 groups, 79 invalid inputs and 13 validator-only local-condition vectors. There are 17,727 adapter requests; rule/assembly traces require 17/119 records, totaling 597,448 successful field records per adapter. No adapter or native rule/world was constructed/executed. Static review and ten tests passed normally and with Python optimization; 220 registration files, 402 previous receipts and all 172 P01k frozen project files matched. See docs/p01n_registration.md, docs/p01n_findings.md and docs/p01n_closure.json. After this registration is committed/pushed, next implement only the separate literal-field Rust/Python v4 adapters, fixed validator and new readiness tests at registered paths without editing frozen Cargo files or old sources. Preserve all attempts and fix implementation against the exact same fixed panel, into fresh output directories. Enforce the 60-second/256-MiB combined-stream per-adapter caps and 300-second aggregate validation deadline, with full source/input/binary closure, independent output/accounting oracle, trace checks and failure receipts. The 13 local conditions are validator-only counterfactual/necessary-condition descriptors, not adapter barrier mode or native applicability. No hash sampler implementation/evaluation, new sampled panel, candidate/world execution, witness, repaired/selected historical input, environment/detector changes or E01 is admitted. Behavioral metrics remain null/not_executed and scientific status untested. Sampled RSS enforcement is not a hard instantaneous memory bound. Scientific status remains untested. Do not start unregistered experiments merely because the project is opened.

Keep versioned profiles, detector thresholds, registered denominators, inconclusive classifications, negative outcomes, independent replay, and original receipts intact. Record a new protocol version when changing a frozen scientific contract. Raw evidence belongs in ignored `artifacts/` paths; public receipts belong in `docs/evidence/`.

## Current next boundary after P01n readiness

P01n literal readiness is complete: 17,727 fixed requests and 597,448 field reads
per adapter passed full Rust/Python JSON, independent operation/accounting and
independently indexed input checks. All 729 four-initial groups, 37 probe groups,
79 invalid rejections and 13 validator-only conditions passed. Thirteen Python
regressions (normal and optimized), two Rust tests, Clippy and release build
passed. Retain the first failed test-filter run and all three build histories;
there was one complete readiness attempt, which passed. See
`docs/p01n_readiness_findings.md` and `docs/p01n_readiness_admission.json`.
All 220 registration source identities and 406 preceding public receipts matched.
The keyed v4 sampler remains unimplemented and unadmitted. Next separately
register its bounded implementation and unfiltered static census/equivalence
panel, including field keys, all cells, path reporting, budgets, failure policy
and execution closure before any keyed draw. No reroll, repair, filtering,
favorable historical law selection, world execution, changed environment or
detector gates, or E01 follows from literal readiness. Preserve all consumed
panels and negative/inconclusive outcomes. Behavioral outcomes remain
null/not_executed and scientific status untested.

## Current next boundary after P01o registration

P01o keyed-v4/static-census registration is complete. See docs/p01o_protocol.json,
docs/p01o_registration.md, docs/p01o_registration_freeze.json and
scripts/check_p01o_registration.py. The fixed future panel is proposals
6000..6031 × initials 0..3, 128 environments, zero epochs; 119 ordered field
records per cell, 15,232 per implementation, 6,208 unique addresses. Static
review and thirteen tests (normal and optimized) passed, with 235 frozen file
identities and 438 prior public receipts preserved. No keyed sampler or call
was implemented/executed. After this registration is committed/pushed, next
implement only the registered new sampler/runner/static-report/auditor paths
and new tests. Keep all frozen sources and Cargo files byte-identical. Tests
before execution admission must use unhashed serialization, literal prefix
arithmetic, injected fields and synthetic report/guard bookkeeping only; no v4
namespace-keyed SHA evaluation on any proposal, including audit helpers.
Require simultaneous donor-state intersection for joined bodies, ordered reads
of both maps and all raw fields, and no inference of behavior from static
correlations. Then freeze full sources/dependencies/tools/binaries/inputs and
commit/push a separate admission binding the exact output before the single
sampled static attempt. Preserve all 32 laws/128 cells, negatives, duplicates,
failures and missingness. No sampled retry/resumption/extension, repair/filter,
favorable-law selection, world transitions, environment/detector changes or
E01. P01g/P01k outcomes remain unchanged; scientific status stays untested.

## Current next boundary after P01o implementation readiness

The separate v4 samplers, runner, static report and independent auditor are
implemented. All 17,727 frozen literal responses and 2,916 recorded mock
assemblies passed full differential/operation/static checks; 347,004 fake-prefix
draw records per implementation were verified. Ten Python tests (normal and
optimized), four Rust tests, Clippy and release build passed. Preserve both
passing development attempts: final audit strictness/negative cases were added
between them, with identical inputs and binary. All 235 frozen identities and
443 preceding public receipts matched. See docs/p01o_implementation_findings.md
and docs/p01o_implementation_readiness.json. No keyed source, sampled census,
live sampled-RSS integration or world execution ran. Next verify/freeze full
sources, dependencies, tools, binaries and inputs and bind one exact fresh
output directory in a separate admission; commit/push before any v4 keyed call.
Keep the fixed 32-law/128-cell panel, budgets, stop/no-retry policy, complete
missingness and all historical negatives/inconclusives intact. No table repair,
filter/reroll, favorable-law selection, world transitions, environment/detector
changes or E01. Static authored coherence and mock equality do not establish
sampled equivalence or chemistry; scientific status remains untested.

## Current next boundary after P01o execution freeze

P01o execution freeze/admission is prepared and identity-checked. See
`docs/p01o_execution_freeze_notes.md`, `docs/p01o_execution_freeze.json` and
`docs/p01o_execution_admission.json`. The pre-execution review verified 740
project/input/receipt files, 3,088 dependency files, four tools, 466 prior public
receipts and the existing tested generator-v4 binary. Fresh Cargo metadata and
complete crate/Python/Rust dependency membership matched. Six new closure tests
passed normally and optimized; retain the initial temporary-directory alias
fixture failure and snapshots. No frozen implementation or gate changed.
Commit/push this freeze/admission before the first v4 keyed evaluation.
After that gate, only the exact single static census command/output
`python3 scripts/p01o_census.py artifacts/p01o-001` is admitted. Verify closure
and probe process/RSS accounting before directory creation; a capability failure
before creation makes no keyed call. Once started, write all 128 planned cells
before any sampler or independent hash-audit call and preserve/seal all outcomes.
No retry/resumption/extension, repaired input, replacement or favorable-law
selection. Post-seal receipt audit uses file hashes only. No sampled attempt or
keyed evaluation occurred in preparing the freeze. No world transitions,
detectors, environment change or E01 are admitted; scientific status untested.

## Current next boundary after P01o execution

P01o sampled static execution is complete and consumed. Execution-freeze commit
29d731e was pushed before keyed evaluation. The sandbox ps probe failed before
attempt-directory creation/draws and is retained; the approved run was the sole
sampled attempt. All 128 initial environments (32 distinct tables), 258 stages,
15,232 logical draws per implementation and 6,208 unique addresses passed exact
Rust/Python, independent output/static and later custody/Decimal-cost checks.
The original 5,127-entry inventory/seal is unchanged. Costs were 32.692696 s
wall, 29.066875 s CPU and 215,277,328 bytes, with no overshoot or missing cell.
There are seven kind/state/material-compatible birth/funding pairs in six
tables, eight birth/recycle matches in five, and 26 child-donor matches in ten.
One joined motif in one table has all immediate type/state/material predicates
aligned. These constructive correlations are authored, with no chemistry gate
or dynamic evidence. See docs/p01o_execution_findings.md and docs/p01o_closure.json.
Preserve original registration/freeze/admission, all cells and seal; no sampled
retry/resume/extension/replacement/repair or favorable-law selection. Next
separately preregister read-only resource/state/topology questions and source
identities across all 32 tables/128 initial records before diagnosis. No keyed
message reevaluation, new sampled panel, world execution, environment/detector
changes or E01. Behavioral outcomes remain null/not_executed and scientific
status untested; all P01g/P01k negatives/inconclusives remain unchanged.

## Current next boundary after P01p review registration

P01p post-hoc read-only resource/state/topology review registration is complete.
See docs/p01p_analysis_plan.md, docs/p01p_protocol.json,
docs/p01p_analysis_freeze.json and docs/p01p_registration_findings.md. Static
review and eight tests (normal and optimized) passed: 260 registration source
files, 264 analysis inputs, original 5,127-entry inventory/seal and 493 previous
public receipts matched. No retained-body diagnosis, keyed call or world
transition occurred in registration. After plan/freeze commit/push, next
implement only scripts/review_p01p.py, scripts/audit_p01p.py and scripts/test_p01p.py
at the new paths, test invented controls before diagnosis, then run/audit only
this fixed all-32-table/128-initial review. Keep old source/Cargo paths unchanged.
Retain all failed attempts and identities, fixing implementation against this
same plan into a fresh directory; never repair laws or original seals.
The plan distinguishes cleanup6 (edge refund, orphan grandchild survives) from
cleanup7 (leaf grandchild refunded/deleted); a parent may become a leaf without
deleting its descendant node if the outgoing edge is removed. Retain both
routes, phase order, distinct node roles with possibly equal kinds, four
conditional ledgers and all incompatible/absent combinations. The 924 future
state-closure comparisons are planned, not already executed. Cooperative
per-tool limits are 120 seconds/128 MiB emitted bytes, with failure receipts and
no hard RSS/time claim. No process creation, sampler/adapter/matcher/interpreter
imports, keyed reevaluation, favorable-law selection, new sampling, world runs,
environment/detector changes or E01. Behavioral outcomes remain null/not_executed
and scientific status untested; preserve all consumed P01g/P01k/P01o outcomes.

## Current next boundary after P01p review

P01p registered all-table review and independent audit are complete. The pushed
plan commit 8acdfcd preceded diagnosis. All 32 laws, 128 initial records and 170
combinations passed independent state/ledger/topology/custody checks; all
negative/absent groups remain. Thirteen invented tests passed normally and
optimized, including 924 interval/five-region comparisons and all registered
controls. There was one passing reviewer attempt and one passing independent
audit, with no implementation/input repair. Review/audit inventories have
538/534 entries; original P01o seal is unchanged. See docs/p01p_findings.md and
docs/p01p_closure.json. One cleanup7 branch is permitted by abstraction in
law 6011, reusing birth 1/recycle 7 with funding 2, and all four saved initial seed
checks pass. Its conditional ledger restores P's matter but spends four
activation, with both descendants removed; it is not observed reproduction.
No cleanup6 branch passes these retained local checks; preserve the orphan
versus refund distinction and all other table results. No keyed evaluation,
world transition, candidate enumeration or process launch occurred in review.
Next separately justify/register a bounded unfiltered dynamical mechanism
assay using all 32 laws/all 128 saved environments without keyed reevaluation;
fix evidence, controls, horizons, gates, budgets and failure policy before any
implementation/execution. No favorable-table trajectory, generator repair,
rerun of the consumed census, environment/detector change or E01 is admitted.
Behavioral outcomes stay null/not_executed and scientific status untested;
all P01g/P01k/P01o outcomes and inconclusives remain unchanged.


## Current next boundary after P01q registration

P01q is registered for first dynamics on all32 saved v4 laws/all128 environments,
128epochs each, without keyed reevaluation or input changes. See
`docs/p01q_protocol.json`, `docs/p01q_registration.md`,
`docs/p01q_registration_freeze.json` and `docs/p01q_findings.md`.
Eight registration tests passed normally/optimized; 271 frozen source files,
264 inputs, 518 prior receipts and the original5127-entry inventory/seal matched.
No new retained-body parsing, candidates or world transitions occurred.
After commit/push, implement only the five registered new paths and validate
all16 invented observation/mock pipeline control groups. Do not edit frozen
Rust/Cargo/Python source, environment or detector paths. No concrete transitions
or candidates, including fixture tests, until a separately committed/pushed
full execution freeze/admission. Preserve every implementation/test failure.
The future single artifacts/p01q-001 attempt uses unchanged P01g mechanism gate,
secondary funding/descendant/cleanup observations, 1200s wall/600s CPU/2GiB caps
and64MiB terminal reserve. Directory creation consumes the attempt; no retry,
resumption, missing-cell completion, repair or favorable-law selection.
Preserve null/not_executed outcomes until observed, all historical negatives and
inconclusives, and original seals. Scientific status untested; no E01.

## Current next boundary after P01q implementation readiness

The five P01q paths are implemented; registration commit d141b61 preceded them.
See docs/p01q_implementation_findings.md and docs/p01q_implementation_readiness.json.
Seventeen invented/mock tests pass, covering all16 control groups and a complete
128-cell/384-stage mock pipeline. Four optimized-Python entry points reject
assertion-disabled execution. Both passing build snapshots are retained; no
failed test, keyed call, candidate enumeration or world transition occurred.
All271 registration files,264 inputs,523 previous public receipts and the original
5127-entry P01o inventory/seal matched. Separate event observations agree on both
cleanup routes, exact identities, branch phase balances and activation burns.
Next prepare/verify full execution closure and separate admission, including
exact membership, tools, worker/report binaries and all saved inputs. Commit/push
that closure before any world transition, including fixture tests. Live watchdog
integration and actual pipeline costs remain untested. The single future attempt
is artifacts/p01q-001; no resume, retry, replacement, repaired input, favorable
subset or extended horizon. Preserve all historical outcomes, null/not_executed
v4 behavior and untested scientific status. E01 remains unauthorized.

## Current next boundary after P01q execution freeze

P01q full execution freeze/admission is prepared and checked. See
`docs/p01q_execution_freeze_notes.md`, `docs/p01q_execution_freeze.json` and
`docs/p01q_execution_admission.json`. Read-only review and the runner's closure
check passed: 1,107 source/input files, 3,846 dependencies, four tools, 23 directory
memberships and 533 previous receipts. Worker/report binaries match P01g exactly.
Six new closure tests passed normally/optimized; no test failure or world run.
All registered inputs, implementation hashes, prior dependencies and seals remain
unchanged. Existing Python caches are additionally pinned; disable bytecode writes.
Commit/push this freeze/admission before the first transition. After that gate,
only `PYTHONDONTWRITEBYTECODE=1 python3 scripts/p01q_campaign.py artifacts/p01q-001`
is admitted. Probe closure/process/RSS before directory creation; creation consumes
the attempt. All128 slots precede worker launch. Keep every outcome and cost,
then audit saved receipts without replaying worlds or keyed sampling. No retry,
resume, missing-cell completion, repaired/replaced input, favorable-law selection,
extended horizon or relaxed gate. Live watchdog behavior and real pipeline costs
remain untested until execution. Scientific status untested; E01 unauthorized.
