# P01f fixed-panel execution implementation

2026-10-20. This implementation adds only a fixed authored-witness binary and
separate Python panel/receipt validators. The immutable P01f design, registry,
protocol, source registration and all previous freezes remain authoritative.
The original protocol's design-only admission fields remain false; the separate
`p01f_execution_admission.json` admits exactly `artifacts/p01f-001` after binding
the new execution freeze. It admits no law sampling or E01.

The binary emits one canonical JSON line per family/seed slot, retaining both
Reference and Indexed results, every committed environment frame, activity,
complete detector record, and failed-epoch pre/post states and candidates. Each
matcher starts from the same literal environment with only its seed replaced.
The frozen Rust observers perform validation replays inside the native stage;
these replays are included in that stage's resource usage and are not additional
experimental cases. Observer errors retain the measured prefix. No retry,
replacement, repair, random generator or search path exists.

The panel audit compares both matchers' full outputs. For each matcher it uses
the original Python native interpreter, environment replay, activity extractor
and full detector construction, plus the separately frozen single-pass adapter.
It checks literal counters, endpoint nodes/resources/topology, allocator/event
continuation, declared event sequences, empty-epoch behavior, full rollback,
independently justified size rejection, newborn proposal eligibility, resource-
only inactivity, and maximum live-child bounds. All 48 slots remain in its
receipt, including failed checks. Partial/missing/duplicated/reordered cases fail
closed. Its receipt has no scientific support endpoint beyond authored fixture
reachability.

The runner reuses the existing frozen campaign guard, atomic publication and
process-CPU accounting. Native and Python audit each run once as separate guarded
processes under the original P01f limits. Stdout and stderr share each registered
output allowance (64 KiB reserved for stderr). Reaped peak RSS is checked in
addition to samples; sampled enforcement is not an instantaneous hard bound.
Launch reservations cover the child, guard/serial ps overhead and final sealing.
The new-directory requirement and exact admitted destination prevent reuse of a
consumed attempt. Source/input/binary identities are checked before and after
execution, and snapshots are verified before launching children. All failures
retain a manifest and inventory/seal when publication remains possible.

The execution freeze binds all repository source/validation files, the prior
source-freeze union, embedded detector/generalization/integration registries,
build and test receipts, the release binary, complete pinned Cargo crate source
trees and tool identities. Dependency sources are copied into the local bundle;
machine-specific provenance and raw traces remain outside public compact receipts.
Cargo.lock and offline locked build prevent dependency resolution changes.
Python scripts use only the standard library; its source/extension identities
and interpreter are included in dependency provenance. OS libraries and hardware
are host provenance, not a hermetic reproducible-build claim.

Before the execution freeze, only compilation, linting, structural checks and
mocked receipt tamper tests may run. No registered native or Python witness
transition is evaluated by these tests. Build/test/toolchain receipts are outside
the campaign clock; snapshotting, both guarded stages, inventory construction and
final seal bytes are inside. The final timing observation precedes publication of
the final seal, matching earlier disclosed accounting practice. Later receipt
audits and publication work are outside measured campaign usage.

Passing this gate would establish authored-fixture reachability. A subsequent
bounded sampling-feasibility protocol must separately specify law IDs, initial
distribution, observable reachable behavior and costs before any law draws. It
must retain negatives/disagreements and explicitly address closed activation
limits. No generated-law prevalence or sustained maintenance follows from these
witnesses.
