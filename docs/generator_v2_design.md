# Generator v2: attached birth and recoverable leaves

Design registration, 2026-10-19. **The proposed v2 alphabet removes v1's template-level prohibition on attached, funded newborns and leaf deletion, using the existing kernel.** This document specifies a future distribution and authored engineering witnesses; neither the sampler nor the witness runner has been implemented or executed. It does not establish that a generated law exhibits these behaviors. The frozen v1 generator, campaign and scientific outcomes remain unchanged.

## Versioned distribution

The namespace becomes `p01-generator-v2`. Retain v1's draw construction: first 16 hexadecimal digits of SHA-256 of canonical JSON `[namespace, proposal, initial, field, index]`, interpreted as big-endian u64 and reduced modulo the stated range. Retain modulo bias and duplicate bodies under distinct rule IDs. Do not rejection-sample, ensure a template appears, repair an unaffordable rule, or insert a witness law. There are still eight rule slots and four initial states per future law, but **no proposal IDs or sampling panel are registered here**.

For rule IDs 0..7, `form` modulo 8 selects the table below. Rule draws use initial=0. Preserve v1 field names/ranges: `kind0`, `kind1`, `new_kind` are 1+draw modulo 3; `state0`, `state1` modulo 4 select 0..2 or wildcard=3; `value` modulo 3; `sign` modulo 2 gives -1/+1; `amount` is 1+draw modulo 2; transfer `matter` modulo 2. New field `route` modulo 2 applies only to form 3: 0=Contact, 1=Structural. Unused fields have no effect. Pair endpoints and directions are ordered `[0,1]`, kind 0. Birth's created slot is 1 because its matched pattern is unary.

| Form | Matched pattern | Ordered operations |
| --- | --- | --- |
| 0 | unary | SetState(0, value) |
| 1 | unary | AddState(0, sign) |
| 2 | unary | Burn(0, amount) |
| 3 | pair joined by selected route | Transfer(0→1, matter, amount activation) |
| 4 | unary donor | CreateNode(account 0, new_kind, value); CreateEdge(account 0, Structural kind 0, ends [0,1]); Transfer(0→1, matter 1, activation 1); Burn(0, 1) |
| 5 | Contact pair, identical Structural edge absent | CreateEdge(account 0, kind 0, ends [0,1]) |
| 6 | Structural pair | DeleteEdge(account 0, kind 0, ends [0,1]) |
| 7 | Structural parent→target pair | DeleteEdge(account 0, kind 0, ends [0,1]); DeleteNode(target 1, recipient 0); Burn(0, 1) |

Forms 4 and 7 deliberately replace the old standalone birth and opposite-direction deletion bodies. Their funding/burn amounts are fixed at one; the generic `amount` draw does not change them. No additional donor-state write or automatic phase/cycle is inserted. Form 3's Structural route allows resources to reach attached descendants. Other forms keep their v1 semantics, including state changes and edge-only edits with no required Burn. A universal energetic cost for activity is not established.

Retain the eight original nodes with eight free matter and eight activation each, kinds 1..3, states 0..2, the directed immutable Contact ring, and zero to eight initial parallel Structural ring edges. Retain all corresponding draw labels, scheduler draw modulo `2^64-1`, closed environment/no channels, and limits (4,096 full pattern matches, 65,536 partial pushes, 128 nodes, 256 edges). Match-budget accounting still includes operation-inapplicable matches; reported applicable candidates do not. The new namespace changes every draw identity. No comparison under identical laws is implied.

## Source-level reachability argument

The existing rule validator permits subsequent operations to reference the newly appended slot. The existing runtime privately stages all operations, then publishes only a successful candidate. An attached birth requires donor matter ≥3 and activation ≥2: one matter binds the node, one the edge, one becomes child free matter; one activation becomes child free activation and one is dissipated. Net donor changes are `(-3 matter, -2 activation)`, child resources `(1,1)`, bound inventory `+2`, dissipation `+1`. Failure at any operation discards all earlier staged edits. No global allocator scan or remote matching is introduced.

The birth event changes a Structural edge joining donor and child. The frozen physical-change definition therefore credits both endpoints; unlike v1's isolated birth, the event need not remain a singleton. When no other Structural component interferes, both estimators can propose the pair at the next sample. This is proposal eligibility, not AP: duration, continuity, feature, activity, identity, size and agreement gates remain unchanged.

An attached child can receive further resources by a form-3 Structural transfer, become a donor when sufficiently funded and matched, and add its own child. A form-7 recycle succeeds for a target with only the matched Structural edge and no Contact incidence, provided donor activation plus the child's returned activation can pay the final Burn. It refunds the edge, bound node and all remaining child free matter/activation exactly once, then dissipates one activation. In particular, a standard birth followed by leaf recycling restores the donor's matter, costs two activation in total, and leaves monotonically advanced allocation/event counters and deletion-writer tombstones.

Contact edges never change. Original ring nodes remain undeletable. Every noninitial Structural edge is either an original Contact-pair edge or a parent→newborn edge; the latter form a forest grown from original nodes, possibly disconnected by edge deletion. No template joins already separated newborn branches. A target with descendants/other incident edges fails deletion atomically. Edge-only deletion may orphan a child, and the alphabet has no unary orphan-reclamation operation. Thus attached birth is a commit-time property, not an invariant that every live child stays attached or recyclable. These restrictions are retained, not silently repaired.

For generated initial matter `80+S`, live nodes remain bounded by `matter_total - 8` because the eight Contact edges retain inventory. Unlike v1, `next_node == live_nodes` is no longer valid: deletion leaves gaps. If B births have committed, `next_node = 8+B`. Each birth burns one activation and the environment is closed, so B≤64 for this proposed initial distribution (a conservative bound, not an attainable maximum). State/edge-only activity can still continue without Burn, and constructive growth remains bounded by the declared resources and counters. None of this establishes thermodynamics or open-ended growth.

These are conditional arguments from template bodies and kernel semantics, not machine-checked dynamical results. The fixed witnesses instantiate legal template bodies. They do **not** supply a proposal ID whose finite hash-keyed draw produces that rule table; representability in the template alphabet is not proof of a preimage or sampling probability in that deterministic sampler. Several witness states are intentionally authored resource/topology boundaries outside the generator's initial-state distribution.

## Fixed witness panel

The [protocol](p01f_protocol.json) expands the 12 families in the [literal registry](p01f_witnesses.json) across scheduler seeds 0,1,2,3, family-major: 48 fixed cases. Each has exactly eight rule instances. Unused slots have kind-1/state-2 SetState bodies, whereas every live state remains 0 under the active witness bodies, so they cannot commit. This padding preserves rule-count multiplicity without adding an active lifecycle. No law is drawn. Prepopulated ID 8 in synthetic states is not evidence that a birth already occurred; actual creation is required in the birth, cycle and descendant witnesses.

| Family | Attempted epochs | Prediction per seed |
| --- | ---: | --- |
| attached_funded_birth | 1 | One attached funded birth; node 8 in both eligible estimator samples |
| birth_recycle_to_exhaustion | 8 | Four births, four deaths, eight commits; root matter restored, activation exhausted |
| descendant_growth | 4 | Birth, two Structural transfers, then created node 8 funds birth of node 9 |
| birth_missing_matter | 1 | Staged creation fails funding; zero commits and no leaked inventory/allocation |
| birth_missing_activation | 1 | Final Burn fails; zero commits, whole candidate discarded |
| recycle_original_contact | 1 | Original Contact incidence blocks deletion; no refund or Burn commits |
| recycle_nonleaf | 1 | Extra incident Structural edge blocks deletion; no partial removal |
| recycle_missing_activation | 1 | Refund cannot fund Burn; both removals roll back |
| contact_is_not_structural_route | 1 | Contact alone cannot satisfy Structural matching; zero commits |
| structural_funding | 1 | Attached synthetic child receives resources; no resource-only activity credit |
| edge_detach_strands_child | 2 | One edge removal, then no match; funded orphan remains live |
| birth_world_cap | 1 | Whole environment epoch fails size cap, with full pre-state unchanged |

The cycle prediction is independent of event order. Only the root can give birth; only its kind-2 leaf children can be recycled. Every candidate shares the root, so at most one commits each epoch. With k live children, root free matter is `8-3k`, so k≤2. Root activation is `8-2B`, where B is cumulative births; recycling returns one child activation and burns one, net zero root activation. Whenever a child exists, recycling is affordable. Whenever no child exists and B<4, birth is affordable. Hence there is one commit per epoch until four births and four recycles finish at epoch 8. All original nodes persist, all four allocated children die, root resources end `(matter 8, activation 0)`, dissipation is 8, and `next_node=next_edge=12`. The exact order/parents must still be checked against each seed's actual scheduler output; none has run here.

The descendant witness uses root resources `(5,6)`, child kinds 2 then 3, and three active rule bodies. After birth the root lacks matter for another birth and the child lacks matter for its own birth. Two unit Structural transfers then force the child to `(3,3)` while leaving the root at zero matter. Only the child's birth is affordable at the fourth epoch. This forces a child-funded construction without phase switches or selecting a seed after a run. It predicts template expressivity at an authored resource boundary, not prevalence in the v2 draw distribution.

All 48 cases must be measured by both Rust matchers and independently audited, preserving every negative result and cap. Predicted totals per matcher are 92 attempted epochs, 88 committed epochs, 60 events, 28 births and 16 deaths. The four world-cap cases have no committed epoch. In contrast, an operation-inapplicable candidate does not abort an otherwise empty epoch: its epoch advances with zero events and unchanged resources/allocators. The registry keeps those two failure modes separate.

## Execution gate and limits

This milestone only creates and statically checks the registration. The checker validates schemas, declared grammar/slots, census, inventories, and internal expected accounting; it neither enumerates candidates nor applies a rule. Its pass cannot confirm any predicted trajectory. The [registration freeze](p01f_registration_freeze.json) binds this design, protocol, registry and checker to the existing source contracts. Future implementation/binary/dependency hashes require a separate execution freeze before native calls; do not overwrite this registration freeze.

Next implement the fixed witness runner and independent validation under the registered limits. No random sampler, new law search, resumed P01/P01e run, altered detector, live-campaign verifier replacement or E01 is admitted. A future witness failure consumes the attempt and remains visible; do not repair inputs, replace seeds, rerun the panel or relax expectations after observing it. A successful panel would establish only bounded engineering reachability for authored fixtures, not AP, maintenance, reproduction, heredity, adaptation or a useful sampled law.
