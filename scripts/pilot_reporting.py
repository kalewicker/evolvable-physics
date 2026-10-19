#!/usr/bin/env python3
"""Independent P01 report verification, including whole-epoch cap justification."""
import copy
import json
from pathlib import Path
import audit
import audit_environment
import audit_integration
import pilot


class Cap(Exception):
    pass


def matching_cap(exp):
    # Separate census of all partial pushes/full patterns, including inapplicable operations.
    visits = matches = 0
    w = exp['world']
    for rule in sorted(exp['rules'], key=lambda r: r['id']):
        choices = [[int(i) for i in sorted(w['nodes'], key=int)
                    if w['nodes'][i]['kind'] == pattern['kind']] for pattern in rule['nodes']]
        stack = [[]]
        while stack:
            binding = stack.pop()
            if len(binding) < len(choices):
                pattern = rule['nodes'][len(binding)]
                for ident in reversed(choices[len(binding)]):
                    if ident in binding or (pattern['state'] is not None and
                                            w['nodes'][str(ident)]['state'] != pattern['state']):
                        continue
                    visits += 1
                    if visits > exp['limits']['max_bindings']: raise Cap('binding_budget_exceeded')
                    stack.append(binding+[ident])
            elif (all(audit.edge_exists(w, p, binding) for p in rule['edges']) and
                  not any(audit.edge_exists(w, p, binding) for p in rule['absent'])):
                matches += 1
                if matches > exp['limits']['max_candidates']: raise Cap('match_budget_exceeded')


def next_epoch(source):
    e, external = audit_environment.apply_environment(source)
    prepared = copy.deepcopy(e['native']); w = e['native']['world']
    matching_cap(e['native'])
    candidates = audit.enumerate_candidates(e['native'], w)
    selected = []; reads = set(); writes = set()
    for candidate in candidates:
        cr, cw = set(candidate['reads']), set(candidate['writes'])
        if cw & (reads | writes) or cr & writes: continue
        selected.append(candidate); reads |= cr; writes |= cw
    selected.sort(key=lambda c: (c['rule'], c['binding']))
    events = []
    for candidate in selected:
        parents = sorted({w['writers'][k] for k in candidate['reads']+candidate['writes'] if k in w['writers']})
        event = {'id': w['next_event'], 'candidate': candidate, 'parents': parents}
        rule = next(r for r in e['native']['rules'] if r['id'] == candidate['rule'])
        w, changed = audit.execute(w, rule, candidate['binding'])
        w['next_event'] += 1
        for key in changed: w['writers'][key] = event['id']
        events.append(event)
    w['epoch'] += 1
    if len(w['nodes']) > prepared['limits']['max_nodes'] or len(w['edges']) > prepared['limits']['max_edges']:
        raise Cap('world_size_exceeded')
    e['native']['world'] = w; audit_environment.validate(e)
    return {'before': audit.digest(source), 'after': audit.digest(e), 'environment_events': external,
            'prepared': prepared, 'native_frame': {'before': audit.digest(prepared['world']),
            'after': audit.digest(w), 'candidates': candidates, 'events': events, 'world': w}, 'state': e}


def verify(request, directory, report):
    assert request['schema'] == 'p01-worker-request-v1' and 0 <= request['epochs'] <= 1000
    raw = (directory/'trace.jsonl').read_bytes()
    assert not raw or raw.endswith(b'\n'), 'Partial record'
    frames = [json.loads(line) for line in raw.splitlines()]
    assert raw == b''.join(audit.canonical(f)+b'\n' for f in frames), 'Noncanonical record'
    summary = json.loads((directory/'worker.json').read_bytes())
    pilot.verify_trace(request['initial'], frames, summary)
    assert len(raw) == summary['trace_bytes'] <= request['max_trace_bytes']
    assert summary['events'] <= request['max_events'] and len(frames) <= request['epochs']
    complete = summary['status'] == 'complete'
    if complete:
        assert len(frames) == request['epochs'], 'Incomplete horizon'
    else:
        assert len(frames) < request['epochs']
        current = summary['final_state']
        try:
            frame = next_epoch(current)
            events = frame['state']['native']['world']['next_event']-request['initial']['native']['world']['next_event']
            if events > request['max_events']:
                reason = 'event_budget_exceeded'
            elif len(audit.canonical(frame))+1 > request['max_trace_bytes']-summary['trace_bytes']:
                reason = 'trace_budget_exceeded'
            else:
                raise AssertionError('Unjustified cap')
        except Cap as cap:
            reason = str(cap)
        assert reason == summary['status'], 'Wrong cap reason'
    detection = audit_integration.analyze_environment(request['initial'], frames, [f['after'] for f in frames])
    expected = {'schema': 'p01-detector-report-v1', 'request_digest': audit.digest(request),
                'worker_result_digest': audit.digest(summary), 'trace_bytes': len(raw),
                'worker_status': summary['status'], 'requested_epochs': request['epochs'],
                'observed_epochs': len(frames), 'coverage': 'complete' if complete else 'censored_prefix',
                'full_horizon_ap': detection['active_persistence'] if complete else None,
                'prefix_detection': detection, 'maintenance_status': 'not_assessed', 'scientific_status': 'untested'}
    assert report == expected, 'Detector report mismatch'
    return report['full_horizon_ap']


if __name__ == '__main__':
    import sys
    verify(json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()))
    print('Independent P01 detector report: pass')
