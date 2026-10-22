#!/usr/bin/env python3
"""Post-seal stage/cost reconciliation only; never evaluates keyed messages."""
import json
import sys
from decimal import Decimal
from pathlib import Path
from p01o_contract import canonical, load, plans, require, sha


def audit(bundle):
    protocol = load(bundle / 'source/docs/p01o_protocol.json')
    manifest = load(bundle / 'manifest.json')
    seal = load(bundle / 'seal.json')
    require(manifest['execution_status'] == 'complete' and len(manifest['rows']) == 128, 'complete campaign')
    stages = []
    for plan, row in zip(plans(protocol), manifest['rows']):
        require(all(row[k] == v for k, v in plan.items()) and row['status'] == 'complete', 'cell identity/status')
        require(set(row['stages']) == {'rust_generation', 'python_generation'}, 'generation stages')
        stages.extend((name, bundle / 'runs' / str(plan['slot']) / name, receipt) for name, receipt in row['stages'].items())
    require(set(manifest['analysis']) == {'static_report', 'independent_audit'}, 'analysis stages')
    stages.extend((name, bundle / 'analysis' / name, receipt) for name, receipt in manifest['analysis'].items())
    require(len(stages) == 258, 'full stage denominator')
    cpu_sum = Decimal(0)
    output_bytes = 0
    peak_rss = 0
    for name, directory, saved in stages:
        receipt = load(directory / 'result.json')
        descriptor = load(directory / 'descriptor.json')
        require(receipt == saved and receipt['status'] == 'exited' and receipt['returncode'] == 0, 'guard receipt identity/status')
        cap = protocol['per_process'][name]
        expected_limits = dict(wall_seconds=cap['wall_seconds'], rss_bytes=cap['sampled_rss_bytes'],
            stdout_bytes=cap['output_bytes'] - 65536, stderr_bytes=65536, poll_seconds=0.01)
        require(descriptor['limits'] == expected_limits, 'unaltered stage limits')
        for stream in ('stdout', 'stderr'):
            size = (directory / (stream + '.bin')).stat().st_size
            require(size == receipt[stream + '_bytes'] <= expected_limits[stream + '_bytes'], 'stream size/ceiling')
            require(receipt[stream + '_observed_bytes'] == size, 'unretained output')
            output_bytes += size
        rss = max(receipt['peak_rss_bytes'], receipt['peak_sampled_rss_bytes'])
        require(rss <= cap['sampled_rss_bytes'] and Decimal(str(receipt['wall_seconds'])) <= cap['wall_seconds'], 'stage RSS/wall ceiling')
        peak_rss = max(peak_rss, rss)
        cpu_sum += Decimal(str(receipt['guard_and_reaped_children_cpu_seconds']))
    usage = seal['resource_usage']
    require(cpu_sum <= Decimal(str(usage['total_process_cpu_seconds'])), 'stage/aggregate CPU reconciliation')
    actual_bytes = sum(p.stat().st_size for p in bundle.rglob('*') if p.is_file())
    require(actual_bytes == usage['artifact_bytes'], 'sealed artifact bytes')
    for key, value in usage.items():
        require(Decimal(str(value)) <= protocol['campaign'][key], 'aggregate ceiling: ' + key)
    require(seal['overshoot'] == [] and seal['engineering_gate_pass'] is True, 'sealed resource gate')
    require(sha(bundle / 'manifest.json') == seal['manifest_sha256'] and
            sha(bundle / 'checksums.json') == seal['checksums_sha256'], 'seal links')
    return dict(schema='p01o-read-only-cost-audit-v1', status='pass', stages_verified=len(stages),
                guarded_stage_cpu_seconds=str(cpu_sum), aggregate_cpu_seconds=str(usage['total_process_cpu_seconds']),
                peak_child_rss_bytes=peak_rss, retained_stage_output_bytes=output_bytes,
                artifact_bytes=actual_bytes, wall_seconds=usage['wall_seconds'],
                keyed_hash_evaluations=0, world_transitions=0,
                seal_sha256=sha(bundle / 'seal.json'), scope='post-seal receipts/costs only; sampled RSS is not an instantaneous bound')


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]))
    with Path(sys.argv[2]).open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(canonical(result))
