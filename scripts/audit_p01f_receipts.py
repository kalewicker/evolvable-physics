#!/usr/bin/env python3
"""Read-only inventory, fixed denominator, admission and resource receipt audit.

Does not execute a native or Python world transition. Transition verification is
the separately guarded, frozen panel audit whose receipt is checked here.
"""
import json
import sys
from decimal import Decimal
from pathlib import Path
import audit
import check_p01f_registration as registration

if not __debug__:
    raise RuntimeError('Receipt audit requires assertions')
load, sha = registration.load, registration.sha


def resources(manifest, seal, protocol, size):
    execution=protocol['future_execution']
    assert seal['resource_usage']['artifact_bytes']==size, 'Artifact size'
    assert not seal['overshoot']
    for key,value in seal['resource_usage'].items():
        assert 0<=value<=execution['campaign'][key], key
        assert manifest['resource_usage_before_seal'][key]<=value, key
    cpu=Decimal(0)
    assert set(manifest['stages'])=={'native','audit'}
    for name,guard in manifest['stages'].items():
        limits=execution['native_panel_process' if name=='native' else 'python_audit_process']
        assert guard['status']=='exited' and guard['returncode']==0
        assert 0<=guard['wall_seconds']<=limits['wall_seconds']
        assert max(guard.get('peak_rss_bytes',0),guard['peak_sampled_rss_bytes'])<=limits['sampled_rss_bytes']
        assert guard['stdout_bytes']==guard['stdout_observed_bytes']<=limits['output_bytes']-65536
        assert guard['stderr_bytes']==guard['stderr_observed_bytes']<=65536
        assert guard['rss_samples']>=0  # A very short child may exit before its first ps sample.
        cpu+=Decimal(str(guard['guard_and_reaped_children_cpu_seconds']))
    assert cpu<=Decimal(str(seal['resource_usage']['total_process_cpu_seconds']))


def verify(out):
    inventory=load(out/'checksums.json'); seal=load(out/'seal.json'); manifest=load(out/'manifest.json')
    actual={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}
    assert actual==set(inventory)|{'checksums.json','seal.json'}, 'Inventory closure'
    for name,expected in inventory.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(out/name)==expected, name
    assert seal['manifest_sha256']==sha(out/'manifest.json')
    assert seal['checksums_sha256']==sha(out/'checksums.json')
    source=out/'source'
    protocol=load(source/'docs/p01f_protocol.json'); registry=load(source/'docs/p01f_witnesses.json')
    registration.validate(protocol,registry)
    freeze=load(source/'docs/p01f_execution_freeze.json')
    admission=load(source/'docs/p01f_execution_admission.json')
    for key,filename in [('execution_freeze','p01f_execution_freeze.json'),
                         ('execution_admission','p01f_execution_admission.json'),
                         ('registration_freeze','p01f_registration_freeze.json')]:
        assert manifest[key+'_sha256']==sha(source/'docs'/filename)
    assert admission['execution_freeze_sha256']==manifest['execution_freeze_sha256']
    assert admission['registration_freeze_sha256']==manifest['registration_freeze_sha256']
    assert admission['native_execution_admitted'] and admission['fixed_slots']==48
    assert admission['admitted_output']=='artifacts/p01f-001'
    assert not admission['law_sampling_admitted'] and not admission['e01_authorized']
    for name,expected in freeze['files'].items(): assert sha(source/name)==expected, name
    for name,expected in load(source/'docs/p01f_registration_freeze.json')['files'].items():
        assert sha(source/name)==expected, name
    assert sha(out/'bin/reachability-witness')==freeze['binary']['sha256']
    deps=load(out/'dependency_inventory.json')
    assert {entry['origin']:entry['sha256'] for entry in deps.values()}==freeze['dependencies']
    for name,entry in deps.items(): assert sha(out/'dependencies'/name)==entry['sha256']
    receipt=load(out/'panel_audit.json')
    assert receipt==load(out/'stages/audit/stdout.bin')
    expected=[(f['id'],s) for f in registry['families'] for s in protocol['scheduler_seeds']]
    assert len(manifest['slots'])==len(receipt['cases'])==48
    rows=[json.loads(line) for line in (out/'stages/native/stdout.bin').read_bytes().splitlines()]
    assert len(rows)==48
    for index,((family,seed),row,slot,check) in enumerate(zip(expected,rows,manifest['slots'],receipt['cases'])):
        for record in (row,slot,check):
            assert (record['slot'],record['family'],record['seed'])==(index,family,seed)
        assert slot['status']==check['status']=='pass'
        # Hash using the same canonical JSON standard, with no transition calls.
        assert check['result_digest']==audit.digest(row['results']['Reference'])
        assert row['results']['Reference']==row['results']['Indexed']
    for name in ('native','audit'):
        directory=out/'stages'/name
        guard=load(directory/'result.json'); desc=load(directory/'descriptor.json')
        assert guard==manifest['stages'][name]
        limits=protocol['future_execution']['native_panel_process' if name=='native' else 'python_audit_process']
        assert desc['limits']=={'wall_seconds':limits['wall_seconds'],'rss_bytes':limits['sampled_rss_bytes'],
                               'poll_seconds':protocol['future_execution']['poll_seconds'],
                               'stdout_bytes':limits['output_bytes']-65536,'stderr_bytes':65536}
        for stream in ('stdout','stderr'):
            assert (directory/(stream+'.bin')).stat().st_size==guard[stream+'_bytes']
        if name=='native':
            assert desc['command']==[str(out/'bin/reachability-witness'),str(source/'docs/p01f_protocol.json'),str(source/'docs/p01f_witnesses.json')]
        else:
            assert desc['command'][1:]==[str(source/'scripts/p01f_audit.py'),str(source/'docs/p01f_protocol.json'),
                                       str(source/'docs/p01f_witnesses.json'),str(out/'stages/native/stdout.bin')]
            assert desc['command'][0] in freeze['tools']
        assert desc['cwd']==str(source) and desc['parent_pid']>0
    assert receipt['status']=='pass' and receipt['matcher_case_passes']==96
    assert set(receipt['per_matcher'])=={'Reference','Indexed'}
    assert all(t==protocol['expected_per_matcher'] for t in receipt['per_matcher'].values())
    resources(manifest,seal,protocol,sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    assert manifest['execution_status']=='complete' and manifest['gate_pass'] and seal['gate_pass']
    assert manifest['scientific_status']==seal['scientific_status']==receipt['scientific_status']=='untested'
    assert not manifest['law_sampling_admitted'] and not receipt['law_sampling_admitted']
    return {'schema':'p01f-receipt-audit-v1','status':'pass','fixed_cases':48,'matcher_case_passes':96,
            'inventory_files':len(inventory),'source_files':len(freeze['files']),
            'dependency_files':len(deps),'per_matcher':receipt['per_matcher'],
            'resource_usage':seal['resource_usage'],'seal_sha256':sha(out/'seal.json'),
            'law_sampling_admitted':False,'scientific_status':'untested',
            'accounting_boundary':'sealed usage includes inventory and seal bytes; excludes later receipt audit/publication'}

if __name__=='__main__': print(json.dumps(verify(Path(sys.argv[1]).resolve()),indent=2))
