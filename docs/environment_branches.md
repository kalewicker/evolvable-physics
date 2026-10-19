# P00d: environment-aware interventions and publication recovery

This component integrates the P00b intervention semantics with the P00c environment wrapper. It changes neither native laws nor environment phase ordering. The scope is controlled engineering evidence, not a calibrated self-maintenance assay.

## Source identity and transition

`environment-intervention-v1` binds the canonical digest of the entire Environment: profile, schedule, cumulative ledgers, native rules, limits, seed, world, allocators, epoch, and provenance. A change to the schedule or accounting invalidates the request even if the embedded native state is identical.

The request exposes the same zero-to-eight ordered SetState/MoveResources operations as P00b. Native operation application is reused; it has an inner native receipt and an outer environment receipt. The latter binds the whole-wrapper before/after identity and outer request digest. The full wrapper is cloned and validated; channels and initial/import/export ledgers are not editable through this API. External resource moves conserve free inventory and therefore do not count as imports or exports.

Interventions occur between complete epochs, before the next environment phase. They neither advance the clock nor consume a scheduled action. Subsequent environment events can depend on their node-writer IDs. Empty requests are bit-identical no-ops; nonempty shams record an external event. Failed compound requests leave their source unchanged.

## Bundle publication and recovery

Publication creates a new directory and writes, in order:

1. `source.json`: environment checkpoint.
2. `branch.json`: full request, both receipts, and resulting environment.
3. `checkpoint.json`: resulting environment checkpoint.
4. `manifest.json`: completion marker and hashes, published last.

Every file uses exclusive `.pending` creation, complete write and file sync, a no-overwrite hard link to the final name, parent-directory sync, pending-name removal, and another directory sync. A completion marker is never overwritten. Missing manifests indicate incomplete publication. Partial files remain inspectable and are never silently replaced or promoted.

`environment-branch-resume` requires a complete bundle, validates both checkpoints, recomputes the entire requested transition, compares all nested receipts and resulting state, and verifies manifest hashes. A valid hash on a forged receipt is insufficient. A complete standalone checkpoint may still be used with `environment-resume`, but that path does not certify retained branch history; use bundle admission when intervention provenance is required.

Recovery tests exit a child process with code 71 after each of the four publication boundaries. The first three states must fail bundle admission; the final state must load exactly. A partial pending checkpoint must block publication without being overwritten. This demonstrates fail-closed recovery at tested process-exit boundaries; it is not certification against arbitrary power loss, storage corruption, or failure inside every filesystem call. Directory syncing improves durability but does not establish universal filesystem guarantees.

## Frozen integrated fixture matrix

Two families × seeds 0–15 × five arms = 32 cases / 160 arms. Each source has two warmup epochs, followed by six continuation epochs per arm (960 continuation epochs). Two disjoint copies of the driven path 0→1→2 are used: the control copy is 3→4→5. Corresponding nodes have equal type, state, balances, and contact degree. Environment channels are identical up to node/edge IDs and a channel-ID offset of 100. Total initial activation is 4 and total matter is 34.

Each lane supplies 2 activation units at its reservoir per epoch, transports 2 to its oscillator, extracts 1, and burns 1 through native firing. Periodic matter transport is unchanged from P00c. Both lanes are driven independently.

| Family | Target/control operation | Expected six-epoch outcome |
|---|---|---|
| state_arrest | Oscillator state 0→9 at node 1 / node 4 | Target node has zero firings; unaffected node has six |
| replenished_activation | Move reservoir's two activation units to its inert holder, 0→2 / 3→5 | Both oscillators still fire six times because scheduled supply replenishes the transported activation |

Each family includes empty baseline, explicit sham, target, unrelated/control, and immediate rescue. Rescue reverses the exact state/resource operation before continuation; it does not reload the ancestral checkpoint or erase intervention history. Baseline/sham/rescue must agree on physical trajectories. The activation-relocation target deliberately has a null firing effect while its inventory distribution differs; that outcome is retained rather than interpreted as failed intervention machinery.

The labels describe registered fixture controls. They do not establish exchangeability, biological individuality, adaptation, or damage repair in unknown worlds.

## Verification

Python independently applies the nested state/resource edit, verifies the outer identity and preservation of schedule/ledgers, then reconstructs every environment and native step. It checks the fixed two-lane initial world, laws, schedule, source warmup, exact arm operations, rescue chain, and intended outcomes. Both Rust matchers agree on all continuations.

Fresh CLI processes apply and resume target/rescue bundles for both families. Adversarial checks reject source/schedule/ledger drift, altered operations/receipts, missing rescue steps, omitted environment/native phases, missing/truncated bundle files, noncomplete manifests, and forged receipt hashes. Older P00a–P00c suites continue to run unchanged.

## Next gate

Detector calibration is now the next bounded P00 task: specify structure tracking and maintenance endpoints, implement positive and adversarial fixtures, and retain ambiguous classifications. Full P00 and all scientific claims remain unaccepted until those assay gates pass. Event-log crash recovery beyond the tested checkpoint/bundle boundaries remains a stated limitation.
