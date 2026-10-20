#!/usr/bin/env python3
"""One sealed, bounded offline verifier preflight. Never starts a native world."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import audit_campaign
import campaign
from campaign_guard import atomic_json

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024**2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def launch_fits(protocol, usage):
    # One single-thread child plus guard/serial ps descendants. Leave sealing space/time.
    wall = protocol['per_process']['wall_seconds']
    return (usage['wall_seconds'] + wall + 5 <= protocol['campaign']['wall_seconds']
            and usage['total_process_cpu_seconds'] + 2 * wall + 5 <= protocol['campaign']['total_process_cpu_seconds']
            and usage['artifact_bytes'] + 40 * MIB <= protocol['campaign']['artifact_bytes'])


def assess(protocol, pairs, fixtures_passed, corruptions, resource_usage):
    slots = protocol['performance_inputs']['slots']
    complete = (len(pairs) == len(slots) and [r['slot'] for r in pairs] == slots
                and all(set(r['results']) == {'reference', 'candidate'} for r in pairs))
    exact = complete and all(all(r['results'][name]['guard']['status'] == 'exited'
                                and r['results'][name]['receipt']['status'] == 'pass'
                                for name in ('reference', 'candidate'))
                             and r['results']['reference']['receipt'] == r['results']['candidate']['receipt']
                             for r in pairs)
    cpu = {name: sum(r['results'].get(name, {}).get('guard', {}).get('child_cpu_seconds', 0) for r in pairs)
           for name in ('reference', 'candidate')}
    cost = exact and cpu['reference'] > 0 and cpu['candidate'] <= cpu['reference'] * protocol['gate']['sum_new_leaf_cpu_at_most_fraction_of_sum_reference']
    tamper = (set(corruptions) == set(protocol['corruptions'])
              and all(r['status'] == 'pass' and set(r['rejections']) == {'reference', 'candidate'}
                      for r in corruptions.values()))
    resources = (resource_usage['wall_seconds'] <= protocol['campaign']['wall_seconds']
                 and resource_usage['total_process_cpu_seconds'] <= protocol['campaign']['total_process_cpu_seconds']
                 and resource_usage['artifact_bytes'] <= protocol['campaign']['artifact_bytes']
                 and resource_usage['peak_observed_rss_bytes'] <= protocol['gate']['observed_peak_rss_bytes_at_most'])
    return {'complete_fixed_pairs': complete, 'exact_full_records_and_endpoints': exact,
            'fixtures_passed': fixtures_passed, 'all_registered_corruptions_rejected': tamper,
            'leaf_cpu_seconds': cpu, 'candidate_to_reference_cpu_ratio': cpu['candidate'] / cpu['reference'] if cpu['reference'] else None,
            'cost_gate_pass': cost, 'resource_gate_pass': resources,
            'gate_pass': bool(exact and fixtures_passed and tamper and cost and resources)}


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    started, cpu_start = time.monotonic(), campaign.process_cpu()
    protocol = load(ROOT / 'docs/p01e_protocol.json')
    freeze = load(ROOT / 'docs/p01e_freeze.json')
    manifest = {'schema': 'p01e-offline-manifest-v1', 'execution_status': 'preparing',
                'protocol_sha256': sha(ROOT / 'docs/p01e_protocol.json'),
                'freeze_sha256': sha(ROOT / 'docs/p01e_freeze.json'), 'source_files': freeze['files'],
                'inputs': freeze['inputs'], 'pairs': [{'slot': slot, 'results': {}} for slot in protocol['performance_inputs']['slots']],
                'stages': {}, 'corruptions': {}, 'fixtures_passed': False, 'new_world_runs': 0,
                'scientific_status': 'untested', 'e01_authorized': False, 'gate_pass': False}
    def save(): atomic_json(out / 'manifest.json', manifest)
    def usage():
        return {'wall_seconds': time.monotonic() - started,
                'total_process_cpu_seconds': campaign.process_cpu() - cpu_start,
                'artifact_bytes': campaign.file_bytes(out),
                'peak_observed_rss_bytes': max((max(r.get('peak_sampled_rss_bytes', 0), r.get('peak_rss_bytes', 0))
                                                for r in manifest['stages'].values()), default=0)}
    def stage(name, arguments):
        if not launch_fits(protocol, usage()): raise RuntimeError('Campaign launch reservation unavailable')
        directory = out / 'stages' / name
        directory.mkdir(parents=True)
        p = protocol['per_process']
        desc = {'command': [sys.executable, str(out / 'source/scripts/p01e_worker.py'), *map(str, arguments)],
                'cwd': str(out / 'source'), 'directory': str(directory), 'parent_pid': os.getpid(),
                'campaign_deadline': started + protocol['campaign']['wall_seconds'],
                'limits': {'wall_seconds': p['wall_seconds'], 'rss_bytes': p['sampled_rss_bytes'],
                           'poll_seconds': p['poll_seconds'], 'stdout_bytes': p['output_bytes'] - MIB // 16,
                           'stderr_bytes': MIB // 16}}
        atomic_json(directory / 'descriptor.json', desc)
        manifest['stages'][name] = {'status': 'running'}
        save()
        guard = subprocess.Popen([sys.executable, str(out / 'source/scripts/campaign_guard.py'),
                                  str(directory / 'descriptor.json')], start_new_session=True)
        try:
            guard.wait()
        except BaseException:
            guard.terminate()
            try: guard.wait(timeout=3)
            except subprocess.TimeoutExpired: guard.kill(); guard.wait()
            raise
        result = load(directory / 'result.json')
        manifest['stages'][name] = result
        save()
        if guard.returncode != 0 or result['status'] != 'exited':
            raise RuntimeError(f'{name}: {result["status"]}')
        receipt = load(directory / 'stdout.bin')
        assert receipt['status'] == 'pass'
        return {'guard': result, 'receipt': receipt}
    save()
    try:
        campaign.check_freezes()
        for kind in ('files', 'inputs'):
            for name, expected in freeze[kind].items():
                assert sha(ROOT / name) == expected, name
        assert freeze['protocol_sha256'] == manifest['protocol_sha256']
        # Verify original input provenance before any paired process is launched.
        input_audit = audit_campaign.verify(ROOT / 'artifacts/p01-001')
        assert input_audit['integrity_verified']
        atomic_json(out / 'input_campaign_audit.json', input_audit)
        p00 = ROOT / 'artifacts/p00g-001'
        inventory = load(p00 / 'checksums.json')
        for name in ('fixtures/suite.json', 'integration/suite.json'):
            assert sha(p00 / name) == inventory[name]
        for name in freeze['files']:
            dest = out / 'source' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        shutil.copyfile(ROOT / 'docs/p01e_freeze.json', out / 'source/docs/p01e_freeze.json')
        manifest['execution_status'] = 'running'
        save()
        native = p00 / 'fixtures/suite.json'
        environment = p00 / 'integration/suite.json'
        fixtures = stage('fixtures', ['fixtures', native, environment])
        manifest['fixtures_passed'] = True
        atomic_json(out / 'fixture_equivalence.json', fixtures['receipt'])
        save()
        # These same fixed pairs are also the eight P01 correctness inputs; no extra timing runs.
        for index, row in enumerate(manifest['pairs']):
            source = ROOT / 'artifacts/p01-001/runs' / str(row['slot'])
            order = ('reference', 'candidate') if index % 2 == 0 else ('candidate', 'reference')
            row['order'] = list(order)
            for label in order:
                row['results'][label] = stage(f'slot-{row["slot"]}-{label}',
                    ['slot', label, source / 'request.json', source / 'native', source / 'rust/stdout.bin'])
                save()
            assert row['results']['reference']['receipt'] == row['results']['candidate']['receipt']
        for name in protocol['corruptions']:
            result = stage('tamper-' + name, ['tamper', environment, name, out / 'corruptions' / name])
            manifest['corruptions'][name] = result['receipt']
            save()
        manifest['execution_status'] = 'complete'
    except BaseException as error:
        manifest.update(execution_status='failed', error=repr(error))
        raise
    finally:
        manifest['resource_usage_before_seal'] = usage()
        manifest['assessment'] = assess(protocol, manifest['pairs'], manifest['fixtures_passed'],
                                        manifest['corruptions'], manifest['resource_usage_before_seal'])
        manifest['gate_pass'] = manifest['execution_status'] == 'complete' and manifest['assessment']['gate_pass']
        save()
        atomic_json(out / 'assessment.json', manifest['assessment'])
        inventory = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*'))
                     if p.is_file() and p != out / 'checksums.json'}
        atomic_json(out / 'checksums.json', inventory)
        # Account for the final seal itself without modifying manifest/inventory afterward.
        seal = {'schema': 'p01e-offline-seal-v1', 'manifest_sha256': sha(out / 'manifest.json'),
                'checksums_sha256': sha(out / 'checksums.json'), 'resource_usage': usage(),
                'gate_pass': manifest['gate_pass'], 'overshoot': [], 'scientific_status': 'untested'}
        cap = protocol['campaign']
        bytes_without_seal = campaign.file_bytes(out)
        while True:
            before = json.dumps(seal, sort_keys=True, indent=2) + '\n'
            seal['resource_usage']['artifact_bytes'] = bytes_without_seal + len(before.encode())
            seal['overshoot'] = [key for key in ('wall_seconds', 'total_process_cpu_seconds', 'artifact_bytes')
                                 if seal['resource_usage'][key] > cap[key]]
            seal['gate_pass'] = manifest['gate_pass'] and not seal['overshoot']
            if before == json.dumps(seal, sort_keys=True, indent=2) + '\n': break
        atomic_json(out / 'seal.json', seal)
    print(json.dumps({'gate_pass': seal['gate_pass'], 'assessment': manifest['assessment']}, indent=2))


if __name__ == '__main__':
    main()
