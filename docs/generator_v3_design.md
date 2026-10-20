# Type-coherent generator v3: design review only

2026-10-20. P01i recommends a **shared per-law total kind map**, using the
existing v2 operation bodies. This is an intentionally altered prior, proposed
after P01g's failed mechanism gate and P01h's exact-table diagnosis. It is not a
repair of those tables, an implementation, a new draw or experiment admission.
The [machine-readable contract](generator_v3_design.json) and
[static review](evidence/p01i-design-001/static_review.json) specify and check
only finite type algebra. Historical freezes, negatives and labels remain intact.

## Choice and alternatives

| Design | Incoming funding/recycling types | Child-as-donor path | Additional bias |
| --- | --- | --- | --- |
| Independent v2 kinds | Uncoordinated ordered pairs | Possible, often disconnected | Retained baseline; consumed panel failed |
| One shared ordered pair P→C | Compatible when bodies present | Blocked if P≠C and no C-donor birth | Can accidentally forbid descendants |
| One shared kind K everywhere constructive | Compatible when bodies present | Same-kind birth matches by type | Restricts constructive chemistry to one kind |
| Shared permutation of three kinds | Compatible for equal donor kinds | Requires the next donor body | Unnecessarily requires one-to-one child kinds |
| **Shared unrestricted total map f: K→K** | **Compatible for equal donor kinds** | **Requires a birth body with donor f(P)** | **Correlates child/target kinds across bodies** |

Choose the last option: it preserves the full three-kind donor alphabet, allows
all nine individual parent/child pairs, and imposes neither a monotyped
constructive subsystem nor bijectivity. The map is authored correlation in the
generator, not a rule evolved by the world. Templates, donor kinds, states and
routes are still independently keyed fields; presence of a usable lifecycle is
not guaranteed. Missing-body tables must be retained, never filtered out.

## Exact proposed field contract

Use namespace `p01-generator-v3`. Keep the v2 hash recipe: SHA-256 of UTF-8
canonical JSON `[namespace, proposal, initial, field, index]` (sorted keys,
compact separators, no ASCII escaping); interpret the first 16 hex digits as
u64 and reduce modulo the range. Preserve modulo bias, duplicate rule bodies
under distinct IDs, eight slots, and all v2 limits. There are no proposal IDs,
execution seeds, panel or budgets registered here.

Define K={1,2,3}. For each law and k in K, set
`f(k) = 1 + draw(proposal, 0, "child_kind_by_donor", k-1, 3)`.
Reuse this one map across every rule slot and all four initial states; do not
derive it from observed worlds, table success, or which forms appear. There are
27 abstract possible maps, including constant maps and maps with fixed points,
two-cycles and three-cycles. Do not select one of these classes preferentially.

Every slot retains its independent `form`, `kind0`, `state0`, `state1`, `value`,
`sign`, `amount`, `matter` and `route` fields with the v2 names, indices and
ranges. Only these effective kind fields change:

| Form | Proposed kinds | Fields no longer effective |
| --- | --- | --- |
| 4, attached birth | Donor `kind0`; CreateNode kind `f(kind0)` | `new_kind` |
| 3 with Structural route=1 | Ordered pattern `[kind0, f(kind0)]` | `kind1` |
| 7, leaf recycling | Ordered pattern `[kind0, f(kind0)]` | `kind1` |

Contact Transfer (form 3, route=0), Contact edge creation (5), edge-only
deletion (6) and all unary forms retain their v2 kinds. In particular, no
coherence is imposed on edge-only deletion: detachment/stranding remains a
possible competing process. Unused keyed fields have no effect; there is no
sequential PRNG position to preserve. Keep all ordered operations, edge kind 0,
state predicates, affordability, candidate/conflict selection and accounting.
Do not force wildcard states, a birth/funding/recycling body, a material
transfer, or a donor of every kind. No repair, rejection, resampling or insertion.

Initial node kinds/states, Structural-edge flags, scheduler key, resources and
no-channel environment use the v2 labels/ranges under the new namespace.
Eight Contact-ring originals still start with (8 matter, 8 activation); all
other initial details are unchanged in distribution recipe. Changing namespace
changes their identities too: a v2/v3 proposal ID does not identify paired laws
or identical worlds. Any future comparison needs its own explicit pairing and
equal-budget contract.

## Necessary paths, including descendants

A birth with donor P creates C=f(P) and an ordered Structural edge P→C.
A Structural funding or recycling body with donor Q matches that edge by type
exactly when Q=P, since its target is f(Q). This replaces two independent kind
equalities with one. It does not eliminate the need for another rule body.

Let B be the set of donor kinds actually represented by birth bodies in a table
(ignoring states only for this algebra). A created child can match a birth
donor **iff f(P)∈B**. For two successive descendant steps require both f(P) and
f(f(P)) in B. For an indefinitely repeatable *type path*, follow f until a kind
is missing from B or a kind repeats. A repeated kind proves only a finite graph
cycle. It does not imply unlimited resources, repeated events or biological
reproduction. Starting at a kind not in B is not a valid initial birth path.

Example: f=(2,3,3), B={1,2} permits a kind-1 parent to create a kind-2 donor,
which could create kind 3; kind 3 cannot continue. B={1,2,3} has no missing-donor
type barrier for any map. By contrast, a single shared pair 1→2 with B={1}
admits coherent funding/recycling yet blocks the first child's construction.
These examples are abstract labels, not authored worlds or witness executions.

A future per-table static report must separately enumerate birth/funding and
birth/recycling ordered matches, child-to-birth-donor matches, material-bearing
funding bodies, and state constraints. It must retain tables with zero matches.
It must not use those reports as admission filters or selectors. A kind-only
pass is a necessary-path result, never an executable-reachability verdict.

## Changed prior and what it cannot buy

Under an **idealized independent uniform field model**, conditional on the
relevant forms/routes being present, a specific birth/funding pair is type
compatible in 1/3 of v3 field assignments versus 1/9 for v2. For a specified
birth, funding and recycling triple the fractions are 1/9 versus 1/81. Requiring
also a second birth donor to match the first child gives 1/27 versus 1/243.
These denominators concern particular slots, not whole-table success rates.
The [checker](../scripts/review_generator_v3_design.py) enumerates these exact
finite alphabets; it never evaluates a hash-keyed draw or constructs a law.

Individual ordered kind-pair marginals remain uniform over nine abstract pairs
in that model, but the joint distribution changes substantially. Birth rules
with the same donor now share their child kind; funding/recycling targets with
that donor are also correlated. Constant maps concentrate all newborn kinds;
non-surjective maps can exclude kinds from newborn output. None is discarded.
The forms/routes and hence nominal template-presence distribution are unchanged.
Hash truncation/modulo bias and correlations over a finite proposal domain mean
these idealized fractions are **not measured or proven sampler probabilities**,
nor proof that any proposal ID produces a specified full table. No preimage
search is performed.

Kinds alone leave all of these barriers:

- A body can be absent, state-incompatible or unable to move matter (form 3
  may draw matter=0). Independent states are not made compatible by f.
- A child starts at (1 matter, 1 activation); its own birth requires (3,2).
  With unit-matter Structural funding, two incoming transfers are needed.
  A standard initial donor after one birth has (5,6), sufficient for those two
  transfers at activation amounts 1 or 2, before competing uses. This is only
  local resource arithmetic, not a scheduling/state guarantee.
- Recycling needs an incident-edge-free leaf after removing its incoming edge,
  plus enough returned/donor activation to pay Burn. A descendant makes its
  parent nonleaf until the descendant is removed. Original Contact nodes remain
  undeletable; edge-only deletion can still strand a newborn.
- Conflicts, match/world caps, locality, component size, duration and both
  detector estimators retain their existing requirements. A coherent type path
  establishes none of their gates.
- Each birth burns one activation; closed initial activation is 64. The existing
  conservative bound of at most 64 births remains. Free state/edge edits remain
  possible; no thermodynamics or open-endedness claim follows.

## Review outcome and next bounded step

Recommend this map as the next **proposed distribution**, with its bias plainly
identified. P01i completes only a design/static-algebra review. No generator,
candidate matcher, simulator, witness or sampled trajectory runs here. The
static report covers all 27 maps and all eight birth-donor subsets, including
counterexamples with coherent incoming pairs and no descendant donor.

Next register implementation-readiness checks for this exact contract: separate
Rust and Python field adapters tested on fixed literal fields, all forms/routes,
map reuse across slots/states, and missing-body/state/material negatives. Those
checks must not call the hash sampler, enumerate candidates or advance worlds.
Then implement and verify those adapters under that registration. A later
sampling question/panel, whole-table static-report policy, budgets, frozen
sources and independent audit require a separate decision and execution freeze.
Do not repeat P01f/P01g, promote their negative gate, extend favorable tables or
start E01. Scientific status remains **untested**.
