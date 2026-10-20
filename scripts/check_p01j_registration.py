#!/usr/bin/env python3
"""Static registration checks; no rule/world construction or generator imports."""
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def barrier_verdict(row):
    p = row['parent']
    c = row['map'][p - 1]
    b = p in row['birth_donors']
    f = b and p in row['funding_donors']
    r = b and p in row['recycle_donors']
    d = b and c in row['birth_donors']
    m = f and row['transfer_matter'] > 0 and row['funding_target_state'] in (None, row['child_state'])
    s = d and row['next_donor_state'] in (None, row['child_state'])
    return [b, f, r, d, m, s]


def rule_descriptors(registry):
    """Case identities only. Does not create pattern nodes or operations."""
    factors = (range(len(registry['maps'])), registry['raw_donor_kinds'],
               range(len(registry['variants'])), range(len(registry['raw_state_pairs'])))
    for ordinal, (m, donor, variant, state) in enumerate(itertools.product(*factors)):
        yield {'ordinal': ordinal, 'map_index': m, 'donor_raw': donor,
               'variant_index': variant, 'state_pair_index': state, 'rule_id': ordinal % 8}


def validate(p, r):
    require(p['schema'] == 'p01j-v3-literal-readiness-registration-v1', 'protocol schema')
    require(r['schema'] == 'p01j-literal-field-registry-v1', 'registry schema')
    require(p['namespace'] == 'p01-generator-v3' and p['proposal_ids'] == [], 'no proposal panel')
    for key, value in [('registration_only_now', True), ('literal_field_validation_executed', False),
                       ('law_sampling_admitted', False), ('world_execution_admitted', False),
                       ('e01_authorized', False), ('scientific_status', 'untested')]:
        require(type(p[key]) is type(value) and p[key] == value, 'admission: ' + key)
    require(p['panels'] == {'rule_field_cases': 11664, 'environment_assembly_cases': 972,
                          'barrier_cases': 8, 'invalid_input_cases': 12,
                          'ignored_field_probe_groups': 6}, 'fixed denominators')
    require(all(type(k) is int for m in r['maps'] for k in m) and
            r['maps'] == [list(m) for m in itertools.product((1, 2, 3), repeat=3)], 'all maps in order')
    require(r['raw_donor_kinds'] == [0, 1, 2], 'all raw donors')
    require(r['raw_state_pairs'] == [list(s) for s in itertools.product(range(4), repeat=2)], 'all state pairs')
    expected_variants = [
        ('set_state', 0, 0, 1, None, ['SetState']),
        ('add_state', 1, 0, 1, None, ['AddState']),
        ('burn', 2, 0, 1, None, ['Burn']),
        ('contact_transfer', 3, 0, 2, 'Contact', ['Transfer']),
        ('structural_transfer', 3, 1, 2, 'Structural', ['Transfer']),
        ('attached_birth', 4, 0, 1, None, ['CreateNode', 'CreateEdge', 'Transfer', 'Burn']),
        ('contact_edge_create', 5, 0, 2, 'Contact', ['CreateEdge']),
        ('structural_edge_delete', 6, 0, 2, 'Structural', ['DeleteEdge']),
        ('leaf_recycle', 7, 0, 2, 'Structural', ['DeleteEdge', 'DeleteNode', 'Burn'])]
    require([tuple(v[k] for k in ('name', 'form', 'route', 'pattern_arity', 'edge_class', 'ops'))
             for v in r['variants']] == expected_variants, 'variant forms/routes/shapes')
    require(p['rule_expansion'] == {
        'order': ['map', 'raw_donor_kind', 'variant', 'raw_state_pair'], 'rule_id': 'ordinal % 8',
        'kind1': '(kind0 + state1) % 3', 'new_kind': '(kind0 + state0 + 1) % 3',
        'value': '(state0 + 2 * state1) % 3', 'sign': '(state0 + state1) % 2',
        'amount': 'state1 % 2', 'matter': 'state0 % 2'}, 'rule expansion')
    require(p['assembly_expansion'] == {
        'order': ['map', 'rotation_0_through_8', 'initial_fields'],
        'variant': '(slot + rotation) % 9', 'kind0': 'slot % 3',
        'state0': '(slot + rotation) % 4', 'state1': '(slot + rotation + 1) % 4',
        'other_fields': 'same formula as rule_expansion', 'rule_id': 'slot',
        'map_reuse': 'one per-law map shared by all eight slots and four initial field records'}, 'assembly expansion')
    require(p['field_domains'] == {'form': 8, 'kind0': 3, 'kind1': 3, 'new_kind': 3,
                                  'state0': 4, 'state1': 4, 'value': 3, 'sign': 2,
                                  'amount': 2, 'matter': 2, 'route': 2}, 'raw field domains')
    initial = r['initial_fields']
    require([v['id'] for v in initial] == [0, 1, 2, 3], 'four initial identities')
    require([v['scheduler'] for v in initial] == [0, 1, 2, 2**64 - 2], 'scheduler boundaries')
    for row in initial:
        for field, n in [('node_kind', 3), ('node_state', 3), ('structural', 2)]:
            require(len(row[field]) == 8 and all(type(x) is int and 0 <= x < n for x in row[field]),
                    'literal initial field range')
    require(initial[0]['structural'] == [0] * 8 and initial[1]['structural'] == [1] * 8,
            'empty/full Structural boundary')
    expected_probes = [('attached_birth', 'new_kind', [0, 1, 2]),
                       ('structural_transfer', 'kind1', [0, 1, 2]),
                       ('leaf_recycle', 'kind1', [0, 1, 2]),
                       ('attached_birth', 'amount', [0, 1]),
                       ('leaf_recycle', 'amount', [0, 1]), ('burn', 'route', [0, 1])]
    require([(v['variant'], v['field'], v['values']) for v in r['ignored_field_probes']] == expected_probes,
            'ignored-field probes')
    require(r['barrier_verdict_order'] == ['birth_present', 'funding_kind_path', 'recycle_kind_path',
            'child_donor_kind_path', 'material_funding_local_predicate', 'child_donor_state_predicate'],
            'barrier interpretation')
    require([b['name'] for b in r['barriers']] == ['coherent_baseline', 'birth_absent', 'funding_absent',
        'recycle_absent', 'child_donor_absent', 'child_donor_state_mismatch', 'funding_state_mismatch',
        'funding_has_no_matter'], 'barrier identities')
    for b in r['barriers']:
        require(all(type(x) is bool for x in b['expected']) and b['expected'] == barrier_verdict(b),
                'barrier verdict: ' + b['name'])
    require([v['name'] for v in r['invalid_inputs']] == ['short_map', 'low_map_kind', 'high_map_kind',
        'bool_map_kind', 'high_form', 'low_kind0', 'high_state0', 'high_route', 'negative_amount',
        'high_initial', 'high_scheduler', 'missing_required_field'], 'invalid case identities')
    # Fixed literal boundaries; no adapter is implemented or invoked here.
    require([(v['target'], json.dumps(v['value'])) for v in r['invalid_inputs']] == [
        ('map', '[1, 2]'), ('map', '[0, 2, 3]'), ('map', '[1, 2, 4]'), ('map', '[true, 2, 3]'),
        ('form', '8'), ('kind0', '-1'), ('state0', '4'), ('route', '2'), ('amount', '-1'),
        ('initial_id', '4'), ('scheduler', str(2**64 - 1)), ('required_kind0', 'null')], 'invalid boundaries')
    ids = list(rule_descriptors(r))
    require(len(ids) == 11664 and len({tuple(d.values()) for d in ids}) == 11664, 'rule census/uniqueness')
    require(Counter(d['rule_id'] for d in ids) == {k: 1458 for k in range(8)}, 'slot identity coverage')
    require(len(r['maps']) * 9 * len(initial) == 972, 'assembly census')
    require(len(p['gate']) == 4, 'four conjunctive readiness gates')
    require(p['future_paths'] == {'rust': 'src/bin/generator-v3-fields.rs',
        'python': 'scripts/generator_v3_fields.py', 'validator': 'scripts/validate_p01j.py'}, 'new source paths')
    require(p['future_validation_limits'] == {'wall_seconds_per_adapter': 30,
        'output_bytes_per_adapter': 67108864, 'aggregate_wall_seconds': 120,
        'note': 'development readiness limits, not a campaign or benchmark; build and ordinary unit tests precede validation; validator must enforce limits and retain truncation/failure receipts'}, 'development limits')
    return {'schema': 'p01j-static-registration-review-v1', 'status': 'pass',
            'rule_field_case_descriptors': len(ids), 'assembly_case_descriptors': 972,
            'maps': 27, 'variants': 9, 'state_pairs': 16, 'barrier_cases': 8,
            'invalid_input_cases': 12, 'ignored_field_groups': 6,
            'ignored_field_evaluations': 15,
            'literal_adapter_implementation_admitted_after_commit': True,
            'adapters_implemented_or_executed_here': False,
            'rule_or_world_constructions': 0, 'sampler_calls': 0, 'transition_applications': 0,
            'sampling_or_world_execution_admitted': False, 'scientific_status': 'untested'}


def main():
    result = validate(load(ROOT / 'docs/p01j_protocol.json'), load(ROOT / 'docs/p01j_literal_fields.json'))
    freeze = load(ROOT / 'docs/p01j_registration_freeze.json')
    for name, expected in freeze['files'].items():
        require(sha(ROOT / name) == expected, 'registration source mismatch: ' + name)
    historical = load(ROOT / 'docs/p01g_execution_freeze.json')['files']
    for name, expected in historical.items():
        require(sha(ROOT / name) == expected, 'historical source mismatch: ' + name)
    inventory = load(ROOT / 'docs/evidence/publication_inventory.json')['files']
    for item in inventory:
        require(sha(ROOT / item['file']) == item['sha256'], 'historical receipt mismatch: ' + item['file'])
    result.update(registration_freeze_sha256=sha(ROOT / 'docs/p01j_registration_freeze.json'),
                  registration_files=freeze['files'], historical_project_files_verified=len(historical),
                  prior_public_receipts_verified=len(inventory))
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'static_review.json').open('x') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'registration_files'}, sort_keys=True))


if __name__ == '__main__':
    main()
