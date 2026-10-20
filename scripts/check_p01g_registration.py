#!/usr/bin/env python3
"""Static P01g registration and decision checks. Never constructs a sampled law."""
import hashlib
import json
import sys
from pathlib import Path

if not __debug__:
    raise RuntimeError('Registration review requires assertions')
ROOT = Path(__file__).resolve().parents[1]


def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def planned_slots(protocol):
    return [{'slot':n,'proposal':p,'initial_state':i}
            for n,(p,i) in enumerate((p,i) for p in protocol['proposal_ids'] for i in protocol['initial_state_ids'])]


def validate(p):
    assert p['schema']=='p01g-generator-v2-feasibility-registration-v1'
    assert p['generator']=='p01-generator-v2'
    assert p['proposal_ids']==list(range(4000,4016)), 'Fixed proposal IDs'
    assert p['initial_state_ids']==[0,1,2,3], 'Fixed initial states'
    assert p['law_denominator']==16 and p['trajectory_denominator']==64, 'Denominators'
    assert len(planned_slots(p))==64 and p['epochs']==128, 'Horizon'
    assert p['worker_request']=={'max_events':16384,'max_trace_bytes':4194304}
    assert p['per_process']=={
        'generation':{'wall_seconds':5,'sampled_rss_bytes':134217728,'output_bytes':1048576},
        'native':{'wall_seconds':10,'sampled_rss_bytes':268435456,'output_bytes':4456448},
        'rust_report':{'wall_seconds':20,'sampled_rss_bytes':536870912,'output_bytes':4194304},
        'python_audit':{'wall_seconds':30,'sampled_rss_bytes':536870912,'output_bytes':1048576}}, 'Stage limits'
    c=p['campaign']
    assert {k:c[k] for k in ('wall_seconds','total_process_cpu_seconds','artifact_bytes','metadata_reserve_bytes','poll_seconds')}=={
        'wall_seconds':600,'total_process_cpu_seconds':300,'artifact_bytes':1073741824,
        'metadata_reserve_bytes':33554432,'poll_seconds':0.01}, 'Campaign limits'
    assert all(2*v['wall_seconds']+5<c['total_process_cpu_seconds'] for v in p['per_process'].values())
    assert p['mechanism_gate']['min_distinct_rule_tables_with_visible_birth']==2
    assert p['mechanism_gate']['min_of_those_tables_with_same_trajectory_visible_birth_recycle_loop']==1
    assert set(p['observables'])=={'attached_funded_birth','visible_birth','additional_structural_funding',
                                 'descendant_construction','newborn_recycling','visible_birth_recycle_loop',
                                 'orphaning','full_detector_record'}
    assert len(p['engineering_gate'])==5 and len(p['requirements_before_execution'])==5
    assert p['execution_admitted_now'] is False and p['law_sampling_admitted_now'] is False
    assert p['e01_authorized'] is False and p['scientific_status']=='untested'
    return {'schema':'p01g-static-registration-review-v1','status':'pass','law_cells':16,
            'trajectory_cells':64,'maximum_requested_epochs':8192,
            'hash_keyed_law_constructions':0,'native_transitions':0,'execution_admitted':False,
            'scope':'static protocol consistency and mock-field sampler structure; no sampled-law equivalence or prevalence',
            'scientific_status':'untested'}


def assess_mechanisms(protocol, cases):
    """Decide only from future audited event-extractor records, never dynamics.

    The event extractor must justify every born/visible/recycled ID. Mock records
    test this aggregation here; real extraction and execution are still pending.
    """
    assert len(cases)==64, 'Retain complete denominator'
    visible_tables, loop_tables, per_proposal = set(), set(), {}
    for plan,case in zip(planned_slots(protocol),cases):
        assert all(case[k]==v for k,v in plan.items()), 'Fixed cell identity'
        table=case.get('law_digest')
        if table is not None:
            assert isinstance(table,str) and len(table)==64 and all(c in '0123456789abcdef' for c in table)
            assert per_proposal.setdefault(case['proposal'],table)==table, 'Law identity across initial states'
        if case['status']!='complete' or not case['full_horizon_verified']:
            continue
        assert isinstance(table,str) and len(table)==64 and all(c in '0123456789abcdef' for c in table)
        born=set(case['attached_funded_birth_ids']); visible=set(case['visible_birth_ids']); recycled=set(case['recycled_ids'])
        assert visible<=born and recycled<=born, 'Only actual same-trajectory births count'
        if visible: visible_tables.add(table)
        if visible & recycled: loop_tables.add(table)
    cfg=protocol['mechanism_gate']
    return {'distinct_tables_with_visible_birth':len(visible_tables),
            'distinct_tables_with_same_trajectory_visible_birth_recycle_loop':len(loop_tables),
            'mechanism_gate_pass':len(visible_tables)>=cfg['min_distinct_rule_tables_with_visible_birth']
                and len(loop_tables)>=cfg['min_of_those_tables_with_same_trajectory_visible_birth_recycle_loop']}


def main():
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
    freeze=load(ROOT/'docs/p01g_registration_freeze.json')
    for name,expected in freeze['files'].items(): assert sha(ROOT/name)==expected,name
    prerequisite=load(ROOT/'docs/p01f_reachability_admission.json')
    assert prerequisite['engineering_gate_pass'] and prerequisite['registration_consumed']
    result=validate(load(ROOT/'docs/p01g_protocol.json'))
    result.update(registration_freeze_sha256=sha(ROOT/'docs/p01g_registration_freeze.json'),
                  registration_files=freeze['files'])
    for name,value in [('static_review.json',result),('checksums.json',None)]:
        if value is None:value={'static_review.json':sha(out/'static_review.json')}
        with (out/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
