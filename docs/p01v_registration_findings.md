# P01v inert campaign integration registration findings

2026-10-24. The [protocol](p01v_protocol.json) and
[integration plan](p01v_integration_plan.md) register orchestration across all 128
unchanged saved requests using three explicitly inert fixture roles per cell.
The prospective denominator is 384 fixture processes. Implementation and retained
integration have not started; no fixture process ran this turn.

The new pipeline will bind actual request bytes, cell identity, role order and each
predecessor's raw stdout digest through native_stub, report_stub and audit_stub.
Every receipt uses an inert schema/label, and final cell status is plumbing_complete.
A separate P01v manifest schema prevents an inert pass being recorded as native or
trajectory completion. Prior P01u native acceptance is verified from frozen receipts;
the native validator is not invoked again. The executor allowlist admits only the
pinned interpreter and new fixture source, rejecting worker/validator/reporter or
arbitrary commands before launch.

Twelve control families fix 70 named subcases. They include the full input-to-receipt
path; wrong identities/chains; failures at cell0, cell63 and cell127; guard/cap bounds;
partial writes; terminal I/O errors; all128 status preservation; exact accounting;
independent-audit mutations; attempt preservation and explicit scientific scope.
Compound cases must expand into authored expected outcomes before future tests.
These controls are registered, not executed.

The five new implementation paths may reuse only the explicitly pinned P01u helper
module and reviewed helper calls. The new guard must adapt terminal manifests at
its own path rather than reusing native-validation completion semantics. Retained
stages keep the 2-second/1-MiB/256-MiB sampled-RSS caps; pipeline/auditor budgets are
cooperative 180 seconds/128 MiB with terminal reserves. Polling and failure closeout
must avoid output-tree scans and original custody rechecks. Exact failure bytes
stay null with a justified conservative bound whenever full accounting is unavailable.

Nine registration tests passed normally and optimized, without failures. The
[custody receipt](evidence/p01v-registration-001/static_review.json) verified 340
frozen files, 520 inputs, all 694 preceding public receipts and all128 request hashes.
P01t request and P01u validation bundles matched complete inventories, file hashes,
completion links and byte totals; every native-acceptance row matched its request.
Original P01o/P01q inventories and seals remained exact (5,127 and 4,960 entries).
All prior failures, including consumed P01q and P01u's post-audit membership-check
history, remain preserved. No retained request/native-roundtrip body was parsed;
registration used metadata and byte hashes only.

After commit/push, implement the five registered paths, test all invented controls
normally and optimized, pin tested interpreter/source/dependency identities, then
perform and independently audit the unchanged all128/384 inert integration panel.
Preserve every attempt. Input repair, regeneration, selective omission and P01q
resumption remain forbidden. Passing stops at campaign-plumbing readiness;
productive dynamics and performance trials require separate registrations. Science
remains untested, behavior null/not_executed and E01 unauthorized.
