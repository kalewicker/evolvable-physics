# P01v inert campaign integration findings

2026-10-24. **All 128 unchanged saved requests passed the complete three-stage
inert pipeline and independent audit.** The final attempt made exactly 384 fixture
process launches. Every cell, role, raw-input identity and predecessor-stdout chain
matched, with exact inventories and accounting. No worker, native validator,
candidate matcher, generator or world transition ran in this milestone.

## Implemented behavior and controls

The new pipeline admits actual saved bytes through the pinned request loader and
prior P01u acceptance receipts, then runs native_stub, report_stub and audit_stub.
The first receives unchanged request bytes; the later roles receive those same
bytes in explicit UTF-8 envelopes plus predecessor stdout. Each emits the strict
p01v-inert-stage-receipt-v1 field set, binds its cell/input/role/predecessor digest
and is checked independently by the parent. Cell success is plumbing_complete;
the manifest uses its own inert schema and behavior stays null/not_executed.

Only the pinned interpreter with fixed -I/-B flags and pinned fixture source/role/
cell arguments can run. Source/interpreter substitutions, worker/validator/reporter
commands and arbitrary argv reject before launch. A process audit hook counts
actual Popen attempts and locks retained execution to the active pinned executor.
The fixture has standard-library imports only. The source gate pins authored call/
import sets and reviewed helper reuse; the unchanged P01u native driver is never
called. Output/guard primitives are reused at their pinned identity, with a new
P01v terminal-manifest adapter instead of native completion semantics.

Twelve test families passed normally and optimized. The 70 registered names
expanded to 101 authored control labels. Tests use actual authored request files,
the real loader and real fixture subprocesses. They cover all 128 cells/384 stages,
relative/absolute paths, stale/wrong/cross-cell receipts, malformed JSON and labels,
source/argv rejection, resource boundaries and injected RSS samples. The full
failure matrix covers before cell0, bad input hash before stage0, each role at cell0,
report_stub at cell63 and audit_stub at cell127. Independent checks verify the
completed prefix, failed cell, unstarted later stages/suffix and exact invocation
count for every case. No later process launches after failure.

Separate inert guard fixtures exercise nonzero exits, capped stdout, partial stderr,
whole-process-group termination, partial syscall writes and terminal I/O errors.
Missing terminal persistence is explicitly missing and preserves the first error.
The unknown-total fixture retains output_bytes=null, a justified conservative bound
and incomplete reconciliation; a false exact total is rejected. Independent spies
reconcile kernel writes, output scans and process launches; forbidden-API traps
confirm budget polls touch no filesystem. Actual stage polling performs no output
tree scan, and terminal closeout does not repeat original custody.

## Preserved attempts and runtime closure correction

The first integration and independent audit passed. Final provenance review found
that the initial runtime closure pinned stdlib source/extensions and loaded images
but omitted existing Python bytecode. The fixed -B flag prevents bytecode writes,
not reads. That first passing attempt, closure and test receipt remain unchanged.
A second closure adds all 186 existing stdlib bytecode files (no project bytecode
was present), and a new receipt binds the unchanged passing tests to that closure.
No tested source, input, control or acceptance threshold changed.

The unchanged full integration and audit then passed again in fresh directories.
All 384 raw inert stdout receipts are byte-identical across attempts. These are
engineering repeats after a provenance correction, not scientific replications.
There were no failed test runs, integration attempts or independent audits; injected
failures remain part of the authored test evidence. Runtime closure now pins 2,132
files/62,776,229 bytes and 2,124 dependency snapshots. It records stdlib/interpreter
and parent loaded dyld images; OS shared-cache images have platform/path identities,
not individual file hashes. This is a disclosed runtime scope, not a universal
reproduction guarantee for a different OS image.

## Final reconciliation and scope

The final integration bundle has 1,553 files totaling 2,926,180 bytes. The final
audit bundle has 14 files totaling 1,547,897 bytes. Independent complete membership,
file hashes, checksum links and totals matched. Closeout reconstructed all 19,054
budget polls. The final run recorded 2,690 stage polls, 1,547 RSS samples, 105,270
combined-stream bytes and zero process-group kills. Maximum sampled RSS was
15,663,104 bytes, an observed sample rather than an instantaneous peak or hard bound.
All retained stages obeyed the unchanged 2-second/1-MiB/256-MiB sampled guard caps;
tool budgets remained cooperative 180 seconds/128 MiB with terminal reserves.
Recorded timings are cost receipts, not performance comparisons or speedup claims.

Custody verified all 340 frozen files, 520 inputs and 699 preceding public receipts.
Original P01o/P01q seals and full inventories stayed exact (5,127 and 4,960 entries).
All saved requests, prior native acceptance and failure histories remain unchanged.
Input scans, output inventory, kernel memory queries and per-stage interpreter/
fixture-hash reads are counted separately. Raw retained requests, request-bearing
stage input and raw stdout, plus source/interpreter/dependency snapshots, stay local.
Published records contain compact identities, statuses, hashes, controls and audit
receipts. The auditor invokes no process and imports no pipeline/guard/fixture
module. It independently reconstructs identities, chains, policy, guards and output
accounting; copied custody scaffolding is disclosed as shared algorithm text.

See the [independent audit](evidence/p01v-002/p01v-audit-002/audit.json),
[128-cell manifest](evidence/p01v-002/p01v-002/manifest.json),
[failure matrix](evidence/p01v-002/tests/failure_results.json),
[closeout](evidence/p01v-002/closeout.json) and [closure](p01v_closure.json).

## Next boundary

Separately register a new bounded dynamics campaign across all 128 unchanged
requests. That registration must fix the production worker/reporter/auditor contracts
and require a source/binary execution freeze before launch, preserving P01q's
original mechanism criteria and consumed status. Inert stage success supplies no
trajectory, applicability, reproduction or causal evidence. Productive execution
and performance assays remain unauthorized here. Science untested, behavior
null/not_executed and E01 unauthorized.
