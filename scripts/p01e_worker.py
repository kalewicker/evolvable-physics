#!/usr/bin/env python3
"""Fixed offline correctness/tamper/performance tasks; emits compact receipts only."""
import copy
import hashlib
import json
import sys
from pathlib import Path
import audit
import audit_detectors as detector
import audit_integration as integration
import audit_single_pass as candidate
import pilot_reporting as reference
import validate_p01b as assembler


def load(path):
    return json.loads(Path(path).read_bytes())


def digest_activity(activity):
    return audit.digest([[sorted(group) for group in epoch] for epoch in activity])


def fixtures(native_path, environment_path):
    native = load(native_path)
    assert len(native['cases']) == 112
    records = []
    for case in native['cases']:
        count = audit.verify_case(case)
        expected = detector.activity(case['initial'], case['frames'])
        world, activity, actual = candidate.native_frames(case['initial'], case['frames'], case['name'])
        assert count == actual and activity == expected
        assert world == case['frames'][-1]['world']
        worlds = [case['initial']['world']] + [frame['world'] for frame in case['frames']]
        a = integration.detection(worlds, activity)
        b = integration.detection(worlds, expected)
        assert a == b
        records.append({'family': case['name'], 'seed': case['initial']['seed'], 'events': actual,
                        'activity_digest': digest_activity(activity), 'detection_digest': audit.digest(a)})
    environment = load(environment_path)
    p = integration.registry()
    assert environment['protocol'] == p and environment['protocol_digest'] == audit.digest(p)
    assert len(environment['cases']) == 96
    extras = 0
    for case in environment['cases']:
        count = integration.verify_case(case, p)  # Includes frozen branch/maintenance checks.
        expected = case['detection']
        actual, world, events, _ = candidate.replay_environment(case['initial'], case['epochs'], case['disabled_digests'])
        assert actual == expected and world == case['epochs'][-1]['state'] and count == events
        m = case['maintenance']
        if m:
            replayed = candidate.replay_environment(case['initial'], m['warmup'], m['disabled_warmup_digests'])
            assert replayed[0] == integration.analyze_environment(case['initial'], m['warmup'], m['disabled_warmup_digests'])
            assert replayed[1] == m['source']
            for arm in m['arms']:
                current = copy.deepcopy(m['source'])
                for branch in arm['chain']:
                    current = integration.env_replay.replay_branch(current, branch)
                result = candidate.replay_environment(current, arm['epochs'], arm['disabled_digests'])
                assert result[0] == integration.analyze_environment(current, arm['epochs'], arm['disabled_digests'])
                assert result[1] == arm['epochs'][-1]['state']
                extras += 1
        records.append({'family': case['family'], 'seed': case['initial']['native']['seed'],
                        'events': events, 'detection_digest': audit.digest(actual)})
    assert extras == 80
    return {'status': 'pass', 'native_cases': 112, 'environment_cases': 96,
            'maintenance_arms_within_environment_cases': extras, 'records': records}


def slot(implementation, request_path, native_path, report_path):
    request, report = load(request_path), load(report_path)
    module = {'reference': reference, 'candidate': candidate}[implementation]
    endpoint = module.verify(request, Path(native_path), report)
    assert report['coverage'] != 'censored_prefix' or endpoint is None
    return {'status': 'pass', 'coverage': report['coverage'], 'full_horizon_ap': endpoint,
            'request_digest': audit.digest(request), 'report_digest': audit.digest(report),
            'trace_sha256': hashlib.sha256((Path(native_path) / 'trace.jsonl').read_bytes()).hexdigest(),
            'summary_sha256': hashlib.sha256((Path(native_path) / 'worker.json').read_bytes()).hexdigest()}


REASONS = {'priority': 'candidate completeness', 'parent': 'dependency parents',
           'event_omission': 'scheduler selection', 'ledger': 'whole state',
           'prepared_order': 'prepared state', 'external_receipt': 'environment phase',
           'world': 'independent state replay', 'summary': '', 'detector_output': 'Detector report mismatch',
           'forged_cap': 'Unjustified cap', 'partial_record': 'Partial record'}


def tamper_inputs(case, name):
    initial, frames = copy.deepcopy(case['initial']), copy.deepcopy(case['epochs'])
    request = assembler.request(initial, len(frames))
    raw = b''.join(audit.canonical(f) + b'\n' for f in frames)
    final = frames[-1]['state']
    summary = {'schema': 'p01-worker-result-v1', 'status': 'complete', 'epochs': len(frames),
               'events': final['native']['world']['next_event'] - initial['native']['world']['next_event'],
               'native_events': sum(len(f['native_frame']['events']) for f in frames),
               'applicable_candidates': sum(len(f['native_frame']['candidates']) for f in frames),
               'trace_bytes': len(raw), 'step_ns': 0, 'serialize_ns': 0, 'write_ns': 0, 'final_state': copy.deepcopy(final)}
    report = {'schema': 'p01-detector-report-v1', 'request_digest': audit.digest(request),
              'worker_result_digest': audit.digest(summary), 'trace_bytes': len(raw), 'worker_status': 'complete',
              'requested_epochs': len(frames), 'observed_epochs': len(frames), 'coverage': 'complete',
              'full_horizon_ap': case['detection']['active_persistence'], 'prefix_detection': copy.deepcopy(case['detection']),
              'maintenance_status': 'not_assessed', 'scientific_status': 'untested'}
    if name == 'priority':
        frame = next(f for f in frames if f['native_frame']['candidates'])
        frame['native_frame']['candidates'][0]['priority'] = 'forged-priority'
    elif name == 'parent':
        event = next(f['native_frame']['events'][0] for f in frames if f['native_frame']['events'])
        event['parents'] = [audit.U64]
    elif name == 'event_omission':
        next(f['native_frame']['events'] for f in frames if f['native_frame']['events']).pop()
    elif name == 'ledger': frames[0]['state']['injected'] += 1
    elif name == 'prepared_order': frames[0]['prepared'] = copy.deepcopy(initial['native'])
    elif name == 'external_receipt': frames[0]['environment_events'][0]['after'] = 'forged-receipt'
    elif name == 'world': frames[0]['native_frame']['world']['nodes']['0']['state'] += 1
    elif name == 'summary': summary['native_events'] += 1
    elif name == 'detector_output': report['prefix_detection']['disagreement'] = not report['prefix_detection']['disagreement']
    elif name == 'forged_cap':
        request['epochs'] += 1
        summary['status'] = 'trace_budget_exceeded'
    elif name not in ('partial_record', 'clean'): raise ValueError(name)
    raw = b''.join(audit.canonical(f) + b'\n' for f in frames)
    if name == 'partial_record': raw = raw[:-1]
    summary['trace_bytes'] = len(raw)
    return request, raw, summary, report


def tamper(environment_path, name, directory):
    suite = load(environment_path)
    case = next(c for c in suite['cases'] if c['family'] == 'driven_pair' and c['initial']['native']['seed'] == 0)
    directory = Path(directory)
    directory.mkdir(parents=True)
    # A positive control is assembled solely from retained records, with no generated epoch.
    clean, raw, summary, report = tamper_inputs(case, 'clean')
    (directory / 'trace.jsonl').write_bytes(raw)
    (directory / 'worker.json').write_bytes(audit.canonical(summary))
    assert reference.verify(clean, directory, report) == candidate.verify(clean, directory, report)
    request, raw, summary, report = tamper_inputs(case, name)
    (directory / 'trace.jsonl').write_bytes(raw)
    (directory / 'worker.json').write_bytes(audit.canonical(summary))
    (directory / 'request.json').write_bytes(audit.canonical(request))
    (directory / 'report.json').write_bytes(audit.canonical(report))
    rejections = {}
    for label, module in (('reference', reference), ('candidate', candidate)):
        try:
            module.verify(request, directory, report)
        except AssertionError as error:
            reason = '' if label == 'reference' and name in ('ledger', 'prepared_order', 'external_receipt') else REASONS[name]
            assert reason in str(error), (label, name, str(error))
            rejections[label] = {'exception': type(error).__name__, 'reason': str(error)}
        else:
            raise AssertionError(f'{label} accepted {name}')
    return {'status': 'pass', 'corruption': name, 'clean_positive_control': 'pass', 'rejections': rejections}


if __name__ == '__main__':
    mode, *args = sys.argv[1:]
    result = {'fixtures': fixtures, 'slot': slot, 'tamper': tamper}[mode](*args)
    print(json.dumps(result, sort_keys=True))
