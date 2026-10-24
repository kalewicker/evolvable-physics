# P01t saved-input transport readiness findings

2026-10-24. **All 128 saved-input requests passed exact transport checks and an
independent audit.** Both saved streams for every cell were hash-verified and
compared with typed equality; every nested environment and fixed request field
survived deterministic serialization and parse-back unchanged. No cell was selected
or omitted. Native semantic acceptance and behavior remain untested.

## Evidence

The 32-law panel 6000..6031 with four initials each yielded exactly 128 inert request
files from 256 original saved streams. Original envelope metadata, maps, draws,
nested rules and resources were preserved by typed comparison and canonical
identity checks. Requests encode epochs=128 but were never sent to a native worker;
executed epochs and world transitions are zero. Request byte identity is distinct
from typed equality to the original envelopes, whose formatting is unchanged.

Fourteen control families expanded to 53 invented subcases. Fourteen tests passed
normally and optimized in each of two retained builds. They cover malformed and
nonfinite JSON, duplicate keys, bool/int/float differences, metadata, altered
requests, all 128 membership/order, relative/absolute paths, partial syscall writes,
terminal I/O failure, depleted reserve, exact byte/time boundaries and independent
inventory/counter mutations. Filesystem traps observed zero access during 100 polls;
spies reconciled actual lstat/write/scan calls. Failure fixtures retained all 128
statuses and the original error even when the terminal artifact was missing.

The auditor imports neither the producer nor its two pinned P01s modules. It
parses both original streams independently, reconstructs each expected request,
compares every typed value and canonical byte serialization, and checks metadata,
source/test identities, complete file membership, inventory digests and byte totals.
Custody infrastructure is reproduced as source text in each tool; it is not a
separate implementation of the custody algorithm. Request parsing/equality and
output inventory/accounting are independently implemented.

## Attempts and accounting

Build001, readiness001 and audit001 all passed. Review then tightened the auditor
from a minimum poll-count check to an exact reconstruction and required producer
input counters to match the independent custody pass. Build002, readiness002 and
audit002 passed the unchanged panel. No test, retained readiness or audit attempt
failed; intentionally injected fixture failures are preserved in the build records.
All 128 request bytes match across both retained attempts. These engineering repeats
are not independent scientific replications.

The final readiness bundle has 140 files totaling 676,722 bytes; the final audit
bundle has 12 files totaling 203,863 bytes. Both totals and complete inventories
reconciled independently. Recorded elapsed times are cooperative cost receipts,
not benchmark or speedup evidence. Both tools completed within the registered
120-second/128-MiB limits. No hard CPU/RSS enforcement is claimed.

Each tool performed one deduplicated input custody pass, including original P01o
and P01q membership/hashes before conversion. The producer cached 256 bounded
stream bytes for conversion rather than rereading them. Two input-bundle membership
scans are separate from the one producer empty-output scan and one auditor output
inventory. Producer output polls used maintained totals; no terminal full-tree scan
or original custody recheck ran. Counters describe explicit file reads/stats and
ledger operations; recursive input membership traversal is separately reported.

Original seals and all bytes in the 5,127-entry P01o and 4,960-entry P01q bundles
remain unchanged. Closeout verified 315 frozen files, 336 inputs and 631 pre-existing
public receipts. All original and historical sources are untouched. Raw retained
requests remain in ignored local artifacts; published records contain hashes,
sizes, cell identities, statuses, invented controls and audit receipts only.

See the [independent audit](evidence/p01t-002/p01t-audit-002/audit.json),
[128-cell manifest](evidence/p01t-002/p01t-002/manifest.json),
[closeout receipt](evidence/p01t-002/closeout.json) and [closure](p01t_closure.json).

## Next boundary

Separately register validator-only native request acceptance across all 128 saved
requests, without candidate matching or world transitions. A Python transport pass
does not establish native deserialization or semantic validation. Native validation,
campaign integration, performance trials and dynamics remain outside P01t; do not
launch them automatically. P01q remains consumed and unrepaired, science untested,
behavior null/not_executed and E01 unauthorized.
