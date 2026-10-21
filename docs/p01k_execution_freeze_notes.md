# P01k execution freeze and admission

2026-10-20. The [freeze](p01k_execution_freeze.json) and
[admission](p01k_execution_admission.json) bind one static census to
`artifacts/p01k-001`: 32 fixed laws, four initial states each, zero epochs.
They must be committed and pushed before any keyed sampler/audit evaluation.
The [pre-execution review](evidence/p01k-execution-readiness-001/readiness.json)
verifies 172 project/input/build-receipt files, 3,088 dependency files, four
tools and the existing tested release binary. No keyed evaluation occurred in
preparing or checking this freeze.

The pinned Cargo manifest/lockfile and fresh Cargo metadata preserve the
dependency-package closure. Every dependency/tool byte from the prior complete
closure was rechecked; none changed. The release binary and eight implementation
source hashes match the successful literal/mock readiness record, so no rebuild
or repeat of that passed preflight was necessary. Compiler/Python/platform
metadata and the previous successful build/test logs are bound in the freeze.
The recorded closure is not a hermetic OS/hardware or instantaneous-RSS claim.

The sole admitted sampled command, after the commit/push gate, is:

```sh
python3 scripts/p01k_census.py artifacts/p01k-001
```

It requires process-memory sampling capability. The runner probes it before
creating the one-attempt directory, writes every planned cell before drawing,
and stops/seals on the first mismatch, guard failure or unavailable reservation.
Preserve failures, zeros, duplicates and unstarted cells. No resume, retry,
replacement, repaired draw, threshold relaxation, favorable-law subset or
trajectory experiment is admitted. After completion, the post-seal audit hashes
files only; it must not repeat namespace-keyed evaluations.

This admission concerns sampler/census engineering only. Static routes are not
observed chemistry. All behavioral endpoints remain null/not_executed; the
P01g failed gate and both inconclusive cases remain unchanged. No world worker,
matcher, transition interpreter, detector, new environment or E01 is authorized.
