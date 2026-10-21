# P01l: retained-table state and resource review

2026-10-20. This is post-hoc static diagnosis, informed by P01k's published
counts, not a preregistered experiment or a new chemistry admission gate. Fix
and publish this plan before reading retained rule bodies for this diagnosis.
Preserve the consumed P01k census and P01g's failed gate and inconclusive labels.

## Inputs and boundary

Use only the sealed `artifacts/p01k-001` records: all 32 proposals 5000..5031,
all four initial IDs, all eight ordered rule slots, duplicates and negatives.
Verify the original inventory/seal and every input file identity. Bind this
plan, the inventory, manifest, seal and source semantics in a separate freeze.
New analysis outputs live outside the original bundle; never rewrite its seal.
Do not import a sampler, adapter, matcher, transition interpreter or subprocess
launcher. File-content SHA-256 is permitted for custody; namespace-keyed message
evaluation, candidate enumeration, world application and new trajectories are
not. No filtering, input repair, extension, replacement laws or E01.

## Fixed questions and units

1. For each birth body, retain its donor/child kinds, donor predicate, newborn
   state and every unary state writer of those kinds. State is signed i32;
   AddState uses checked addition, not wrapping or clamping. Only unary
   SetState/AddState changes an existing node's state in these templates.
2. Compute algebraic unary-state closure, allowing arbitrary finite sequences
   of those writers and ignoring scheduling. Represent reachable states as
   unions of closed integer intervals. A wildcard +1/-1 writer saturates the
   corresponding direction to the i32 bound; exact-guard writers add a point
   only when its guard is reachable. SetState adds its constant similarly.
   This computes state possibilities, never a world history. Retain initial
   and final intervals and accepted subsets at each phase. Empty means a
   state-only exclusion; nonempty means only that this abstraction permits it.
3. Cross every birth with every Structural Transfer, recycle body and next
   birth in the same table. Retain all pairs, with kind and state failures
   separate. Compare immediate-state predicates with sequential possibilities.
   For funding/recycling, let the donor start in any state satisfying the
   first birth's guard; let the child start in its exact birth state. Test the
   target body's predicates after unary closure, with no simultaneous-state
   requirement across different phases. Also test child-to-next-birth states.
4. Cross birth/funding/next-birth triples and birth/funding/next-birth/recycling
   quadruples, including incompatible cases. Fix the phase order as funding,
   next birth, then recycling. Donor phases are birth -> funding -> recycling;
   child phases are newborn -> funding -> next birth -> recycling. Predicate
   filtering at an earlier phase restricts the later closure's starting set.
   Funding may repeat in its accepted states because Transfer preserves state.
   Report type-only, phased-state, material-bearing and local-budget conditions
   separately. These are conditions for this specified motif, not every possible
   lifecycle. A descendant must be removed before its parent can be a leaf;
   passing the state test does not establish that removal or event ordering.
5. Record local resource arithmetic without executing operations. A newborn
   starts at (1 matter, 1 activation), versus (3,2) to construct. A material
   Structural Transfer moves one matter and one or two activation; two such
   transfers supply the matter deficit. A hypothetical untouched original
   donor starts at (8,8), has (5,6) after birth and can afford those transfers.
   Keep this conditional budget distinct from actual available resources.
   Zero-matter Transfer cannot fill the matter deficit. Record activation
   dissipation and topology prerequisites, not just kind/state compatibility.
6. Across all 128 saved initial inventories, report original-node kind/state
   seeds and unary-state availability for each birth body, aggregated by
   kind/state rather than concrete rule bindings. Absence on originals alone
   does not exclude a later newborn source. Do not report generated events.
7. Check the source-level topology premise: no template creates Contact edges;
   form 5 requires an existing Contact edge and creates a Structural edge on
   those same endpoints. Newborns therefore have no Contact edge and their only
   incoming Structural edge comes from birth. Deletion refunds the ordered
   source. Before a newborn's first birth, unary/Burn/deletion cannot supply its
   missing matter via outgoing newborn edges that do not yet exist. Document
   how this constrains bootstrap funding, without treating a permitted motif
   as executable reachability or an impossibility result for the kernel/prior.

Counts use rule pairs/triples/quadruples and distinct tables, never independent
trajectory observations. Publish all 32 rows and all 128 initial IDs. No
chemistry threshold is introduced. Behavioral endpoints stay null/not_executed.

## Verification, outputs and stopping

Test invented records for no-op/absent writers, directional wildcard drift,
guard chaining, signed bounds, phase-order failure, zero-matter funding and
missing bodies. Check interval closure independently with a finite quotient:
states below 0, exact 0/1/2 and states above 2. This quotient is valid only for
the validated template alphabet (guards/constants 0..2, deltas +/-1); reject
other forms. Compare accepted predicates/phase feasibility rather than claiming
every exterior integer is represented by one concrete state. Exhaustively
cross the 20 possible writer schemas per kind (three guarded states plus
wildcard, SetState constants and +/-1), in invented sets of zero, one or two
writers, with all three singleton starts and wildcard starts.

Retain full pair/phase details, source hashes, input custody audit, independent
state checks, tests, analysis inventory and descriptive totals. Commit/push the
plan first; implement new helpers without editing any frozen path. Fix analysis
defects against the same plan and retain failed outputs, never repair input laws.
Stop after the review and one stated next design boundary. It admits no new
generator, sampling panel, dynamics, changed environment/detector or E01.
Scientific status remains untested.
