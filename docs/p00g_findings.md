# P00g logging equivalence and complete-environment analysis findings

Date: 2026-10-19. Execution and independent verification: passed. **P00 admitted for the bounded engineering profiles and disclosed fixture panels.** Scientific status: untested. P01 execution readiness: incomplete.

## Outcome

Closed the two named P00f admission blockers. Full and disabled-output execution preserve identical semantic state, and the versioned environment adapter validates complete environment epochs before extracting native activity. The original frozen detector source and thresholds remain unchanged.

Current evidence: [manifest](evidence/p00g-001/manifest.json), [integration audit](evidence/p00g-001/integration_audit.json), [P00g admission audit](evidence/p00g-001/p00g_admission_audit.json), [test log](evidence/p00g-001/tests.txt), and [checksums](evidence/p00g-001/checksums.json). The full raw bundle is local at `artifacts/p00g-001/`; published receipts retain their original bytes. Historical P00f assessments remain included as the prior baseline, rather than being rewritten.

[Registration](p00g_registration.md), [protocol](p00g_protocol.json), [source freeze](p00g_freeze.json), and [admission addendum](p00g_admission_addendum.json) specify the matrix and acceptance conditions. No threshold, expected label, seed or scientific criterion changed in response to results.

## Fixed denominators and results

- All 37 Rust test entries passed (36 substantive tests plus the existing recovery child-process helper). Formatting and Clippy with warnings denied passed.
- Logging equivalence: 4,256 paired epochs across 112 legacy native runs, 64 legacy environment runs, 96 integrated runs, 80 maintenance arms, and 16 two-epoch warmups.
- Complete-environment analysis: six families × 16 seeds × 12 epochs = 96 primary runs / 1,152 epochs; 976 native events independently replayed.
- Environment-aware maintenance: 16 sources × five arms × 12 epochs = 80 arms / 960 epochs, plus 32 warmup epochs.
- The versioned observation engine matches every field of all 144 frozen calibration outputs and all 176 transfer-panel outputs: 320 complete detector comparisons.
- All six prior emitted suite files remain byte-identical to P00f, including the P00e detector and P00f transfer panels.

Per run, every result held for all 16 seeds:

| Family | Native events | AP | Control interpretation |
|---|---:|---|---|
| Driven pair | 12 | supported | Native joint state changes in a stable two-node structural component |
| External resource flux | 0 | not_supported | Environment supply/transport/extraction earns no native activity credit |
| Unfunded pair | 1 | not_supported | One initially funded firing does not pass the fixed activity horizon |
| No-op state pair | 12 | not_supported | State no-ops and resource burns do not earn physical activity credit |
| Mixed islands | 12 | supported for native pair | External-only component has no activity credit and cannot borrow from the active component |
| Driven renewal | 24 | supported | Aging/removal/repair persists under explicit supply with exact accounting |

The renewal maintenance occupancy vector is unchanged: baseline/sham/target/unrelated/rescue = [8,8,0,8,8]. Thus loss of the physical motif, not merely activity cessation, remains the controlled maintenance endpoint. Supplies are matched at both anchors; no environmental bookkeeping is substituted for material turnover or native repair.

## Logging semantics

Disabled mode returns no exported frame and avoids exported event/epoch histories, their parent lists and output-only digests. It retains candidate/footprint work needed for physics, atomic staging, semantic event IDs, writer metadata, allocator continuation, all resources/ledgers, and schedule/time state. This is an output control, not a different physics or a no-provenance model. No speedup claim is made.

Full state equality is checked after every paired epoch. Independent Python replay verifies the logged trajectories and all disabled-mode prefix digests. Direct Rust tests require None in disabled mode and compare errors and complete rollback on specified native/environment failure paths.

Fresh processes continue checkpoints with full, quiet and quiet-to-full modes for every integrated family, plus a native quiet checkpoint continuation. All final checkpoint payloads match uninterrupted full execution exactly. No source checkpoint is overwritten.

## Environment analysis and evidence

The adapter verifies each complete Environment/Epoch with reference execution, including channel order, ledgers, writer provenance and prepared native state. Native activity is computed only from actual native type/state/existence/structural-incidence changes after that validated environment phase. External-only resource movements, event counts, provenance updates and rule availability earn no activity credit.

The frozen engine remains in `src/analysis.rs`; `src/environment_analysis.rs` is a versioned observation engine and adapter. Full output equivalence on the 320 old cases detects drift in proposals, tracks, ambiguity, births/deaths, similarity, estimator disagreements and agreement pairs.

The independent Python checker reconstructs every new initial world, replays all environment and native transitions, recomputes all detector outputs, validates intervention receipts and exact physical occupancy, and checks logging prefix equality. Eight altered-evidence controls were rejected: prepared state, environment records, ledgers, disabled-mode digest, external activity credit, native records, occupancy and rescue chain. A fresh Python process repeated the integrated audit.

## Admission decision and limits

`p00g_admission_audit.json` applies the registered addendum to the unchanged P00f requirement inventory. Both named blockers have evidence-backed support; no P00 blocking requirements remain. The P00f audit is preserved as historical baseline evidence. The current manifest names the P00g admission receipt and marks `p00_complete: true`.

This is bounded engineering admission of the implemented closed/driven profiles and disclosed 2–6 node AP/maintenance assays. It does not demonstrate arbitrary-world detector sensitivity, biological individuality, spontaneous reproduction, heritable variation, adaptation, open-endedness, or useful search. Existing size, identity, coactivity and power-loss/event-store recovery limits remain explicit. Logging-disabled intervals still require deterministic replay to recover missing event evidence for analysis.

P01 has not run. Its registered rule generator, profiling/cost budget, and total-event/wall-clock/memory run limits are still missing or partial. Those are the next execution-readiness tasks; P00 admission alone does not admit an unbounded or unregistered pilot.

## Reproduce

From the project directory, with pinned dependencies available, use a new destination:

```sh
python3 scripts/validate.py artifacts/p00g-new-run
```

To audit the retained complete raw evidence locally:

```sh
python3 scripts/audit_integration.py artifacts/p00g-001/integration/suite.json
```

The CLI also supports `resume-quiet` and `environment-resume-quiet` for output-disabled checkpoint continuation. See [semantics](p00g_semantics.md) for their limits.
