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

Implementation resumed on 2026-10-19 at the user’s request after publication. Current P00g admission is recorded in `docs/p00g_findings.md` and `docs/evidence/p00g-001/p00g_admission_audit.json`. P00 is admitted only for bounded engineering profiles and disclosed fixture panels. P01a has completed a registered 64-run generator/cost preflight; see `docs/p01a_findings.md`. P01b registers the full pilot budgets and sampled memory policy and verifies frozen detector reporting; see `docs/p01b_findings.md`. P01c implements and validates the sealed campaign runner; `docs/evidence/p01c-001/readiness_audit.json` admits the registered bounded P01 development pilot. The first full P01 development pilot has finished at its CPU launch-reserve check: 469 complete horizons, one censored prefix and 42 unstarted slots out of 512; see `docs/p01_findings.md` and `docs/evidence/p01-001/campaign_audit.json`. It found 436 not_supported and 33 inconclusive full-horizon AP labels, zero supported. This registration is consumed: do not resume unstarted slots, extend the capped run, reroll, repeat it or expand budgets. P01d has completed read-only diagnosis and closed the consumed protocol; see `docs/p01d_findings.md` and `docs/p01_closure.json`. Generator v1 cannot attach/fund/delete newborns or execute node deletion; this is not a kernel limitation or an AP impossibility proof. All 33 disagreements remain inconclusive. P01e is complete and consumed: the fixed panel matched exactly, all 11 corruptions were rejected, and paired child CPU fell 50.174%. The frozen receipt auditor failed float-sum equality; preserve that failure and the disclosed post-hoc Decimal audit, which confirms gate arithmetic without a rerun. See `docs/p01e_findings.md` and `docs/p01e_admission.json`. The new adapter is separate; the original frozen campaign pipeline is unchanged. Do not repeat timing, tune against the consumed panel or revise its freeze. Next design and register generator-v2 reachability witnesses for funded attached birth and created-member deletion/recycling, including fixed positive/negative expectations and a source-level argument before any native fixture execution or sampling. Preserve every check and original contract; do not evolve new worlds or admit E01. Sampled RSS enforcement is not a hard instantaneous memory bound. Scientific status remains untested. Do not start unregistered experiments merely because the project is opened.

Keep versioned profiles, detector thresholds, registered denominators, inconclusive classifications, negative outcomes, independent replay, and original receipts intact. Record a new protocol version when changing a frozen scientific contract. Raw evidence belongs in ignored `artifacts/` paths; public receipts belong in `docs/evidence/`.
