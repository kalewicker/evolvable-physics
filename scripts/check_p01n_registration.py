#!/usr/bin/env python3
"""Static case descriptors and conditions only; no adapters, rules or worlds."""
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {'form': 8, 'kind0': 3, 'kind1': 3, 'new_kind': 3, 'state0': 4,
           'state1': 4, 'value': 3, 'sign': 2, 'amount': 2, 'matter': 2, 'route': 2}
C = ['structural_transfer', 'attached_birth', 'leaf_recycle']
U = ['set_state', 'add_state', 'burn', 'contact_transfer', 'contact_edge_create', 'structural_edge_delete']
PANELS = dict(constructive_rule_cases=6561, unchanged_rule_cases=7776,
              environment_assembly_cases=2916, ignored_field_probe_groups=37,
              ignored_field_evaluations=395, invalid_input_cases=79,
              validator_only_local_conditions=13, adapter_requests=17727)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal(left, right):
    # JSON comparison also distinguishes booleans from integer labels.
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def rule_descriptors():
    ordinal = 0
    for m, s, donor, variant in itertools.product(range(27), range(27), range(3), C):
        yield dict(ordinal=ordinal, panel='constructive', map_index=m, state_map_index=s,
                   donor_raw=donor, variant=variant, state_pair_index=None, rule_id=ordinal % 8)
        ordinal += 1
    for m, donor, variant, pair in itertools.product(range(27), range(3), U, range(16)):
        yield dict(ordinal=ordinal, panel='unchanged', map_index=m, state_map_index=19,
                   donor_raw=donor, variant=variant, state_pair_index=pair, rule_id=ordinal % 8)
        ordinal += 1


def assembly_descriptors():
    for ordinal, (m, s, initial) in enumerate(itertools.product(range(27), range(27), range(4))):
        yield dict(ordinal=ordinal, map_index=m, state_map_index=s, initial=initial, rotation=(3 * m + s) % 9)


def condition_verdict(row):
    p = row['parent']
    c = row['map'][p - 1]
    b = p in row['birth_donors']
    f = b and p in row['funding_donors']
    r = b and p in row['recycle_donors']
    d = b and c in row['birth_donors']
    creator = row['creator_state'] == row['state_map'][p - 1]
    child = row['child_state'] == row['state_map'][c - 1]
    return [b, f, r, d, f and creator and child, d and child,
            f and row['transfer_matter'] == 1,
            row['child_resources'][0] >= 3 and row['child_resources'][1] >= 2,
            row['leaf_after_edge_removal'], row['creation_edge_present'], row['required_bodies'] <= row['slot_cap']]


def expected_probes(registry):
    domains = {'kind1': 3, 'new_kind': 3, 'state0': 4, 'state1': 4, 'value': 3,
               'sign': 2, 'amount': 2, 'matter': 2, 'route': 2}
    probes = []
    for variant, fields in [('attached_birth', list(domains)),
                            ('structural_transfer', ['kind1', 'new_kind', 'state0', 'state1', 'value', 'sign', 'matter']),
                            ('leaf_recycle', list(domains))]:
        probes.extend(dict(variant=variant, field=f, values=list(range(domains[f]))) for f in fields)
    for variant in U:
        probes.extend([dict(variant=variant, field='map', values=registry['type_maps']),
                       dict(variant=variant, field='state_map', values=registry['state_maps'])])
    return probes


def expected_invalids():
    rows = []
    def add(name, target, value=None, mode='assembly'):
        rows.append(dict(name=name, target=target, value=value, mode=mode))
    for field, n in DOMAINS.items():
        for label, value in [('low', -1), ('high', n), ('boolean', True)]:
            add(field + '_' + label, 'rule_fields[7].' + field, value)
    for field, base, low, high in [('map', [1, 2, 3], 0, 4), ('state_map', [0, 1, 2], -1, 3)]:
        for label, value in [('short', base[:2]), ('long', base + [base[0]]), ('low', [low] + base[1:]),
                             ('high', [high] + base[1:]), ('boolean', [True] + base[1:]),
                             ('float', [0.5] + base[1:]), ('string', ['0'] + base[1:]), ('missing', None)]:
            add(field + '_' + label, field, value)
    for label, value in [('low', -1), ('high', 4), ('boolean', True)]:
        add('initial_id_' + label, 'initial_id', value)
    add('initial_record_id_mismatch', 'initial_fields.id', 1)
    for label, value in [('low', -1), ('high', 2**64 - 1), ('boolean', True)]:
        add('scheduler_' + label, 'initial_fields.scheduler', value)
    for field, n in [('node_kind', 3), ('node_state', 3), ('structural', 2)]:
        for label, value in [('short', [0] * 7), ('high', [0] * 7 + [n]), ('boolean', [0] * 7 + [True])]:
            add(field + '_' + label, 'initial_fields.' + field, value)
    for label, value in [('short', 'first_seven'), ('missing', None), ('not_list', {})]:
        add('rule_fields_' + label, 'rule_fields', value)
    add('unknown_mode', 'mode', 'unknown')
    add('missing_raw_kind0', 'rule_fields[7].kind0', None)
    add('floating_raw_value', 'rule_fields[7].value', 0.5)
    add('string_raw_value', 'rule_fields[7].value', '1')
    for field in ('node_kind', 'node_state', 'structural'):
        add(field + '_long', 'initial_fields.' + field, [0] * 9)
    for label, value in [('low', -1), ('high', 8), ('boolean', True)]:
        add('rule_id_' + label, 'rule_id', value, mode='rule')
    add('missing_initial_fields', 'initial_fields', None)
    return rows


def validate(p, r):
    require(p['schema'] == 'p01n-v4-literal-readiness-registration-v1' and r['schema'] == 'p01n-v4-literal-registry-v1', 'schema')
    require(p['namespace'] == 'p01-generator-v4' and p['proposal_ids'] == [], 'no proposal panel')
    for k, v in [('registration_only_now', True), ('literal_validation_executed', False), ('sampling_admitted', False),
                 ('world_execution_admitted', False), ('e01_authorized', False), ('scientific_status', 'untested')]:
        require(equal(p[k], v), 'admission: ' + k)
    require(equal(p['panels'], PANELS), 'fixed denominators')
    require(equal(r['type_maps'], [list(m) for m in itertools.product((1, 2, 3), repeat=3)]), 'type maps')
    require(equal(r['state_maps'], [list(s) for s in itertools.product(range(3), repeat=3)]), 'state maps')
    require(r['raw_donor_kinds'] == [0, 1, 2] and equal(r['raw_state_pairs'], [list(s) for s in itertools.product(range(4), repeat=2)]), 'raw donor/state domains')
    old = load(ROOT / 'docs/p01j_literal_fields.json')
    require(equal(r['variants'], old['variants']) and equal(r['initial_fields'], old['initial_fields']), 'frozen variants/initials')
    require(r['constructive_variants'] == C and r['unchanged_variants'] == U, 'factored variant coverage')
    require(equal(p['field_domains'], DOMAINS) and list(p['field_domains']) == list(DOMAINS), 'raw domains/order')
    require(p['constructive_expansion'] == dict(order=['type_map', 'state_map', 'raw_donor_kind', 'constructive_variant'],
        rule_id='global_rule_ordinal % 8', kind1_and_new_kind='type_map[kind0] % 3; deliberately differs from the mapped raw child kind',
        state0=3, state1=3, value='(state_map[type_map[kind0]-1] + 1) % 3', sign_and_amount='global_rule_ordinal % 2', matter=0,
        form_and_route='registered variant'), 'constructive poison expansion')
    require(p['unchanged_expansion'] == dict(order=['type_map', 'raw_donor_kind', 'unchanged_variant', 'raw_state_pair'],
        rule_id='global_rule_ordinal % 8, continuing after constructive panel', state_map=[2, 0, 1],
        kind1='(kind0 + state1) % 3', new_kind='(kind0 + state0 + 1) % 3', value='(state0 + 2 * state1) % 3',
        sign='(state0 + state1) % 2', amount='state1 % 2', matter='state0 % 2', form_and_route='registered variant'), 'unchanged expansion')
    require(p['assembly_expansion'] == dict(order=['type_map', 'state_map', 'initial_fields'],
        rotation='(3 * type_map_index + state_map_index) % 9', variant='(slot + rotation) % 9',
        kind0='(slot + type_map_index) % 3', state0='(slot + rotation) % 4', state1='(slot + rotation + 1) % 4',
        other_fields='unchanged_expansion formulas', rule_id='slot',
        reuse='both maps and all eight rules identical across four initial IDs in each of 729 groups'), 'assembly expansion')
    require(equal(r['ignored_field_probes'], expected_probes(r)), 'ignored-field groups')
    require(sum(len(v['values']) for v in r['ignored_field_probes']) == 395, 'probe evaluations')
    require(equal(r['invalid_inputs'], expected_invalids()), 'invalid boundaries')
    require(r['local_condition_order'] == ['birth_present', 'funding_kind_path', 'recycling_kind_path', 'child_donor_kind_path',
        'funding_state_match', 'child_donor_state_match', 'material_funding', 'construction_budget',
        'leaf_after_edge_removal', 'creation_edge_present', 'fits_slot_cap'], 'local-condition meanings')
    names = ['coherent_local_conditions', 'birth_absent', 'funding_absent', 'recycle_absent', 'child_donor_absent',
             'state_only_control', 'material_only_control', 'creator_drift', 'child_drift', 'unfunded_newborn',
             'nonleaf_after_descendant', 'creation_edge_missing', 'three_kind_full_role_cycle']
    require([c['name'] for c in r['local_conditions']] == names, 'condition cases')
    for c in r['local_conditions']:
        require(all(type(v) is bool for v in c['expected']) and equal(c['expected'], condition_verdict(c)), 'condition verdict: ' + c['name'])
    require(r['local_conditions'][5]['scope'].startswith('counterfactual') and r['local_conditions'][6]['scope'].startswith('counterfactual') and
            r['local_conditions'][-1]['scope'] == 'abstract_profile_not_an_eight_slot_table', 'control interpretation')
    require(p['interface']['rule_field_records'] == 17 and p['interface']['assembly_field_records'] == 119 and
            len(p['interface']['read_order']) == 6, 'complete raw recording')
    require(p['case_ids'] == dict(order=['constructive_rules', 'unchanged_rules', 'assemblies', 'probes', 'invalid_inputs'],
        rules='rule-{global_rule_ordinal:05d}', assemblies='assembly-{ordinal:04d}',
        probes='probe-{group_index:02d}-{value_index:02d}', invalid_inputs='invalid-{entry_name}',
        validator_only_conditions='condition-{entry_name}'), 'case identity/order')
    require(p['invalid_inputs']['validate_ignored_fields'] is True, 'validate ignored raw values')
    require(p['future_paths'] == dict(rust='src/bin/generator-v4-fields.rs', python='scripts/generator_v4_fields.py',
        validator='scripts/validate_p01n.py', readiness_tests='scripts/test_p01n_readiness.py'), 'new implementation paths')
    limits = p['future_validation_limits']
    require(limits['wall_seconds_per_adapter'] == 60 and limits['combined_stdout_stderr_bytes_per_adapter'] == 268435456 and
            limits['aggregate_wall_seconds'] == 300 and len(p['gate']) == 4, 'limits/gates')
    rules = list(rule_descriptors())
    assemblies = list(assembly_descriptors())
    require(len(rules) == 14337 and len({tuple(v.values()) for v in rules}) == 14337, 'rule descriptor census')
    require(Counter(v['panel'] for v in rules) == {'constructive': 6561, 'unchanged': 7776}, 'factored counts')
    require(Counter(v['rule_id'] for v in rules) == {0: 1793, **{i: 1792 for i in range(1, 8)}}, 'rule slot coverage')
    require(len(assemblies) == 2916 and Counter(v['rotation'] for v in assemblies) == {i: 324 for i in range(9)}, 'assembly rotations')
    groups = Counter((v['map_index'], v['state_map_index']) for v in assemblies)
    require(len(groups) == 729 and set(groups.values()) == {4}, 'four initial IDs per map pair')
    require(14337 + 2916 + 395 + 79 == PANELS['adapter_requests'], 'request denominator')
    return dict(schema='p01n-static-registration-review-v1', status='pass', panels=PANELS,
                map_pair_groups=729, rule_records_per_success=17, assembly_records_per_success=119,
                expected_successful_field_records_per_adapter=(14337 + 395) * 17 + 2916 * 119,
                literal_implementation_admitted_after_commit=True, adapters_implemented_or_executed_here=False,
                native_rule_or_world_constructions=0, keyed_hash_evaluations=0, world_transitions=0,
                sampling_admitted=False, scientific_status='untested')


def main(out):
    result = validate(load(ROOT / 'docs/p01n_protocol.json'), load(ROOT / 'docs/p01n_literal_fields.json'))
    freeze = load(ROOT / 'docs/p01n_registration_freeze.json')
    for section in ('files', 'prior_public_receipts'):
        for name, digest in freeze[section].items():
            require(sha(ROOT / name) == digest, section + ': ' + name)
    historical = load(ROOT / 'docs/p01k_execution_freeze.json')['files']
    for name, digest in historical.items():
        require(sha(ROOT / name) == digest, 'historical source: ' + name)
    for path in load(ROOT / 'docs/p01n_protocol.json')['future_paths'].values():
        require(not (ROOT / path).exists(), 'implementation precedes registration: ' + path)
    result.update(registration_freeze_sha256=sha(ROOT / 'docs/p01n_registration_freeze.json'),
                  registration_files=freeze['files'], prior_public_receipts_verified=len(freeze['prior_public_receipts']),
                  historical_project_files_verified=len(historical))
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'static_review.json').open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'registration_files'}, sort_keys=True))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
