#!/usr/bin/env python3
"""Independent P00a transition interpreter. Uses only Python's standard library."""
import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path

if not __debug__:
    raise RuntimeError('Independent audit requires assertions; do not use Python -O')

U64 = 2**64 - 1

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def validate(w):
    assert all(0 <= int(i) < w['next_node'] for i in w['nodes'])
    assert all(0 <= int(i) < w['next_edge'] for i in w['edges'])
    assert all(0 <= w[k] <= U64 for k in ('next_node', 'next_edge', 'next_event', 'epoch', 'dissipated', 'matter_total', 'activation_total'))
    for n in w['nodes'].values():
        assert -(2**31) <= n['state'] < 2**31
        assert 0 <= n['matter'] <= U64 and 0 <= n['activation'] <= U64
    seen = set()
    for e in w['edges'].values():
        assert 2 <= len(e['ends']) <= 4
        assert len(set(e['ends'])) == len(e['ends'])
        assert all(str(i) in w['nodes'] for i in e['ends'])
        key = (e['class'], e['kind'], tuple(e['ends']))
        assert key not in seen
        seen.add(key)
    assert sum(n['matter'] + 1 for n in w['nodes'].values()) + len(w['edges']) == w['matter_total']
    assert sum(n['activation'] for n in w['nodes'].values()) + w['dissipated'] == w['activation_total']
    assert all(0 <= e < w['next_event'] for e in w['writers'].values())

def edge_exists(w, p, b):
    return any(e == {'class': p['class'], 'kind': p['kind'], 'ends': [b[i] for i in p['ends']]} for e in w['edges'].values())

def execute(w, r, binding):
    z = copy.deepcopy(w)
    b = list(binding)
    writes = set()
    def ident(slot):
        v = b[slot]
        assert str(v) in z['nodes']
        return v
    def node(slot):
        return z['nodes'][str(ident(slot))]
    def touch(slot):
        writes.add(f'node:{ident(slot)}')
    for op in r['ops']:
        tag = op['op']
        if tag in ('SetState', 'AddState'):
            n = node(op['node']); touch(op['node'])
            n['state'] = op['value'] if tag == 'SetState' else n['state'] + op['delta']
            assert -(2**31) <= n['state'] < 2**31
        elif tag == 'Transfer':
            assert ident(op['from']) != ident(op['to'])
            a, d = node(op['from']), node(op['to'])
            touch(op['from']); touch(op['to'])
            for k in ('matter', 'activation'):
                assert a[k] >= op[k]
                a[k] -= op[k]; d[k] += op[k]
                assert d[k] <= U64
        elif tag == 'Burn':
            a = node(op['node']); touch(op['node'])
            assert a['activation'] >= op['amount']
            a['activation'] -= op['amount']; z['dissipated'] += op['amount']
            assert z['dissipated'] <= U64
        elif tag == 'CreateNode':
            a = node(op['account']); touch(op['account'])
            assert a['matter'] >= 1
            a['matter'] -= 1
            i = z['next_node']; z['next_node'] += 1
            assert z['next_node'] <= U64
            z['nodes'][str(i)] = {'kind': op['kind'], 'state': op['state'], 'matter': 0, 'activation': 0}
            b.append(i); writes.update((f'node:{i}', f'adj:{i}'))
        elif tag == 'DeleteNode':
            i, dest = ident(op['node']), ident(op['recipient'])
            assert i != dest and not any(i in e['ends'] for e in z['edges'].values())
            touch(op['node']); touch(op['recipient']); writes.add(f'adj:{i}')
            old = z['nodes'].pop(str(i)); n = node(op['recipient'])
            n['matter'] += old['matter'] + 1; n['activation'] += old['activation']
            assert n['matter'] <= U64 and n['activation'] <= U64
        elif tag in ('CreateEdge', 'DeleteEdge'):
            ids = [ident(s) for s in op['ends']]
            e = {'class': 'Structural', 'kind': op['kind'], 'ends': ids}
            found = [i for i, existing in z['edges'].items() if existing == e]
            a = node(op['account']); touch(op['account'])
            writes.update(f'adj:{i}' for i in ids)
            if tag == 'CreateEdge':
                assert not found and a['matter'] >= 1
                a['matter'] -= 1
                i = z['next_edge']; z['next_edge'] += 1
                assert z['next_edge'] <= U64
                z['edges'][str(i)] = e
            else:
                assert len(found) == 1
                del z['edges'][found[0]]; a['matter'] += 1
                assert a['matter'] <= U64
        else:
            raise ValueError(f'Unknown operation {tag}')
    validate(z)
    return z, writes

def enumerate_candidates(exp, w):
    candidates = []
    for r in exp['rules']:
        choices = [[int(i) for i, n in w['nodes'].items()
                    if n['kind'] == p['kind'] and (p['state'] is None or n['state'] == p['state'])]
                   for p in r['nodes']]
        for b in itertools.product(*choices):
            if len(set(b)) != len(b):
                continue
            if not all(edge_exists(w, p, b) for p in r['edges']) or any(edge_exists(w, p, b) for p in r['absent']):
                continue
            try:
                _, writes = execute(w, r, b)
            except AssertionError:
                continue
            reads = {f'{prefix}:{i}' for i in b for prefix in ('node', 'adj')}
            writes = {key for key in writes if key.split(':')[1] in w['nodes']}
            candidates.append({'rule': r['id'], 'binding': list(b),
                               'priority': digest(['priority-v1', exp['seed'], w['epoch'], r['id'], list(b)]),
                               'reads': sorted(reads), 'writes': sorted(writes)})
    return sorted(candidates, key=lambda c: (c['priority'], c['rule'], c['binding']))

def verify_case(case):
    exp = case['initial']
    assert exp['profile'] == 'p00a-local-closed-v1'
    w = copy.deepcopy(exp['world']); validate(w)
    count = 0
    for frame in case['frames']:
        assert frame['before'] == digest(w), 'before digest'
        candidates = enumerate_candidates(exp, w)
        assert candidates == frame['candidates'], 'candidate completeness / priority / footprints'
        accepted, reads, writes = [], set(), set()
        for c in candidates:
            cr, cw = set(c['reads']), set(c['writes'])
            if cw & (reads | writes) or cr & writes:
                continue
            accepted.append(c); reads |= cr; writes |= cw
        accepted.sort(key=lambda c: (c['rule'], c['binding']))
        assert [e['candidate'] for e in frame['events']] == accepted, 'scheduler selection'
        for event, c in zip(frame['events'], accepted):
            assert event['id'] == w['next_event']
            parents = sorted({w['writers'][k] for k in c['reads'] + c['writes'] if k in w['writers']})
            assert parents == event['parents'], 'dependency parents'
            r = next(r for r in exp['rules'] if r['id'] == c['rule'])
            w, all_writes = execute(w, r, c['binding'])
            w['next_event'] += 1
            for k in all_writes:
                w['writers'][k] = event['id']
            count += 1
        w['epoch'] += 1
        validate(w)
        assert len(w['nodes']) <= exp['limits']['max_nodes']
        assert len(w['edges']) <= exp['limits']['max_edges']
        assert w == frame['world'], 'independent state replay'
        assert digest(w) == frame['after'], 'after digest'
    if case['name'] in ('frozen', 'resource_exhaustion'):
        assert count == 0 and w['nodes'] == exp['world']['nodes']
    if case['name'] == 'oscillator':
        assert count == 24 and w['nodes'] == exp['world']['nodes']
    return count

def audit(suite):
    assert suite['schema'] == 'p00a-suite-v1'
    names = {'frozen', 'oscillator', 'attach_detach', 'growth_recycling', 'transfer', 'absence_conflict', 'resource_exhaustion'}
    assert {(c['name'], c['initial']['seed']) for c in suite['cases']} == {(n,s) for n in names for s in range(16)}
    assert len(suite['cases']) == 112
    assert all(len(c['frames']) == 12 for c in suite['cases'])
    count = sum(verify_case(c) for c in suite['cases'])
    return {'status': 'pass', 'cases': 112, 'epochs': 1344, 'events': count,
            'scientific_status': 'untested', 'scope': 'P00a closed fixed-contact transition fixtures'}

if __name__ == '__main__':
    result = audit(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(result, indent=2))
