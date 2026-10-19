# P00g exported-output modes and environment detector adapter

The closed and driven physics profiles retain their existing schema and transition rules. This stage adds observer-output controls and the versioned `p00g-environment-analysis-v1` adapter. The frozen `src/analysis.rs` and detector protocol remain byte-identical to P00e/P00f.

## Trace output modes

Native and environment `step_with_logging` accept Full or Disabled and return an optional exported record. Disabled must return None. Both execute the same match enumeration, conflict selection, checked operations, atomic staging and commit. Both retain event IDs, allocator continuation, provenance writer keys, resource balances and ledgers, seed/schedule/epoch state and validation.

Disabled output avoids exported Event/Frame/Epoch construction, event-parent lists used only for those records, and their output-only before/after digests and state snapshots. Match candidates, conflict footprints, semantic provenance and transactional copies remain required work. This is not a no-provenance model or a performance result. No observer mode is added to checkpoint identity, so switching modes preserves exact continuation.

Existing `step` APIs continue to request Full output. CLI `resume-quiet` and `environment-resume-quiet` disable exported output while continuing a validated checkpoint. Final checkpoints remain fully validated. Analysis still requires retained full traces; logging-disabled intervals alone cannot reconstruct missing event evidence without a separately verified deterministic rerun.

## Environment analysis

The adapter starts from the complete Environment, validates each full Epoch against reference execution, checks the environment phase and prepared native state, then extracts actual native event changes from that prepared state. It samples post-native world structure for temporal tracking and uses the unchanged P00e thresholds.

Supply/extraction/transport and their writer/counter/ledger changes are external. They cannot create native state/topology activity credit. A native firing may depend on environmental resources, but only its actual type/state/existence/structural-incidence changes enter the activity graph. No-op state writes, resource burns/transfers, pure reads, event count, or native rule availability alone establish activity.

`src/environment_analysis.rs` contains a versioned observation engine using the frozen detector's public data structures and feature definitions. The old engine remains available to reproduce the frozen panel. Full output equality is required on all 320 old detector/transfer cases so future drift is visible rather than hidden by shared thresholds.

Low-level observation functions are for validated inputs. The public native/environment analysis entry points replay their corresponding traces. Truncated, altered, phase-shifted or forged records are rejected; missing environment steps cannot be bypassed by flattening the native frames.

## Evidence and admission

The exact matrix, controls, logging epoch counts, and acceptance criteria are in `p00g_registration.md` and `p00g_protocol.json`. `p00g_admission_addendum.json` retains the frozen P00f requirement inventory and updates only its two named blocker assessments using the new evidence. The current admission receipt is `p00g_admission_audit.json`; the P00f receipt remains historical baseline evidence.

Passing P00 admits bounded engineering fixtures and the declared 2–6 node AP/maintenance analysis. It does not establish detector validity on arbitrary worlds, reproduction/heredity, evolved functionality, or search superiority. P01 still requires its own generator, instrumentation/budget and event/time/memory-cap readiness work.
