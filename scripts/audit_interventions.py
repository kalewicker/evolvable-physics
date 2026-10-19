#!/usr/bin/env python3
"""Independent external-operation, matched-control, and native-continuation checker."""
import copy
import json
import sys
from pathlib import Path
import audit

if not __debug__:
    raise RuntimeError('Audit requires assertions; do not use -O')

FAMILIES = ('state_arrest', 'activation_relocation')
ARMS = ('baseline', 'sham', 'target', 'unrelated', 'rescue')

def replay_branch(source, record):
    assert set(record) == {'request', 'receipt', 'experiment'}
    req = record['request']
    assert set(req) == {'schema', 'expected_source', 'operations'}
    assert req['schema'] == 'intervention-v1'
    assert req['expected_source'] == audit.digest(source), 'source identity'
    assert len(req['operations']) <= 8
    out = copy.deepcopy(source)
    audit.validate(out['world'])
    keys = set()
    for op in req['operations']:
        nodes = out['world']['nodes']
        if op['op'] == 'SetState':
            assert set(op) == {'op', 'node', 'expected', 'value'}
            n = nodes[str(op['node'])]
            assert n['state'] == op['expected'], 'state precondition'
            assert -(2**31) <= op['value'] < 2**31
            n['state'] = op['value']
            keys.add(f"node:{op['node']}")
        elif op['op'] == 'MoveResources':
            assert set(op) == {'op', 'from', 'to', 'matter', 'activation'}
            assert op['from'] != op['to']
            a, b = nodes[str(op['from'])], nodes[str(op['to'])]
            for channel in ('matter', 'activation'):
                amount = op[channel]
                assert 0 <= amount <= audit.U64 and a[channel] >= amount
                a[channel] -= amount
                b[channel] += amount
                assert b[channel] <= audit.U64
            keys.update((f"node:{op['from']}", f"node:{op['to']}"))
        else:
            raise AssertionError('unknown intervention')
    parents = sorted({source['world']['writers'][k] for k in keys if k in source['world']['writers']})
    event_id = None
    if req['operations']:
        event_id = out['world']['next_event']
        out['world']['next_event'] += 1
        assert out['world']['next_event'] <= audit.U64
        for k in keys:
            out['world']['writers'][k] = event_id
    audit.validate(out['world'])
    assert record['experiment'] == out, 'branch transition / immutable configuration'
    receipt = {'schema': 'intervention-receipt-v1', 'request_digest': audit.digest(req),
               'before': audit.digest(source), 'after': audit.digest(out), 'epoch': source['world']['epoch'],
               'event_id': event_id, 'reads': sorted(keys), 'writes': sorted(keys), 'parents': parents}
    assert record['receipt'] == receipt, 'receipt provenance'
    return out

def prescribed_operations(source, family, arm):
    if arm == 'baseline':
        return []
    node = 2 if arm == 'unrelated' else 0
    n = source['world']['nodes'][str(node)]
    if family == 'state_arrest':
        return [{'op': 'SetState', 'node': node, 'expected': n['state'], 'value': n['state'] if arm == 'sham' else 9}]
    return [{'op': 'MoveResources', 'from': node, 'to': 1, 'matter': 0, 'activation': 0 if arm == 'sham' else n['activation']}]

def physical(world):
    return {k:v for k,v in world.items() if k not in ('writers', 'next_event')}

def verify_case(case):
    family = case['family']
    assert family in FAMILIES
    initial = case['initial']
    assert initial['world'] == {
        'nodes': {'0': {'kind':1,'state':0,'matter':8,'activation':8},
                  '1': {'kind':2,'state':0,'matter':0,'activation':8},
                  '2': {'kind':1,'state':0,'matter':8,'activation':8}},
        'edges': {'0': {'class':'Contact','kind':0,'ends':[0,1]},
                  '1': {'class':'Contact','kind':0,'ends':[2,1]}},
        'next_node':3,'next_edge':2,'epoch':0,'dissipated':0,'matter_total':21,
        'activation_total':24,'next_event':0,'writers':{}}
    rules = []
    for state in (0,1):
        ops = [{'op':'SetState','node':0,'value':1-state}]
        if family == 'activation_relocation': ops.append({'op':'Burn','node':0,'amount':1})
        rules.append({'id':state,'nodes':[{'kind':1,'state':state}],'edges':[],'absent':[],'ops':ops})
    assert initial['rules'] == rules, 'fixture law registry'
    assert len(case['warmup']) == 2
    warmup_events = audit.verify_case({'name':'intervention_warmup','initial':initial,'frames':case['warmup']})
    source = copy.deepcopy(initial); source['world'] = case['warmup'][-1]['world']
    assert case['source'] == source, 'source must follow registered warmup'
    assert source['world']['nodes']['0'] == source['world']['nodes']['2'], 'matched type/state/resources'
    degrees = {i:sum(int(i) in e['ends'] for e in source['world']['edges'].values()) for i in ('0','2')}
    assert degrees['0'] == degrees['2'] == 1
    assert len(case['arms']) == 5 and [a['name'] for a in case['arms']] == list(ARMS)
    baseline = case['arms'][0]
    total = 0
    outcomes = {}
    for arm in case['arms']:
        name = arm['name']; current = copy.deepcopy(source)
        assert len(arm['chain']) == (2 if name == 'rescue' else 1), 'complete intervention chain'
        assert arm['chain'][0]['request']['operations'] == prescribed_operations(source, family, name), 'registered arm'
        if name == 'rescue':
            restore = ({'op':'SetState','node':0,'expected':9,'value':source['world']['nodes']['0']['state']}
                       if family == 'state_arrest' else
                       {'op':'MoveResources','from':1,'to':0,'matter':0,'activation':source['world']['nodes']['0']['activation']})
            assert arm['chain'][1]['request']['operations'] == [restore], 'registered rescue'
        for record in arm['chain']:
            current = replay_branch(current, record)
        if name == 'baseline': assert current == source
        if name in ('sham','rescue'): assert physical(current['world']) == physical(source['world'])
        assert len(arm['frames']) == 8
        total += audit.verify_case({'name':'intervention_continuation','initial':current,'frames':arm['frames']})
        counts = {i:sum(e['candidate']['binding'] == [i] for f in arm['frames'] for e in f['events']) for i in (0,2)}
        full = 8 if family == 'state_arrest' else 6
        assert counts[0] == (0 if name == 'target' else full), 'focal-node effect'
        assert counts[2] == (0 if name == 'unrelated' else full), 'control-node effect'
        outcomes[name] = {'focal_events':counts[0], 'control_events':counts[2]}
        if name in ('sham','rescue'):
            for frame, original in zip(arm['frames'], baseline['frames']):
                assert physical(frame['world']) == physical(original['world']), 'rescue/sham physical trajectory'
                assert frame['candidates'] == original['candidates'], 'common candidate priority coupling'
    return total, warmup_events, outcomes

def audit_suite(suite):
    assert suite['schema'] == 'p00b-intervention-suite-v1'
    assert suite['scientific_status'] == 'untested'
    assert len(suite['cases']) == 32
    assert {(c['family'],c['initial']['seed']) for c in suite['cases']} == {(f,s) for f in FAMILIES for s in range(16)}
    total = warmup = 0
    outcomes = {}
    for case in suite['cases']:
        count, prelude, result = verify_case(case)
        total += count; warmup += prelude
        if case['family'] in outcomes: assert outcomes[case['family']] == result
        outcomes[case['family']] = result
    return {'status':'pass','cases':32,'arms':160,'continuation_epochs':1280,
            'continuation_events':total,'warmup_epochs':64,'warmup_events':warmup,
            'expected_engineering_outcomes':outcomes,'scientific_status':'untested'}

def verify_bundle(path):
    path = Path(path)
    manifest = json.loads((path/'manifest.json').read_text())
    assert manifest['schema'] == 'branch-bundle-v1' and manifest['execution_status'] == 'complete'
    def checkpoint(name):
        cp = json.loads((path/name).read_text())
        assert cp['schema'] == 'checkpoint-v1' and cp['digest'] == audit.digest(cp['payload'])
        return cp['payload']
    source = checkpoint('source.json')
    record = json.loads((path/'branch.json').read_text())
    out = replay_branch(source, record)
    assert checkpoint('checkpoint.json') == out
    assert manifest['source_digest'] == audit.digest(source)
    assert manifest['branch_digest'] == audit.digest(record)
    assert manifest['checkpoint_digest'] == audit.digest(out)
    return out

if __name__ == '__main__':
    print(json.dumps(audit_suite(json.loads(Path(sys.argv[1]).read_text())), indent=2))
