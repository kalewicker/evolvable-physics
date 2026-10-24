# P01u native validation registration

2026-10-24. Register the validation-only native boundary over the exact128 requests
already accepted by P01t transport checks. This turn performs registration and
custody only. Do not compile a new adapter, run a validator or parse retained request
payloads during registration. Existing manifests and inventories supply identities.

## Exact native boundary

After this registration is committed/pushed, implement only the six listed paths.
Build a standalone nested Cargo package with its own workspace, importing the
unchanged root library through a path dependency. Pin the existing Cargo.lock;
use a lock matching its exact dependency versions, offline and locked builds,
with an isolated target directory. Do not edit the original Cargo files, library
sources, worker or old scripts. Preserve every build attempt and toolchain/source/
dependency/binary identity in readiness receipts. The nested manifest and its separately registered generated lock are engineering
artifacts, never modifications to the old frozen lock. Commit the new lock with
the manifest/source and retain its exact build snapshot and identity.

The new executable has one validation-only stdin interface. It deserializes exactly
causal_alife::pilot::Request using the pinned serde_json/serde types. Reproduce the
worker's pre-loop predicate: schema p01-worker-request-v1 and epochs<=1000. Then
call request.initial.validate(), following the existing immutable Environment,
Experiment, World and Rule validators. Emit acceptance/rejection, rejection stage,
error diagnostic, input digest, pre/post world identity and a serialized roundtrip
request. Preserve full native stdout locally for independent value comparison.
Rejections are classified as parse, worker_prefix or initial_validate; guard/I/O
failures are execution failures, never semantic rejections. Do not infer a
validation stage from a generic nonzero exit alone. Well-formed rejection reports
may exit normally; acceptance and report validity must be checked explicitly.

The worker's pre-loop acceptance is different from the P01t panel contract. The
runner checks epochs=128, max_events=16384 and max_trace_bytes=4194304 independently.
Changed caps or epochs127 can satisfy the native prefix while failing panel policy;
controls preserve both labels. Native acceptance does not claim those event/trace
caps are enforced by validators. Preserve original saved bytes; do not set epochs=0,
add a barrier flag, strip fields or modify a request to make validation safe.

Duplicate object keys, nonfinite input and exact typed/canonical preservation are
independent strict runner/auditor checks. Existing serde struct duplicate fields
may reject while duplicate map keys can be normalized by native parsing; label
strict-precheck and native parsing separately. No claim that existing validators
reject all semantically dubious inputs: acceptance means only the pinned routines.

## Static non-execution gate

The new binary must expose no generate/run/step mode. Its authored code may invoke
JSON parsing/serialization, immutable validation, hashing and bounded I/O only.
Before any retained request invocation, inspect the exact source and validator
call closure. Reject calls to bounded_step, environment::step, runtime matchers,
applicability, candidate enumeration, mutation/commit, generator evaluation, or
process/network APIs. The linked library contains runtime code, so linkage alone
is not proof of isolation. Record the reviewed call sites and immutable validator
spans/hashes. Test that an injected forbidden call or substituted source/binary
fails this gate. A self-reported zero counter is not sufficient evidence of no
transitions. Compare complete input/roundtrip typed values and world identities
independently; no rule application or biological interpretation is performed.

## Fixed panel, input custody and controls

All128 proposals6000..6031 times initials0..3 remain in proposal-major order.
Use only artifacts/p01t-002/requests/000.json through127.json at the pinned hashes.
All128 manifest rows exist before work. Verify request bundle inventory, completion
link and bytes plus both original P01o/P01q seals/inventories. Pin P01t closure and
all prior receipts. Each tool makes one deduplicated input custody pass, retaining
bounded request bytes for later invocation/audit; original inventory scans are
separate from output scans. No generator or source request is rerun or repaired.

The protocol fixes15 control families and their named invented subcases. Author
all fixture descriptors and expected acceptance/stage/policy values before tests.
Run Python tests normally and optimized; run native fixture tests through the
actual new binary. Invalid native fixtures exercise frozen validation branches,
not candidate matching. Source-based expected error codes must be explicit; serde
parse diagnostics need stable stage/type classification, not platform line text.
Compound subcase names must expand all named alternatives before execution.
Neither tests nor retained runner may substitute a mocked parser for the real
bytes->native-request->validation path. Wrapper failure accounting may use inert
fixture processes, clearly labeled and separate from the validator call closure.
Only invented input controls may be modified to test rejections; saved128 inputs
stay exact. Final native control results, static non-execution gate, Python tests,
source/dependency/binary closure and independent auditor mutation tests must all
pass before retained input validation begins.

The complete panel gate requires all128 guard-successful native reports accepted,
all128 panel-contract checks passing, exact input digests, complete roundtrip typed
preservation, equal pre/post worlds, no missing/extra/duplicate/reordered rows,
complete inventories/byte accounting and the independent audit. Native rejection
is a failed acceptance gate, not an observed biological zero. Stop on first retained
failure and retain all later unstarted statuses. No fallback parser or input repair.

## Process limits, accounting and failure closeout

Each retained cell has one native invocation, bounded by2 seconds wall time,
1 MiB combined stdout/stderr and256 MiB sampled RSS. Requests are <512 KiB.
Stage wall/output equality rejects (test one unit below/equal/above). Sampled RSS
is not a hard instantaneous limit; preserve sample frequency and maximum observed.
The runner may launch only the exact hash-pinned native binary for retained work.
Terminate its whole process group on a cap failure, retain partial streams and
stage status. No native child processes are allowed by the adapter contract.
Tests may use separate inert guard fixtures without claiming they are validators.

Runner and auditor each have cooperative180-second/128-MiB output limits, reserving
5 seconds/1 MiB for closeout. Poll maintained bytes and monotonic elapsed time;
never rescan output trees during polling. Reserve full1-MiB stage output allowance
before launch; cap read chunks, preserve partial writes, include simultaneous
temporary bytes, snapshots, logs, metadata, inventories and seal bytes. Record actual
write/receipt bytes, stage polls, samples, kills, status, hashes, output/input scans
and budget checks. Test counters with independent spies and reconciliation. One
initial empty-root check per runner and one independent full output inventory per
auditor are allowed; no original custody recheck or tree scan during failure closeout.

Initialize all128 rows before work. Keep first error and closeout errors distinct.
Partial data and failures remain inventoried. Use maintained paths for terminal
records; if exact total is unavailable, report null plus a justified conservative
bound and incomplete reconciliation. Missing terminal persistence stays explicitly
missing in the outer harness receipt. Inventories do not hash themselves or final
completion, but independent complete membership/byte totals include both.

## Independent audit, publication and decision

The new auditor imports neither runner nor native adapter implementation. It does
not invoke the binary again: independently parse both native report and original
request bytes, compare every roundtrip typed value and world identity, reconstruct
panel policy, check input/binary/source digests, guard receipts and all128 rows,
and reconcile counters, full output membership, hashes and totals. Semantic
acceptance is supplied by the pinned native validators; this receipt/value audit
is not a second implementation of all Rust validators. Preserve that distinction.
Record its own source/input/test identities, costs, inventory and completion.

Raw requests, native roundtrips and source/dependency/binary snapshots stay local.
Publish compact cell identity/hash/status/guard/control/audit receipts only; sanitize
native diagnostics if they echo input contents. Passing admits only native prefix
and immutable-validator acceptance on this finite panel. It establishes no candidate
applicability, productive trajectory, reproduction or causal mechanism. Stop here;
campaign integration, performance trials and dynamics need separate registrations.
P01q remains consumed and unrepaired; science untested, behavior null/not_executed
and E01 unauthorized. Retain every implementation/test/validation attempt; corrections
may repeat unchanged engineering criteria only in fresh directories. A request
or validator-contract change requires a new protocol, never a silent repair.
