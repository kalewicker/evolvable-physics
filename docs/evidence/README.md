# Published validation receipts

This directory contains byte-identical manifests, audit receipts, checksum inventories, and test logs from the local P00a–P00g and P01 readiness/development evidence bundles. `publication_inventory.json` lists the files included here and their SHA-256 hashes.

Raw traces, checkpoints, binary outputs, and historical source snapshots remain in the local ignored `artifacts/` directory. The historical `checksums.json` files intentionally inventory both published and unpublished files; they do not imply every listed file is hosted here. Historical source/binary hashes describe the original sealed run, not a claim that each snapshot equals today's source.

To create a complete new bundle from a fresh clone, fetch pinned dependencies with `cargo fetch --locked`, then run `python3 scripts/validate.py artifacts/publication-rerun` in the repository root. Use a new output path. The current runner executes all retained fixture suites and the frozen transfer panel, including the admission audit. The current P00g receipt admits bounded engineering profiles; the newer P01c receipt admits the registered bounded development pilot, and scientific status remains untested. Earlier unadmitted P00f receipts are preserved as historical baseline assessments.

The parent Playground repository, generated raw evidence, build products, and machine-local settings are outside this public repository.

P01a adds the preserved sandbox-blocked attempt 001, the successful fixed 64-run attempt 002, and a complete P00 regression bundle. [P01a findings](../p01a_findings.md) distinguish engineering completion from full-P01 readiness. `p01a-002/independent_audit.json` is a later read-only audit receipt bound to the original sealed manifest and checksum inventory; `suite_equivalence.json` compares all seven retained P00 suite files. These two receipts were written outside the sealed bundles and therefore are not entries in their original checksum inventories.

P01b publishes a sealed reporting-readiness bundle over the 64 retained P01a trajectories and fixed controls. It registers the full development pilot but does not launch it. `supplemental_verification.json` and `supported_prefix_tests.txt` were produced afterward outside that sealed bundle; the supplemental receipt anchors the original bundle and a regression showing that an AP-positive capped prefix still has no full-horizon endpoint. See [P01b findings](../p01b_findings.md).

P01c publishes the 30-check runner-readiness receipt, test logs, checksum inventory and per-control read-only audits. The native/analysis outputs, source/binary copies and deliberately interrupted parent-loss bundle remain local. Readiness admits only the already registered bounded P01 development pilot; it is not evidence that the full pilot ran or that scientific acceptance passed.

P01 publishes the first registered pilot's original sealed manifest, inventory, seal and read-only campaign audit, plus descriptive findings and all 512 slot outcomes. `report_checksums.json` covers the separate report; `publication_context.json` anchors report/context/build/test files added outside the scientific bundle. They are not inserted into the original campaign inventory. The registration is consumed; the 42 unstarted slots and capped prefix must not be resumed under it. See [P01 findings](../p01_findings.md).
