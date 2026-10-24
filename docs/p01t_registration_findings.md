# P01t saved-input readiness registration findings

2026-10-24. The [protocol](p01t_protocol.json) and
[readiness plan](p01t_readiness_plan.md) now fix transport readiness for all 32 laws,
128 cells and 256 saved P01o streams. No implementation or retained conversion has
started. The future output is exactly 128 inert request files, not trajectories.

Fourteen control families cover complete-envelope transport, typed preservation,
malformed inputs, identities, metadata, independent request mutations, relative
paths, partial writes, terminal failures, reserves, omitted/extra rows and accounting.
The producer may reuse only the two explicitly pinned P01s boundary/accounting
modules. The independent auditor must reconstruct the expected requests without
importing either module or the producer. No raw retained request is published.

The plan incorporates P01s's failed-path and incomplete-accounting lessons: test
relative and absolute launch paths; preserve all128 statuses and first errors;
report unknown exact failure bytes as null with a justified conservative bound;
never confuse known-path bytes with complete output accounting. Original input
custody is a single deduplicated pass, separate from output scans and budget polls.

Eight registration tests passed normally and with Python optimization, with no
failed tests. These are descriptor mutation checks, not execution of the 14 future
control families. The [custody receipt](evidence/p01t-registration-001/static_review.json)
verified 315 frozen files, 336 inputs and all 626 preceding public receipts.
Original P01o/P01q inventory membership, hashes and seal links matched exactly
(5,127 and 4,960 entries). Frozen P01s reusable sources and its independent audit
gate were verified. No saved environment payload was parsed and no request,
keyed evaluation or world transition was produced.

After this registration is committed and pushed, implement the three new registered
paths, test the declared invented controls normally and optimized, then perform
and independently audit the unchanged all128 transport panel. Retain every attempt;
implementation corrections may repeat the same panel only in fresh directories.
Never repair or replace saved inputs or resume consumed P01q. Native semantic
validation, campaign integration, performance measurement and world execution
remain outside scope. Behavioral outcomes stay null/not_executed, scientific
status untested and E01 unauthorized.
