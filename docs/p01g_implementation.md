# P01g fixed campaign and event-level audit

2026-10-20. This adds the fixed campaign, cell audit, receipt auditor and synthetic
tests in separate files. All earlier frozen sources and the P01g sampler/protocol
registration remain unchanged. A separate full execution freeze/admission is
required before the first hash-keyed sampler construction or native trajectory.
The only proposed output is `artifacts/p01g-001`, once, with all 64 cells retained.

The campaign reuses `campaign_guard`, `pilot-worker`, `pilot-report`, original
`pilot_reporting` Python verification and the separate single-pass adapter. It
publishes the entire pending manifest before generating any law, snapshots the
frozen sources/dependencies/binaries, and runs generation, native, Rust reporting
and Python audit as separate guarded stages per cell. It independently constructs
and compares the Python initial state before native execution and again inside
the cell audit. Those are validation reconstructions of the same cell, not new
sampled proposals. All generation and reconstructions are inside campaign cost.

The cell audit first verifies the entire trajectory/report with both frozen
Python paths. A further checked committed-event application emits physical
mechanism records, updating writer/event metadata and comparing every endpoint.
Every frame also receives the original complete pattern/binding-budget census.
Per-event before/after records distinguish integrated birth funding from later
Structural Transfer, identify descendants by actual created donor IDs and retain
leaf-deletion refunds. This construction relation makes no biological ancestry
or causal reproduction claim.

Visibility requires that the actual funded newborn is live in the retained
sample and appears in proposals from both estimators at that same sample. The
earliest qualifying sample and both complete proposals are retained per newborn.
Recycling records must refer to an earlier birth of that same ID, and a visible
birth/recycling loop must have its visible sample before deletion. Initial nodes
and fabricated prehistory do not qualify. Orphan observations are compressed per
born node into first/last event IDs and the exact number of observed post-event
states without incident Structural edges; these are not uninterrupted-duration
claims. Raw traces retain every state needed to inspect intermediate events.

Only complete independently verified horizons contribute to the frozen mechanism
continuation gate. Censored prefixes retain observed IDs/counts as lower bounds,
with null full-horizon counts and AP. Failed/unstarted cells retain null
unobserved endpoints and explicit reasons. All 16 law summaries retain all four
initial states, duplicates are reported and qualifying tables count once. A
legitimate mechanism-negative result can have a passing engineering gate.

The original process/campaign limits and launch policy are unchanged. Each stage
reserves its full wall allowance, twice that in CPU, its output and the 32 MiB
metadata reserve, plus five seconds of conservative time/CPU sealing margin.
Native stdout permits exactly 4 MiB trace and stderr 256 KiB summary; other
stages reserve 64 KiB of their total output allowance for stderr. Reaped peak RSS
is checked in addition to sampling. Sampling is not a hard instantaneous bound.
No unavailable reservation is bypassed. Censored cells may be fully audited and
retained while remaining fixed cells proceed if reservations permit; a failed
stage stops the batch. Interrupted guards are terminated/reaped and their
available receipts retained. No resume, replacement or repair path exists.

Aggregate CPU includes the parent and reaped descendants. Build/static tests
precede campaign measurement. Sources, dependencies, guard work, generation,
both native matcher/report validation work, all Python checks, extraction,
summarization and inventory publication are inside the campaign clock. Seal
bytes are included; final timing precedes publication of the final seal. Later
receipt audits/publication are outside measured usage. Stage sums use a fixed
stage order so JSON key sorting cannot change floating-point display arithmetic;
the resource ceilings are never relaxed.

The read-only receipt auditor checks full inventory closure, source/dependency/
binary and input identities, every retained stage descriptor/output/guard,
all cell/report/extraction receipt links, fixed slot order, visibility and
recycling proof links, summaries, null endpoints, ceilings and the final
engineering/mechanism decisions. It performs no sampler call or transition.
It preserves negative or incomplete outcomes without treating them as evidence
of impossibility. Original negative/inconclusive P01 outcomes remain unchanged.

Before freezing execution, new tests use invented before/after records and
synthetic bookkeeping only. They do not invoke a transition interpreter, read
registered trajectories, construct a hash-keyed law or rehearse the real panel.
Tests exercise funding/attachment rejection, same-ID and cross-generation
records, non-Structural funding exclusion, original-node exclusion, disagreement,
orphan compression, null endpoints, negative/positive/incomplete decisions,
reservations, stream splitting, deterministic cost display and assertion guards.
