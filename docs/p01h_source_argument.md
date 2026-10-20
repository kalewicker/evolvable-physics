# Why the 16 retained P01g tables cannot fund or recycle their newborns

2026-10-20. This is a source-level conditional argument for the **16 exact
retained ordered rule tables**, under the frozen v2 generator's initial-world
and environment contract. The [independent kind matrix](evidence/p01h-001/independent_audit.json)
and [law diagnoses](evidence/p01h-001/law_diagnoses.json) identify those tables.
It is stronger than absence in 128 epochs, but is not a formal proof-assistant
result or a statement about every possible v2 draw, custom initial worlds,
other grammars or the kernel's capabilities. P01f's authored positive witnesses
remain valid.

## Necessary ordered kind equality

The frozen [sampler](../src/bin/generator-v2.rs) and
[runtime](../src/runtime.rs) establish the following conditions:

- All initial nodes are the original eight. Contact edges form an immutable
  ring on them; no template creates or removes Contact edges.
- Node kinds never change. Unary SetState/AddState changes state only.
- A birth rule whose donor pattern has kind `P` and whose CreateNode operation
  creates kind `C` adds exactly the ordered Structural edge `donor -> child`.
- Other Structural creation requires an existing Contact pair, so it cannot
  add an incoming edge to a newborn. Deletion cannot create an alternate route.
- Structural Transfer and recycling patterns both bind the ordered pair
  `[0,1]`; transfer goes from 0 to 1, and recycling deletes 1 with recipient 0.

Consequently, any remaining incoming Structural edge to a newborn has the
ordered kind pair `(P,C)` of its birth body. Funding or recycling through that
edge requires a same-law pair body with exactly those two pattern kinds in
that order. State matching, affordability and scheduler selection cannot repair
a kind mismatch.

Across the retained tables there are 12 birth bodies, 12 Structural Transfer
bodies and 17 recycling bodies. Ten tables contain birth; five contain both
birth and Structural Transfer, and seven contain birth and recycling. Only
same-law combinations are relevant: nine birth/transfer pairs and 15
birth/recycling pairs. **None has matching ordered kinds.** The independent
auditor extracts these pairs directly from the retained requests without using
the diagnostic's compatibility/state classifier. Six tables have no birth body.

Thus these tables cannot apply a Structural Transfer to their own newborns or
recycle one through its incoming birth edge, regardless of the newborn's state,
available resources or scheduler seed. Contact Transfer cannot reach a newborn
because it has no Contact incidence. Original nodes cannot be deleted because
the recycling bundle removes only one Structural edge and their Contact edges
remain. Hence node deletion is also excluded for these particular tables under
the stated initial-world contract.

## Why created nodes cannot become construction donors

A newborn starts with one free matter and one activation. Another birth requires
three matter and two activation: one matter each for the bound node, bound edge
and child's free matter; one activation to the child and one to Burn.

Suppose there were a first birth funded by an earlier newborn. Before that first
event, every newborn has only its incoming birth edge or has become detached;
none has an outgoing edge to its own child. It cannot gain incoming resources
from Contact or Structural Transfer by the kind/topology argument above. It
cannot gain refunds for its own child or outgoing birth edge because that would
require an earlier newborn-funded birth. Deleting its incoming edge refunds
the parent in slot 0, not the newborn in slot 1. Contact-based edge creation
cannot involve it. State changes do not create resources and Burn only removes
activation. Node recycling is excluded as above.

It therefore still has one matter and at most one activation before the alleged
first construction event, contradicting the birth requirement. There can be no
first newborn-funded birth. This also explains the retained invariant of one
newborn matter and activation in `{0,1}`; the finite scan corroborates the
argument rather than proving it by observation alone.

## Scope of the conclusion

Longer horizons or different initial/scheduler seeds within this same contract
cannot enable these missing typed routes in the same 16 tables. This does not
authorize a new draw, predict a coherent law's prevalence, show that the entire
finite hash sampler lacks coherent tables, or assess active persistence on
original-node/state dynamics. It does not establish causal maintenance,
reproduction, heredity or adaptation.

The lesson for any future design is to check type-path compatibility before
spending a trajectory budget. A new type-coherent grammar would change the
sampling prior and require its own question and registration. Merely sharing a
parent/child kind pair can still block descendant construction if children can
never match a donor pattern; a design review must check that path too. No such
new grammar or experiment is admitted by this argument.
