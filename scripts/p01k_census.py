#!/usr/bin/env python3
"""One admitted static census. No matcher, transition worker or detector imports."""
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path
from campaign_guard import atomic_json
from p01k_contract import ROOT, canonical, load, plans, require, sha, verify_closure
from p01k_static import table_digest


class ReservationStop(Exception):
    pass


def process_cpu():
    return sum(resource.getrusage(resource.RUSAGE_SELF)[:2]) + sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2])


def file_bytes(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())


def launch_fits(protocol, usage, name):
    stage, cap = protocol['per_process'][name], protocol['campaign']
    return (usage['wall_seconds'] + stage['wall_seconds'] <= cap['wall_seconds'] and
            usage['total_process_cpu_seconds'] + 2 * stage['wall_seconds'] <= cap['total_process_cpu_seconds'] and
            usage['artifact_bytes'] + stage['output_bytes'] + cap['metadata_reserve_bytes'] <= cap['artifact_bytes'])


def stream_limits(protocol, name):
    stage = protocol['per_process'][name]
    return {'wall_seconds': stage['wall_seconds'], 'rss_bytes': stage['sampled_rss_bytes'],
            'stdout_bytes': stage['output_bytes'] - 65536, 'stderr_bytes': 65536,
            'poll_seconds': protocol['campaign']['poll_seconds']}


def manifest_rows(protocol):
    return [dict(row, status='pending', stages={}) for row in plans(protocol)]


def execute_pipeline(bundle, protocol, manifest, stage, save):
    """Injected stage interface permits literal-only integration tests."""
    tables = {}
    for row in manifest['rows']:
        row['status'] = 'generating'
        save()
        generated = []
        for name in ('rust_generation', 'python_generation'):
            directory = stage(name, row)
            generated.append(load(directory / 'stdout.bin'))
        a, b = generated
        require(canonical(a) == canonical(b), 'cross-language mismatch at slot ' + str(row['slot']))
        require(a['schema'] == 'p01k-generated-environment-v1' and
                all(a[k] == row[k] for k in ('slot', 'proposal', 'initial')) and len(a['draws']) == 116,
                'sampled cell schema/identity/count')
        digest = table_digest(a['environment']['native']['rules'])
        law = canonical({'map': a['map'], 'rules': a['environment']['native']['rules']})
        require(tables.setdefault(row['proposal'], law) == law, 'law changed across initials')
        row.update(status='complete', law_digest=digest)
        save()
    stage('static_report', None)
    audited = stage('independent_audit', None)
    receipt = load(audited / 'stdout.bin')
    require(receipt['schema'] == 'p01k-independent-audit-v1' and receipt['status'] == 'pass' and
            receipt['cells'] == 128 and receipt['independent_output_and_static_checks'] is True, 'independent audit failed')


def summarize(protocol, manifest, usage):
    cap = protocol['campaign']
    overshoot = [key for key, value in usage.items() if value > cap[key]]
    rows = manifest['rows']
    generation_ok = all(row['status'] == 'complete' and set(row['stages']) == {'rust_generation', 'python_generation'} and
                        all(s['status'] == 'exited' for s in row['stages'].values()) for row in rows)
    analysis_ok = set(manifest['analysis']) == {'static_report', 'independent_audit'} and all(
        s['status'] == 'exited' for s in manifest['analysis'].values())
    return {'schema': 'p01k-assessment-v1', 'engineering_gate_pass':
            manifest['execution_status'] == 'complete' and len(rows) == 128 and generation_ok and analysis_ok and not overshoot,
            'execution_status': manifest['execution_status'], 'law_denominator': 32, 'environment_denominator': 128,
            'complete_environments': sum(r['status'] == 'complete' for r in rows),
            'distinct_observed_tables': len({r['law_digest'] for r in rows if r.get('law_digest')}),
            'chemistry_continuation_gate': None, 'resource_usage_before_seal': usage, 'overshoot_before_seal': overshoot,
            'world_transitions': 0, 'e01_authorized': False, 'scientific_status': 'untested'}


def main():
    started, cpu_start = time.monotonic(), process_cpu()
    out = Path(sys.argv[1]).resolve()
    protocol, freeze, admission = verify_closure()
    require(out == Path(admission['output_absolute']), 'wrong campaign path')
    # Probe sampled-RSS capability before creating the single-attempt directory.
    probe = subprocess.run(['ps', '-o', 'rss=', '-p', str(os.getpid())], capture_output=True, text=True, check=True)
    require(int(probe.stdout.strip()) > 0, 'RSS unavailable')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'schema': 'p01k-census-manifest-v1', 'execution_status': 'preparing', 'active_stage': None,
                'protocol_sha256': sha(ROOT / 'docs/p01k_protocol.json'),
                'execution_admission_sha256': sha(ROOT / 'docs/p01k_execution_admission.json'),
                'execution_freeze_sha256': sha(ROOT / 'docs/p01k_execution_freeze.json'),
                'rows': manifest_rows(protocol), 'analysis': {}, 'scientific_status': 'untested'}
    def save():
        atomic_json(out / 'manifest.json', manifest)
    def usage():
        return dict(wall_seconds=time.monotonic() - started, total_process_cpu_seconds=process_cpu() - cpu_start,
                    artifact_bytes=file_bytes(out))
    def stage(name, row):
        if not launch_fits(protocol, usage(), name):
            raise ReservationStop(name)
        slot = None if row is None else row['slot']
        directory = out / ('analysis' if row is None else 'runs/' + str(slot)) / name
        directory.mkdir(parents=True)
        if name == 'rust_generation':
            command = [str(out / 'bin/generator-v3'), str(out), str(slot)]
        elif name == 'python_generation':
            command = [sys.executable, str(out / 'source/scripts/generator_v3.py'), str(out), str(slot)]
        else:
            script = 'p01k_static.py' if name == 'static_report' else 'audit_p01k.py'
            command = [sys.executable, str(out / 'source/scripts' / script), str(out)]
        descriptor = dict(command=command, cwd=str(out / 'source'), directory=str(directory), parent_pid=os.getpid(),
                          campaign_deadline=started + protocol['campaign']['wall_seconds'], limits=stream_limits(protocol, name))
        atomic_json(directory / 'descriptor.json', descriptor)
        target = manifest['analysis'] if row is None else row['stages']
        target[name] = {'status': 'running'}
        manifest['active_stage'] = {'name': name, 'slot': slot}
        save()
        guard = subprocess.Popen([sys.executable, str(out / 'source/scripts/campaign_guard.py'), str(directory / 'descriptor.json')], start_new_session=True)
        try:
            guard.wait()
        except BaseException:
            guard.terminate()
            try:
                guard.wait(timeout=3)
            except subprocess.TimeoutExpired:
                guard.kill()
                guard.wait()
            if (directory / 'result.json').exists():
                target[name] = load(directory / 'result.json')
                save()
            raise
        result = load(directory / 'result.json')
        target[name] = result
        save()
        require(guard.returncode == 0 and result['status'] == 'exited', 'guard failed: ' + name)
        require(max(result.get('peak_rss_bytes', 0), result['peak_sampled_rss_bytes']) <= protocol['per_process'][name]['sampled_rss_bytes'], 'reaped/sampled RSS ceiling')
        return directory
    save()  # Every planned cell exists before any source or hash-audit invocation.
    try:
        for name, digest in freeze['files'].items():
            target = out / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
            require(sha(target) == digest, 'snapshot identity')
        for name in ('p01k_execution_freeze.json', 'p01k_execution_admission.json'):
            shutil.copyfile(ROOT / 'docs' / name, out / 'source/docs' / name)
        (out / 'dependencies').mkdir()
        dependency_inventory = {}
        for i, (name, digest) in enumerate(freeze['dependencies'].items()):
            target = out / 'dependencies' / str(i)
            shutil.copyfile(name, target)
            require(sha(target) == digest, 'dependency snapshot')
            dependency_inventory[str(i)] = dict(origin=name, sha256=digest)
        atomic_json(out / 'dependency_inventory.json', dependency_inventory)
        (out / 'bin').mkdir()
        for name, item in freeze['binaries'].items():
            target = out / 'bin' / name
            shutil.copyfile(ROOT / item['path'], target)
            target.chmod(0o755)
            require(sha(target) == item['sha256'], 'binary snapshot')
        manifest['execution_status'] = 'running'
        save()
        execute_pipeline(out, protocol, manifest, stage, save)
        manifest['execution_status'] = 'complete'
    except BaseException as error:
        manifest.update(execution_status='budget_stopped' if isinstance(error, ReservationStop) else 'failed', error=repr(error))
    finally:
        manifest['active_stage'] = None
        for row in manifest['rows']:
            if row['status'] == 'pending':
                row.update(status='unstarted', reason=manifest.get('error', 'preparation stopped'))
            elif row['status'] == 'generating':
                row.update(status='failed' if row['stages'] else 'unstarted', reason=manifest.get('error', 'stage stopped'))
        try:
            verify_closure()
        except BaseException as error:
            manifest.update(execution_status='failed', provenance_error=repr(error))
        save()
        assessment = summarize(protocol, manifest, usage())
        atomic_json(out / 'assessment.json', assessment)
        inventory = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        atomic_json(out / 'checksums.json', inventory)
        seal = dict(schema='p01k-census-seal-v1', manifest_sha256=sha(out / 'manifest.json'),
                    checksums_sha256=sha(out / 'checksums.json'), resource_usage=usage(), overshoot=[],
                    engineering_gate_pass=assessment['engineering_gate_pass'], chemistry_continuation_gate=None,
                    world_transitions=0, scientific_status='untested')
        base = file_bytes(out)
        while True:
            text = json.dumps(seal, sort_keys=True, indent=2) + '\n'
            seal['resource_usage']['artifact_bytes'] = base + len(text.encode())
            seal['overshoot'] = [k for k, v in seal['resource_usage'].items() if v > protocol['campaign'][k]]
            if seal['overshoot']:
                seal['engineering_gate_pass'] = False
            if text == json.dumps(seal, sort_keys=True, indent=2) + '\n':
                break
        atomic_json(out / 'seal.json', seal)
    print(canonical(seal))
    if not seal['engineering_gate_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
