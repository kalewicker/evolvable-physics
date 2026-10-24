# P01s recovery engineering findings

2026-10-24. **The registered invented-fixture engineering gate passed**, with an
independent audit. Thirteen tests passed normally and with Python optimization;
all 24 controls and 55 subcases passed. This establishes fixture transport and
accounting behavior, not retained-panel readiness, native acceptance or speedup.

## Implemented behavior

The new boundary consumes two complete envelope byte streams, checks their pinned
digests and typed identity, preserves metadata and nested environment, and builds
the exact fixed request. Duplicate JSON keys, malformed/nonfinite input, wrong
schema/cell/hash, missing objects, already-unwrapped input and disagreement are
rejected. The fixtures contain authored inert native fields; no original saved
environment was parsed or converted.

The owned-output ledger accounts append/truncation/copy, partial syscall writes,
replacement overlap, deletion, snapshots, metadata and seals. External changes
invalidate accounting. Stage reconciliation is confined to declared names, 16
files and an 8 MiB maximum allowance, with no retry after failure. The suite uses
smaller declared stage allowances to exercise both sides of the limit. Budget
polls touch no files; filesystem spies and independent receipt checks reconcile
stat/read/write/discovery work, while a separate trap test forbids all filesystem
access during 100 repeated polls.

Four terminal cases preserve 128 initialized records each (512 audited rows),
first error, subsequent error and incomplete reconciliation. Terminal I/O failure
is explicitly missing rather than claimed persisted. The outer fixture harness
reserves 2 MiB for each of its 33 isolated accounting cases before work; successful
completion replaces that bound with exact known-path accounting. Failure reports
exact bytes as null and retains a conservative bound without a terminal tree scan.

## Retained attempts and corrections

All four build histories passed their tests: builds 001/002 had 12 tests per mode;
003/004 had 13. Review after build001 added ledger invalidation after unexpected
external mutation. No test logs, sources or prior attempt outputs were replaced.

Readiness attempt001 failed on the absolute-path fixture when invoked with a
relative output path: the fixture itself constructed a relative path. Tests had
used an absolute output directory. The fixture now canonicalizes its root and a
relative-launch regression covers that boundary. Attempt001 also recorded only
50,766 known-path bytes; independent closeout found 78,114 actual bytes across 37
entries. Its failed receipt and misleading pending-audit label remain unchanged,
and must not be read as a complete accounting seal.

Attempt002 passed and its independent audit passed. Review then corrected the
outer harness's failure accounting to reserve fixture space and report incomplete
exact accounting honestly. The unchanged 24-control panel passed again in
attempt003 with build004; independent audit002 passed. Attempt003 contains 40
entries and 164,638 bytes, exactly reconciled. The two successful attempts are
engineering repeats after implementation changes, not scientific replications.

A separate injected harness failure after writing partial output exercised the
corrected closeout: 52,090 actual bytes were preserved, exact reported bytes were
null, and the 69,258,082-byte conservative bound remained below the 128 MiB limit.
The failure probe is intentional and separate from the three readiness attempts.

## Evidence and limits

See the [independent audit](evidence/p01s-003/independent/p01s-audit-002/audit.json),
[complete results](evidence/p01s-003/results.json),
[closeout](evidence/p01s-003/closeout.json) and [closure](p01s_closure.json).
All 302 frozen files, 296 inputs and 580 preregistration public receipts remained
unchanged. Original P01o/P01q inventories and seals matched: 5,127 and 4,960 entries.
All pre-existing public receipts are preserved; generated fixture files and source
snapshots remain local, with compact receipts and authored descriptors published.

Counters distinguish each isolated fixture directory from the complete attempt
root. Across 33 accounting subcases there were 46 local fixture scans, four stage
reconciliations, 115 budget polls, 123 explicit lstat calls, 332 read bytes and
27,352 written bytes. The 100-poll control performed zero filesystem operations.
The attempt-root initial empty check and independent final inventory are separate;
no terminal full-tree scan or original custody recheck is used. These are work
counts on fixed tiny fixtures, not timing attribution for P01q or a speedup claim.
Limits are cooperative, with no hard CPU/RSS enforcement claim. Actual stage
process execution, full native semantic validation and campaign integration are
outside this milestone.

Next, separately register unfiltered all-128 saved-envelope-to-request readiness,
with exact preservation and an independent audit. No retained conversion starts
here. P01q remains consumed and unrepaired, behavior null/not_executed, science
untested and E01 unauthorized. No native worker, generator, candidate matcher or
world transition was executed.
