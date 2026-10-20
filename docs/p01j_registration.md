# P01j: fixed literal-field adapter readiness registration

2026-10-20. This milestone registers implementation checks for the exact
[v3 kind-map design](generator_v3_design.md). The
[protocol](p01j_protocol.json) and [literal registry](p01j_literal_fields.json)
are fixed before either adapter is implemented. This registration constructs
neither a rule table nor an initial world. Its static checker enumerates case
identities and local descriptor predicates only.

## Panel and independent expectations

| Panel | Fixed expansion | Count |
| --- | --- | ---: |
| Individual rule fields | 27 maps × three raw donor kinds × nine form/route variants × 16 raw state pairs | 11,664 |
| Eight-slot environment assembly | 27 maps × nine rotations × four literal initial-field records | 972 |
| Local barrier descriptors | Literal positive and missing-body/state/material cases | 8 |
| Invalid inputs | Literal domain, missing-field and map-shape cases | 12 |
| Ignored-field probes | Six groups with fixed alternatives | 6 groups / 15 evaluations |

Rule cases are map-major, donor-major, variant-major, state-pair-minor; ID is
ordinal modulo eight. The registry lists all maps, state pairs and variants,
including Contact and Structural Transfer separately. The protocol fixes all
remaining raw-field formulas. This crosses every map/donor/form/state pair;
it does not exhaust every joint value/sign/amount/matter combination.

Assembly uses slot IDs 0..7, variant `(slot+rotation)%9`, donor raw kind
`slot%3`, state0 `(slot+rotation)%4`, and state1 `(slot+rotation+1)%4`.
Other raw fields follow the rule-panel formulas. No initial ID affects the
map or rule fields. Some rotations omit birth, funding or recycling; retain
them. These are authored field vectors, not draws from the finite hash sampler
or claims about template prevalence.

Future Rust and Python adapters must independently build complete JSON values
from literal fields. They must not call each other or the v2 generator to
construct their expected output. Full decoded equality alone is insufficient:
the validator must also check pattern kinds/states, edge class/kind/ordering,
negative edge predicate, all operation operands/order/costs, and exact
environment/accounting/counter/limit fields against the frozen v2 contract,
with only the three declared v3 kind substitutions. In particular, birth must
remain CreateNode, CreateEdge, fixed (1,1) Transfer, fixed Burn(1); recycling
must delete edge then node to recipient 0 then Burn(1). Generic amount fields
must not alter either bundle. No rule operation is applied.

An injected field source accepts `(initial_id, field, index, modulus)` with no
proposal ID, PRNG, hash implementation or default sampling fallback. It must
record accesses. Map fields always use initial=0, indices 0,1,2 and modulus=3,
read once each per assembly. Law fields also use initial=0; initial-world
fields use only the requested initial ID. State/resource/limit literals remain
unchanged. Check complete law identity across each four-initial group, not just
one rule. Both adapters must validate literal maps and every provided field
(including unused fields) strictly, excluding booleans, before conversion;
unused valid fields have no effect. A missing required key must fail without
sampling. A short map fails shape validation; do not pad it or coerce booleans
while subtracting one for the source's raw values.

All ignored-field probes use the protocol's one fixed base and the named
variant's form/route. Count each listed value once, retain equal baselines,
and compare exact output across alternatives within each adapter as well as
between adapters. Invalid-input cases use the same base with form 3/route 1,
initial=0 and the first initial-field record; apply only the stated mutation.
`required_kind0=null` means remove the kind0 key. Invalid maps replace the whole
map, and invalid initial/scheduler values replace the corresponding input.
Every case must be rejected with a structured error and no output environment.

## Barrier descriptors are not world matching

For parent P and C=f(P), let b mean a P-donor birth body is listed. The six
registered verdicts, in registry order, are:

1. b.
2. b and a P-donor funding body is listed.
3. b and a P-donor recycling body is listed.
4. b and a C-donor birth body is listed.
5. Verdict 2, positive transfer matter, and funding target state is wildcard or
   equals the child's listed state.
6. Verdict 4 and next-donor state is wildcard or equals the child's listed state.

All pair targets use the shared map, so another donor kind cannot fund the
listed P→C pair. Descriptor states concern one listed local state only; later
state changes are not excluded. Verdicts 5 and 6 are deliberately separate:
state-compatible child-donor typing does not imply that the child has resources.
These are necessary local predicates, never candidate enumeration or operation
applicability. They do not instantiate worlds or execute authored witnesses.

## Gate, failure handling and implementation boundary

Require every fixed case, exact differential output, the independent invariants,
all source-routing/map-reuse assertions, all negative verdicts and all rejections.
No partial pass or aggregate percentage can admit readiness. Future validation
must enforce the protocol's output/time ceilings and retain failures with case
identity; development limits are not performance evidence. Use a new directory
per attempt, bind source/binary/input hashes, and preserve the earliest failing
output. Implementation defects may be fixed and the same engineering panel
repeated, with each attempt retained. Inputs, criteria and original receipts
must remain frozen; no input repair or threshold relaxation.

The [registration freeze](p01j_registration_freeze.json) binds this specification,
registry, checker/tests and relevant historical sources. It does not freeze an
unwritten adapter or authorize hash sampling. After the registration passes and
is committed/pushed, next implement only the separate literal-field Rust and
Python adapters and fixed readiness validator at the protocol's new paths;
do not edit frozen source paths or Cargo files. Ordinary literal-field tests
may run during that work. Record the built implementations and every validation
attempt separately rather than overwriting this registration freeze.

The actual hash sampler, proposal IDs, sampled panel, world execution, detector
runs, new environment and E01 remain unadmitted. Any later experiment requires
its own question, budgets, criteria, source/binary/input freeze and admission.
P01g's failed gate and both inconclusive outcomes remain unchanged. Readiness
would establish agreement on authored fields only, not law-sampler equivalence,
reachable mechanisms, active persistence or evolution.
