# P01u native validation registration findings

2026-10-24. The [protocol](p01u_protocol.json) and
[validation plan](p01u_validation_plan.md) register validator-only native acceptance
for all 128 unchanged P01t request files. No adapter implementation, compilation,
native invocation or retained request parsing occurred this turn.

The proposed executable will deserialize the frozen pilot::Request, apply the
worker's pre-loop schema/horizon check and call the existing immutable initial
validators. A source/call-closure gate must reject stepping, matching, generator
or process entry points before retained validation. Exact request roundtrip and
world identity checks accompany acceptance. The worker prefix and the stricter
P01t request policy are separate results: a changed event/trace cap can satisfy
the former while failing the latter. Native parsing is also distinct from the
runner's strict JSON precheck, including duplicate map keys.

Fifteen control families fix 74 named subcases; compound cases must expand every
named alternative into authored descriptors before tests. They cover parsing,
worker versus panel policy, profiles, allocator/endpoints, conservation/writers,
rule grammar/slots/IDs, world limits, environment balance/channels, immutability,
forbidden execution paths, process guards, failure closeout and audit tampering.
These controls have been registered, not executed.

The future build uses six new paths, including a separate nested Cargo package
and lock, without changing the original Cargo/library/worker sources. Retained
validation permits one exact hash-pinned binary invocation per cell, with a
2-second wall, 1-MiB combined-stream and 256-MiB sampled-RSS stage cap. Runner and
auditor limits are cooperative 180 seconds and 128 MiB, with terminal reserves.
No hard instantaneous RSS claim or benchmark is implied. Raw request roundtrips
stay local; compact receipts and metadata are the public deliverables.

Eight registration tests passed normally and optimized, with no failed tests.
The [custody receipt](evidence/p01u-registration-001/static_review.json) verified
326 frozen files, 495 inputs, all 663 preceding public receipts and all 128
request hashes. The complete P01t request bundle matched membership, file bytes,
inventory/completion links and total size. Original P01o/P01q inventories and
seal links matched exactly (5,127 and 4,960 entries), preserving consumed P01q's
input/terminal errors, one failed cell and 127 unstarted cells. Registration
checked descriptors, metadata and bytes by hash; it parsed no retained request
body and executed no native validator or world transition.

After commit/push, implement the six registered paths, complete invented/native
control tests and binary/source/dependency closure, then perform and independently
audit the fixed 128-cell validation. Every attempt stays preserved. The auditor
will independently check report values, typed roundtrips, policy, guard receipts
and accounting; it does not reimplement every Rust validator or rerun the binary.
Passing stops at finite-panel native validation. Campaign integration, performance
trials and dynamics need separate registrations. P01q remains consumed and
unrepaired, science untested, behavior null/not_executed and E01 unauthorized.
