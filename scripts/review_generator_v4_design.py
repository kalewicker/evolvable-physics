#!/usr/bin/env python3
"""Finite role-label algebra only. No adapters, samplers, worlds or processes."""
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS, STATES = (1, 2, 3), (0, 1, 2)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write('\n')


def stable(mapping, allowed):
    """Independent greatest fixed point: never leaves the allowed donor set."""
    current = set(allowed)
    while True:
        reduced = {k for k in current if mapping[k - 1] in current}
        if reduced == current:
            return current
        current = reduced


def orbit(mapping, allowed, start):
    visited, current = [], start
    while current in allowed and current not in visited:
        visited.append(current)
        current = mapping[current - 1]
    return dict(visited=visited, terminus=current, closed=current in visited)


def state_algebra():
    checks = symmetry = funded = joined = 0
    state_marginals = Counter()
    for mapping in itertools.product(KINDS, repeat=3):
        for states in itertools.product(STATES, repeat=3):
            for k in KINDS:
                state_marginals[k, states[k - 1]] += 1
            # Compare complete ordered role labels with the reduced kind-only
            # identity. These tuples are abstract labels, not native rules.
            for p, u, q, d in itertools.product(KINDS, repeat=4):
                parent = (p, states[p - 1])
                child = (mapping[p - 1], states[mapping[p - 1] - 1])
                funding = ((u, states[u - 1]), (mapping[u - 1], states[mapping[u - 1] - 1]))
                recycle = ((q, states[q - 1]), (mapping[q - 1], states[mapping[q - 1] - 1]))
                next_donor = (d, states[d - 1])
                direct = (parent, child) == funding and child == next_donor
                require(direct == (p == u and mapping[p - 1] == d), 'funded descendant identity')
                both = direct and (parent, child) == recycle
                require(both == (p == u == q and mapping[p - 1] == d), 'joined identity')
                funded += direct
                joined += both
                checks += 1
            for pi in itertools.permutations(KINDS):
                renamed_map = [0] * 3
                for k in KINDS:
                    renamed_map[pi[k - 1] - 1] = pi[mapping[k - 1] - 1]
                for tau in itertools.permutations(STATES):
                    renamed_states = [0] * 3
                    for k in KINDS:
                        renamed_states[pi[k - 1] - 1] = tau[states[k - 1]]
                    for k in KINDS:
                        child = mapping[k - 1]
                        renamed_child = renamed_map[pi[k - 1] - 1]
                        require(renamed_child == pi[child - 1] and
                                renamed_states[renamed_child - 1] == tau[states[child - 1]], 'joint kind/state relabeling')
                        symmetry += 1
    require(checks == 59049 and symmetry == 78732, 'label/symmetry denominators')
    require(set(state_marginals.values()) == {243}, 'state-map role marginal symmetry')
    return dict(type_maps=27, state_maps=27, donor_label_cases=checks,
                funded_identity_true=funded, joined_identity_true=joined,
                kind_and_state_relabeling_comparisons=symmetry,
                role_state_counts=[dict(kind=k, state=s, assignments=n) for (k, s), n in sorted(state_marginals.items())],
                scope='exhaustive abstract labels conditional on roles; not sampled-law or trajectory frequencies')


def subset(mask):
    return {k for k in KINDS if mask & (1 << (k - 1))}


def availability():
    profiles = []
    exclusive = Counter()
    cycle_lengths = Counter()
    min_bodies = Counter()
    for mapping in itertools.product(KINDS, repeat=3):
        cycles = set()
        for k in KINDS:
            walk = orbit(mapping, set(KINDS), k)
            seq = walk['visited']
            cycle = seq[seq.index(walk['terminus']):]
            cycles.add(min(tuple(cycle[i:] + cycle[:i]) for i in range(len(cycle))))
        for cycle in cycles:
            cycle_lengths[len(cycle)] += 1
            require(3 * len(cycle) <= 8 if len(cycle) < 3 else 3 * len(cycle) > 8,
                    'fully covered cycle slot limit')
        for bm, fm, rm in itertools.product(range(8), repeat=3):
            b, f, r = subset(bm), subset(fm), subset(rm)
            starts = {p for p in b & f if mapping[p - 1] in b}
            local_recycle = starts & r
            allowed_bf, allowed_bfr = b & f, b & f & r
            recurrent_bf = {k for k in KINDS if orbit(mapping, allowed_bf, k)['closed']}
            recurrent_bfr = {k for k in KINDS if orbit(mapping, allowed_bfr, k)['closed']}
            require(recurrent_bf == stable(mapping, allowed_bf) and
                    recurrent_bfr == stable(mapping, allowed_bfr), 'orbit/fixed-point availability')
            # Independent relational join over role sets.
            via_pairs = {p for p, u, d in itertools.product(b, f, b)
                         if (p, mapping[p - 1]) == (u, mapping[u - 1]) and d == mapping[p - 1]}
            require(starts == via_pairs, 'set intersection/relational join')
            needed = len(b) + len(f) + len(r)
            # The slot witness is only a multiset of role/kind labels; not a
            # law. A unary filler can occupy any remaining slot.
            labels = [(role, k) for role, group in [('B', b), ('F', f), ('R', r)] for k in group]
            require(len(labels) == len(set(labels)) == needed, 'distinct role body minimum')
            if needed <= 8:
                padded = labels + [('other', 0)] * (8 - needed)
                require(len(padded) == 8 and set(labels) <= set(padded), 'abstract eight-slot feasibility')
            reason = ('no_birth_donor' if not b else 'no_local_funded_descendant' if not starts else
                      'funded_descendant_without_local_recycle' if not local_recycle else 'local_joined_labels_available')
            exclusive[reason] += 1
            min_bodies[needed] += 1
            profiles.append(dict(type_map=list(mapping), birth_mask=bm, funding_mask=fm, recycling_mask=rm,
                                 minimum_bodies=needed, fits_eight_slots=needed <= 8,
                                 funded_descendant_starts=sorted(starts), local_recycling_starts=sorted(local_recycle),
                                 recurrent_birth_funding_starts=sorted(recurrent_bf),
                                 recurrent_all_three_role_starts=sorted(recurrent_bfr), reason=reason))
    require(len(profiles) == 13824 and min_bodies[9] == 27 and sum(min_bodies.values()) == 13824, 'all profiles including slot-infeasible')
    require(dict(cycle_lengths) == {1: 27, 2: 9, 3: 2}, 'independent cycle census')
    summary = dict(profiles=len(profiles), slot_feasible_profiles=sum(p['fits_eight_slots'] for p in profiles),
                   slot_infeasible_profiles=27, exclusive_partition=dict(exclusive),
                   minimum_bodies_histogram=dict(min_bodies), cycles_across_all_type_maps=dict(cycle_lengths),
                   fully_covered_cycle_body_minimum={'1_kind': 3, '2_kinds': 6, '3_kinds': 9},
                   type_subset_profiles_are_not_a_sampling_distribution=True,
                   local_funded_profile_count=sum(bool(p['funded_descendant_starts']) for p in profiles),
                   local_joined_profile_count=sum(bool(p['local_recycling_starts']) for p in profiles),
                   scope='role availability only; recurrent labels do not establish resource cycles or events')
    return profiles, summary


def counterexamples_and_budgets():
    examples = [
        dict(name='state_coherence_without_material', kind_and_state_match=True, matter=0, closes_matter_deficit=False),
        dict(name='material_without_state_coherence', newborn_state=1, funding_guard=0, next_birth_guard=2,
             unary_writers=0, matter=1, state_permitted=False),
        dict(name='missing_child_donor', type_map=[2, 2, 3], B=[1], F=[1], first_child_can_be_donor=False),
        dict(name='missing_funding', type_map=[1, 2, 3], B=[1], F=[], funded_start=False),
        dict(name='state_writer_can_leave_role_state', role_state=0, later_state=1, exact_guard_accepts=False),
        dict(name='full_three_kind_cycle_over_slot_cap', type_map=[2, 3, 1], B=[1, 2, 3], F=[1, 2, 3], R=[1, 2, 3], minimum_bodies=9, slot_cap=8)]
    require(2 * examples[0]['matter'] < 3 - 1, 'zero-matter negative')
    require(examples[1]['newborn_state'] not in (examples[1]['funding_guard'], examples[1]['next_birth_guard']), 'immutable child-state negative')
    require(orbit((2, 2, 3), {1}, 1)['terminus'] == 2 and not orbit((2, 2, 3), {1}, 1)['closed'], 'missing next donor')
    budgets = []
    for activation in (1, 2):
        donor_after_birth = [8 - 3, 8 - 2]
        donor_after_funding = [donor_after_birth[0] - 2, donor_after_birth[1] - 2 * activation]
        child = [1 + 2, 1 + 2 * activation]
        require(min(donor_after_funding) >= 0 and child[0] >= 3 and child[1] >= 2, 'conditional local budget')
        budgets.append(dict(activation_per_transfer=activation, transfer_count=2,
                            original_creator_after_birth=donor_after_birth, creator_after_funding=donor_after_funding,
                            child_after_funding=child, child_after_own_birth=[child[0] - 3, child[1] - 2]))
    require(1 < 3 and 1 < 2 and all(b['child_after_own_birth'][0] == 0 for b in budgets), 'newborn bootstrap and nonrecursive budget')
    return dict(counterexamples=examples, conditional_budgets=budgets,
                closed_initial_activation=64, activation_dissipated_per_birth=1, conservative_birth_bound=64,
                no_resource_or_scheduling_history_constructed=True)


def verify_contract(spec):
    require(spec['schema'] == 'generator-v4-design-only-v1' and spec['status'] == 'proposed_not_implemented', 'design status')
    require(spec['namespace'] == 'p01-generator-v4' and spec['rule_slots'] == 8 and
            spec['kinds'] == list(KINDS) and spec['states'] == list(STATES), 'label contract')
    require(spec['type_map'] == dict(field='child_kind_by_donor', scope='per_law', initial=0,
            indices=[0, 1, 2], modulus=3, offset=1, requires_bijection=False), 'type map')
    require(spec['state_map'] == dict(field='role_state_by_kind', scope='per_law', initial=0,
            indices=[0, 1, 2], modulus=3, offset=0), 'state map')
    require(spec['effective_overrides'] == {
        'birth_4': dict(donor_kind='kind0+1', donor_state='state_map[donor_kind]', child_kind='type_map[donor_kind]', child_state='state_map[child_kind]'),
        'structural_transfer_3_route_1': dict(donor_kind='kind0+1', target_kind='type_map[donor_kind]', donor_state='state_map[donor_kind]', target_state='state_map[target_kind]', matter=1),
        'recycling_7': dict(donor_kind='kind0+1', target_kind='type_map[donor_kind]', donor_state='state_map[donor_kind]', target_state='state_map[target_kind]')}, 'effective fields')
    require(spec['body_presence'] == 'independent_form_donor_kind_and_route_fields_no_insertion' and
            spec['unused_raw_fields'] == 'retain_all_11_v3_fields_per_slot_even_when_overridden', 'presence/raw field retention')
    require(set(spec['unchanged_except_namespace']) == {
        'all_8_slot_form_and_donor_fields', 'unary_and_Contact_and_edge_only_templates',
        'Structural_transfer_activation_amount', 'operation_order_and_costs',
        'initial_world_fields_resources_topology_and_closed_environment',
        'kernel_matchers_scheduler_caps_and_detectors'}, 'unchanged semantics')
    require(spec['logical_field_records_per_environment'] == 3 + 3 + 11 * 8 + 3 * 8 + 1 == 119, 'field accounting')
    require(not spec['proposal_ids'] and spec['execution_protocol'] is None, 'no execution panel')
    require(set(spec['not_admitted']) == {'generator_implementation', 'namespace_keyed_hash_evaluation',
        'law_repair_filter_reroll_or_selection', 'candidate_enumeration', 'world_transitions',
        'witness_execution', 'new_environment_or_detector_thresholds', 'E01'}, 'scope')


def run(out):
    spec = load(ROOT / 'docs/generator_v4_design.json')
    verify_contract(spec)
    frozen = load(ROOT / 'docs/p01k_execution_freeze.json')['files']
    for name, digest in frozen.items():
        require(sha(ROOT / name) == digest, 'frozen project file: ' + name)
    prior = load(ROOT / 'docs/evidence/publication_inventory.json')['files']
    for row in prior:
        require(sha(ROOT / row['file']) == row['sha256'], 'prior public receipt: ' + row['file'])
    profiles, coverage = availability()
    algebra, negatives = state_algebra(), counterexamples_and_budgets()
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'profiles.jsonl').open('x') as f:
        for profile in profiles:
            f.write(json.dumps(profile, sort_keys=True, separators=(',', ':')) + '\n')
    sources = ['docs/generator_v4_design.json', 'docs/generator_v4_design.md',
               'scripts/review_generator_v4_design.py', 'docs/p01l_closure.json', 'docs/p01l_source_argument.md']
    source_hashes = {}
    for name in sources:
        original = ROOT / name
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original.read_bytes())
        source_hashes[name] = sha(original)
    receipt = dict(schema='p01m-static-role-design-review-v1', date='2026-10-20', checks_passed=True,
                   scope='finite abstract labels only; no native law, hash draws, candidate matching or world execution',
                   source_sha256=source_hashes, frozen_project_files_unchanged=len(frozen),
                   prior_public_receipts_verified=len(prior), state_algebra=algebra, availability=coverage,
                   counterexamples_and_resources=negatives, profiles_sha256=sha(out / 'profiles.jsonl'),
                   generator_implemented=False, sampling_admitted=False, world_execution_admitted=False,
                   keyed_hash_evaluations=0, world_transitions=0, behavioral_outcomes=None,
                   behavioral_missing_reason='not_executed', chemistry_continuation_gate=None,
                   scientific_status='untested', e01_authorized=False)
    write(out / 'static_review.json', receipt)
    write(out / 'checksums.json', {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
    return {k: v for k, v in receipt.items() if k not in ('source_sha256', 'state_algebra', 'counterexamples_and_resources')}


if __name__ == '__main__':
    print(json.dumps(run(Path(sys.argv[1])), sort_keys=True))
