#!/usr/bin/env python3
"""Read-only P01g receipt/seal audit, including legitimate negative outcomes."""
import json
import sys
from decimal import Decimal
from pathlib import Path
import audit
import p01g_cell
import p01g_campaign as runner
import check_p01g_registration as registration

if not __debug__:raise RuntimeError('Receipt audit requires assertions')
load,sha=registration.load,registration.sha


def verify(out):
    manifest=load(out/'manifest.json');seal=load(out/'seal.json');inventory=load(out/'checksums.json')
    assert manifest['schema']=='p01g-campaign-manifest-v1' and seal['schema']=='p01g-campaign-seal-v1'
    assert {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}==set(inventory)|{'checksums.json','seal.json'}
    for name,h in inventory.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(out/name)==h,name
    assert seal['manifest_sha256']==sha(out/'manifest.json') and seal['checksums_sha256']==sha(out/'checksums.json')
    source=out/'source';protocol=load(source/'docs/p01g_protocol.json');registration.validate(protocol)
    freeze=load(source/'docs/p01g_execution_freeze.json');admission=load(source/'docs/p01g_execution_admission.json')
    for key in ('execution_freeze','execution_admission','registration_freeze'):
        assert manifest[key+'_sha256']==sha(source/'docs'/('p01g_'+key+'.json'))
    assert manifest['protocol_sha256']==sha(source/'docs/p01g_protocol.json')==admission['protocol_sha256']
    assert admission['execution_freeze_sha256']==manifest['execution_freeze_sha256']
    assert admission['registration_freeze_sha256']==manifest['registration_freeze_sha256']
    assert admission['schema']=='p01g-execution-admission-v1' and admission['law_sampling_admitted'] is True
    assert admission['fixed_slots']==64 and admission['admitted_output']=='artifacts/p01g-001'
    assert admission['e01_authorized'] is False
    for name,h in freeze['files'].items():assert sha(source/name)==h,name
    for name,h in load(source/'docs/p01g_registration_freeze.json')['files'].items():assert sha(source/name)==h,name
    deps=load(out/'dependency_inventory.json')
    assert {r['origin']:r['sha256'] for r in deps.values()}==freeze['dependencies']
    for name,row in deps.items():assert sha(out/'dependencies'/name)==row['sha256']
    for name,row in freeze['binaries'].items():assert sha(out/'bin'/name)==row['sha256']
    assert len(manifest['rows'])==64
    cpu=Decimal(0);checked=0;valid_stages=0
    for plan,row in zip(registration.planned_slots(protocol),manifest['rows']):
        assert all(row[k]==v for k,v in plan.items()),'Fixed row'
        directory=out/'runs'/str(row['slot'])
        names=list(row['stages'])
        # JSON sorted keys need not be launch order; the set must be a prefix.
        assert set(names) in [set(runner.STAGES[:n]) for n in range(5)]
        for name,guard in row['stages'].items():
            stage=directory/name;desc=load(stage/'descriptor.json')
            assert guard==load(stage/'result.json')
            assert desc['limits']==runner.stream_limits(protocol,name)
            assert desc['cwd']==str(source) and desc['directory']==str(stage)
            if guard['status']=='exited':
                limit=protocol['per_process'][name]
                assert guard['returncode']==0 and guard['wall_seconds']<=limit['wall_seconds']
                assert max(guard.get('peak_rss_bytes',0),guard['peak_sampled_rss_bytes'])<=limit['sampled_rss_bytes']
                for stream in ('stdout','stderr'):
                    filename=desc.get('output_names',{}).get(stream,stream+'.bin')
                    assert (stage/filename).stat().st_size==guard[stream+'_bytes']==guard[stream+'_observed_bytes']
                    assert guard[stream+'_bytes']<=desc['limits'][stream+'_bytes']
                valid_stages+=1
            else:assert row['status']=='failed' and manifest['execution_status']=='failed'
            cpu+=Decimal(str(guard.get('guard_and_reaped_children_cpu_seconds',0)))
            proto=str(source/'docs/p01g_protocol.json');adm=str(source/'docs/p01g_execution_admission.json')
            request=directory/'request.json';native=directory/'native'
            commands={'generation':[str(out/'bin/generator-v2'),proto,adm,str(row['slot'])],
                      'native':[str(out/'bin/pilot-worker'),'run',str(request)],
                      'rust_report':[str(out/'bin/pilot-report'),str(request),str(native)],
                      'python_audit':[desc['command'][0],str(source/'scripts/p01g_cell.py'),proto,adm,
                                      str(row['slot']),str(request),str(native),str(directory/'rust_report/stdout.bin')]}
            assert desc['command']==commands[name], 'Stage identity'
            if name=='python_audit':assert desc['command'][0] in freeze['tools']
            if name=='native':assert desc['output_names']=={'stdout':'trace.jsonl','stderr':'worker.json'}
        if row.get('law_digest'):
            initial=load(directory/'generation/stdout.bin')
            table=audit.digest([{k:v for k,v in r.items() if k!='id'} for r in initial['native']['rules']])
            assert row['law_digest']==table
            if (directory/'request.json').exists():
                assert load(directory/'request.json')=={'schema':'p01-worker-request-v1','initial':initial,
                    'epochs':protocol['epochs'],**protocol['worker_request']}
        if row['status'] in ('complete','censored'):
            assert set(row['stages'])==set(runner.STAGES)
            receipt=load(directory/'python_audit/stdout.bin')
            assert row['receipt_sha256']==sha(directory/'python_audit/stdout.bin')
            assert all(receipt[k]==row[k] for k in ('slot','proposal','initial_state','law_digest','status'))
            assert row['observation']==p01g_cell.compact(receipt)
            for key,path in [('request',directory/'request.json'),('trace',directory/'native/trace.jsonl'),
                             ('summary',directory/'native/worker.json'),('report',directory/'rust_report/stdout.bin')]:
                assert receipt['inputs_sha256'][key]==sha(path)
            observations=receipt['prefix_observations']
            for field,records,idkey in [('attached_funded_birth_ids','births','node'),('visible_birth_ids','visibility','node'),
                                        ('recycled_ids','recycling','node')]:
                assert receipt[field]==sorted(r[idkey] for r in observations[records])==observations[field]
            visible={r['node']:r for r in observations['visibility']}
            births={r['node']:r for r in observations['births']}
            recycled={r['node']:r for r in observations['recycling']}
            for node,proof in visible.items():
                assert node in births and births[node]['birth_sample']<=proof['sample']
                for est in ('connected','interaction'):
                    assert node in proof[est]['members']
                    assert proof[est] in load(directory/'rust_report/stdout.bin')['prefix_detection'][est]['samples'][proof['sample']]
            for node,proof in recycled.items():
                assert node in births and proof['birth_event']==births[node]['birth_event']<proof['deletion_event']
                if node in visible:assert visible[node]['sample']<proof['sample']
            assert observations['visible_birth_recycle_ids']==sorted(set(visible)&set(recycled))
            assert receipt['full_horizon_verified']==(row['status']=='complete')
            if row['status']=='censored':assert receipt['full_horizon_counts'] is None and receipt['full_horizon_ap'] is None
            checked+=1
    size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    assert seal['resource_usage']['artifact_bytes']==size
    expected_overshoot=[k for k,v in seal['resource_usage'].items() if v>protocol['campaign'][k]]
    assert seal['overshoot']==expected_overshoot
    assert cpu<=Decimal(str(seal['resource_usage']['total_process_cpu_seconds']))
    assessment=manifest['assessment'];assert assessment==load(out/'assessment.json')
    assert assessment==runner.summarize(protocol,manifest['rows'],assessment['resource_usage_before_seal'],manifest['execution_status'])
    for k,v in assessment['resource_usage_before_seal'].items():assert v<=seal['resource_usage'][k]
    engineering=assessment['engineering_gate_pass'] and not expected_overshoot
    assert seal['engineering_gate_pass']==engineering and seal['mechanism_gate_pass']==assessment['mechanism_gate_pass']
    assert seal['continuation_gate_pass']==(engineering and assessment['mechanism_gate_pass'])
    decision='engineering_failure_or_incomplete' if not engineering else 'both_pass' if seal['mechanism_gate_pass'] else 'engineering_pass_mechanism_fail'
    assert seal['decision']==decision and manifest['e01_authorized'] is False
    assert manifest['scientific_status']==seal['scientific_status']=='untested'
    return {'schema':'p01g-receipt-audit-v1','status':'pass','inventory_files':len(inventory),
            'verified_trajectory_receipts':checked,'valid_stage_receipts':valid_stages,
            'engineering_gate_pass':engineering,'mechanism_gate_pass':seal['mechanism_gate_pass'],
            'continuation_gate_pass':seal['continuation_gate_pass'],'decision':decision,
            'resource_usage':seal['resource_usage'],'seal_sha256':sha(out/'seal.json'),
            'scientific_status':'untested','e01_authorized':False,
            'scope':'inventory/provenance and sealed receipts; no sampler call or transition replay'}

if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]).resolve()),indent=2))
