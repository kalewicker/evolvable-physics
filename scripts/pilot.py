#!/usr/bin/env python3
"""P01a development supervisor; independent generation and complete epoch replay."""
import copy
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
import audit
import audit_environment

ROOT = Path(__file__).resolve().parents[1]
if not __debug__:
    raise RuntimeError('Audit requires assertions; do not use -O')


def draw(p, initial, field, index, n):
    return int(audit.digest(['p01-generator-v1', p, initial, field, index])[:16], 16) % n


def generate(p, initial):
    assert initial in range(4)
    rules = []
    for i in range(8):
        def d(field, n): return draw(p, 0, field, i, n)
        form = d('form', 8)
        pair = form in (3, 5, 6, 7)
        nodes = []
        for slot in range(2 if pair else 1):
            state = d(f'state{slot}', 4)
            nodes.append({'kind': 1+d(f'kind{slot}', 3), 'state': None if state == 3 else state})
        structural = {'class': 'Structural', 'kind': 0, 'ends': [0, 1]}
        edges = ([{'class': 'Structural' if form >= 6 else 'Contact', 'kind': 0, 'ends': [0, 1]}]
                 if pair else [])
        amount = 1+d('amount', 2)
        ops = [
            [{'op': 'SetState', 'node': 0, 'value': d('value', 3)}],
            [{'op': 'AddState', 'node': 0, 'delta': -1 if d('sign', 2) == 0 else 1}],
            [{'op': 'Burn', 'node': 0, 'amount': amount}],
            [{'op': 'Transfer', 'from': 0, 'to': 1, 'matter': d('matter', 2), 'activation': amount}],
            [{'op': 'CreateNode', 'account': 0, 'kind': 1+d('new_kind', 3), 'state': d('value', 3)}],
            [{'op': 'CreateEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]}],
            [{'op': 'DeleteEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]}],
            [{'op': 'DeleteEdge', 'account': 1, 'kind': 0, 'ends': [0, 1]},
             {'op': 'DeleteNode', 'node': 0, 'recipient': 1}],
        ][form]
        rules.append({'id': i, 'nodes': nodes, 'edges': edges,
                      'absent': [structural] if form == 5 else [], 'ops': ops})
    nodes = {str(i): {'kind': 1+draw(p, initial, 'node_kind', i, 3),
                     'state': draw(p, initial, 'node_state', i, 3), 'matter': 8, 'activation': 8}
             for i in range(8)}
    edges = {str(i): {'class': 'Contact', 'kind': 0, 'ends': [i, (i+1) % 8]} for i in range(8)}
    for i in range(8):
        if draw(p, initial, 'structural', i, 2):
            edges[str(len(edges))] = {'class': 'Structural', 'kind': 0, 'ends': [i, (i+1) % 8]}
    return {'profile': 'p00c-local-driven-v1', 'channels': [], 'initial_activation': 64,
            'injected': 0, 'extracted': 0, 'native': {
                'profile': 'p00a-local-closed-v1', 'seed': draw(p, initial, 'scheduler', 0, 2**64-1),
                'rules': rules, 'limits': {'max_candidates': 4096, 'max_bindings': 65536,
                                         'max_nodes': 128, 'max_edges': 256},
                'world': {'nodes': nodes, 'edges': edges, 'next_node': 8, 'next_edge': len(edges),
                          'epoch': 0, 'dissipated': 0, 'matter_total': 72+len(edges),
                          'activation_total': 64, 'next_event': 0, 'writers': {}}}}


def supervise(command, directory, limits):
    """Single child; kill/reap before returning. wait4 provides this child's exact rusage."""
    if sys.platform not in ('darwin', 'linux'):
        raise RuntimeError('Unsupported RSS units/platform')
    started = time.monotonic()
    reason = None
    peak_sampled = samples = 0
    directory.mkdir()
    with (directory/'trace.jsonl').open('xb') as out, (directory/'worker.json').open('xb') as err:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err, start_new_session=True)
        try:
            while True:
                pid, wait_status, usage = os.wait4(proc.pid, os.WNOHANG)
                if pid:
                    proc.returncode = os.waitstatus_to_exitcode(wait_status)
                    break
                if time.monotonic()-started >= limits['wall_seconds']:
                    reason = 'wall_budget_exceeded'
                else:
                    # Bounded observation: ps can return empty if the child exits during sampling.
                    try:
                        sample = subprocess.run(['ps', '-o', 'rss=', '-p', str(proc.pid)],
                                                capture_output=True, text=True, timeout=0.5)
                        rss = int(sample.stdout.strip())*1024 if sample.stdout.strip() else 0
                    except (ValueError, subprocess.TimeoutExpired) as error:
                        raise RuntimeError('RSS observation failed') from error
                    if sample.returncode not in (0, 1):
                        raise RuntimeError('RSS observation failed')
                    samples += bool(rss)
                    peak_sampled = max(peak_sampled, rss)
                    if rss > limits['rss_bytes']:
                        reason = 'rss_budget_exceeded'
                if reason:
                    os.killpg(proc.pid, signal.SIGKILL)
                    _, wait_status, usage = os.wait4(proc.pid, 0)
                    proc.returncode = os.waitstatus_to_exitcode(wait_status)
                    break
                time.sleep(limits['poll_seconds'])
        finally:
            if proc.returncode is None:
                os.killpg(proc.pid, signal.SIGKILL)
                _, wait_status, _ = os.wait4(proc.pid, 0)
                proc.returncode = os.waitstatus_to_exitcode(wait_status)
    return {'status': reason or ('exited' if proc.returncode == 0 else 'infrastructure_error'),
            'returncode': proc.returncode, 'wall_seconds': time.monotonic()-started,
            'worker_cpu_seconds': usage.ru_utime+usage.ru_stime,
            'peak_rss_bytes': int(usage.ru_maxrss)*(1 if sys.platform == 'darwin' else 1024),
            'peak_sampled_rss_bytes': peak_sampled, 'rss_samples': samples}


def verify_trace(initial, frames, result):
    e = copy.deepcopy(initial)
    native = candidates = 0
    for frame in frames:
        assert frame['before'] == audit.digest(e)
        e, events = audit_environment.apply_environment(e)
        assert frame['environment_events'] == events
        assert frame['prepared'] == e['native']
        native += audit.verify_case({'name': 'pilot', 'initial': e['native'], 'frames': [frame['native_frame']]})
        candidates += len(frame['native_frame']['candidates'])
        e['native']['world'] = frame['native_frame']['world']
        audit_environment.validate(e)
        assert frame['state'] == e and frame['after'] == audit.digest(e)
    assert result['schema'] == 'p01-worker-result-v1'
    assert result['final_state'] == e
    assert result['epochs'] == len(frames)
    assert result['events'] == e['native']['world']['next_event']-initial['native']['world']['next_event']
    assert result['native_events'] == native and result['applicable_candidates'] == candidates
    return {'epochs': len(frames), 'events': result['events'], 'applicable_candidates': candidates}


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2)+'\n')


def read_worker(directory, initial):
    raw = (directory/'trace.jsonl').read_bytes()
    frames = [json.loads(line) for line in raw.splitlines()]
    summary = json.loads((directory/'worker.json').read_bytes())
    assert summary['trace_bytes'] == len(raw)
    verify_trace(initial, frames, summary)
    return summary, frames


def check_freezes():
    for name in ('p00f_freeze.json', 'p00g_freeze.json', 'p01a_freeze.json'):
        for path, expected in json.loads((ROOT/'docs'/name).read_text())['files'].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path


def guard_checks(binary, out, limits):
    controls = out/'controls'
    controls.mkdir()
    initial = generate(2000, 0)
    # Force activity regardless of generator draw, in separate control worlds.
    initial['native']['rules'] = [
        {'id': state, 'nodes': [{'kind': 1, 'state': state}], 'edges': [], 'absent': [],
         'ops': [{'op': 'SetState', 'node': 0, 'value': 1-state}]} for state in (0, 1)]
    for node in initial['native']['world']['nodes'].values():
        node.update(kind=1, state=0)
    outcomes = {}
    for name, events, trace in [('event', 0, 1000000), ('trace', 1000, 0), ('complete', 1000, 1000000)]:
        request = {'schema': 'p01-worker-request-v1', 'initial': initial, 'epochs': 3,
                   'max_events': events, 'max_trace_bytes': trace}
        path = controls/f'{name}-request.json'; write(path, request)
        metrics = supervise([str(binary), 'run', str(path)], controls/name, limits)
        assert metrics['status'] == 'exited'
        summary, frames = read_worker(controls/name, initial)
        assert summary['status'] == {'event': 'event_budget_exceeded', 'trace': 'trace_budget_exceeded', 'complete': 'complete'}[name]
        if name != 'complete':
            assert not frames and summary['final_state'] == initial
        else:
            assert summary['epochs'] == 3 and summary['events'] == 24
        outcomes[name] = summary['status']
    # Exact event and byte equality permits the first epoch, then rejects the next whole epoch.
    full, frames = read_worker(controls/'complete', initial)
    first_bytes = len(audit.canonical(frames[0]))+1
    for name, events, trace in [('event_boundary', 8, 1000000), ('trace_boundary', 1000, first_bytes)]:
        request.update(max_events=events, max_trace_bytes=trace)
        path = controls/f'{name}-request.json'; write(path, request)
        metrics = supervise([str(binary), 'run', str(path)], controls/name, limits)
        assert metrics['status'] == 'exited'
        summary, _ = read_worker(controls/name, initial)
        assert summary['epochs'] == 1 and summary['events'] == 8
        assert summary['final_state'] == frames[0]['state']
        assert summary['status'] == ('event_budget_exceeded' if name.startswith('event') else 'trace_budget_exceeded')
        outcomes[name] = summary['status']
    for name, overrides in [('wall', {'wall_seconds': 0.1}), ('rss', {'rss_bytes': 1})]:
        metrics = supervise([sys.executable, '-c', 'import time; time.sleep(5)'], controls/name, limits | overrides)
        assert metrics['status'] == name+'_budget_exceeded' and metrics['returncode'] == -signal.SIGKILL
        assert metrics['wall_seconds'] < 3
        outcomes[name] = metrics
    metrics = supervise([sys.executable, '-c', 'raise SystemExit(7)'], controls/'failure', limits)
    assert metrics['status'] == 'infrastructure_error' and metrics['returncode'] == 7
    outcomes['infrastructure'] = metrics
    # Tampering rejection on data with actual activity.
    full, frames = read_worker(controls/'complete', initial)
    for name in ('priority', 'state', 'initial', 'summary'):
        bad_frames = copy.deepcopy(frames); bad_initial = copy.deepcopy(initial); bad_full = copy.deepcopy(full)
        if name == 'priority': bad_frames[0]['native_frame']['candidates'][0]['priority'] = '0'*64
        elif name == 'state': bad_frames[0]['state']['injected'] += 1
        elif name == 'initial': bad_initial['native']['world']['nodes']['0']['state'] = 9
        else: bad_full['events'] += 1
        try:
            verify_trace(bad_initial, bad_frames, bad_full)
        except AssertionError:
            outcomes['tamper_'+name] = 'rejected'
        else:
            raise AssertionError('Tamper accepted: '+name)
    return outcomes


def planned_runs(protocol):
    return [{'proposal': p, 'initial_state': i, 'status': 'pending'}
            for p in range(protocol['proposal_ids']['start'],
                           protocol['proposal_ids']['start']+protocol['proposal_ids']['count'])
            for i in protocol['initial_states']]


def mark_infrastructure_failure(runs, error):
    for run in runs:
        if run['status'] == 'pending':
            run['status'] = 'not_started_infrastructure'
        elif run['status'] in ('launching', 'exited'):
            run.update(status='infrastructure_error', error=str(error))


def can_launch(protocol, elapsed, cpu, trace):
    return (elapsed+protocol['supervisor']['wall_seconds'] <= protocol['campaign']['wall_seconds'] and
            cpu+protocol['supervisor']['wall_seconds'] <= protocol['campaign']['worker_cpu_seconds'] and
            trace+protocol['worker']['max_trace_bytes'] <= protocol['campaign']['trace_bytes'])


def main():
    import shutil
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((ROOT/'docs/p01a_protocol.json').read_text())
    manifest = {'schema': 'p01a-manifest-v2', 'execution_status': 'running', 'scientific_status': 'untested',
                'p01_ready': False, 'full_p01_started': False, 'protocol': protocol, 'source_files': {},
                'runs': planned_runs(protocol), 'platform': platform.platform(), 'python': sys.version, 'gate_pass': False}
    def save(): write(out/'manifest.json', manifest)
    save()
    try:
        check_freezes()
        for folder in ('src', 'tests', 'scripts', 'docs'):
            for path in sorted((ROOT/folder).rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts: continue
                rel = path.relative_to(ROOT); dest = out/'source'/rel
                dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, dest)
                manifest['source_files'][str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ('Cargo.toml', 'Cargo.lock'):
            shutil.copyfile(ROOT/name, out/'source'/name)
            manifest['source_files'][name] = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name, cmd in [('python_tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_pilot.py']),
                          ('tests', ['cargo', 'test', '--locked', '--offline']),
                          ('clippy', ['cargo', 'clippy', '--locked', '--offline', '--all-targets', '--', '-D', 'warnings']),
                          ('format', ['cargo', 'fmt', '--check']),
                          ('build', ['cargo', 'build', '--release', '--locked', '--offline', '--bin', 'pilot-worker'])]:
            with (out/f'{name}.txt').open('x') as log:
                subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        binary = ROOT/'target/release/pilot-worker'
        manifest['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        manifest['guard_checks'] = guard_checks(binary, out, protocol['supervisor']); save()
        campaign_start = time.monotonic()
        cpu = trace = 0
        rule_hashes = []
        runs = out/'runs'; runs.mkdir()
        for proposal in range(protocol['proposal_ids']['start'], protocol['proposal_ids']['start']+protocol['proposal_ids']['count']):
            rules = generate(proposal, 0)['native']['rules']
            rule_hashes.append(audit.digest([{k: v for k, v in r.items() if k != 'id'} for r in rules]))
            for initial_id in protocol['initial_states']:
                run = next(r for r in manifest['runs'] if r['proposal'] == proposal and r['initial_state'] == initial_id)
                elapsed = time.monotonic()-campaign_start
                if not can_launch(protocol, elapsed, cpu, trace):
                    run['status'] = 'not_started_campaign_budget'
                else:
                    run['status'] = 'launching'; save()
                    directory = runs/f'{proposal}-{initial_id}'
                    initial = generate(proposal, initial_id)
                    generated = subprocess.run([str(binary), 'generate', str(proposal), str(initial_id)], capture_output=True, timeout=5, check=True)
                    assert json.loads(generated.stdout) == initial, 'Independent generator mismatch'
                    request = {'schema': 'p01-worker-request-v1', 'initial': initial, 'epochs': protocol['epochs'], **protocol['worker']}
                    path = runs/f'{proposal}-{initial_id}-request.json'; write(path, request)
                    run.update(supervise([str(binary), 'run', str(path)], directory, protocol['supervisor']))
                    cpu += run['worker_cpu_seconds']
                    trace += (directory/'trace.jsonl').stat().st_size
                    if run['status'] == 'exited':
                        summary, frames = read_worker(directory, initial)
                        run['status'] = summary['status']
                        run['independent_replay'] = 'pass'
                        for key in ('epochs', 'events', 'native_events', 'applicable_candidates', 'trace_bytes', 'step_ns', 'serialize_ns', 'write_ns'):
                            run[key] = summary[key]
                        assert run['epochs'] <= protocol['epochs'] and run['events'] <= request['max_events']
                        assert run['trace_bytes'] <= request['max_trace_bytes']
                        if run['status'] == 'complete': assert run['epochs'] == protocol['epochs']
                save()
        manifest['campaign_wall_seconds'] = time.monotonic()-campaign_start
        manifest['worker_cpu_seconds'] = cpu
        manifest['trace_bytes'] = trace
        manifest['duplicate_rule_sets'] = len(rule_hashes)-len(set(rule_hashes))
        manifest['completed_runs'] = sum(r['status'] == 'complete' for r in manifest['runs'])
        assert len(manifest['runs']) == protocol['denominator']
        manifest['gate_pass'] = manifest['completed_runs'] == protocol['gate']['completed_runs']
        manifest['execution_status'] = 'complete'
        manifest['cost_scenarios'] = cost_scenarios(manifest)
    except Exception as error:
        mark_infrastructure_failure(manifest['runs'], error)
        manifest.update(execution_status='failed', error=str(error))
        raise
    finally:
        save()
        checksums = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(out.rglob('*')) if p.is_file() and p != out/'checksums.json'}
        write(out/'checksums.json', checksums)
    print(json.dumps({k: manifest[k] for k in ('execution_status', 'gate_pass', 'completed_runs', 'worker_cpu_seconds', 'trace_bytes', 'cost_scenarios')}, indent=2))


def cost_scenarios(manifest):
    import math
    runs = [r for r in manifest['runs'] if r['status'] == 'complete']
    if not runs: return {'status': 'unavailable'}
    factor = 1000/manifest['protocol']['epochs']
    def quantile(key, q):
        values = sorted(r[key] for r in runs)
        return values[max(0, math.ceil(len(values)*q)-1)]
    return {'label': 'linear 512-run by 1000-epoch scenarios; not a tail bound or readiness gate',
            'worker_cpu_hours_mean': sum(r['worker_cpu_seconds'] for r in runs)/len(runs)*factor*512/3600,
            'worker_cpu_hours_p95': quantile('worker_cpu_seconds', .95)*factor*512/3600,
            'worker_cpu_hours_observed_max': quantile('worker_cpu_seconds', 1)*factor*512/3600,
            'trace_bytes_mean': sum(r['trace_bytes'] for r in runs)/len(runs)*factor*512,
            'trace_bytes_observed_max': quantile('trace_bytes', 1)*factor*512,
            'observed_peak_rss_bytes': max(r['peak_rss_bytes'] for r in runs)}


if __name__ == '__main__':
    main()
