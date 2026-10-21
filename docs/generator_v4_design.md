# Generator v4: proposed state and material coherence

2026-10-20. Recommend a shared per-kind state map and material-bearing
Structural funding, while retaining independent rule forms, donor kinds and
routes. This is a **proposed changed prior**, following P01l's exact-table
exclusion. It is not implemented or admitted for sampling. It neither edits
the retained tables nor changes their negative outcomes.

## Minimal choice and alternatives

| Proposed change | What it addresses | Remaining cost or limitation |
| --- | --- | --- |
| Only force Structural matter=1 | Removes zero-matter funding | Independent states can still block it |
| Only correlate constructive states | Removes immediate state mismatch by design | Structural funding may still move no matter |
| Make all constructive predicates wildcard | Avoids state recognition constraints | Removes state specificity from these roles |
| Use one fixed constructive state | Coordinates states cheaply | Concentrates all roles on one state |
| **Per-kind shared states + Structural matter=1** | **Coordinates immediate role states and material funding** | **Authored correlations; no body-presence guarantee** |
| Insert a complete lifecycle bundle | Supplies required bodies | Forces an architecture and changes the form prior |
| Prefund newborns by changing birth operations | Reduces later funding needs | Changes investment/cost semantics instead of just field correlations |

Choose the shared map plus material override. It changes effective fields only,
adds three per-law state fields, and leaves the eight-slot body distribution
and all kernel operations/costs intact. "Minimal" means this scoped change,
not an optimization proof or the fewest possible constraints. Do not insert,
repair or reject a table to make the chosen mechanism present.

## Exact proposed contract

Use namespace `p01-generator-v4`, retaining v3's canonical-JSON SHA-256 / first
16 hex digits as big-endian u64 / modulo draw recipe. Preserve its modulo bias.
No namespace-keyed message is evaluated in this design review, including tests.
There are no registered proposal IDs, sampled panel, seeds, budgets or epochs.

Keep the unrestricted shared type function f:{1,2,3}->{1,2,3} with per-law
`child_kind_by_donor` fields, initial=0, indices 0..2, modulus=3, offset=1.
Independently introduce s:{1,2,3}->{0,1,2}: `role_state_by_kind`, initial=0,
indices 0..2, modulus=3, offset=0. Reuse both maps across every slot and initial
ID. Allow all 27 maps in each family, including constant maps. Do not require
distinct role states, bijective types or a particular cycle.

For a slot with donor P=`kind0+1`, its child/target kind remains C=f(P).

| Body | Effective donor predicate | Effective child/target state | Other override |
| --- | --- | --- | --- |
| Birth (form 4) | kind P, exact s(P) | CreateNode kind C, state s(C) | none |
| Structural Transfer (form 3, route=1) | kind P, exact s(P) | kind C, exact s(C) | matter=1 |
| Recycling (form 7) | kind P, exact s(P) | kind C, exact s(C) | none |

The birth operations still allocate node/edge, transfer (1 matter,1 activation)
and burn one activation in their original order. Structural funding still
draws activation amount 1 or 2. Birth donor state0/newborn value, constructive
pair state0/state1 and Structural matter fields become ineffective where
overridden; their raw values are still recorded. Keep all eleven v3 raw fields
per slot, including already ineffective kind fields, and all initial fields.
There are 3 type + 3 state + 88 slot + 25 initial = 119 logical field records
per environment. Shared initial=0 addresses are reused, not independent draws.

Contact Transfer, all unary forms and both edge-only templates retain their v3
field interpretation, including possible zero-matter Contact Transfer and
wildcards. State writers can therefore move nodes *away* from the coordinated
states. Original nodes still independently start in states 0..2 with (8,8),
the original Contact ring and sampled Structural flags. No node is initialized
in its role state by fiat. Keep the closed environment, caps, matchers,
scheduler and detectors. A new namespace changes all identities; equal proposal
numbers would not pair v3/v4 laws or worlds. This is not a registered comparison.

## What the correlation does and does not establish

Conditional on bodies with the requisite donor kinds being present, birth P
creates C in exactly the state accepted by C-donor birth bodies. A funding or
recycle body with donor P accepts the creator/newborn pair immediately at their
birth states. Funding moves matter and preserves both states. These are label
equalities imposed by the proposed prior; they are not discovered dynamics.

Let B, F and R denote represented donor kinds for birth, Structural funding and
recycling. The local funded-descendant condition for a start P becomes
**P in B∩F and f(P) in B**. Adding local recycling of that newborn also requires
P in R. Missing any such body remains a negative table, with no resampling.
These conditions permit labels only. They do not ensure a creator exists in
its required state, or resources, topology, scheduling, detector visibility or
accepted events. In particular, a child that creates a descendant is no longer
a leaf; recycling its parent requires removing that descendant first.

For an otherwise untouched original creator, birth leaves (5,6). Two material
transfers leave the creator at (3,4) or (3,2), and the child at (3,3) or (3,5),
depending on activation amount. That child can afford one local birth on these
conditional balances. It then has zero free matter; the original's (8,8)
assumption cannot be reused recursively for descendants. This arithmetic is
not a resource cycle or a funding schedule. Global initial activation remains
64, each birth dissipates one, and the conservative bound of at most 64 births
remains. No unlimited growth or thermodynamic claim follows.

## Body availability and the eight-slot limit

Review every abstract f and every B/F/R subset, retaining infeasible profiles
with an explicit slot-feasibility flag. A given profile needs at least
|B|+|F|+|R| distinct bodies, because these are different template forms/routes.
There are 27×8³=13,824 profiles. Only the 27 profiles with all three subsets
full need nine slots; all others can fit in eight with duplicate/filler slots.
These are abstract subset counts, not frequencies under a hash sampler. The
subset masks are **not** independent/uniform representations of sampled tables.

For a fully covered local birth/funding/recycling cycle, each cycle kind must
lie in B∩F∩R. A cycle on one, two or three distinct kinds therefore requires
at least three, six or nine bodies respectively. The three-kind version does
not fit eight slots under this template palette. A three-kind birth/funding
path without per-kind recycling needs six and can fit. This distinction is
specific to these role-coverage predicates, not a general bound on possible
chemistry or all ways of detaching/recycling a descendant. Do not increase
the slot cap or enforce short cycles to conceal this limit.

## Authored bias and verification boundary

Compared with v3, this prior forces effective Structural matter=1, removes
wildcards from constructive roles, replaces independently keyed state
predicates/newborn states with shared s, and correlates them across slots and
generations. Equal-kind roles always share states; distinct-kind roles may
share them. Exact predicates can reduce applicability on original nodes versus
v3 wildcard predicates. Independent unary writers may undo alignment. This
distribution is not a superset of v3 and is not "unbiased random physics".
The constructive form/donor/route distribution is unchanged in recipe only;
finite namespace/hash effects still need a separately registered measurement.

Finite checks enumerate abstract type/state labels, all donor-subset profiles,
independent graph closure, relabeling symmetry and local resource arithmetic.
They construct no native law, evaluate no keyed source and advance no world.
Counterexamples cover state-only, material-only, absent funding/child donor,
drift from role states and the slot boundary. Conditional equalities are not
whole-table success rates, hash preimage claims, adaptation or life evidence.

Next separately register literal-field readiness for independent Rust/Python
adapters, covering all maps/roles, reuse, ignored raw fields, unchanged forms,
negative body/state/resource/topology cases and exact recording of all fields.
Use fixed literal inputs with hashes-as-draws prohibited. Implement only after
that registration is committed/pushed. Any future actual sampler/census or
trajectory question needs its own registration, budgets and execution freeze;
no sample is admitted by this proposal. P01g/P01k/P01l results remain intact,
scientific status untested, and E01 unauthorized.
