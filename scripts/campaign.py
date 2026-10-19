#!/usr/bin/env python3
"""P01 sealed sequential campaign; frozen P00/P01a/P01b code remains unchanged."""
import copy
import hashlib
import json
import math
import os
import resource
import shutil
import signal
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
import audit
import pilot
from campaign_guard import atomic_json

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024**2
class PreparationBudget(Exception):
    pass


CAPS = {'wall_budget_exceeded', 'rss_budget_exceeded', 'stdout_budget_exceeded', 'stderr_budget_exceeded',
        'campaign_wall_budget_exceeded'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def file_bytes(root): return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())


def process_cpu():
    return sum(resource.getrusage(resource.RUSAGE_SELF)[:2])+sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2])


def check_freezes():
    pilot.check_freezes()
    for name in ('p01b_freeze.json', 'p01c_freeze.json'):
        for path, expected in json.loads((ROOT/'docs'/name).read_text())['files'].items():
            if sha(ROOT/path) != expected: raise RuntimeError('Frozen source mismatch: '+path)


def ledger(protocol):
    rows = pilot.planned_runs(protocol)
    assert len(rows) == protocol['denominator']
    for i, row in enumerate(rows):
        row.update(slot=i, status='pending', stages={}, full_horizon_ap=None, coverage='unmeasured')
    return rows


def reservations(protocol, stage='slot'):
    g = .25*MIB + .0625*MIB
    w = protocol['worker']['max_trace_bytes']+.25*MIB
    r = protocol['rust_analysis']['max_output_bytes']+.0625*MIB
    a = protocol['python_audit']['max_output_bytes']+.0625*MIB
    walls = [protocol['supervisor']['wall_seconds'], protocol['rust_analysis']['wall_seconds'], protocol['python_audit']['wall_seconds']]
    if stage == 'slot': return sum(walls), int(protocol['worker']['max_trace_bytes']+r+a+3*MIB), protocol['worker']['max_trace_bytes']
    if stage == 'rust': return sum(walls[1:]), int(r+a+.25*MIB), 0
    if stage == 'audit': return walls[2], int(a+.125*MIB), 0
    if stage == 'native': return walls[0], int(w+r+a+MIB), protocol['worker']['max_trace_bytes']
    raise ValueError(stage)


def can_launch(protocol, usage, stage='slot'):
    seconds, artifacts, trace = reservations(protocol, stage)
    cap = protocol['campaign']
    return (usage['wall_seconds']+seconds <= cap['wall_seconds'] and
            usage['total_process_cpu_seconds']+seconds <= cap['total_process_cpu_seconds'] and
            usage['trace_bytes']+trace <= cap['trace_bytes'] and
            usage['artifact_bytes']+artifacts+cap['metadata_reserve_bytes'] <= cap['total_artifact_bytes'])


def stage_limits(protocol, name):
    if name == 'generate': return dict(protocol['supervisor'], stdout_bytes=MIB//4, stderr_bytes=MIB//16)
    if name == 'native': return dict(protocol['supervisor'], stdout_bytes=protocol['worker']['max_trace_bytes'], stderr_bytes=MIB//4)
    key = 'rust_analysis' if name == 'rust' else 'python_audit'
    p = protocol[key]
    return {'wall_seconds': p['wall_seconds'], 'rss_bytes': p['rss_bytes'],
            'poll_seconds': protocol['supervisor']['poll_seconds'], 'stdout_bytes': p['max_output_bytes'], 'stderr_bytes': MIB//16}


def source_snapshot(out, cap, metadata_reserve):
    files = [ROOT/'Cargo.toml', ROOT/'Cargo.lock']
    for folder in ('src', 'scripts', 'tests', 'docs'):
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    required = sum(p.stat().st_size for p in files)+sum((ROOT/'target/release'/n).stat().st_size for n in ('pilot-worker','pilot-report'))
    if file_bytes(out)+required+metadata_reserve > cap: raise PreparationBudget('Source snapshot does not fit')
    hashes = {}
    for path in sorted(files):
        if path.is_symlink(): raise RuntimeError('Source symlink rejected')
        rel = path.relative_to(ROOT); dest = out/'source'/rel
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, dest); hashes[str(rel)] = sha(dest)
    binaries = {}
    (out/'bin').mkdir()
    for name in ('pilot-worker', 'pilot-report'):
        path = ROOT/'target/release'/name; dest = out/'bin'/name
        shutil.copyfile(path, dest); dest.chmod(0o755); binaries[name] = sha(dest)
    return hashes, binaries


def summarize(rows):
    labels = Counter(r['full_horizon_ap'] or ('censored' if r['coverage'] == 'censored_prefix' else 'unmeasured') for r in rows)
    started = [r for r in rows if r['stages']]
    costs = {}
    for key in ('wall_seconds', 'child_cpu_seconds'):
        values = sorted(sum(s.get(key, 0) for s in r['stages'].values()) for r in started)
        costs[key] = ({'mean': statistics.mean(values), 'median': statistics.median(values),
                       'p95_nearest_rank': values[math.ceil(.95*len(values))-1], 'maximum': values[-1]} if values else None)
    laws = {}
    for row in rows:
        laws.setdefault(str(row['proposal']), []).append({'initial_state': row['initial_state'],
            'status': row['status'], 'full_horizon_ap': row['full_horizon_ap'], 'coverage': row['coverage']})
    return {'registered_slots': len(rows), 'started_slots': len(started), 'status_counts': dict(Counter(r['status'] for r in rows)),
            'endpoint_counts_all_slots': dict(labels),
            'complete_case_endpoint_counts': dict(Counter(r['full_horizon_ap'] for r in rows if r['status']=='verified_complete')),
            'duplicate_laws_among_generated_proposals': len({r['proposal'] for r in rows if 'rules_digest' in r})-len({r['rules_digest'] for r in rows if 'rules_digest' in r}), 'costs_started_including_censored_lower_observations': costs,
            'laws': laws, 'laws_with_verified_supported_state': sum(any(s['full_horizon_ap']=='supported' for s in states) for states in laws.values())}


def run_campaign(out, protocol, mode='full', controls=None, faults=None):
    if mode not in ('full', 'engineering_control'): raise ValueError(mode)
    if mode == 'full' and (controls is not None or faults): raise RuntimeError('Full campaign overrides forbidden')
    faults = faults or {}; out = out.resolve(); out.mkdir(parents=True, exist_ok=False)
    rows = ledger(protocol)
    manifest = {'schema': 'p01-campaign-manifest-v1', 'mode': mode, 'execution_status': 'preparing',
        'scientific_status': 'untested', 'full_p01_started': mode == 'full', 'protocol': protocol,
        'runs': rows, 'source_files': {}, 'binaries': {}, 'e01_authorized': False}
    atomic_json(out/'manifest.json', manifest)
    started = None; cpu_start = None; trace = 0; stop_reason = None
    def save(): atomic_json(out/'manifest.json', manifest)
    def usage():
        return {'wall_seconds': time.monotonic()-started, 'total_process_cpu_seconds': process_cpu()-cpu_start,
                'trace_bytes': sum(p.stat().st_size for p in (out/'runs').rglob('trace.jsonl')) if (out/'runs').exists() else 0,
                'artifact_bytes': file_bytes(out)}
    def stage(row, name, command, remaining_wall=None):
        directory = out/'runs'/str(row['slot'])/name; directory.mkdir(parents=True)
        limits = stage_limits(protocol, name)
        if remaining_wall is not None: limits['wall_seconds'] = max(.001, remaining_wall)
        fault = faults.get((row['slot'], name))
        if fault == 'crash_parent': command = [sys.executable, '-c', 'import time; time.sleep(10)']
        elif fault == 'fail': command = [sys.executable, '-c', 'raise SystemExit(7)']
        elif fault == 'sleep': command = [sys.executable, '-c', 'import time; time.sleep(10)']
        elif fault == 'stdout': command = [sys.executable, '-c', "import os; os.write(1,b'x'*2000000)"]; limits['stdout_bytes'] = 1024
        elif fault == 'stderr': command = [sys.executable, '-c', "import os; os.write(2,b'x'*2000000)"]; limits['stderr_bytes'] = 1024
        elif fault == 'bad_report': command = [sys.executable, '-c', "print('{}')"]
        elif fault == 'bad_summary': command = [sys.executable, '-c', "print('garbage')"]
        elif fault == 'rss': command = [sys.executable, '-c', 'import time; time.sleep(10)']; limits['rss_bytes'] = 1
        desc = {'command': list(map(str, command)), 'cwd': str(out/'source'), 'directory': str(directory),
                'output_names': {'stdout':'trace.jsonl','stderr':'worker.json'} if name == 'native' else {},
                'parent_pid': os.getpid(), 'campaign_deadline': started+protocol['campaign']['wall_seconds'], 'limits': limits}
        atomic_json(directory/'descriptor.json', desc)
        row['stages'][name] = {'status': 'running'}; save()
        guard = subprocess.Popen([sys.executable, str(out/'source/scripts/campaign_guard.py'), str(directory/'descriptor.json')], start_new_session=True)
        try:
            if fault == 'crash_parent':
                # Control-only fault: guard must detect this parent's loss and reap its own child.
                time.sleep(.15); os._exit(91)
            guard.wait()
        except BaseException:
            guard.terminate()
            try: guard.wait(timeout=3)
            except subprocess.TimeoutExpired: guard.kill(); guard.wait()
            raise
        result_path = directory/'result.json'
        if guard.returncode != 0 or not result_path.exists(): raise RuntimeError('Guard failed without receipt')
        result = json.loads(result_path.read_text()); row['stages'][name] = result; save()
        return result, directory
    try:
        check_freezes()
        if mode == 'full':
            frozen_protocol = json.loads((ROOT/'docs/p01_protocol.json').read_text())
            if protocol != frozen_protocol: raise RuntimeError('Unregistered full protocol')
            status = json.loads((ROOT/'docs/status.json').read_text())
            readiness_path = ROOT/status['campaign_readiness_receipt']
            if not readiness_path.resolve().is_relative_to((ROOT/'docs/evidence').resolve()): raise RuntimeError('Invalid readiness receipt path')
            published = json.loads((ROOT/'docs/evidence/publication_inventory.json').read_text())
            anchors = {e['file']:e['sha256'] for e in published['files']}
            if sha(readiness_path) != anchors[str(readiness_path.relative_to(ROOT))]: raise RuntimeError('Readiness receipt hash mismatch')
            readiness = json.loads(readiness_path.read_text())
            if not readiness.get('p01_ready') or readiness['source_freeze_sha256'] != sha(ROOT/'docs/p01c_freeze.json'):
                raise RuntimeError('Current runner readiness receipt required')
        started = time.monotonic(); cpu_start = process_cpu()
        manifest['source_files'], manifest['binaries'] = source_snapshot(out,protocol['campaign']['total_artifact_bytes'],protocol['campaign']['metadata_reserve_bytes'])
        manifest['execution_status'] = 'running'; save()
        for row in rows:
            if not can_launch(protocol, usage()):
                stop_reason = 'campaign_budget'; break
            if shutil.disk_usage(out).free < reservations(protocol)[1]+protocol['campaign']['metadata_reserve_bytes']:
                stop_reason = 'disk_capacity'; break
            row['status'] = 'running'; save()
            directory = out/'runs'/str(row['slot']); directory.mkdir(parents=True, exist_ok=True)
            native_start = time.monotonic()
            if controls is None:
                result, gen_dir = stage(row, 'generate', [out/'bin/pilot-worker', 'generate', row['proposal'], row['initial_state']])
                if result['status'] != 'exited':
                    row['status'] = 'generate_'+result['status']
                    if result['status'] not in CAPS: stop_reason='infrastructure'
                    save()
                    if stop_reason: break
                    continue
                initial = json.loads((gen_dir/'stdout.bin').read_bytes())
                if initial != pilot.generate(row['proposal'], row['initial_state']): raise RuntimeError('Independent generator mismatch')
            else: initial = copy.deepcopy(controls[row['slot']])
            row['rules_digest'] = audit.digest([{k:v for k,v in rule.items() if k!='id'} for rule in initial['native']['rules']])
            request = {'schema': 'p01-worker-request-v1', 'initial': initial, 'epochs': protocol['epochs'], **protocol['worker']}
            request_path = directory/'request.json'; atomic_json(request_path, request)
            if request_path.stat().st_size > MIB//4: raise RuntimeError('Request allowance exceeded')
            if not can_launch(protocol, usage(), 'native'):
                row['status'] = 'campaign_budget_before_native'; stop_reason = 'campaign_budget'; break
            remaining = protocol['supervisor']['wall_seconds']-(time.monotonic()-native_start)
            result, native_dir = stage(row, 'native', [out/'bin/pilot-worker', 'run', request_path], remaining)
            if result['status'] != 'exited':
                row['status'] = 'native_'+result['status']
                if result['status'] not in CAPS: stop_reason='infrastructure'
                save()
                if stop_reason: break
                continue
            if not can_launch(protocol, usage(), 'rust'):
                row['status']='campaign_budget_before_rust'; stop_reason='campaign_budget'; break
            result, rust_dir = stage(row, 'rust', [out/'bin/pilot-report', request_path, native_dir])
            if result['status'] != 'exited':
                row['status']='rust_'+result['status']
                if result['status'] not in CAPS: stop_reason='infrastructure'
                save()
                if stop_reason: break
                continue
            if not can_launch(protocol, usage(), 'audit'):
                row['status']='campaign_budget_before_audit'; stop_reason='campaign_budget'; break
            command = [sys.executable, out/'source/scripts/campaign_audit_child.py', request_path, native_dir, rust_dir/'stdout.bin']
            if controls is None: command += [str(row['proposal']), str(row['initial_state'])]
            result, audit_dir = stage(row, 'audit', command)
            if result['status'] != 'exited':
                row['status']='audit_'+result['status']
                if result['status'] not in CAPS: stop_reason='infrastructure'
                save()
                if stop_reason: break
                continue
            receipt = json.loads((audit_dir/'stdout.bin').read_bytes())
            if (receipt['status'] != 'pass' or receipt['request_digest'] != audit.digest(request)
                    or receipt['report_sha256'] != sha(rust_dir/'stdout.bin')
                    or receipt['trace_sha256'] != sha(native_dir/'trace.jsonl')): raise RuntimeError('Audit binding mismatch')
            row.update(status='verified_complete' if receipt['coverage']=='complete' else 'verified_censored',
                       coverage=receipt['coverage'], full_horizon_ap=receipt['full_horizon_ap'],
                       observed_epochs=receipt['observed_epochs'], events=receipt['events'],
                       applicable_candidates=receipt['applicable_candidates'], worker_status=receipt['worker_status'])
            save()
        manifest['execution_status'] = 'complete' if stop_reason != 'infrastructure' else 'failed'
    except PreparationBudget as error:
        manifest.update(execution_status='complete', preparation_stop=str(error)); stop_reason='campaign_budget'
    except BaseException as error:
        manifest.update(execution_status='failed', error=repr(error)); stop_reason='infrastructure'
        if isinstance(error, (KeyboardInterrupt, SystemExit)): stop_reason='interruption'
    finally:
        for row in rows:
            if row['status']=='pending': row['status']='not_started_'+(stop_reason or 'infrastructure')
            elif row['status']=='running': row['status']='interrupted_unmeasured'
        manifest['stop_reason'] = stop_reason
        manifest['summary'] = summarize(rows)
        if started is not None: manifest['resource_usage_before_sealing'] = usage()
        save()
        # Hash large files first; charge that work before the final resource observation.
        inventory = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*'))
                     if p.is_file() and p.name not in ('manifest.json.pending',) and p != out/'manifest.json'}
        atomic_json(out/'checksums.json', inventory)
        final = usage() if started is not None else {'artifact_bytes':file_bytes(out)}
        cap = protocol['campaign']; over = {key:final.get(key,0)>cap[key] for key in ('wall_seconds','total_process_cpu_seconds','trace_bytes')}
        seal = {'schema':'p01-campaign-seal-v1', 'manifest_sha256':sha(out/'manifest.json'),
                'checksums_sha256':sha(out/'checksums.json'), 'resource_usage':final, 'overshoots':over,
                'measurement_boundary':'after inventory and manifest fsync; final seal publication overhead excluded'}
        # Include the seal's own retained byte size in final artifact accounting.
        for _ in range(5):
            encoded = (json.dumps(seal,sort_keys=True,indent=2)+'\n').encode()
            seal['resource_usage']['artifact_bytes']=file_bytes(out)+len(encoded)
            seal['overshoots']['total_artifact_bytes']=seal['resource_usage']['artifact_bytes']>cap['total_artifact_bytes']
        atomic_json(out/'seal.json', seal)
    return manifest


if __name__ == '__main__':
    p = json.loads((ROOT/'docs/p01_protocol.json').read_text())
    result = run_campaign(Path(sys.argv[1]), p)
    print(json.dumps({'execution_status':result['execution_status'],'stop_reason':result['stop_reason'],'summary':result['summary']},indent=2))
    if result['execution_status']=='failed': raise SystemExit(1)
