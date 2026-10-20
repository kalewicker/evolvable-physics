#!/usr/bin/env python3
"""Finite kind algebra only: no generator, matcher, interpreter or world imports.

Enumerates abstract labels, not proposed laws or hash sampler outputs. Writes
one new review receipt; never changes historical evidence or a frozen source.
"""
import hashlib
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = (1, 2, 3)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def orbit(mapping, donors, start):
    """Follow a finite type function until a missing donor or repetition."""
    visited = []
    current = start
    while current in donors and current not in visited:
        visited.append(current)
        current = mapping[current - 1]
    return {'start': start, 'visited': visited,
            'terminus': current,
            'type_cycle': current in visited,
            'first_child_can_be_donor': start in donors and mapping[start - 1] in donors}


def stable_donors(mapping, donors):
    """Independent greatest fixed point of donor-set closure under f."""
    remaining = set(donors)
    while True:
        reduced = {k for k in remaining if mapping[k - 1] in remaining}
        if reduced == remaining:
            return remaining
        remaining = reduced


def ratio(passed, total):
    return {'compatible_assignments': passed, 'assignments': total,
            'fraction': str(Fraction(passed, total))}


def field_algebra():
    # v2: first birth (p,c), funding (u,v), recycling (x,y), next donor d.
    pair = triple = descendant = total = 0
    for p, c, u, v, x, y, d in itertools.product(KINDS, repeat=7):
        total += 1
        pair += (p, c) == (u, v)
        triple += (p, c) == (u, v) == (x, y)
        descendant += (p, c) == (u, v) == (x, y) and d == c
    v2 = {key: ratio(count, total) for key, count in
          [('pair', pair), ('triple', triple), ('triple_and_child_donor', descendant)]}
    # v3: each unrestricted f, then four independently assigned donor kinds.
    pair = triple = descendant = total = 0
    for mapping in itertools.product(KINDS, repeat=3):
        for p, u, x, d in itertools.product(KINDS, repeat=4):
            total += 1
            birth = (p, mapping[p - 1])
            funding = (u, mapping[u - 1])
            recycling = (x, mapping[x - 1])
            pair += birth == funding
            triple += birth == funding == recycling
            descendant += birth == funding == recycling and d == mapping[p - 1]
    v3 = {key: ratio(count, total) for key, count in
          [('pair', pair), ('triple', triple), ('triple_and_child_donor', descendant)]}
    require([x['fraction'] for x in v2.values()] == ['1/9', '1/81', '1/243'], 'v2 algebra')
    require([x['fraction'] for x in v3.values()] == ['1/3', '1/9', '1/27'], 'v3 algebra')
    # Marginal symmetry and compatibility reductions, independently of ratios.
    marginal = {(p, c): 0 for p in KINDS for c in KINDS}
    for mapping in itertools.product(KINDS, repeat=3):
        for p in KINDS:
            marginal[p, mapping[p - 1]] += 1
        for p, q in itertools.product(KINDS, repeat=2):
            require(((p, mapping[p - 1]) == (q, mapping[q - 1])) == (p == q),
                    'ordered pair equality must reduce to donor equality')
    require(set(marginal.values()) == {9}, 'ordered pair marginals')
    return {'assumption': 'idealized independent uniform fields, conditional on specified forms/routes',
            'not_a_hash_sampler_probability_or_whole_table_success_rate': True,
            'v2': v2, 'proposed_v3': v3,
            'v3_ordered_pair_marginals': [
                {'pair': list(pair), 'assignments': count} for pair, count in marginal.items()],
            'v3_marginal_assignment_denominator': 81}


def type_profiles():
    profiles = []
    relabel_checks = 0
    for mapping in itertools.product(KINDS, repeat=3):
        for mask in range(8):
            donors = {k for k in KINDS if mask & (1 << (k - 1))}
            paths = [orbit(mapping, donors, k) for k in KINDS]
            closed = stable_donors(mapping, donors)
            require({p['start'] for p in paths if p['type_cycle']} == closed,
                    'orbit/fixed-point disagreement')
            for permutation in itertools.permutations(KINDS):
                renamed = [0, 0, 0]
                for k in KINDS:
                    renamed[permutation[k - 1] - 1] = permutation[mapping[k - 1] - 1]
                renamed_donors = {permutation[k - 1] for k in donors}
                for path in paths:
                    other = orbit(renamed, renamed_donors, permutation[path['start'] - 1])
                    require(other['type_cycle'] == path['type_cycle'] and
                            other['first_child_can_be_donor'] == path['first_child_can_be_donor'],
                            'kind relabeling changed type-path verdict')
                    relabel_checks += 1
            profiles.append({'map': list(mapping), 'birth_donors': sorted(donors),
                             'paths': paths})
    require(len(profiles) == 216, 'profile census')
    require(not orbit((2, 2, 3), {1}, 1)['first_child_can_be_donor'],
            'shared-pair counterexample lost')
    short = orbit((2, 3, 3), {1, 2}, 1)
    require(short['first_child_can_be_donor'] and not short['type_cycle'] and
            short['terminus'] == 3, 'one-step path is not a closed type path')
    require(all(orbit(m, set(KINDS), k)['type_cycle']
                for m in itertools.product(KINDS, repeat=3) for k in KINDS),
            'full donor palette closure')
    return {'maps': 27, 'birth_donor_subsets_per_map': 8,
            'profiles': profiles, 'kind_relabeling_comparisons': relabel_checks,
            'valid_start_paths': sum(p['start'] in row['birth_donors'] for row in profiles for p in row['paths']),
            'first_child_donor_paths': sum(p['first_child_can_be_donor'] for row in profiles for p in row['paths']),
            'closed_type_paths': sum(p['type_cycle'] for row in profiles for p in row['paths']),
            'not_a_resource_state_or_trajectory_claim': True}


def review():
    spec = json.loads((ROOT / 'docs/generator_v3_design.json').read_text())
    require(spec['status'] == 'proposed_not_implemented', 'design-only status')
    require(spec['namespace'] == 'p01-generator-v3' and spec['kinds'] == list(KINDS), 'namespace/kinds')
    require(spec['rule_slots'] == 8 and spec['form_modulus'] == 8, 'slot/form contract')
    require(spec['type_map'] == {'scope': 'per_law', 'field': 'child_kind_by_donor',
                                'initial': 0, 'indices': [0, 1, 2], 'range': 3,
                                'value_offset': 1, 'requires_bijection': False}, 'map contract')
    require(spec['bindings'] == {
        'birth_form': 4, 'birth_donor': 'kind0', 'birth_child': 'type_map[kind0]',
        'transfer_form': 3, 'transfer_route': 1, 'transfer_donor': 'kind0',
        'transfer_target': 'type_map[kind0]', 'recycle_form': 7,
        'recycle_donor': 'kind0', 'recycle_target': 'type_map[kind0]'}, 'effective type fields')
    require(not spec['proposal_ids'] and spec['execution_protocol'] is None, 'no execution panel')
    require(set(spec['not_admitted']) == {
        'generator_implementation', 'sampler_calls', 'law_repair_filter_or_reroll',
        'candidate_enumeration', 'world_transition_application', 'witness_execution',
        'new_environment_or_thresholds', 'E01'}, 'scope')
    # Immutable historical sources and publication receipts, read only.
    freeze_path = ROOT / 'docs/p01g_execution_freeze.json'
    frozen = json.loads(freeze_path.read_text())['files']
    for name, expected in frozen.items():
        require(sha(ROOT / name) == expected, 'historical source changed: ' + name)
    inventory = json.loads((ROOT / 'docs/evidence/publication_inventory.json').read_text())
    for item in inventory['files']:
        require(sha(ROOT / item['file']) == item['sha256'], 'public receipt changed: ' + item['file'])
    sources = ['docs/generator_v3_design.json', 'docs/generator_v3_design.md',
               'scripts/review_generator_v3_design.py', 'docs/p01g_execution_freeze.json',
               'docs/p01g_closure.json', 'docs/p01h_findings.md', 'docs/p01h_source_argument.md']
    return {'schema': 'p01i-static-type-design-review-v1', 'date': '2026-10-20',
            'scope': 'design-only finite type algebra; no laws, hashes used as draws, candidates or transitions',
            'source_sha256': {name: sha(ROOT / name) for name in sources},
            'historical_frozen_project_files_unchanged': len(frozen),
            'prior_public_receipts_verified': len(inventory['files']),
            'field_algebra': field_algebra(), 'type_profiles': type_profiles(),
            'checks_passed': True, 'generator_implemented': False,
            'new_world_runs_admitted': False, 'scientific_status': 'untested'}


if __name__ == '__main__':
    result = review()
    # Exclusive creation also prevents accidental replacement of an old review.
    with Path(sys.argv[1]).open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('source_sha256', 'type_profiles', 'field_algebra')}, sort_keys=True))
