# P01l: conditional exclusion of newborn-funded construction in these tables

This is a source-level argument for the **32 exact retained P01k tables** under
their frozen initial/topology contract. It is not a formal proof-assistant
result, a v3 sampler-wide impossibility claim, or an observed trajectory result.
The independent audit checks every table's operation/topology premises and all
163 body combinations. File identities bind the reviewed source semantics.

## Matter must enter through the birth edge before a first descendant birth

Consider the first event, in any hypothetical admitted history of one of these
tables, at which any previously created newborn constructs its own child.
Before that event, every newborn has never constructed a child.

1. Original nodes have a Contact ring. No operation in these tables creates or
   deletes a Contact edge: runtime CreateEdge/DeleteEdge acts on Structural
   edges. The standalone edge-creation template requires an existing Contact
   edge with the same ordered endpoints. It therefore cannot connect a newborn.
   Birth's CreateNode allocates a fresh ID, never an existing node.
2. A newborn consequently has no Contact incidence. Its only possible incoming
   Structural edge is the edge from its creator. Before the proposed first
   descendant event it has no outgoing Structural edge: those could arise only
   from its own birth operation or the Contact-dependent edge template.
3. Birth gives a newborn one free matter. Its own construction requires three:
   one for the node, one for the edge, and one transferred to the new child.
   State writers preserve matter; Burn only consumes activation. Edge and node
   deletion refund the ordered source, so removing its incoming edge cannot
   supply matter to the newborn. Deletion of an outgoing child cannot help
   before that child has been constructed. Contact Transfer cannot reach it.
4. At least one matter-bearing Structural Transfer must therefore have funded
   this newborn along its creation edge before its first construction. Retained
   material transfers move one matter, so at least two are actually needed.
   Even permitting arbitrary resources, schedules and repeated transfers, a
   necessary condition is one type-compatible birth/funding/next-birth triple
   with donor and child state phases admitted by unary-state closure.

Only unary SetState/AddState changes existing states in these tables. Their
algebraic closure permits any finite sequence, ignores competing activity, and
respects signed i32 bounds. Letting the creator begin in *any* state satisfying
its birth guard further relaxes real initial-history constraints. Failure in
this permissive state abstraction is thus sufficient to exclude the required
triple; success would establish neither affordability nor world reachability.
Different funding bodies or interleaved transfers do not evade the condition:
all transfers preserve state, so the state at any material transfer and the
state of the later birth must still be connected by these unary writers.

## Exhaustive retained-table result

| Exclusive static reason, in the order shown | Tables |
| --- | ---: |
| No birth body | 8 |
| Birth exists; no kind-compatible funding/next-birth triple | 22 |
| Kind-compatible triple exists; its funding moves no matter | 1 |
| Material type-compatible triple exists; unary states exclude it | 1 |
| Not excluded by this necessary-condition review | 0 |

The last two nonempty rows are laws 5015 and 5030. In 5015 the relevant
Structural Transfer moves zero matter. In 5030, birth rule 1 creates kind 1 in
state 1; material Transfer rule 4 requires child state 0, while kind-1 next-birth
rule 2 requires state 2. There is no kind-1 state writer, so the child remains
in state 1. Law 5027 has a state-compatible material funding pair, but both
birth bodies require kind 2 and their children have kind 1; it belongs to the
22-table missing-type-path row. All other tables and their reasons are retained
in the public audit and complete per-table review, rather than omitted here.

Thus no first newborn-as-parent birth can occur for these exact tables under
these premises. This leaves births by originals, some funding/recycling, other
activity and every detector outcome as separate questions. It neither scores a
behavioral endpoint nor changes P01k into a chemistry gate. Its original
behavioral outcomes remain null/not_executed. Changing templates, environment,
initial topology or the law panel would require a new argument and protocol.
