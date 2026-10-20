#!/usr/bin/env python3
"""Independent Python replay with activity emitted during checked event application.

The reference audit, environment interpreter, detector and cap validator are frozen.
No native simulator or Rust transition code is called by this adapter.
"""
import copy
import json
from pathlib import Path
import audit
import audit_detectors as detector
import audit_environment as environment
import audit_integration as integration
import pilot_reporting as reference

if not __debug__:
    raise RuntimeError('Independent audit requires assertions')


def native_frames(initial, frames, name='single_pass'):
    """Check candidates, scheduler, provenance, accounting and states; emit activity."""
    assert initial['profile'] == 'p00a-local-closed-v1'
    world = copy.deepcopy(initial['world'])
    audit.validate(world)
    activities = []
    count = 0
    for frame in frames:
        assert frame['before'] == audit.digest(world), 'before digest'
        candidates = audit.enumerate_candidates(initial, world)
        assert candidates == frame['candidates'], 'candidate completeness / priority / footprints'
        accepted, reads, writes = [], set(), set()
        for candidate in candidates:
            cr, cw = set(candidate['reads']), set(candidate['writes'])
            if cw & (reads | writes) or cr & writes:
                continue
            accepted.append(candidate)
            reads |= cr
            writes |= cw
        accepted.sort(key=lambda c: (c['rule'], c['binding']))
        assert [e['candidate'] for e in frame['events']] == accepted, 'scheduler selection'
        activity = []
        for event, candidate in zip(frame['events'], accepted):
            assert event['id'] == world['next_event'], 'event id'
            parents = sorted({world['writers'][k] for k in candidate['reads'] + candidate['writes']
                              if k in world['writers']})
            assert parents == event['parents'], 'dependency parents'
            rule = next(r for r in initial['rules'] if r['id'] == candidate['rule'])
            after, changed_writes = audit.execute(world, rule, candidate['binding'])
            activity.append(detector.changed(world, after))
            world = after
            world['next_event'] += 1
            for key in changed_writes:
                world['writers'][key] = event['id']
            count += 1
        world['epoch'] += 1
        audit.validate(world)
        assert len(world['nodes']) <= initial['limits']['max_nodes']
        assert len(world['edges']) <= initial['limits']['max_edges']
        assert world == frame['world'], 'independent state replay'
        assert audit.digest(world) == frame['after'], 'after digest'
        activities.append(activity)
    if name in ('frozen', 'resource_exhaustion'):
        assert count == 0 and world['nodes'] == initial['world']['nodes']
    if name == 'oscillator':
        assert count == 24 and world['nodes'] == initial['world']['nodes']
    return world, activities, count


def replay_environment(initial, frames, quiet):
    assert len(quiet) == len(frames)
    current = copy.deepcopy(initial)
    worlds = [current['native']['world']]
    activities = []
    native_events = candidates = 0
    for frame, disabled in zip(frames, quiet):
        assert frame['before'] == audit.digest(current), 'environment before'
        current, external = environment.apply_environment(current)
        assert frame['environment_events'] == external, 'environment phase'
        assert frame['prepared'] == current['native'], 'prepared state'
        world, activity, count = native_frames(current['native'], [frame['native_frame']])
        native_events += count
        candidates += len(frame['native_frame']['candidates'])
        current['native']['world'] = world
        environment.validate(current)
        after = audit.digest(current)
        assert frame['state'] == current and frame['after'] == after and disabled == after, 'whole state/logging prefix'
        worlds.append(world)
        activities.append(activity[0])
    return integration.detection(worlds, activities), current, native_events, candidates


def verify(request, directory, report):
    assert request['schema'] == 'p01-worker-request-v1' and 0 <= request['epochs'] <= 1000
    raw = (directory / 'trace.jsonl').read_bytes()
    assert not raw or raw.endswith(b'\n'), 'Partial record'
    frames = [json.loads(line) for line in raw.splitlines()]
    assert raw == b''.join(audit.canonical(f) + b'\n' for f in frames), 'Noncanonical record'
    summary = json.loads((directory / 'worker.json').read_bytes())
    detection, final, native, candidates = replay_environment(request['initial'], frames,
                                                            [f['after'] for f in frames])
    assert summary['schema'] == 'p01-worker-result-v1'
    assert summary['final_state'] == final
    assert summary['epochs'] == len(frames)
    assert summary['events'] == final['native']['world']['next_event'] - request['initial']['native']['world']['next_event']
    assert summary['native_events'] == native and summary['applicable_candidates'] == candidates
    assert len(raw) == summary['trace_bytes'] <= request['max_trace_bytes']
    assert summary['events'] <= request['max_events'] and len(frames) <= request['epochs']
    complete = summary['status'] == 'complete'
    if complete:
        assert len(frames) == request['epochs'], 'Incomplete horizon'
    else:
        assert len(frames) < request['epochs']
        try:
            frame = reference.next_epoch(final)
            events = frame['state']['native']['world']['next_event'] - request['initial']['native']['world']['next_event']
            if events > request['max_events']:
                reason = 'event_budget_exceeded'
            elif len(audit.canonical(frame)) + 1 > request['max_trace_bytes'] - summary['trace_bytes']:
                reason = 'trace_budget_exceeded'
            else:
                raise AssertionError('Unjustified cap')
        except reference.Cap as cap:
            reason = str(cap)
        assert reason == summary['status'], 'Wrong cap reason'
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
    result = verify(json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]),
                    json.loads(Path(sys.argv[3]).read_text()))
    print(json.dumps({'status': 'pass', 'full_horizon_ap': result}))
