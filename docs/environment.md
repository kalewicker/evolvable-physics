# P00c environment profile and fixed engineering protocol

Profile: `p00c-local-driven-v1`. The unchanged `p00a-local-closed-v1` kernel is embedded as the native substep. This wrapper owns scheduled supply/extraction and transport; these are fixed environment laws, not outer-search mutations or biological agents.

## Epoch contract

Validate the entire environment, clone it, execute due channels by ascending channel ID, then execute one native epoch. Commit the complete wrapper only after every validation and native operation succeeds. A native matching cap or overflow after successful environment actions rolls back those actions, their ledgers, writer metadata, event counters, and the native world together.

Channels have unique u64 IDs, an inclusive start, optional exclusive end, and a positive integer period. A channel is due when `start <= epoch < end` (if bounded) and `(epoch-start) % period == 0`. At most 32 channels are allowed. No mutable schedule cursor or random environment stream exists. Checkpoints preserve the schedule and current epoch, so interrupted continuation cannot repeat or skip an environment phase.

Actions:

- Supply: add a positive fixed activation amount at a registered existing node and increment cumulative injection.
- Extract: remove exactly a positive fixed activation amount from an existing node and increment cumulative extraction. This is environmental removal, distinct from native dissipation.
- Transport: move specified free matter and/or activation from one endpoint to the other along a registered **binary Contact edge**, in its declared endpoint order. Structural edges, reversed endpoints, remote node pairs, and higher-arity contact edges are not valid routes in this profile. At least one amount is nonzero.

An unaffordable extraction or transport is recorded as `insufficient_resource`, transfers nothing, changes no writers, and allocates no event ID. It is not clipped to the available balance. Supply overflow, invalid/missing route or node, invalid schedule, and any invariant failure are errors, not skipped events. Referenced nodes/routes must remain valid even when their channels are not due; native deletion of a registered environmental node causes the full epoch to reject. This pins configured infrastructure explicitly and is a baseline restriction.

Environment actions are sequential. Later channels see earlier channels' resource changes; native matching sees the completed environment phase. This is an explicit discrete scheduling policy, not simultaneous diffusion or continuous kinetics. Changing channel IDs can change execution order and therefore physics. Reordering stored channels without changing their IDs cannot change physical evolution, though configuration digests retain storage order.

## Ledgers

The original matter invariant remains unchanged. The wrapper adds constant `initial_activation` and cumulative u64 `injected` and `extracted` counters:

```
free matter + bound node/edge matter = initial matter_total
free activation + native dissipated = native activation_total
initial_activation + injected = native activation_total + extracted
```

Equivalently, initial plus imported activation equals free plus dissipated plus extracted activation. The native `activation_total` is the current net admitted inventory in this profile, not the initial inventory; its old closed-profile meaning is unchanged outside this wrapper. Ledger comparisons use u128 sums; each stored counter and node balance remains checked u64. Cumulative overflow rejects rather than wraps or saturates. Matter is never supplied or extracted. This bookkeeping is not a thermodynamic model.

## Provenance and checkpoint identity

Every due attempt records channel ID, status, before/after full-wrapper digest, read/write keys, prior writer IDs, and optional event ID. Successful actions share the native world's monotone event namespace and write node keys. Transport reads both endpoint node and adjacency keys. Insufficient-resource attempts retain read dependencies without becoming writers. Native events can therefore depend on environment events. The fixed schedule and epoch explain timing; ledger counters are accounting, not rule-visible mutable resources.

Each frame includes the post-environment/pre-native Experiment and the full native frame. This makes phase ordering independently checkable. Records are conservative execution dependencies, not evidence of causal necessity.

Environment checkpoints use `environment-checkpoint-v1`, bind the full wrapper and schedule by canonical SHA-256, and use the existing no-overwrite publication helper. Old `resume`/`branch` commands reject them; use `environment-resume`. P00b state-changing interventions on an environment wrapper are not yet supported. Extracting and manually running just its native payload would discard its environment and is not valid continuation. Preserve trace/receipt history alongside checkpoints.

## Fixed fixture matrix

Four modes × seeds 0–15 × 8 epochs = 64 runs / 512 epochs. Initial worlds are identical: contact path 0 → 1 → 2 and disconnected node 3. Node 0 holds two activation units; every other node starts with zero. Nodes 1 and 3 are native oscillators that burn one unit per firing. Node 0/2 are inert holders. Node matter balances are 8, 4, 0, 4; total matter is 22 including four nodes and two edges.

| Mode | Channels | Expected native firings in eight epochs |
|---|---|---:|
| closed | None | 0 |
| local_transport | ID 20 moves 1 activation 0→1 every epoch; ID 40 moves 1 matter 1→2 at epochs 1,3,5 | 2 |
| driven | ID 10 supplies 2 activation at node 0; ID 20 moves 2 units 0→1; ID 30 extracts 1 unit at node 1, every epoch; ID 40 as above | 8 |
| blocked | Same supply as driven, with no transport | 0 |

Node 3 must remain unchanged in every mode. Driven and blocked each receive 16 units; only driven extracts 8. Transport modes move exactly three matter units. The local-transport mode records six unfunded activation transfers without spending resources or allocating events. These constructed outcomes test locality and bookkeeping, not persistence or adaptation.

## Gate and limits

The independent Python interpreter reconstructs due channels, exact order, transfers, imported/extracted totals, dependency parents, event IDs, and native transitions. Fixture outcomes, corrupted traces, invalid geometry/schedules, full-epoch rollback, and fresh-process continuation must pass. The original kernel and intervention suites must remain passing.

No changing contact topology, stochastic diffusion, continuous kinetics, joint environment/intervention API, arbitrary power-loss recovery, structure detector, or scientific search is admitted by this gate. After this component, complete environment-aware interventions and recovery coverage before detector calibration and final P00 admission.

## P00d integration update

The previously deferred environment-aware intervention API is now implemented separately; see [P00d](environment_branches.md). Native-only commands still reject environment checkpoints.
