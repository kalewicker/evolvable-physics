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

Implementation resumed on 2026-10-19 at the user’s request after publication. Current P00g admission is recorded in `docs/p00g_findings.md` and `docs/evidence/p00g-001/p00g_admission_audit.json`. P00 is admitted only for bounded engineering profiles and disclosed fixture panels. P01 requires its registered generator, profiling/budget and run-limit readiness work before execution. Scientific status remains untested. Do not start unregistered experiments merely because the project is opened.

Keep versioned profiles, detector thresholds, registered denominators, inconclusive classifications, negative outcomes, independent replay, and original receipts intact. Record a new protocol version when changing a frozen scientific contract. Raw evidence belongs in ignored `artifacts/` paths; public receipts belong in `docs/evidence/`.
