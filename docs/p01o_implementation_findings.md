# P01o implementation and literal/mock readiness

2026-10-22. **The separate v4 samplers, census runner, static report and
independent auditor are implemented and passed literal/mock readiness.**
Registration commit `45ff81d9d2d0c8ccd7eea5e51f263abdc00cb6ad` preceded this work.
All 235 frozen project/registration files, all 443 preceding public receipts,
and the older P01n/P01k freezes remain unchanged. No Cargo change was needed.

## Implemented behavior

Both samplers retain the ordered 119-field trace: type map, state map, all eleven
raw fields per slot, then initial-world fields. Constructive states and material
funding follow the frozen v4 contract. Python uses the frozen literal adapter;
the new Rust binary contains separate v4 construction code. Literal modes use
injected fields and deliberately fake prefix metadata, never SHA-derived draws.
The sampled entry points reject missing or inactive execution admission before
using a keyed source. No execution admission has been created here.

The runner creates all 128 planned cells before any source call and enforces
per-stage reservations, bounded process execution, stop-on-first-failure,
explicit missing cells, snapshots, cost accounting and final receipts. Both
maps and ordered rules must remain identical across a proposal's initials.
Its frozen process guard allocates the combined output budget between stdout
and stderr (64 KiB reserved for stderr), which can stop a stream conservatively
before the combined ceiling. Live sampled-RSS integration has not been exercised
by this literal/mock milestone.

The report retains every body/combination, type path and initial inventory.
Joined motifs require one common donor-state intersection. Designed v4
state/material coherence is checked as an engineering invariant; missing
funding or child-donor bodies remain possible. The independent auditor rebuilds
ordered messages, fields and complete environments using a separate frozen
operation oracle, and separately derives report predicates from raw fields
with the registered effective overrides. It rejects reordered records,
boolean map substitutions, altered report denominators/claims and missing cells.
Behavioral outcomes remain null/not_executed.

## Evidence

| Readiness check | Result per implementation |
| --- | ---: |
| Complete frozen P01n literal responses | 17,727 matched |
| Successful literal field reads | 597,448 matched |
| Recorded authored mock assemblies | 2,916 matched |
| Mock draw records, with fake digest metadata | 347,004 verified |
| Injected full pipeline test | 128 cells, duplicate tables retained |

Every recorded assembly also passed independent raw-to-operation/accounting and
static-report checks. The large authored assembly batch revisits mock proposal
coordinates with different literal tables; it is not a sampled census. The
separate 128-cell integration test verifies shared-law reuse across initials.
Neither establishes actual SHA-sampler equivalence or route prevalence.

Ten Python tests passed normally and optimized; four Rust tests, Clippy with
warnings denied and the release build passed. Python tests reject SHA calls on
v4 keyed preimages, and the Rust test build replaces keyed hashing with a panic.
Unhashed primitive vectors and literal prefix arithmetic were checked. The
full pipeline uses injected stages; reservation/failure tests do not launch the
sampled runner or claim its live RSS watchdog was exercised.

There were two passing build/test and full readiness attempts, both retained.
After the first pass, review tightened audit rejection of boolean maps, altered
report denominators/scientific status and missing manifests, adding negative
regression cases. The identical frozen input files and byte-identical binary
were then rechecked with the final auditor in attempt 002. No input, criterion
or sampled result was changed; no test/build/readiness failure occurred.

The final bulk readiness attempt took 14.771316 seconds including its inventory,
within its 300-second development limit. Literal outputs were 25,103,603 bytes
and recorded outputs 96,646,832 bytes per implementation, each within the
60-second/256-MiB combined-stream development guards. These bulk checks use
literal inputs only; they do not consume or validate the future per-cell sampled
campaign budget. The later read-only integrity audit checked both complete
inventories, snapshots, retained binary, registered input coordinates,
differential streams, ceilings and unchanged inputs without invoking adapters.

Full JSONL streams, binary and snapshots remain in ignored artifacts. Compact
byte-identical receipts are published under
[evidence/p01o-implementation-001](evidence/p01o-implementation-001/assessment.json).
The original checksum inventories are unchanged; completion, later integrity
receipt, build logs and closeout documents are bound separately by publication
context.

## Next boundary

[Readiness](p01o_implementation_readiness.json) admits implementation/mock
correctness only. **No v4 keyed source, sampled census, candidate enumeration,
world transition, witness or detector ran.** Scientific status remains untested.
P01g's failed gate and both inconclusive cases, and all P01k outcomes, remain
unchanged. No favorable-law selection, repair, filtering or reroll is admitted.

Next verify and freeze the full source/dependency/tool/binary/input closure and
bind one exact fresh output path in a separate execution admission. Commit/push
that closure before the first namespace-keyed hash evaluation, including audit
helpers or tests. Only then can the single registered zero-epoch census run;
no world trajectories or E01 follow automatically.
