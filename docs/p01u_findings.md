# P01u native validation findings

2026-10-24. **All 128 unchanged saved requests passed the native worker prefix
and immutable initial validators.** The independent audit confirmed exact typed
roundtrips and unchanged worlds for every cell. This is finite-panel native
acceptance; candidate matching and world transitions were not executed.

## Native boundary and controls

The isolated Cargo binary deserializes the existing pilot::Request, checks the
worker's schema and epochs<=1000 predicate, then calls initial.validate(). It has
one stdin interface and no run/generate/step mode. The reviewed source gate pins
its exact bytes, records its authored call set and five immutable validator spans,
and rejects stepping/matching calls or substituted sources/binaries. The linked
library includes runtime code; the gate concerns reviewed reachable calls, not
mere linkage or a self-reported zero counter.

The producer separately enforced the exact P01t schema/epoch/event/trace contract.
Controls demonstrated that epochs 127 and changed event/trace caps can be accepted
by the worker prefix while failing that stricter policy. Strict JSON duplicate-key
checking is also separate: serde can normalize duplicate map keys. Parse rejection,
worker-prefix rejection, immutable-validator rejection and process/guard failure
remain distinct labels. Every retained input was passed unchanged through stdin;
no horizon-zero substitution or altered safety flag was used.

Fifteen registered control families/74 named subcases expanded to 93 explicit cases,
including 53 actual native fixture invocations per Python mode. Fifteen tests passed
normally and optimized. Native fixtures exercised parser/numeric bounds, profiles,
allocator/endpoints, conservation/writers, rule grammar/connectivity/slots/IDs,
world limits and environment balance/channels. Engineering cases covered immutable
roundtrips, false acceptance/error stages, missing/extra/reordered rows, inventory/
counter changes, source substitution, guard failures, partial writes and terminal
I/O errors. The deliberately failing fixture processes are not failed retained
validation attempts. Their outputs and receipts remain local and hashed.

Native control results, source gate, compiler/binary/dependency identities and
independent-auditor mutation checks passed before the first retained invocation.
No test, build, retained validation or independent audit failed. One later closeout
check compared Path-sorted and string-sorted dependency lists and falsely rejected
membership. That failed check is preserved. Exact set membership and every file
hash then verified; no dependency, source, input or acceptance criterion changed.

## Accounting and provenance

One retained attempt invoked the exact pinned binary once for each of 128 cells.
All 128 reports were guard-successful and accepted; exact typed requests and world
identities matched. No retained process group required termination. The guard did
exercise termination on invented capped processes. The retained run recorded 559
stage polls, 175 RSS samples and 456,597 combined-stream bytes. Maximum sampled RSS
was 671,744 bytes; this is the largest observed sample, not an instantaneous peak
or hard memory bound. Sampling begins before stdin is delivered and targets 5 ms.
The registered 2-second/1-MiB/256-MiB sampled stage limits were preserved.

The full validation bundle contains 400 files totaling 2,370,845 bytes; its audit
contains 14 files totaling 867,935 bytes. Complete inventories, digest links and
byte totals reconciled. Closeout independently reconstructed all 13,653 producer
budget polls. Input-bundle scans, output scans, kernel RSS queries, fixed semantic
source rechecks and per-stage binary-hash reads have distinct scopes. Custody
counters cover the single deduplicated custody pass; additional static source
checks read 32,105 bytes and per-stage binary checks read 108,634,112 bytes. Those
are explicit rechecks outside output polling, not claimed reductions or benchmark
evidence. No terminal tree scan or original custody recheck occurred.

The build closure pins 1,146 files and 21 registry packages with the same exact
versions/checksums as the original Cargo.lock. All 1,103 dependency snapshot files
and registry membership matched. The original Cargo/library/worker sources are
unchanged; the nested Cargo package has its own committed lock. Final custody
verified 326 frozen files, 495 inputs and 668 preceding public receipts, plus the
original 5,127-entry P01o and 4,960-entry P01q bundles and seals. P01q remains consumed
with its original failures and unstarted cells.

The independent auditor never invokes the validator and imports neither runner
nor native implementation. It checks input/report/binary/source identities,
all 128 guard receipts, complete typed values, policy, immutable digests, inventories
and accounting. Its input-custody scaffold is reproduced source text, not an
independently designed custody algorithm. It does not reimplement every Rust
semantic validator; semantic acceptance comes from the pinned native binary.
Raw request/native roundtrip bodies and dependency/binary snapshots stay local.
Public records contain compact hashes, statuses, controls and audit receipts.

See the [independent audit](evidence/p01u-001/independent/audit.json),
[128-cell manifest](evidence/p01u-001/manifest.json),
[closeout](evidence/p01u-001/closeout.json) and [closure](p01u_closure.json).

## Next boundary

Separately register bounded campaign integration and failure-injection readiness
at new paths, using these validated requests and the disclosed guard/accounting
contract. Productive dynamics and any performance trial need their own subsequent
registration. Native acceptance establishes no applicability, productive trajectory,
reproduction or causal mechanism. No generator, candidate matcher or world step
ran. Science remains untested, behavior null/not_executed and E01 unauthorized.
