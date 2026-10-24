# P01s recovery engineering registration

2026-10-23. Register a bounded engineering fixture suite before implementing it.
P01r diagnosed the wrapper mismatch and source-level repeated scans. It did not
measure their runtime contribution. P01q remains consumed, with its original
input error, terminal CPU-reserve error, one failed cell and 127 unstarted cells.

## Boundary and scope

Implement only the five paths in the protocol after this registration is committed
and pushed. Do not import old project runtime modules or change frozen sources.
Read old contracts as text if needed. Do not invoke a worker, generator, candidate
matcher or subprocess from the readiness/audit tools. Fixtures use authored inert
native fields; they are not sampled worlds. No retained payload is parsed or
converted by P01s: the saved streams are pinned as custody inputs only. A later
separate all-128 readiness registration must precede retained request construction.

The boundary accepts two complete envelope byte streams and their expected SHA256
and cell identity. Reject malformed JSON, duplicate keys, nonfinite numbers,
wrong schema, absent/non-object environment/native, mismatched IDs (bool is not
int), wrong hashes and any type-sensitive stream disagreement. Require
p01o-generated-environment-v1 and exact slot/proposal/initial identity. Preserve
the entire envelope, metadata, maps and draws; expose its nested environment
without changing any field. Build a request with that exact environment as
initial and the frozen P01q epochs/event/trace caps from the protocol. Never
silently accept an already-unwrapped fixture. This is transport validation,
not native semantic validation. Tests must traverse bytes -> reader -> request
without replacing the reader; the independent audit checks exact request values
and absence of native/rule/resource mutations against original fixture bytes.

## Accounting and bounded work

Use an owned-output byte ledger. Track actual write progress, append, truncate,
copy, temporary creation, rename and deletion; reserve capacity before writes.
Count old and temporary replacement bytes simultaneously until rename. Partial
writes and failed copies stay inventoried; repeated registration cannot double
count a path. Include source snapshots, logs, metadata, checksums and seal bytes.
Reject traversal, symlinks and paths outside the owned output root. Unknown
external changes invalidate accounting, rather than silently accepting them.

Budget polls read maintained bytes, injected monotonic/process CPU readings and
counters only: no filesystem discovery, stat or hashing. Strict reserve predicates
reject equality at a boundary. Real fixture files exercise the writer; clock/CPU
readings are deterministic injected values, not benchmark measurements.

Two full output inventories are allowed per successful readiness attempt: initial
empty-root validation and final independent reconciliation. On failure, skip the
final full scan and mark reconciliation incomplete. Each declared simulated stage
may reconcile only its own directory once, with at most 16 files and 8 MiB. Reserve
that full allowance before handing ownership over; polling uses the reserved
upper bound until reconciliation. Reject unknown names or size overruns; retain
files and mark failure. No actual child process is launched. Input custody hashing
is a separate counted, once-per-tool pass, not a polling or terminal operation.

Record counters for input/output full scans, stage reconciliations, discovered
entries, stat calls, hash-read bytes, write bytes, ledger updates and budget polls.
Tests independently spy on filesystem APIs: repeated polls must cause zero
filesystem work; counters must match spies, not self-reported estimates. Counts
are measured work on fixtures only, not speedups or P01q timing attribution.

## Failure closeout and reconciliation

Initialize all 128 fixture slot records before work. Preserve first error and
subsequent closeout errors separately; never promote failed/unstarted to success.
Stop ordinary work before the 1 MiB / 5 second terminal reserve. Terminal records
use the ledger and preinitialized cells; no original custody recheck or output
full scan. Preserve partial output. Record inventory scope and reconciliation
status explicitly; a partial seal is not a successful inventory audit. If terminal
writes fail, preserve the original error in the outer test receipt and mark the
terminal receipt missing, never claim guaranteed persistence under total I/O failure.
Final checksum/seal files must be included in byte accounting but cannot hash
themselves: inventory data files, link the inventory digest in completion, and
check exact full file membership/total bytes separately in the independent audit.

## Fixed controls, outputs and gates

The protocol fixes 24 named controls. Each is required, including all ten prior
interface and ten prior accounting controls plus zero-work polling, bounded stage
reconciliation, depleted-reserve closeout and unsafe/external path handling.
Expand each name into explicit subcases before tests; do not replace or drop one.
The complete-envelope control includes duplicate keys, nonfinite numbers, wrong
hashes and malformed JSON rejection. All counter assertions use independent
filesystem spies. Inventory mismatch controls include an equal-size external
mutation, an unlisted file and missing file. Boundary controls cover exact equality
and one unit on either side for byte/time/CPU reserves. Terminal controls include
input failure before stage0, partial write, exhausted reserve and terminal I/O error.

Retain source snapshots, normal and optimized test logs, authored fixture packet,
per-control expected/actual records, work counters, all128 terminal records,
identity/custody records, inventory, completion and independent audit. No raw
historical streams are republished. Both normal and optimized tests must pass;
all24 controls and their prescribed subcases must pass; inventory/accounting and
counter reconciliation must agree. A separate auditor imports neither implementation
module nor readiness runner; it recomputes typed envelope/request equality, file
sizes/hashes/membership, reserves and all128 statuses from fixtures and receipts.
Auditor also needs mutation tests proving bad requests/counters/inventories fail.
Cooperative 120-second and 128-MiB per-tool limits include snapshots and receipts;
no hard resource-enforcement claim. Retain failed attempts without rewriting them.

Passing admits only this engineering fixture conclusion. It does not establish
worker acceptance, saved-panel readiness, performance improvement or behavior.
E01 remains unauthorized and science untested. No campaign integration this stage.
