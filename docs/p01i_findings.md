# P01i: type-coherent distribution design review

2026-10-20. **Design complete; generator not implemented or admitted for sampling.**
The [proposed v3 contract](generator_v3_design.md) replaces independent
constructive child/target kinds with an unrestricted, shared per-law function
on the three existing kinds. It retains independently keyed forms, donor kinds,
states and routes. This intentionally changes the joint sampling prior, and
does not repair, filter or replace any P01g table.

## Static results

The [review receipt](evidence/p01i-design-001/static_review.json), produced by
[finite algebra checks](../scripts/review_generator_v3_design.py), records:

- All 27 maps × eight birth-donor subsets: 216 profiles and 648 start paths.
  Of these, 324 start at a represented birth donor, 216 can pass to a represented
  child donor, and 198 reach a repeated kind without leaving the donor set.
  These are exhaustive abstract counts, not sampled-law or trajectory rates.
- Orbit walks agree with a separate greatest-fixed-point elimination check on
  all profiles; 3,888 comparisons preserve the verdict under all kind renamings.
- A shared ordered pair with a different child kind can be fully compatible for
  incoming funding/recycling yet lack the child's birth-donor body. The review
  retains this counterexample and a path that stops after one descendant donor.
- Conditional on specified template forms/routes in an idealized uniform field
  model, birth/funding compatibility is 1/3 versus v2's 1/9. Adding recycling
  gives 1/9 versus 1/81; adding a second birth donor gives 1/27 versus 1/243.
  Both designs are enumerated over 2,187 field assignments for each comparison.
  These are not hash-sampler probabilities, whole-table success rates or
  preimage claims. The model retains all nine marginal ordered kind pairs.
- All 116 project files in the P01g execution freeze and all 343 prior public
  receipts match their original hashes. This check concerns project files and
  receipts; it does not re-audit dependency trees or execution binaries.

No sampler, candidate enumerator, transition interpreter or native executable
is imported or called by the checker. SHA-256 is used only for file identities.
The receipt contains abstract maps/donor sets, not generated rules or worlds.
No historical campaign or diagnostic was repeated. The public receipt is a
byte-identical copy of the local static report; publication context separately
binds the final documents and sources.

## Decision and remaining boundary

Recommend the shared total-map design over a single shared pair (which can
block descendants), one shared kind (which narrows constructive diversity),
or a permutation (which imposes unnecessary bijectivity). This creates authored
cross-body correlation; it does not establish useful sampled chemistry.
Absent bodies, material-free transfers, incompatible states, scarce resources,
nonleaf deletion, orphaning, conflicts, detector gates and finite activation
remain. Even a closed type cycle cannot exceed the closed-resource birth bound.

Next is a separate **implementation-readiness registration**, fixing literal
field tests for independent Rust/Python adapters, all forms/routes, map reuse,
and missing-body/state/material negatives before implementation. No hash draws,
candidate enumeration, world transitions or witness runs are part of that step.
Do not add a new sampling panel by implication. Any later sampled feasibility
experiment needs its own question, denominators, criteria, budgets and execution
freeze. P01g's failed continuation gate and both inconclusive labels remain;
scientific status is **untested**, and E01 remains unauthorized.
