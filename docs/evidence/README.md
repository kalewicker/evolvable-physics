# Published validation receipts

This directory contains byte-identical manifests, audit receipts, checksum inventories, and test logs from the local P00a–P00g evidence bundles. `publication_inventory.json` lists the files included here and their SHA-256 hashes.

Raw traces, checkpoints, binary outputs, and historical source snapshots remain in the local ignored `artifacts/` directory. The historical `checksums.json` files intentionally inventory both published and unpublished files; they do not imply every listed file is hosted here. Historical source/binary hashes describe the original sealed run, not a claim that each snapshot equals today's source.

To create a complete new bundle from a fresh clone, fetch pinned dependencies with `cargo fetch --locked`, then run `python3 scripts/validate.py artifacts/publication-rerun` in the repository root. Use a new output path. The current runner executes all retained fixture suites and the frozen transfer panel, including the admission audit. The current P00g receipt admits bounded engineering profiles; P01 readiness remains incomplete and scientific status remains untested. Earlier unadmitted P00f receipts are preserved as historical baseline assessments.

The parent Playground repository, generated raw evidence, build products, and machine-local settings are outside this public repository.
