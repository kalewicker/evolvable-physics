#!/usr/bin/env python3
"""Read-only P01g receipt/seal audit, including legitimate negative outcomes."""
import json
import sys
from decimal import Decimal
from pathlib import Path
import audit
import p01q_cell
import p01q_campaign as runner
import check_p01q_registration as registration

if not __debug__:raise RuntimeError('Receipt audit requires assertions')
load,sha=registration.load,registration.sha


def validate_observations(receipt):
    assert receipt['independent_events_pass'] is True
    obs=receipt['prefix_observations']
    counts={key:len(obs[key]) for key in ('births','recycling','visibility','additional_structural_funding',
        'descendant_construction','orphaning','visible_birth_recycle_ids','cleanup_events')}
    counts['ordered_branch']=len({(*r['roles'],r['cleanup_form']) for r in obs['ordered_branch']})
    assert counts['ordered_branch']==obs['ordered_branch_count']
    assert receipt['prefix_counts']==counts
    assert receipt['full_horizon_counts']==(counts if receipt['full_horizon_verified'] else None)
    if not receipt['full_horizon_verified']:assert receipt['full_horizon_ap'] is None
    born={b['node']:b for b in obs['births']};clean={c['event']:c for c in obs['cleanup_events']}
    funds={f['event']:f for f in obs['additional_structural_funding']}
    for f in funds.values():
        assert f['recipient'] in born and born[f['recipient']]['birth_event']==f['birth_event']<f['event']
    for d in obs['descendant_construction']:
        assert d['donor'] in born and born[d['donor']]['birth_event']==d['donor_birth_event']<d['event']
        assert born[d['node']]['birth_event']==d['event'] and born[d['node']]['donor']==d['donor']
    for c in clean.values():
        assert c['form'] in (6,7) and c['donor']!=c['child']
        recycle=c['form']==7
        assert c['child_survives'] is (not recycle) and c['burn']==int(recycle)
        assert c['returned_matter']==(c['child_before'][0]+2 if recycle else 1)
        assert c['returned_activation']==(c['child_before'][1] if recycle else 0)
        assert [c['donor_after'][i]-c['donor_before'][i] for i in (0,1)]==[c['returned_matter'],c['returned_activation']-c['burn']]
    for b in obs['ordered_branch']:
        P,C,G=b['roles'];assert len({P,C,G})==3
        ids=b['events'];assert len(ids)==6 and all(a<c for a,c in zip(ids,ids[1:]))
        assert (born[C]['donor'],born[C]['birth_event'])==(P,ids[0])
        assert (born[G]['donor'],born[G]['birth_event'])==(C,ids[3])
        for e in ids[1:3]:assert (funds[e]['donor'],funds[e]['recipient'],funds[e]['matter'])==(P,C,1)
        assert (clean[ids[4]]['donor'],clean[ids[4]]['child'],clean[ids[4]]['form'])==(C,G,b['cleanup_form'])
        assert (clean[ids[5]]['donor'],clean[ids[5]]['child'],clean[ids[5]]['form'])==(P,C,7)
        assert b['creation_edges']==[clean[ids[5]]['edge'],clean[ids[4]]['edge']]
        assert [p['event'] for p in b['phase_balances']]==ids
        assert all(ids[0]<e<ids[-1] and e not in ids for e in b['intervening_events'])
    return counts


def verify(out):
    manifest=load(out/'manifest.json');seal=load(out/'seal.json');inventory=load(out/'checksums.json')
    assert manifest['schema']=='p01q-campaign-manifest-v1' and seal['schema']=='p01q-campaign-seal-v1'
    assert {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}==set(inventory)|{'checksums.json','seal.json'}
    for name,h in inventory.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(out/name)==h,name
    assert seal['manifest_sha256']==sha(out/'manifest.json') and seal['checksums_sha256']==sha(out/'checksums.json')
    source=out/'source';protocol=load(source/'docs/p01q_protocol.json');registration.validate(protocol)
    freeze=load(source/'docs/p01q_execution_freeze.json');admission=load(source/'docs/p01q_execution_admission.json')
    for key in ('execution_freeze','execution_admission','registration_freeze'):
        assert manifest[key+'_sha256']==sha(source/'docs'/('p01q_'+key+'.json'))
    assert manifest['protocol_sha256']==sha(source/'docs/p01q_protocol.json')==admission['protocol_sha256']
    assert admission['execution_freeze_sha256']==manifest['execution_freeze_sha256']
    assert admission['registration_freeze_sha256']==manifest['registration_freeze_sha256']
    assert admission['schema']=='p01q-execution-admission-v1' and admission['world_execution_admitted'] is True and admission['keyed_evaluation_admitted'] is False
    assert admission['fixed_slots']==128 and admission['admitted_output']=='artifacts/p01q-001'
    assert admission['e01_authorized'] is False
    for name,h in freeze['files'].items():assert sha(source/name)==h,name
    for section in ('files','inputs','prior_public_receipts'):
        for name,h in load(source/'docs/p01q_registration_freeze.json')[section].items():assert sha(source/name)==h,name
    deps=load(out/'dependency_inventory.json')
    assert {r['origin']:r['sha256'] for r in deps.values()}==freeze['dependencies']
    for name,row in deps.items():assert sha(out/'dependencies'/name)==row['sha256']
    for name,row in freeze['binaries'].items():assert sha(out/'bin'/name)==row['sha256']
    assert len(manifest['rows'])==128
    cpu=Decimal(0);checked=0;valid_stages=0
    for plan,row in zip(runner.planned_slots(protocol),manifest['rows']):
        assert all(row[k]==v for k,v in plan.items()),'Fixed row'
        directory=out/'runs'/str(row['slot'])
        names=list(row['stages'])
        # JSON sorted keys need not be launch order; the set must be a prefix.
        assert set(names) in [set(runner.STAGES[:n]) for n in range(4)]
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
            else:assert row['status'] in ('failed','incomplete_budget') and manifest['execution_status'] in ('failed','budget_stopped')
            cpu+=Decimal(str(guard.get('guard_and_reaped_children_cpu_seconds',0)))
            proto=str(source/'docs/p01q_protocol.json');adm=str(source/'docs/p01q_execution_admission.json')
            request=directory/'request.json';native=directory/'native'
            commands={'native':[str(out/'bin/pilot-worker'),'run',str(request)],
                      'rust_report':[str(out/'bin/pilot-report'),str(request),str(native)],
                      'python_audit':[desc['command'][0],str(source/'scripts/p01q_cell.py'),proto,adm,
                                      str(row['slot']),str(request),str(native),str(directory/'rust_report/stdout.bin')]}
            assert desc['command']==commands[name], 'Stage identity'
            if name=='python_audit':assert desc['command'][0] in freeze['tools']
            if name=='native':assert desc['output_names']=={'stdout':'trace.jsonl','stderr':'worker.json'}
        if row.get('law_digest'):
            _,initial=p01q_cell.saved_initial(source,row['slot'],protocol)
            table=audit.digest([{k:v for k,v in r.items() if k!='id'} for r in initial['native']['rules']])
            assert row['law_digest']==table
            if (directory/'request.json').exists():
                assert registration.equal(load(directory/'request.json'),{'schema':'p01-worker-request-v1','initial':initial,
                    'epochs':protocol['epochs'],**protocol['worker_request']})
        if row['status'] in ('complete','censored'):
            assert set(row['stages'])==set(runner.STAGES)
            receipt=load(directory/'python_audit/stdout.bin')
            assert row['receipt_sha256']==sha(directory/'python_audit/stdout.bin')
            assert all(receipt[k]==row[k] for k in ('slot','proposal','initial_state','law_digest','status'))
            assert row['observation']==p01q_cell.compact(receipt)
            for key,path in [('request',directory/'request.json'),('trace',directory/'native/trace.jsonl'),
                             ('summary',directory/'native/worker.json'),('report',directory/'rust_report/stdout.bin')]:
                assert receipt['inputs_sha256'][key]==sha(path)
            validate_observations(receipt)
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
    return {'schema':'p01q-receipt-audit-v1','status':'pass','inventory_files':len(inventory),
            'verified_trajectory_receipts':checked,'valid_stage_receipts':valid_stages,
            'engineering_gate_pass':engineering,'mechanism_gate_pass':seal['mechanism_gate_pass'],
            'continuation_gate_pass':seal['continuation_gate_pass'],'decision':decision,
            'resource_usage':seal['resource_usage'],'seal_sha256':sha(out/'seal.json'),
            'scientific_status':'untested','e01_authorized':False,
            'scope':'inventory/provenance and sealed receipts; no sampler call or transition replay'}

if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]).resolve()),indent=2))
