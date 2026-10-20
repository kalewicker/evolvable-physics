#!/usr/bin/env python3
"""Read-only verification of offline-preflight seals, stage receipts and gate arithmetic."""
import hashlib
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle):
    manifest = load(bundle / 'manifest.json')
    seal = load(bundle / 'seal.json')
    inventory = load(bundle / 'checksums.json')
    assert seal['manifest_sha256'] == sha(bundle / 'manifest.json')
    assert seal['checksums_sha256'] == sha(bundle / 'checksums.json')
    actual = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file()}
    assert actual == set(inventory) | {'checksums.json', 'seal.json'}
    for name, expected in inventory.items():
        path = bundle / name
        assert path.resolve().is_relative_to(bundle.resolve()) and not path.is_symlink()
        assert sha(path) == expected, name
    freeze = load(bundle / 'source/docs/p01e_freeze.json')
    protocol = load(bundle / 'source/docs/p01e_protocol.json')
    assert sha(bundle / 'source/docs/p01e_freeze.json') == manifest['freeze_sha256']
    assert sha(bundle / 'source/docs/p01e_protocol.json') == manifest['protocol_sha256'] == freeze['protocol_sha256']
    assert manifest['source_files'] == freeze['files'] and manifest['inputs'] == freeze['inputs']
    for name, expected in freeze['files'].items(): assert sha(bundle / 'source' / name) == expected
    assert manifest['new_world_runs'] == 0 and not manifest['e01_authorized']
    assert manifest['scientific_status'] == 'untested'
    for name, result in manifest['stages'].items():
        stage = bundle / 'stages' / name
        assert result == load(stage / 'result.json')
        assert result['status'] == 'exited' and result['returncode'] == 0, name
        descriptor = load(stage / 'descriptor.json')
        limits = descriptor['limits']
        assert limits['stdout_bytes'] + limits['stderr_bytes'] == protocol['per_process']['output_bytes']
        assert limits['wall_seconds'] == protocol['per_process']['wall_seconds']
        assert limits['rss_bytes'] == protocol['per_process']['sampled_rss_bytes']
        assert limits['poll_seconds'] == protocol['per_process']['poll_seconds']
        for stream in ('stdout', 'stderr'):
            n = (stage / (stream + '.bin')).stat().st_size
            assert n == result[stream + '_bytes'] == result[stream + '_observed_bytes'] <= limits[stream + '_bytes']
        assert result['child_cpu_seconds'] >= 0
        assert load(stage / 'stdout.bin')['status'] == 'pass'
    fixture = load(bundle / 'stages/fixtures/stdout.bin')
    assert fixture == load(bundle / 'fixture_equivalence.json')
    assert fixture['native_cases'] == 112 and fixture['environment_cases'] == 96 and len(fixture['records']) == 208
    assert fixture['maintenance_arms_within_environment_cases'] == 80
    assert manifest['fixtures_passed']
    assert [row['slot'] for row in manifest['pairs']] == protocol['performance_inputs']['slots']
    cpu = {'reference': 0, 'candidate': 0}
    for index, row in enumerate(manifest['pairs']):
        order = ['reference', 'candidate'] if index % 2 == 0 else ['candidate', 'reference']
        assert row['order'] == order and set(row['results']) == set(order)
        for label in order:
            name = f'slot-{row["slot"]}-{label}'
            result = row['results'][label]
            assert result['guard'] == manifest['stages'][name]
            assert result['receipt'] == load(bundle / 'stages' / name / 'stdout.bin')
            prefix = f'artifacts/p01-001/runs/{row["slot"]}/native/'
            assert result['receipt']['trace_sha256'] == freeze['inputs'][prefix + 'trace.jsonl']
            assert result['receipt']['summary_sha256'] == freeze['inputs'][prefix + 'worker.json']
            if row['slot'] == 177:
                assert result['receipt']['coverage'] == 'censored_prefix' and result['receipt']['full_horizon_ap'] is None
            cpu[label] += result['guard']['child_cpu_seconds']
        assert row['results']['reference']['receipt'] == row['results']['candidate']['receipt']
    assert set(manifest['corruptions']) == set(protocol['corruptions'])
    for name, result in manifest['corruptions'].items():
        assert result == load(bundle / 'stages' / ('tamper-' + name) / 'stdout.bin')
        assert result['corruption'] == name and result['clean_positive_control'] == 'pass'
        assert set(result['rejections']) == {'reference', 'candidate'}
        assert all(r['exception'] == 'AssertionError' for r in result['rejections'].values())
    assert len(manifest['stages']) == 1 + 2 * len(manifest['pairs']) + len(protocol['corruptions'])
    usage = seal['resource_usage']
    caps = protocol['campaign']
    assert usage['artifact_bytes'] == sum(p.stat().st_size for p in bundle.rglob('*') if p.is_file())
    assert not seal['overshoot']
    within = all(usage[k] <= caps[k] for k in ('wall_seconds', 'total_process_cpu_seconds', 'artifact_bytes'))
    rss = max(max(r['peak_rss_bytes'], r['peak_sampled_rss_bytes']) for r in manifest['stages'].values())
    assert rss == usage['peak_observed_rss_bytes']
    within = within and rss <= protocol['gate']['observed_peak_rss_bytes_at_most']
    ratio = cpu['candidate'] / cpu['reference']
    cost = ratio <= protocol['gate']['sum_new_leaf_cpu_at_most_fraction_of_sum_reference']
    assessment = load(bundle / 'assessment.json')
    assert assessment == manifest['assessment']
    assert assessment['leaf_cpu_seconds'] == cpu and assessment['candidate_to_reference_cpu_ratio'] == ratio
    assert assessment['cost_gate_pass'] == cost
    assert manifest['execution_status'] == 'complete'
    assert seal['gate_pass'] == manifest['gate_pass'] == assessment['gate_pass'] == (cost and within)
    return {'schema': 'p01e-independent-receipt-audit-v1', 'integrity_verified': True,
            'manifest_sha256': seal['manifest_sha256'], 'seal_sha256': sha(bundle / 'seal.json'),
            'freeze_sha256': manifest['freeze_sha256'], 'native_cases': 112, 'environment_cases': 96,
            'maintenance_arms': 80, 'paired_inputs': len(manifest['pairs']), 'corruptions': len(manifest['corruptions']),
            'exact_equivalence': True, 'cost_gate_pass': cost, 'resource_gate_pass': within,
            'leaf_cpu_seconds': cpu, 'cpu_ratio': ratio, 'gate_pass': seal['gate_pass'],
            'new_world_runs': 0, 'scientific_status': 'untested', 'e01_authorized': False}


if __name__ == '__main__':
    bundle, destination = map(Path, sys.argv[1:3])
    result = verify(bundle.resolve())
    with destination.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))
