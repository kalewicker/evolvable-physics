# P01o registration findings

2026-10-22. **The v4 keyed-sampler/static-census registration passed static
review.** This turn registered the next implementation and future zero-epoch
panel; it neither implemented nor invoked a keyed sampler.

The [protocol](p01o_protocol.json) fixes 32 proposals (6000..6031), four initials
(0..3) per proposal and 128 environments. It requires complete ordered records
for both maps and every raw field, independent message/hash/reduction checks,
full Rust/Python output equality and an independent construction/static audit.
There are 119 logical fields per cell, 15,232 per implementation and 6,208 unique
message addresses. These are symbolic address counts, not evaluated draws.

The [static review](evidence/p01o-registration-001/static_review.json) verified
the registration, six unhashed serialization vectors, six literal prefix
arithmetic vectors, 235 frozen project/registration identities and all 438
preceding public receipts. The prior 220-file P01n registration and 172-file
P01k execution freezes also matched before the new freeze was written.
Thirteen tests passed normally and under Python optimization. They reject
changed panels, admission flags, budgets, key scopes/order, vector messages,
state-map offsets and missing/reordered/inconsistent synthetic cells. A patched
SHA function forbids any hash during contract validation; file hashing for
custody occurs separately. Synthetic duplicate tables and zero/positive route
counts cannot admit dynamics or hide missing cells. No test failure occurred.

The report contract explicitly requires a simultaneous donor-state intersection
for joined motifs. Exact constructive states and positive Structural matter
are authored v4 correlations and must not be reported as independent biological
evidence. A namespace change prevents pairing this panel with P01k; this is not
a superiority comparison or a state-versus-matter ablation.

No sampled outcome is available. Behavioral values remain null/not_executed,
and scientific status remains **untested**. P01g's failed continuation gate,
both inconclusive cases, the consumed P01k panel and all previous receipts stay
unchanged. Positive paths or zero static routes have no chemistry continuation
threshold; every table and explicit missing cell must be retained.

After this registration is committed/pushed, next implement only the registered
new sampler/runner/report/auditor paths with literal/mock tests. Keep Cargo and
all frozen sources unchanged. Then prepare a separately committed/pushed full
execution closure and exact-output admission before any v4 keyed evaluation,
including tests or audit helpers. Only that admission can permit the single
future static attempt. World trajectories, favorable-law selection, changed
environment/detector gates and E01 remain unadmitted.
