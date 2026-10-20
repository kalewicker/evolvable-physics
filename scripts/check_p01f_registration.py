#!/usr/bin/env python3
"""Static registration review only. Never matches, schedules or applies transitions."""
import copy
import hashlib
import json
import sys
from pathlib import Path

if not __debug__:
    raise RuntimeError('Static registration checks require assertions')

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = [
    'attached_funded_birth', 'birth_recycle_to_exhaustion', 'descendant_growth',
    'birth_missing_matter', 'birth_missing_activation', 'recycle_original_contact',
    'recycle_nonleaf', 'recycle_missing_activation', 'contact_is_not_structural_route',
    'structural_funding', 'edge_detach_strands_child', 'birth_world_cap',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def template(rule):
    nodes, edges, ops = rule['nodes'], rule['edges'], rule['ops']
    tags = tuple(op['op'] for op in ops)
    forms = {('SetState',): 0, ('AddState',): 1, ('Burn',): 2, ('Transfer',): 3,
             ('CreateNode', 'CreateEdge', 'Transfer', 'Burn'): 4, ('CreateEdge',): 5,
             ('DeleteEdge',): 6, ('DeleteEdge', 'DeleteNode', 'Burn'): 7}
    assert tags in forms, 'Unregistered template'
    form = forms[tags]
    assert len(nodes) == (2 if form in (3, 5, 6, 7) else 1)
    for node in nodes:
        assert set(node) == {'kind', 'state'} and node['kind'] in (1, 2, 3)
        assert node['state'] in (None, 0, 1, 2)
    structural = {'class': 'Structural', 'kind': 0, 'ends': [0, 1]}
    if form in (3, 5, 6, 7):
        route = edges[0]['class'] if form == 3 else ('Contact' if form == 5 else 'Structural')
        assert route in ('Contact', 'Structural')
        assert edges == [{'class': route, 'kind': 0, 'ends': [0, 1]}]
    else:
        assert not edges
    assert rule['absent'] == ([structural] if form == 5 else [])
    op = ops[0]
    if form == 0:
        assert op == {'op': 'SetState', 'node': 0, 'value': op['value']} and op['value'] in (0, 1, 2)
    elif form == 1:
        assert op == {'op': 'AddState', 'node': 0, 'delta': op['delta']} and op['delta'] in (-1, 1)
    elif form == 2:
        assert op == {'op': 'Burn', 'node': 0, 'amount': op['amount']} and op['amount'] in (1, 2)
    elif form == 3:
        assert op == {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': op['matter'], 'activation': op['activation']}
        assert op['matter'] in (0, 1) and op['activation'] in (1, 2)
    elif form == 4:
        assert op['kind'] in (1, 2, 3) and op['state'] in (0, 1, 2)
        assert ops == [
            {'op': 'CreateNode', 'account': 0, 'kind': op['kind'], 'state': op['state']},
            {'op': 'CreateEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]},
            {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1},
            {'op': 'Burn', 'node': 0, 'amount': 1},
        ], 'Birth slot/funding order'
    elif form in (5, 6):
        assert op == {'op': tags[0], 'account': 0, 'kind': 0, 'ends': [0, 1]}
    else:
        assert ops == [
            {'op': 'DeleteEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]},
            {'op': 'DeleteNode', 'node': 1, 'recipient': 0},
            {'op': 'Burn', 'node': 0, 'amount': 1},
        ]
    return form


def initial_inventory(initial):
    assert initial['profile'] == 'p00c-local-driven-v1'
    assert initial['channels'] == [] and initial['injected'] == initial['extracted'] == 0
    native = initial['native']
    assert native['profile'] == 'p00a-local-closed-v1' and native['seed'] == 0
    assert [r['id'] for r in native['rules']] == list(range(8))
    for rule in native['rules']:
        form = template(rule)
        if form == 0:
            assert rule['nodes'] == [{'kind': 1, 'state': 2}] and rule['ops'][0]['value'] == 2, 'Inactive padding'
        if form == 4:
            assert rule['ops'][0]['state'] == 0, 'Witness state invariant'
    world = native['world']
    assert world['epoch'] == world['next_event'] == 0 and world['writers'] == {}
    assert set(world['nodes']) == {str(i) for i in range(world['next_node'])}
    assert set(world['edges']) == {str(i) for i in range(world['next_edge'])}
    contacts = {str(i): {'class': 'Contact', 'kind': 0, 'ends': [i, (i + 1) % 8]} for i in range(8)}
    assert {i: e for i, e in world['edges'].items() if e['class'] == 'Contact'} == contacts
    for node in world['nodes'].values():
        assert node['kind'] in (1, 2, 3) and node['state'] == 0
        assert node['matter'] >= 0 and node['activation'] >= 0
    for edge in world['edges'].values():
        assert edge['class'] in ('Contact', 'Structural') and edge['kind'] == 0
        assert len(edge['ends']) == len(set(edge['ends'])) == 2
        assert all(str(i) in world['nodes'] for i in edge['ends'])
    assert len({(e['class'], e['kind'], tuple(e['ends'])) for e in world['edges'].values()}) == len(world['edges'])
    matter = sum(n['matter'] + 1 for n in world['nodes'].values()) + len(world['edges'])
    activation = sum(n['activation'] for n in world['nodes'].values()) + world['dissipated']
    assert matter == world['matter_total'] and activation == world['activation_total'] == initial['initial_activation']
    assert len(world['nodes']) <= native['limits']['max_nodes'] and len(world['edges']) <= native['limits']['max_edges']


def expected_accounting(family):
    world, expected = family['initial']['native']['world'], family['expected']
    assert expected['live_nodes'] == len(world['nodes']) + expected['births'] - expected['deaths']
    assert expected['next_node'] == world['next_node'] + expected['births']
    assert expected['next_edge'] == world['next_edge'] + expected['births']
    assert expected['live_newborns'] == sorted(set(expected['live_newborns']))
    assert all(8 <= i < expected['next_node'] for i in expected['live_newborns'])
    resources = {i: copy.deepcopy(n) for i, n in world['nodes'].items() if int(i) < 8}
    resources['0'].update(expected['root'])
    for i in expected['live_newborns']:
        value = expected.get('newborn_resources', {}).get(str(i), world['nodes'].get(str(i)))
        assert value is not None, 'Missing declared newborn resources'
        resources[str(i)] = value
    assert len(resources) == expected['live_nodes']
    assert all(n['matter'] >= 0 and n['activation'] >= 0 for n in resources.values())
    assert sum(n['matter'] + 1 for n in resources.values()) + expected['live_edges'] == world['matter_total'], 'Expected matter inventory'
    assert sum(n['activation'] for n in resources.values()) + expected['dissipated'] == world['activation_total'], 'Expected activation inventory'
    endpoints = expected.get('structural_endpoints')
    if endpoints is not None:
        assert len(endpoints) == expected['live_edges'] - 8
        assert len(set(map(tuple, endpoints))) == len(endpoints)
        assert all(len(set(pair)) == len(pair) == 2 and all(str(i) in resources for i in pair) for pair in endpoints)
    if expected['outcome'] == 'whole_epoch_error':
        assert expected['error'] == 'world_size_exceeded' and expected['full_environment_unchanged']
        assert expected['committed_epochs'] == expected['committed_events'] == expected['births'] == expected['deaths'] == 0
    else:
        assert expected['outcome'] == 'complete' and expected['committed_epochs'] == family['attempted_epochs']
    if 'commits_per_epoch' in expected:
        assert len(expected['commits_per_epoch']) == expected['committed_epochs']
        assert sum(expected['commits_per_epoch']) == expected['committed_events']
    rules = family['initial']['native']['rules']
    for commit in family.get('declared_commits', []):
        assert 0 <= commit['rule'] < 8
        assert len(commit['binding']) == len(set(commit['binding'])) == len(rules[commit['rule']]['nodes'])
        assert all(0 <= i < expected['next_node'] for i in commit['binding'])
    if 'declared_commits' in family:
        assert len(family['declared_commits']) == expected['committed_events']


def validate(protocol, registry):
    assert protocol['schema'] == 'p01f-reachability-registration-v1'
    assert registry['schema'] == 'p01f-reachability-witnesses-v1'
    assert protocol['family_order'] == FAMILIES == [f['id'] for f in registry['families']], 'Family census/order'
    assert protocol['scheduler_seeds'] == [0, 1, 2, 3], 'Fixed seeds'
    assert protocol['denominator'] == 48 == len(FAMILIES) * len(protocol['scheduler_seeds']), 'Denominator'
    assert protocol['matching_engines'] == ['Reference', 'Indexed']
    assert protocol['new_world_runs_admitted_now'] is False and protocol['future_execution']['execution_admitted_now'] is False
    assert not protocol['law_sampling_admitted'] and not protocol['e01_authorized'] and protocol['scientific_status'] == 'untested'
    totals = {k: 0 for k in protocol['expected_per_matcher']}
    for family in registry['families']:
        initial_inventory(family['initial'])
        expected_accounting(family)
        e = family['expected']
        assert 1 <= family['attempted_epochs'] <= 8
        for _ in protocol['scheduler_seeds']:
            totals['attempted_epochs'] += family['attempted_epochs']
            for field in ('committed_epochs', 'committed_events'): totals[field] += e[field]
            totals['node_births'] += e['births']
            totals['node_deaths'] += e['deaths']
            totals['complete_cases' if e['outcome'] == 'complete' else 'whole_epoch_world_cap_cases'] += 1
    assert totals == protocol['expected_per_matcher'], 'Predicted census totals'
    eligible = registry['families'][0]['expected']['eligible_proposals']
    assert eligible == {'sample': 1, 'members': [0, 8], 'estimators': ['connected', 'interaction']}
    return {'schema': 'p01f-static-registration-review-v1', 'static_checks_pass': True,
            'families': 12, 'fixed_slots': 48, 'matching_engines': 2, 'predicted_per_matcher': totals,
            'candidate_enumerations': 0, 'transition_applications': 0, 'native_world_runs': 0,
            'trajectory_predictions_empirically_verified': False, 'execution_admitted': False,
            'scientific_status': 'untested', 'e01_authorized': False}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    freeze = load(ROOT / 'docs/p01f_registration_freeze.json')
    for name, expected in freeze['files'].items(): assert sha(ROOT / name) == expected, name
    result = validate(load(ROOT / 'docs/p01f_protocol.json'), load(ROOT / 'docs/p01f_witnesses.json'))
    result['registration_freeze_sha256'] = sha(ROOT / 'docs/p01f_registration_freeze.json')
    result['registration_files'] = freeze['files']
    for name, value in (('static_review.json', result), ('checksums.json', None)):
        if value is None: value = {'static_review.json': sha(out / 'static_review.json')}
        with (out / name).open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
