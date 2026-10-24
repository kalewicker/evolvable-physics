# P01r read-only engineering diagnosis

2026-10-23. **The saved-input mismatch is confirmed across all 128 cells.**
Both Rust and Python saved streams match with typed JSON equality in every cell.
Every pair has the registered wrapper schema/IDs and an `environment.native`
object; none has a root-level `native` object. There were no JSON parse failures.
This verifies the boundary and paired records, not full worker semantic validity,
rule applicability, or executable reachability.

Registration commit `86bfa40` was pushed before implementation and diagnosis.
Nine tests passed normally and with Python optimization, covering all ten
invented complete-envelope controls and ten accounting controls. One review and
one independent audit then passed without implementation repair. The audit
verified all 256 streams, all 128 rows, 20 control results, nine source spans and
22 static call sites. Old runtime modules were never imported; no worker request,
world transition, candidate enumeration or keyed evaluation occurred.

The [source evidence](evidence/p01r-001/source_analysis.json) connects the mismatch:

- The generator returns an envelope containing `environment`.
- `saved_initial` verifies the paired streams and returns that whole envelope.
- The runner then reads `initial['native']['rules']` before writing a request.
- The mocked full-pipeline test replaces the loader with an already-unwrapped
  `native` descriptor, so it never tests that producer/consumer boundary.
- The worker consumes `request.initial` as the environment and accesses its
  `native` field. Its validation was never reached by the failed attempt.

The [cell table](evidence/p01r-001/cells.json) retains every initial, byte identity,
metadata result and equality check. Unknown semantic validity remains null.
The original P01q failure and all prior passing readiness receipts are preserved.
The failure was an implementation/test-boundary defect, not a reason to modify
sampled laws, resources, scheduler or detector criteria.

The accounting source shows `check_budget` calling `usage`, which calls
`campaign.file_bytes` to recursively enumerate/stat the artifact tree. Custody
loops invoke the supplied `tick` callback, and the runner supplies `check_budget`
for both preparation and terminal custody. Snapshot-copy loops also call it;
the guarded-stage polling loop has budget/usage calls as well, though no such
stage ran in P01q. Repeated traversal is therefore a source-derived design risk.
The 22 sites are lexical source locations, not measured invocation counts.
Actual traversal counts and per-operation CPU/wall attribution remain
null/uninstrumented. No benchmark, timing reconstruction, speedup claim or
allocation of the observed 595.554482 CPU seconds to particular calls was made.

Saved-file accounting reconciles P01q's 248,815,477 inventoried bytes plus
488,346 inventory/seal bytes to its recorded 249,303,823 bytes. It records 1,107
declared source entries, 3,846 dependency entries and 25,564,664 bytes in the
listed source snapshot set. The original manifest still has one failed cell,
127 unstarted cells, zero stages, the input KeyError and the terminal CPU-reserve
failure. Later successful custody checks do not replace that terminal failure.
Both original P01o/P01q inventories and seals remain unchanged.

The review emitted 519,602 bytes in 2.004470 seconds; its audit emitted 308,819
bytes in 1.050429 seconds, within the registered cooperative limits. These are
diagnostic cost receipts, not a performance comparison with the campaign.
Inputs were referenced by verified hashes; the new implementation and plan were
snapshotted. The auditor uses separate typed-value and accounting algorithms and
an independently traversed AST; both tools share duplicated custody/output
scaffolding, with no import of the reviewer by the auditor.

Next register a bounded engineering recovery protocol at new source paths. The
recommended design has an explicit saved-envelope boundary that validates both
streams and metadata before exposing the unchanged nested environment, exercised
by complete-envelope fixtures without mocking that boundary away. It also needs
bounded accounting with explicit byte updates and scheduled full reconciliation,
measured accounting work counters, and a terminal path that preserves failure
receipts without repeatedly scanning the whole tree under a shrinking reserve.
Temporary replacements, partial writes, snapshots and seal bytes must be included.
Test the complete input-to-request path and failure/closeout paths with inert
fixtures before considering a separately registered performance or trajectory
attempt. This is a design recommendation only: no corrected runner, benchmark
or new execution is authorized by P01r, and consumed P01q cannot be repaired or
resumed. Scientific status remains untested; behavior null/not_executed; E01
unauthorized.
