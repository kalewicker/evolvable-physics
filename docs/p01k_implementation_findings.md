# P01k implementation: literal/mock readiness passed

2026-10-20. **The registered implementation is complete and passed literal/mock
checks. No keyed sampler message has been hashed, and the static census has not
run.** Sampling remains blocked by the absent execution freeze/admission.

Implemented at new paths, preserving all 149 registration-frozen file identities:

- Independent [Rust](../src/bin/generator-v3.rs) and
  [Python](../scripts/generator_v3.py) keyed-source implementations, serialization,
  prefix/modulo arithmetic, complete draw records and admission checks.
- A [runner](../scripts/p01k_census.py) that writes all 128 planned cells before
  sampling, reserves registered resources, uses the unchanged watchdog, stops on
  failure, retains missingness and seals the prefix.
- A [static report](../scripts/p01k_static.py) of every law/body pair, joined
  motif, type path and initial inventory, keeping behavioral outcomes null.
- An [independent auditor](../scripts/audit_p01k.py) that reconstructs messages,
  raw fields, full environments and report predicates, plus a post-seal mode
  that hashes files only and does not repeat any sampler-message evaluation.
- A shared admission/custody helper and separate literal-only preflight/tests.

Python reuses the frozen literal adapter's construction API. Rust keeps an
independent constructor in its new binary; the old Rust source remains intact.
Neither imports a matcher, transition worker or detector. Actual keyed entry
points require the exact admitted directory, source/binary identities, a full
128-cell manifest and the currently active stage before field hashing.

## Measured engineering checks

The [preflight assessment](evidence/p01k-implementation-001/assessment.json)
records exact Rust/Python equality and independent output invariants for:

| Literal/mock panel | Count per implementation |
| --- | ---: |
| Frozen individual rule cases | 11,664 |
| Frozen eight-slot environment assemblies | 972 |
| Frozen local barriers | 8 |
| Frozen invalid inputs | 12 |
| Frozen ignored-field alternatives | 15 |
| Total frozen literal responses | 12,671 |
| Additional recorded mock assemblies | 972 |
| Fake draw records in those assemblies | 112,752 |

Recorded assemblies use the same frozen assembly vectors with explicit cell
metadata and **fake digests made from literal raw values**, not SHA-256 outputs.
Their preimage strings, prefixes, reductions, map/rule/initial scopes and full
environments are checked independently. They are not observations from the
registered proposal panel, despite using its numeric metadata labels.

All four bounded child stages completed: each literal stream retained
11,458,375 bytes and each recorded-mock stream 31,394,258 bytes, below separate
64 MiB ceilings; all finished below 30 seconds. Preflight including inventory
creation took 5.524536 seconds against its 120-second development ceiling.
These receipts do not forecast keyed sampling, watchdog or trajectory costs.

Four Rust tests, ten Python tests, Clippy with warnings denied and release build
passed. The Python suite rejects every actual SHA-256 call whose bytes begin
with the v3 keyed-message prefix. It tests primitive strings/arithmetic, absent
admission, raw-field/preimage/operation corruption, missing funding, zero matter,
missing descendant donors, reservations, stop-on-first-failure and a complete
128-cell pipeline with injected mock stages and a literal digest oracle.

A regression covers a subtle state distinction: a wildcard birth donor can
intersect pairwise with funding state 0 and recycling state 1, while no one
donor state satisfies all three. Joined motifs require joint state intersection,
not just two pairwise flags. The independent report audit checks this separately.
Immediate child-state acceptance, material transfer, child-donor typing and
creation-time resource insufficiency remain distinct predicates.

The [integrity receipt](evidence/p01k-implementation-001/integrity_audit.json)
verifies the 19-entry original inventory, completion linkage, source snapshots,
built binary, all four stream sizes/counts/ceilings, all 149 frozen identities
and all 366 preexisting public receipts. It calls no adapter or keyed source.
Completion, later integrity audit, build/test logs and final documentation are
outside the original checksum inventory and separately bound by publication
context. Raw literal inputs/outputs, mock digests, source snapshots and binaries
remain local; public compact receipts are byte-identical copies.

## Remaining boundary

The [readiness record](p01k_implementation_readiness.json) admits no sampling.
The actual SHA-backed source path, live sampled-RSS watchdog integration and
end-to-end keyed census have deliberately not run. Mock equality cannot prove
finite sampler equivalence or tell us how many sampled laws contain useful
routes. The fixed actual census remains unconsumed.

Next prepare and verify the complete execution source/dependency/tool/binary/
input freeze and exact output-path admission, then commit/push them before any
keyed call, including independent audit calls. Only afterward execute the
single registered 32-law/128-environment static panel with its original budgets,
all negative/duplicate/unstarted cells and no filtering, repair, reroll or retry.
Audit and close that attempt without interpreting static paths as world
behavior. No trajectory, changed environment/detector, E01 or scientific
capability claim is admitted; P01g's failed gate and both inconclusive cases
remain unchanged. Scientific status remains **untested**.
