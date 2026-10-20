#!/usr/bin/env python3
"""Independent fixed-panel replay and literal expectations; no native subprocess."""
import copy
import json
import sys
from pathlib import Path
import audit
import audit_detectors
import audit_environment
import audit_integration
import audit_single_pass
import check_p01f_registration as registration
import pilot_reporting

if not __debug__:
    raise RuntimeError('Audit requires assertions')


def slots(protocol, registry):
    return [(family, seed) for family in registry['families']
            for seed in protocol['scheduler_seeds']]


def endpoint(family, initial, result):
    expected = family['expected']
    frames, failures = result['frames'], result['failures']
    final = result['final_state']
    start, world = initial['native']['world'], final['native']['world']
    assert len(frames) == expected['committed_epochs'], 'Committed epoch count'
    assert len(frames) + len(failures) == family['attempted_epochs'], 'Attempt count'
    assert len(failures) == (expected['outcome'] == 'whole_epoch_error'), 'Outcome'
    if failures:
        failure = failures[0]
        assert failure['attempt'] == len(frames)
        assert failure['error'] == expected['error'] == 'world_size_exceeded'
        assert failure['before'] == failure['after'] == final == initial, 'Full rollback'
        assert failure['candidates'] == audit.enumerate_candidates(final['native'], world)
        try:
            pilot_reporting.next_epoch(final)
        except pilot_reporting.Cap as error:
            assert str(error) == failure['error'], 'Independent cap reason'
        else:
            raise AssertionError('Unjustified whole-epoch error')
    assert final == dict(initial, native=dict(initial['native'], world=world)), 'Non-world mutation'
    assert world['epoch'] == start['epoch'] + len(frames)
    counts = [len(f['native_frame']['events']) for f in frames]
    assert sum(counts) == expected['committed_events']
    assert world['next_event'] == start['next_event'] + sum(counts)
    if 'commits_per_epoch' in expected: assert counts == expected['commits_per_epoch']
    if 'declared_commits' in family:
        assert [{'rule':e['candidate']['rule'], 'binding':e['candidate']['binding']}
                for f in frames for e in f['native_frame']['events']] == family['declared_commits']
    worlds = [start] + [f['state']['native']['world'] for f in frames]
    births = sum(len(set(b['nodes']) - set(a['nodes'])) for a,b in zip(worlds, worlds[1:]))
    deaths = sum(len(set(a['nodes']) - set(b['nodes'])) for a,b in zip(worlds, worlds[1:]))
    assert births == expected['births'] and deaths == expected['deaths'], 'Turnover'
    for field, actual in [('live_nodes',len(world['nodes'])), ('live_edges',len(world['edges']))]:
        assert actual == expected[field], field
    for field in ('next_node','next_edge','dissipated'): assert world[field] == expected[field], field
    for field in ('matter_total','activation_total'): assert world[field] == start[field], field
    assert [int(i) for i in sorted(world['nodes'], key=int) if int(i) >= 8] == expected['live_newborns']
    nodes = {i:copy.deepcopy(n) for i,n in start['nodes'].items() if int(i)<8}
    nodes['0'].update(expected['root'])
    birth_rule = next((r for r in initial['native']['rules']
                       if r['ops'][0]['op']=='CreateNode'), None)
    for ident in expected['live_newborns']:
        key = str(ident)
        if key in start['nodes']:
            node = copy.deepcopy(start['nodes'][key])
        else:
            # These literal positive cases fix kinds 2 for ID8, 3 for ID9.
            assert birth_rule is not None and ident in (8,9)
            node = {'kind':ident-6, 'state':0, 'matter':0, 'activation':0}
        node.update(expected.get('newborn_resources',{}).get(key,{}))
        nodes[key] = node
    assert world['nodes'] == nodes, 'Full endpoint nodes'
    contacts = {k:e for k,e in start['edges'].items() if e['class']=='Contact'}
    assert {k:e for k,e in world['edges'].items() if e['class']=='Contact'} == contacts
    structural = [e for e in world['edges'].values() if e['class']=='Structural']
    if 'structural_endpoints' in expected:
        assert sorted(e['ends'] for e in structural) == sorted(expected['structural_endpoints'])
        assert all(e['kind']==0 for e in structural)
    else:
        assert world['edges'] == start['edges'], 'Unchanged edges'
    if 'max_live_newborns_at_most' in expected:
        assert max(sum(int(i)>=8 for i in w['nodes']) for w in worlds) <= expected['max_live_newborns_at_most']
    if sum(counts)==0:
        unchanged = copy.deepcopy(start); unchanged['epoch'] += len(frames)
        assert world == unchanged, 'Empty epoch leaked staged changes'
    eligible = expected.get('eligible_proposals')
    if eligible:
        for estimator in eligible['estimators']:
            proposals = result['detection'][estimator]['samples'][eligible['sample']]
            assert any(p['members']==eligible['members'] for p in proposals), 'Newborn eligibility'
    if family['id']=='structural_funding':
        assert all(not members for epoch in result['activities'] for members in epoch), 'Resource-only activity'
    return {'attempted_epochs':len(frames)+len(failures),'committed_epochs':len(frames),
            'committed_events':sum(counts),'node_births':births,'node_deaths':deaths,
            'complete_cases':int(not failures),'whole_epoch_world_cap_cases':len(failures)}


def verify_result(family, initial, result):
    assert 'runner_error' not in result, result
    frames = result['frames']
    quiet = [f['after'] for f in frames]
    current = copy.deepcopy(initial)
    old_activity = []
    for frame in frames:
        # Original interpreter verifies candidate completeness, ordering, parents,
        # writes, resources and states. No transition logic is shared with Rust.
        current, _ = audit_environment.apply_environment(current)
        audit.verify_case({'name':'p01f','initial':current['native'],
                           'frames':[frame['native_frame']]})
        old_activity.append(audit_detectors.activity(current['native'],[frame['native_frame']])[0])
        current['native']['world'] = frame['native_frame']['world']
    reference = audit_integration.analyze_environment(initial, frames, quiet)
    fused, final, _, _ = audit_single_pass.replay_environment(initial, frames, quiet)
    assert reference == fused == result['detection'], 'Full detector record'
    assert final == current == result['final_state'], 'Final environment'
    fused_activity = []
    for frame in frames:
        _, activities, _ = audit_single_pass.native_frames(frame['prepared'],[frame['native_frame']])
        fused_activity.extend(activities)
    assert old_activity == fused_activity, 'Independent activity agreement'
    serial_activity = [[sorted(group) for group in epoch] for epoch in old_activity]
    assert serial_activity == result['activities'], 'Full native activity record'
    return endpoint(family, initial, result)


def verify_panel(protocol, registry, rows):
    registration.validate(protocol, registry)
    planned = slots(protocol, registry)
    assert len(rows) == len(planned) == 48, 'Fixed denominator'
    totals = {name:{key:0 for key in protocol['expected_per_matcher']}
              for name in protocol['matching_engines']}
    receipts = []
    for slot, ((family, seed), row) in enumerate(zip(planned, rows)):
        receipt = {'slot':slot,'family':family['id'],'seed':seed,'status':'failed'}
        try:
            initial = copy.deepcopy(family['initial']); initial['native']['seed']=seed
            assert row['schema']=='p01f-witness-slot-v1'
            assert (row['slot'],row['family'],row['seed'])==(slot,family['id'],seed), 'Fixed slot identity'
            assert row['initial']==initial, 'Fixed initial state'
            assert list(sorted(row['results']))==['Indexed','Reference'], 'Matchers'
            assert row['results']['Reference']==row['results']['Indexed'], 'Exact matcher records'
            for name in protocol['matching_engines']:
                measured = verify_result(family, initial, row['results'][name])
                for key,value in measured.items(): totals[name][key]+=value
            receipt.update(status='pass',result_digest=audit.digest(row['results']['Reference']))
        except (AssertionError,KeyError,TypeError,ValueError,IndexError) as error:
            receipt['error']=repr(error)
        receipts.append(receipt)
    passed = all(r['status']=='pass' for r in receipts)
    passed = passed and all(t==protocol['expected_per_matcher'] for t in totals.values())
    return {'schema':'p01f-panel-audit-v1','status':'pass' if passed else 'failed',
            'fixed_slots':48,'matcher_case_passes':2*sum(r['status']=='pass' for r in receipts),
            'per_matcher':totals,'cases':receipts,'scientific_status':'untested',
            'scope':'authored fixture reachability only','law_sampling_admitted':False}


def main():
    protocol, registry, trace = map(Path, sys.argv[1:])
    raw = trace.read_bytes()
    assert raw.endswith(b'\n'), 'Partial record'
    rows = [json.loads(line) for line in raw.splitlines()]
    assert raw == b''.join(audit.canonical(row)+b'\n' for row in rows), 'Noncanonical trace'
    print(json.dumps(verify_panel(registration.load(protocol),registration.load(registry),rows),sort_keys=True))

if __name__=='__main__': main()
