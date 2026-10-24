# P01r: diagnose the failed input boundary and accounting path

2026-10-23. Registration only. The consumed P01q attempt never reached a native
stage. Its first saved input caused `KeyError('native')`, then terminal custody
checking hit the CPU reserve. The original seal, false gates, 127 unstarted cells
and later successful read-only audits remain intact. This is a post-failure
engineering diagnosis, informed by those known results.

The [protocol](p01r_protocol.json) fixes four questions across all 32 laws, 128
cells and both saved streams per cell. First, compare complete saved envelopes,
metadata and nested environment/native key paths against the frozen consumer
contract. Second, identify the producer/consumer accesses and mock substitution
that bypassed the boundary. Third, map recursive byte-accounting call sites and
the loops containing them. Fourth, reconcile early failure, terminal reserve
failure and later custody records without treating one as a replacement for
another. Existing source is read as text/AST, never imported or executed.

No retained input will be converted into a worker request or persisted as an
unwrapped environment. Typed JSON equality must distinguish booleans from
integers, retain metadata and detect nested changes. All 256 stream identities
and all 128 cell rows remain mandatory, including malformed or absent outcomes.
Rule bodies are opaque data for equality; no applicability or mechanism analysis
is admitted. Hashes pin both original inventories and seals and the prior
failure/readiness receipts.

Before inspecting retained payloads, test ten invented interface controls and
ten accounting controls. Complete envelopes contain inert native descriptors;
they are never interpreted. Accounting uses in-memory path/byte maps and Decimal
cost records, with an independent sum/boundary oracle. Temporary and replaced
files, partial failures, snapshots, metadata and seal bytes must remain visible.
No benchmark, watchdog launch, kernel call or sampled-field evaluation is allowed.

Classify findings as confirmed from saved records, source-derived, or unresolved.
Static call sites can show potential repeated traversal; they cannot recover
missing runtime counters or per-operation CPU/wall timing. Keep those quantities
null/uninstrumented. The elapsed time of the diagnostic itself is only its cost
receipt, not an estimate of P01q's runtime breakdown or an optimization speedup.

Implement only the three new paths after this registration is committed/pushed.
A separate auditor must independently check metadata/equalities, source spans,
row membership, descriptors and classifications without importing the reviewer
or old runtime. Each tool has cooperative 120-second/128-MiB output limits and a
1-MiB terminal receipt reserve. Hash references may avoid repeated snapshots of
immutable inputs. Preserve all failed attempts; corrections may only repair the
new diagnosis implementation against the unchanged plan into a fresh directory.

The deliverable is an audited diagnosis and a specific recovery-design
recommendation. It does not authorize a corrected runner, performance assay or
new trajectories. Those require a separately justified protocol and execution
admission. No P01q retry/resume, repaired historical input, favorable-law subset,
changed gate or E01 follows. Behavioral outcomes remain null/not_executed and
scientific status remains untested.
