# Published validation receipts

This directory contains byte-identical manifests, audit receipts, checksum inventories, and test logs from the local P00a–P00g and P01 readiness/development evidence bundles. `publication_inventory.json` lists the files included here and their SHA-256 hashes.

Raw traces, checkpoints, binary outputs, and historical source snapshots remain in the local ignored `artifacts/` directory. The historical `checksums.json` files intentionally inventory both published and unpublished files; they do not imply every listed file is hosted here. Historical source/binary hashes describe the original sealed run, not a claim that each snapshot equals today's source.

To create a complete new bundle from a fresh clone, fetch pinned dependencies with `cargo fetch --locked`, then run `python3 scripts/validate.py artifacts/publication-rerun` in the repository root. Use a new output path. The current runner executes all retained fixture suites and the frozen transfer panel, including the admission audit. The current P00g receipt admits bounded engineering profiles; the newer P01c receipt admits the registered bounded development pilot, and scientific status remains untested. Earlier unadmitted P00f receipts are preserved as historical baseline assessments.

The parent Playground repository, generated raw evidence, build products, and machine-local settings are outside this public repository.

P01a adds the preserved sandbox-blocked attempt 001, the successful fixed 64-run attempt 002, and a complete P00 regression bundle. [P01a findings](../p01a_findings.md) distinguish engineering completion from full-P01 readiness. `p01a-002/independent_audit.json` is a later read-only audit receipt bound to the original sealed manifest and checksum inventory; `suite_equivalence.json` compares all seven retained P00 suite files. These two receipts were written outside the sealed bundles and therefore are not entries in their original checksum inventories.

P01b publishes a sealed reporting-readiness bundle over the 64 retained P01a trajectories and fixed controls. It registers the full development pilot but does not launch it. `supplemental_verification.json` and `supported_prefix_tests.txt` were produced afterward outside that sealed bundle; the supplemental receipt anchors the original bundle and a regression showing that an AP-positive capped prefix still has no full-horizon endpoint. See [P01b findings](../p01b_findings.md).

P01c publishes the 30-check runner-readiness receipt, test logs, checksum inventory and per-control read-only audits. The native/analysis outputs, source/binary copies and deliberately interrupted parent-loss bundle remain local. Readiness admits only the already registered bounded P01 development pilot; it is not evidence that the full pilot ran or that scientific acceptance passed.

P01 publishes the first registered pilot's original sealed manifest, inventory, seal and read-only campaign audit, plus descriptive findings and all 512 slot outcomes. `report_checksums.json` covers the separate report; `publication_context.json` anchors report/context/build/test files added outside the scientific bundle. They are not inserted into the original campaign inventory. The registration is consumed; the 42 unstarted slots and capped prefix must not be resumed under it. See [P01 findings](../p01_findings.md).

P01d publishes the read-only diagnostic manifest, inventory, input campaign audit, corpus counts, all 470 slot diagnoses and the 33 unchanged inconclusive cases. Its original checksum inventory also covers unpublished diagnostic source snapshots. The later `tests.txt` and `publication_context.json` remain outside that diagnostic inventory; publication context anchors the test log, source-level argument, closure and next offline protocol. No new world runs or detector reruns occurred. See [P01d findings](../p01d_findings.md).

P01e publishes the immutable offline-preflight manifest/inventory/seal, fixed-panel fixture receipts, and per-stage guard/output receipts (no raw trajectories). Its checksum inventory also covers unpublished source snapshots and mutated record copies; published stage files are byte-identical originals. The v1 receipt-auditor traceback, later v2 read-only audit, preflight/post-correction test logs and publication context are outside the original bundle. Context binds those external files and the post-hoc correction source. The candidate/harness freeze, timing inputs, gate and measurements were not changed or repeated. See [P01e findings](../p01e_findings.md).

P01f registration publishes a static schema/census/inventory review and its checksum inventory. The separate test log and publication context anchor later review documentation and unchanged kernel/build hashes. No native world, candidate enumeration or transition application was executed; all 48 witness cases and their event/resource totals are predictions awaiting a separate implementation/execution freeze. This is not a simulator-run seal or reachability admission. See [registration findings](../p01f_findings.md).

P01f execution publishes the subsequent single-batch manifest, inventory, seal,
panel and receipt audits, stage guard/descriptors and pre-execution build/lint/test
logs. All 48 authored cases passed; see [execution findings](../p01f_execution_findings.md).
The implementation freeze/admission was committed and pushed before execution.
Raw transition records, source/binary copies and dependency snapshots remain
local. The checksum inventory covers those unpublished files too. The separate
receipt audit and publication context are outside the original bundle; context
binds byte-identical copies, pre-execution logs and later closeout documentation.
The registration is consumed. Reachability admission concerns authored fixtures;
the law sampler is not implemented and no law draw or E01 is admitted.

P01g registration publishes the subsequent static 16-law/64-trajectory protocol
review and its inventory, plus build/lint logs, three mock-field Rust tests and
40 Python tests. No hash-keyed law construction or native transition ran. The
separate publication context binds those original copies and later status and
findings. The registration freeze covers sampler sources, not a future execution
binary/dependency admission. The fixed campaign and event-level mechanism audit
remain to be implemented and frozen before sampling. See [P01g findings](../p01g_findings.md).

P01g execution publishes the subsequent single-batch manifest, assessment,
inventory, seal and read-only receipt audit, all 64 original cell-audit outputs
(renamed to `runs/SLOT/receipt.json`), the two inconclusive detector reports and
pre-execution build/test logs. Publication context maps every byte-identical copy
to its original retained path and binds the later closeout documents. All 256
guard results remain in the manifest; full descriptors, raw trajectories and
source/dependency/binary snapshots stay local and in the original inventory.
Engineering passed for all 64 cells; the mechanism continuation criterion failed
with zero newborn recycling loops. Both inconclusive labels and all negatives
remain unchanged. The registration is consumed; next scope is read-only
diagnosis, with no new sampling or E01. See [execution findings](../p01g_execution_findings.md).

P01h publishes the subsequent read-only diagnostic manifest, inventory, input
receipt audit, full law/cell diagnoses, findings and retained inconclusive cases.
Its later independent kind-matrix audit and two targeted test logs are outside
the original diagnostic inventory. Publication context binds those copies,
later audit sources and the conditional source argument. Raw source snapshots
remain local; no sampler, interpreter, native executable or subprocess was
called during the diagnostic/audit. The failed P01g gate is unchanged. See
[diagnostic findings](../p01h_findings.md) for the exact-table kind restriction
and design-only next scope.

P01i publishes a design-only static review over all 27 abstract kind maps and
eight birth-donor subsets, finite field-alphabet compatibility counts and
cross-checked type paths. It includes no rule tables, initial worlds, sampled
laws or trajectories. Publication context binds the byte-identical local
receipt and final design/checker/status files. It is not an execution seal or
sampling admission. See [design findings](../p01i_findings.md).

P01j registration publishes a static descriptor-census review and the optimized-
Python registration-test log. Publication context binds the byte-identical
copies, final findings/guidance and 130-file registration freeze. This is not
adapter execution or law sampling: no rule table or initial world was built.
The next literal-field implementation step is bounded by the fixed registration;
future sampling and world execution remain unadmitted. See
[registration findings](../p01j_findings.md).
