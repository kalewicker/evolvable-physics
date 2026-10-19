#!/usr/bin/env python3
"""Seal P01b readiness evidence without evaluating any full-P01 slot."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
import audit
import audit_pilot
import pilot
import pilot_reporting

ROOT = pilot.ROOT


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as out: json.dump(value, out, indent=2); out.write('\n')


def request(initial, epochs):
    return {'schema': 'p01-worker-request-v1', 'initial': initial, 'epochs': epochs,
            'max_events': 200000, 'max_trace_bytes': 33554432}


def fixture_bundle(directory, req, frames):
    directory.mkdir(parents=True)
    raw = b''.join(audit.canonical(f)+b'\n' for f in frames)
    (directory/'trace.jsonl').write_bytes(raw)
    final = frames[-1]['state'] if frames else req['initial']
    summary = {'schema': 'p01-worker-result-v1', 'status': 'complete', 'epochs': len(frames),
               'events': final['native']['world']['next_event']-req['initial']['native']['world']['next_event'],
               'native_events': sum(len(f['native_frame']['events']) for f in frames),
               'applicable_candidates': sum(len(f['native_frame']['candidates']) for f in frames),
               'trace_bytes': len(raw), 'step_ns': 0, 'serialize_ns': 0, 'write_ns': 0, 'final_state': final}
    write(directory/'worker.json', summary)
    # Timing zero is an assembler placeholder, not a measured worker invocation.
    write(directory.parent/(directory.name+'-request.json'), req)


def check_report(binary, req_path, directory, dest):
    output = subprocess.run([str(binary), str(req_path), str(directory)], capture_output=True, timeout=30)
    (dest.parent/(dest.name+'.stderr.txt')).write_bytes(output.stderr)
    assert output.returncode == 0, output.stderr.decode()
    dest.write_bytes(output.stdout)
    report = json.loads(output.stdout)
    req = json.loads(req_path.read_text())
    pilot_reporting.verify(req, directory, report)
    return report


def native_wrapper(case):
    native = copy.deepcopy(case['initial'])
    current = {'profile': 'p00c-local-driven-v1', 'channels': [],
               'initial_activation': native['world']['activation_total'], 'injected': 0, 'extracted': 0,
               'native': native}
    initial = copy.deepcopy(current); frames = []
    for frame in case['frames']:
        before = audit.digest(current); prepared = copy.deepcopy(current['native'])
        current['native']['world'] = copy.deepcopy(frame['world'])
        frames.append({'before': before, 'after': audit.digest(current), 'environment_events': [],
                       'prepared': prepared, 'native_frame': frame, 'state': copy.deepcopy(current)})
    return initial, frames


def main():
    out = Path(sys.argv[1]).resolve(); out.mkdir(parents=True, exist_ok=False)
    preflight = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT/'artifacts/p01a-002'
    p00 = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else ROOT/'artifacts/p00g-001'
    manifest = {'schema': 'p01b-readiness-manifest-v1', 'execution_status': 'running',
                'scientific_status': 'untested', 'full_p01_started': False, 'p01_ready': False,
                'source_files': {}, 'generated_runs': [], 'controls': {}, 'gate_pass': False}
    def save(): (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    save()
    try:
        pilot.check_freezes()
        freeze = json.loads((ROOT/'docs/p01b_freeze.json').read_text())
        for name, expected in freeze['files'].items(): assert sha(ROOT/name) == expected, name
        for folder in ('src', 'scripts', 'tests', 'docs'):
            for path in sorted((ROOT/folder).rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts: continue
                rel = path.relative_to(ROOT); dest = out/'source'/rel
                dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, dest)
                manifest['source_files'][str(rel)] = sha(path)
        for name in ('Cargo.toml', 'Cargo.lock'):
            shutil.copyfile(ROOT/name, out/'source'/name); manifest['source_files'][name] = sha(ROOT/name)
        commands = [('tests', ['cargo', 'test', '--locked', '--offline']),
                    ('python_tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_pilot*.py']),
                    ('clippy', ['cargo', 'clippy', '--locked', '--offline', '--all-targets', '--', '-D', 'warnings']),
                    ('format', ['cargo', 'fmt', '--check']),
                    ('build', ['cargo', 'build', '--release', '--locked', '--offline', '--bin', 'pilot-report', '--bin', 'pilot-worker'])]
        for name, command in commands:
            with (out/(name+'.txt')).open('x') as log:
                subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        binary = ROOT/'target/release/pilot-report'; worker = ROOT/'target/release/pilot-worker'
        manifest['binaries'] = {str(p.relative_to(ROOT)): sha(p) for p in (binary, worker)}
        source_receipt = audit_pilot.verify(preflight)
        write(out/'input_preflight_audit.json', source_receipt)
        manifest['preflight_manifest_sha256'] = sha(preflight/'manifest.json')
        source_manifest = json.loads((preflight/'manifest.json').read_text())
        manifest['generated_runs'] = [{'proposal': r['proposal'], 'initial_state': r['initial_state'], 'status': 'pending'}
                                      for r in source_manifest['runs']]
        save()
        reports = out/'reports'; reports.mkdir()
        for row in manifest['generated_runs']:
            row['status'] = 'reporting'; save()
            p, i = row['proposal'], row['initial_state']
            req = preflight/f'runs/{p}-{i}-request.json'; directory = preflight/f'runs/{p}-{i}'
            report = check_report(binary, req, directory, reports/f'{p}-{i}.json')
            assert report['coverage'] == 'complete' and report['observed_epochs'] == 64
            row.update(status='verified', full_horizon_ap=report['full_horizon_ap'],
                       report_sha256=sha(reports/f'{p}-{i}.json'),
                       excluded_large={k: report['prefix_detection'][k]['excluded_large'] for k in ('connected', 'interaction')})
            save()
        labels = Counter(row['full_horizon_ap'] for row in manifest['generated_runs'])
        manifest['generated_label_counts'] = {k: labels[k] for k in ('supported', 'not_supported', 'inconclusive')}
        cases = out/'controls'; cases.mkdir()
        p00_inventory = json.loads((p00/'checksums.json').read_text())
        for name in ('integration', 'detectors'):
            path = p00/name/'suite.json'; assert sha(path) == p00_inventory[f'{name}/suite.json']
        manifest['fixture_input_sha256'] = {name: sha(p00/name/'suite.json') for name in ('integration', 'detectors')}
        suite = json.loads((p00/'integration/suite.json').read_text())
        selected = [c for c in suite['cases'] if c['initial']['native']['seed'] == 0]
        assert len(selected) == 6
        for case in selected:
            name = case['family']; directory = cases/name
            req = request(case['initial'], len(case['epochs'])); fixture_bundle(directory, req, case['epochs'])
            report = check_report(binary, cases/(name+'-request.json'), directory, cases/(name+'-report.json'))
            assert report['prefix_detection'] == case['detection']
            manifest['controls'][name] = report['full_horizon_ap']
        del suite
        detector_suite = json.loads((p00/'detectors/suite.json').read_text())
        case = next(c for c in detector_suite['cases'] if c['family'] == 'attached_inert' and c['initial']['seed'] == 0)
        initial, frames = native_wrapper(case); directory = cases/'attached_inert'
        fixture_bundle(directory, request(initial, len(frames)), frames)
        report = check_report(binary, cases/'attached_inert-request.json', directory, cases/'attached_inert-report.json')
        assert report['prefix_detection'] == case['detection'] and report['full_horizon_ap'] == 'inconclusive'
        manifest['controls']['attached_inert'] = 'inconclusive'
        del detector_suite
        for name in ('event', 'trace', 'complete', 'event_boundary', 'trace_boundary'):
            req_path = preflight/f'controls/{name}-request.json'; directory = preflight/f'controls/{name}'
            report = check_report(binary, req_path, directory, cases/(name+'-report.json'))
            if name != 'complete':
                assert report['coverage'] == 'censored_prefix' and report['full_horizon_ap'] is None
            manifest['controls'][name] = report['coverage']
        initial = json.loads((preflight/'controls/complete-request.json').read_text())['initial']
        for name in ('binding', 'match', 'world'):
            modified = copy.deepcopy(initial)
            if name == 'binding': modified['native']['limits']['max_bindings'] = 0
            elif name == 'match': modified['native']['limits']['max_candidates'] = 0
            else:
                modified['native']['limits']['max_nodes'] = len(modified['native']['world']['nodes'])
                modified['native']['rules'] = [{'id': 0, 'nodes': [{'kind': 1, 'state': None}], 'edges': [], 'absent': [],
                                              'ops': [{'op': 'CreateNode', 'account': 0, 'kind': 1, 'state': 0}]}]
            req_path = cases/(name+'-request.json'); write(req_path, request(modified, 3))
            directory = cases/name; directory.mkdir()
            with (directory/'trace.jsonl').open('xb') as stdout, (directory/'worker.json').open('xb') as stderr:
                subprocess.run([str(worker), 'run', str(req_path)], stdout=stdout, stderr=stderr, check=True, timeout=5)
            report = check_report(binary, req_path, directory, cases/(name+'-report.json'))
            assert report['full_horizon_ap'] is None and report['coverage'] == 'censored_prefix'
            manifest['controls'][name] = report['worker_status']
        # Cross-check the independent next-epoch builder against an actual exported epoch.
        control = preflight/'controls/complete'
        first = json.loads((control/'trace.jsonl').read_bytes().splitlines()[0])
        assert pilot_reporting.next_epoch(initial) == first
        manifest['controls']['independent_next_epoch'] = 'equal'
        rejected = []
        for name in ('missing_summary', 'partial_line', 'forged_complete', 'forged_cap', 'bad_count', 'bad_world'):
            source_name = 'event' if name in ('forged_complete', 'forged_cap') else 'complete'
            directory = cases/('tamper_'+name); directory.mkdir()
            raw = (preflight/f'controls/{source_name}/trace.jsonl').read_bytes()
            summary = json.loads((preflight/f'controls/{source_name}/worker.json').read_text())
            if name == 'partial_line': raw = raw[:-1]
            elif name == 'forged_complete': summary['status'] = 'complete'
            elif name == 'forged_cap': summary['status'] = 'trace_budget_exceeded'
            elif name == 'bad_count': summary['events'] += 1
            elif name == 'bad_world':
                records = [json.loads(line) for line in raw.splitlines()]
                records[0]['state']['injected'] += 1
                raw = b''.join(audit.canonical(f)+b'\n' for f in records)
                summary['trace_bytes'] = len(raw)
            (directory/'trace.jsonl').write_bytes(raw)
            if name != 'missing_summary': write(directory/'worker.json', summary)
            output = subprocess.run([str(binary), str(preflight/f'controls/{source_name}-request.json'), str(directory)], capture_output=True, timeout=5)
            (directory/'rejection.txt').write_bytes(output.stderr)
            assert output.returncode != 0, name
            rejected.append(name)
        report = json.loads((cases/'complete-report.json').read_text())
        report['prefix_detection']['disagreement'] = not report['prefix_detection']['disagreement']
        try:
            pilot_reporting.verify(json.loads((preflight/'controls/complete-request.json').read_text()), control, report)
        except AssertionError: rejected.append('detector_output')
        else: raise AssertionError('Changed detector output accepted')
        manifest['tamper_rejections'] = rejected
        manifest.update(execution_status='complete', gate_pass=True,
                        registration_ready=True, reporting_ready=True, campaign_runner_ready=False)
        receipt = {k: manifest[k] for k in ('schema', 'execution_status', 'scientific_status', 'full_p01_started',
                   'p01_ready', 'gate_pass', 'registration_ready', 'reporting_ready', 'campaign_runner_ready',
                   'preflight_manifest_sha256', 'generated_label_counts', 'controls', 'tamper_rejections')}
        receipt.update(registered_reused_runs=64, generated_epochs_reported=4096,
                       source_freeze_sha256=sha(ROOT/'docs/p01b_freeze.json'), protocol_sha256=sha(ROOT/'docs/p01_protocol.json'))
        write(out/'readiness_audit.json', receipt)
    except Exception as error:
        for row in manifest['generated_runs']:
            if row['status'] == 'pending': row['status'] = 'not_started_infrastructure'
            elif row['status'] == 'reporting': row.update(status='infrastructure_error', error=str(error))
        manifest.update(execution_status='failed', error=str(error))
        raise
    finally:
        save()
        inventory = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*'))
                     if p.is_file() and p != out/'checksums.json'}
        write(out/'checksums.json', inventory)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()
