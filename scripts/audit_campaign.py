#!/usr/bin/env python3
"""Read-only seal/accounting audit. Unsealed evidence never exports accepted endpoints."""
import copy
import json
import sys
from pathlib import Path
import audit
import campaign
import pilot


def verify(out):
    manifest = json.loads((out/'manifest.json').read_text())
    rows = copy.deepcopy(manifest['runs']); p = manifest['protocol']
    expected = campaign.ledger(p)
    assert [(r['slot'],r['proposal'],r['initial_state']) for r in rows] == [(r['slot'],r['proposal'],r['initial_state']) for r in expected]
    if not (out/'seal.json').exists():
        for row in rows:
            row.update(full_horizon_ap=None, coverage='unmeasured',
                       status='not_started_interruption' if row['status']=='pending' else 'unsealed_unmeasured')
        return {'schema':'p01-campaign-audit-v1','integrity_verified':False,'execution_status':'interrupted_unsealed',
                'registered_slots':len(rows),'accepted_endpoints':0,'effective_outcomes':rows,'scientific_status':'untested'}
    seal = json.loads((out/'seal.json').read_text())
    assert seal['manifest_sha256'] == campaign.sha(out/'manifest.json')
    assert seal['checksums_sha256'] == campaign.sha(out/'checksums.json')
    inventory = json.loads((out/'checksums.json').read_text())
    actual = {str(f.relative_to(out)):campaign.sha(f) for f in out.rglob('*')
              if f.is_file() and f not in (out/'manifest.json',out/'checksums.json',out/'seal.json')}
    assert actual == inventory, 'Inventory/hash mismatch'
    for path,digest in manifest['source_files'].items(): assert campaign.sha(out/'source'/path)==digest
    for path,digest in manifest['binaries'].items(): assert campaign.sha(out/'bin'/path)==digest
    assert seal['resource_usage']['artifact_bytes'] == campaign.file_bytes(out)
    trace = sum(f.stat().st_size for f in (out/'runs').rglob('trace.jsonl')) if (out/'runs').exists() else 0
    assert seal['resource_usage'].get('trace_bytes',0)==trace
    child_cpu = 0; endpoints = 0
    for row in rows:
        root = out/'runs'/str(row['slot'])
        for name,result in row['stages'].items():
            assert json.loads((root/name/'result.json').read_text()) == result
            descriptor = json.loads((root/name/'descriptor.json').read_text())
            for stream in ('stdout','stderr'):
                filename = descriptor.get('output_names',{}).get(stream,stream+'.bin')
                assert (root/name/filename).stat().st_size==result[stream+'_bytes']<=descriptor['limits'][stream+'_bytes']
            child_cpu += result.get('child_cpu_seconds',0)
        if row['status'].startswith('verified_'):
            for stage in ('native','rust','audit'): assert row['stages'][stage]['status']=='exited'
            if manifest['mode']=='full': assert row['stages']['generate']['status']=='exited'
            req = json.loads((root/'request.json').read_text())
            assert req['epochs']==p['epochs'] and req['max_events']==p['worker']['max_events'] and req['max_trace_bytes']==p['worker']['max_trace_bytes']
            if manifest['mode']=='full': assert req['initial']==pilot.generate(row['proposal'],row['initial_state'])
            receipt = json.loads((root/'audit/stdout.bin').read_text())
            assert receipt['status']=='pass' and receipt['request_digest']==audit.digest(req)
            assert receipt['trace_sha256']==campaign.sha(root/'native/trace.jsonl')
            assert receipt['report_sha256']==campaign.sha(root/'rust/stdout.bin')
            for key in ('full_horizon_ap','coverage','observed_epochs','events','applicable_candidates','worker_status'): assert row[key]==receipt[key]
            if row['coverage']=='complete':
                assert row['full_horizon_ap'] in ('supported','not_supported','inconclusive')
                assert row['observed_epochs']==p['epochs']; endpoints += 1
            else: assert row['coverage']=='censored_prefix' and row['full_horizon_ap'] is None
        else: assert row['full_horizon_ap'] is None and row['coverage']=='unmeasured'
    if 'total_process_cpu_seconds' in seal['resource_usage']:
        assert seal['resource_usage']['total_process_cpu_seconds']+1e-5>=child_cpu, 'Descendant CPU accounting incomplete'
    assert manifest['summary']==campaign.summarize(rows)
    return {'schema':'p01-campaign-audit-v1','integrity_verified':True,'execution_status':manifest['execution_status'],
            'registered_slots':len(rows),'accepted_endpoints':endpoints,'summary':manifest['summary'],
            'manifest_sha256':campaign.sha(out/'manifest.json'),'seal_sha256':campaign.sha(out/'seal.json'),
            'resource_usage':seal['resource_usage'],'overshoots':seal['overshoots'],'scientific_status':'untested'}


if __name__=='__main__':
    receipt = verify(Path(sys.argv[1]).resolve())
    with Path(sys.argv[2]).open('x') as out: json.dump(receipt,out,indent=2);out.write('\n')
    print(json.dumps({k:receipt[k] for k in ('integrity_verified','registered_slots','accepted_endpoints')},indent=2))
