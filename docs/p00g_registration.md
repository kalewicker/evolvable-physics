# P00g logging equivalence and complete-environment analysis

Registered 2026-10-19 before the sealed matrix run. The P00e detector protocol, archived source, P00f panel and original admission requirements remain frozen. This stage closes the two named P00f blockers using versioned additions and a recorded admission addendum.

## Observer mode

`TraceMode::Full` preserves the existing frame format. `TraceMode::Disabled` runs the same candidate selection and atomic commit, retains world state, allocators, event IDs, writer metadata and checkpoint identity, but does not construct/export Frame/Event/Epoch records or compute their output-only digests and parent lists. It is not a provenance-free physics model. No logging setting is stored in a checkpoint because it is not semantic state. Returning None in disabled mode is required.

Both modes must have identical full state after every epoch, identical errors and complete rollback on registered rejection paths, and exact continuation when switching modes. No speedup claim is registered.

## Versioned analysis adapter

`p00g-environment-analysis-v1` verifies each supplied Environment/Epoch against reference environment execution. It extracts actual native state/type/existence/structural-incidence changes from the validated post-environment/pre-native state and feeds a versioned observation engine with the same P00e thresholds and data types. Environment-only supply, extraction, transport and ledger/provenance changes receive no native activity credit.

The frozen analysis source remains untouched. The observation engine's full native outputs must equal the frozen detector for all 144 P00e cases and all 176 P00f transfer cases, including proposals, tracks, births/deaths, ambiguity, disagreement and candidate pairing. These comparisons are an explicit regression contract; reuse of thresholds alone is insufficient.

## Fixed matrix

`p00g_protocol.json` fixes six families × seeds 0–15 × twelve epochs = 96 primary runs / 1,152 epochs. The fixture generator and independent Python reconstruction must agree exactly.

- driven_pair: environmental supply funds joint physical state changes in a structural pair; AP supported.
- external_flux: supply, transport between the two structural members and extraction operate every epoch; native rules are absent. AP not_supported.
- unfunded_pair: one initial funded firing followed by exhaustion. AP not_supported over the fixed horizon.
- no_op_pair: funded native rule firings retain both state values and burn activation. Event/resource activity alone must not earn AP.
- mixed_islands: an active native pair and an external-only pair coexist in disconnected components. Only the native pair receives activity credit.
- driven_renewal: the earlier aging/removal/repair fixture runs with explicit activation supply at both matched anchors. AP and repeated material turnover remain supported.

Driven renewal additionally uses sixteen source warmups (two epochs each) and five twelve-epoch environment-aware arms each: 80 maintenance arms / 960 epochs. The physical occupancy vector must remain [8,8,0,8,8] with the original topology/type fingerprint and matched baseline/sham/target/unrelated/rescue edits. No state-based endpoint substitution is allowed.

Logging comparisons cover 112 legacy native runs, 64 legacy environment runs, the 96 primary runs, 80 maintenance arms, and 16 warmups: 4,256 paired epochs in 368 segments. Disabled prefixes must equal all fields of logged execution. Existing reference/indexed comparisons remain in place.

## Verification and admission

Python reconstructs the new fixtures, validates every environment phase, independently replays native events and analysis, verifies quiet-mode state digests and physical maintenance endpoints. Adversarial checks reject altered prepared states, environment actions/ledgers, mode digests, external activity credit, native records and controlled occupancy. Fresh processes resume checkpoints in quiet/full/mixed modes.

The updated admission receipt is `p00g_admission_audit.json`; the P00f audit is retained as the frozen baseline assessment. The new receipt can close only the two named blockers and only after all new and prior checks pass. P00 admission is bounded engineering acceptance of the implemented profiles and assays, not a life/evolution result or arbitrary-world detector validity. P01 execution readiness remains separately unfulfilled.

Unexpected labels, replay differences, old-profile drift, missing evidence, or failed controls stop admission with the original denominator. Failed run bundles remain retained; fixes must be distinguishable from threshold/criterion changes.
