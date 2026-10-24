# P01q execution closeout: engineering failure before dynamics

2026-10-23. **The sole P01q attempt is consumed. No world transitions ran.**
The first cell (law6000, initial0) failed with `KeyError('native')`; the other
127 cells remained unstarted. No native/report/replay stage launched, no worker
request was written, and no behavioral outcome was measured. All full-horizon
behavioral fields remain null/not_executed. This is not evidence against the
registered mechanisms and does not alter P01g's earlier negative results.

Execution freeze/admission commit `d4f56b1` was verified on the remote before
launch. The first invocation failed its sandbox-blocked `ps` probe before attempt
directory creation or transitions. That log is preserved. The approved second
invocation created the one attempt, wrote all 128 planned slots and snapshotted
the frozen closure. There was no second consumed attempt or resumed cell.

The original terminal manifest records two errors:

- `KeyError('native')` at the first saved-input boundary.
- `AssertionError('aggregate CPU reserve')` during the final custody recheck.

The [original seal](evidence/p01q-001/seal.json) records 604.1816673753783 seconds
wall, 595.554482 seconds total process CPU, and 249,303,823 artifact bytes, with
no registered ceiling overshoot. Engineering and continuation gates are false.
The stored mechanism gate is also false because there are no eligible verified
trajectories; it must not be interpreted as observed absence of mechanisms.
The error occurred before any native stage. The controller consumed the measured
budget in preparation/checking/closure, not in simulated dynamics. Exact cost
attribution among those operations was not measured and is not claimed.

The frozen [receipt auditor](evidence/p01q-001/receipt_audit.json) passed without
world replay. It verified the 4,960-entry inventory, exact membership, source and
dependency snapshots, manifest/seal identities, accounting and zero trajectory/
stage receipts. The original seal remains
`eabecddbe5ea1a14d537a56af96a2bd9516bf9dca6d1998137e7cc277df7dcf4`.
A separate [post-seal custody check](evidence/p01q-001/post_seal_custody.json)
verified all 1,107 current frozen files, 3,846 dependencies, four tools and 23
memberships, plus the unchanged original P01o inventory/seal and P01p receipts.
That later check does not replace or erase the in-attempt CPU-reserve failure.

The source-level interface mismatch is explicit: the saved generator output
contains an `environment` field ([generator_v4.py](../scripts/generator_v4.py));
`saved_initial` returns the whole wrapper ([p01q_cell.py](../scripts/p01q_cell.py)),
and the runner immediately accesses `initial['native']`
([p01q_campaign.py](../scripts/p01q_campaign.py)). The complete mock-pipeline test
replaced `saved_initial` with an already-unwrapped `native` fixture, bypassing
this boundary. Its passing readiness result therefore did not establish actual
saved-envelope compatibility. All original source, tests and passing receipts
remain unchanged so this testing gap stays inspectable.

No repair, input conversion, rerun, retry, new sampling or completion of missing
cells was attempted. The runner also calls full-tree byte accounting inside
frequent custody budget checks; this is a source-level concern for a future
engineering diagnosis, not a measured timing attribution.

Next separately register a bounded read-only engineering diagnosis of the saved
record/worker boundary and budget-accounting/closeout path. It should specify
complete-envelope invented fixtures and accounting controls before any new
implementation or performance assay. Any corrected execution needs a separately
justified protocol, unchanged historical outcomes, fixed inputs/denominators and
a new freeze/admission. P01q itself cannot be repaired or resumed. Scientific
status remains untested; E01 stays unauthorized.
