#!/usr/bin/env python3
"""Read-only source/trace/report diagnosis. Never executes a transition or changes an AP label."""
import ast
import collections
import hashlib
import json
import sys
from pathlib import Path
import audit
import audit_campaign
import campaign


def write(path,value):
    with path.open('x') as out:json.dump(value,out,indent=2);out.write('\n')


def rule_form(rule):
    ops=rule['ops'];tags=[op['op'] for op in ops]
    forms={('SetState',):0,('AddState',):1,('Burn',):2,('Transfer',):3,('CreateNode',):4,
           ('CreateEdge',):5,('DeleteEdge',):6,('DeleteEdge','DeleteNode'):7}
    form=forms[tuple(tags)];pair=form in (3,5,6,7)
    assert len(rule['nodes'])==(2 if pair else 1)
    assert all(set(n)=={'kind','state'} and n['kind'] in (1,2,3) and n['state'] in (None,0,1,2) for n in rule['nodes'])
    structural={'class':'Structural','kind':0,'ends':[0,1]}
    assert rule['edges']==([{'class':'Structural' if form>=6 else 'Contact','kind':0,'ends':[0,1]}] if pair else [])
    assert rule['absent']==([structural] if form==5 else [])
    a=ops[0]
    if form==0:assert a=={'op':'SetState','node':0,'value':a['value']} and a['value'] in (0,1,2)
    elif form==1:assert a=={'op':'AddState','node':0,'delta':a['delta']} and a['delta'] in (-1,1)
    elif form==2:assert a=={'op':'Burn','node':0,'amount':a['amount']} and a['amount'] in (1,2)
    elif form==3:assert a=={'op':'Transfer','from':0,'to':1,'matter':a['matter'],'activation':a['activation']} and a['matter'] in (0,1) and a['activation'] in (1,2)
    elif form==4:assert a=={'op':'CreateNode','account':0,'kind':a['kind'],'state':a['state']} and a['kind'] in (1,2,3) and a['state'] in (0,1,2)
    elif form in (5,6):assert a=={'op':tags[0],'account':0,'kind':0,'ends':[0,1]}
    else:assert ops==[{'op':'DeleteEdge','account':1,'kind':0,'ends':[0,1]},{'op':'DeleteNode','node':0,'recipient':1}]
    return form


def world_scope(initial,world,previous):
    audit.validate(world)
    original=set(initial['nodes']);assert original=={str(i) for i in range(8)}
    contacts={i:e for i,e in initial['edges'].items() if e['class']=='Contact'}
    assert contacts=={str(i):{'class':'Contact','kind':0,'ends':[i,(i+1)%8]} for i in range(8)}
    assert {i:e for i,e in world['edges'].items() if e['class']=='Contact'}==contacts
    assert set(previous['nodes'])<=set(world['nodes']), 'Node deletion observed'
    assert set(world['nodes'])=={str(i) for i in range(world['next_node'])}
    assert world['next_node']==len(world['nodes'])
    assert len(world['nodes'])<=initial['matter_total']-8, 'Contact/matter bound'
    pairs={tuple(e['ends']) for e in contacts.values()}
    for e in world['edges'].values():
        if e['class']=='Structural':assert e['kind']==0 and tuple(e['ends']) in pairs, 'Newborn/novel structural route'
    for ident,node in world['nodes'].items():
        if ident not in original:assert node['matter']==node['activation']==0, 'Newborn resource gain'
        if ident in previous['nodes']:assert node['kind']==previous['nodes'][ident]['kind']
    assert world['matter_total']==initial['matter_total'] and world['activation_total']==initial['activation_total']
    return len(set(world['nodes'])-set(previous['nodes']))


def failed_gates(track,p):
    duration=track['last']-track['first']
    failed=[]
    if track['ambiguous']:failed.append('ambiguous')
    if duration<p['min_duration']:failed.append('duration')
    if track['observations']!=duration+1:failed.append('continuity')
    if track['similar_observations']!=track['observations']:failed.append('feature_similarity')
    if track['active_epochs']*p['min_active_epoch_denominator']<duration*p['min_active_epoch_numerator']:failed.append('active_fraction')
    if not set(track['all_members'])<=set(track['active_members']):failed.append('inactive_members')
    assert track['active_persistence']==(not failed), 'Stored track gate mismatch'
    return failed


def report_diagnosis(report,p):
    d=report['prefix_detection'];summary={};supported={}
    for name in ('connected','interaction'):
        estimator=d[name];fail=collections.Counter();ap=[]
        for index,track in enumerate(estimator['tracks']):
            assert all(i<8 for i in track['all_members']), 'Newborn detector track'
            assert track['births']==track['deaths']==0
            reasons=failed_gates(track,p);fail.update(reasons)
            if not reasons:ap.append({'index':index,**track})
        for proposals in estimator['samples']:
            for proposal in proposals:assert all(i<8 for i in proposal['members']), 'Newborn proposal'
        assert estimator['supported']==bool(ap)
        summary[name]={'tracks':len(estimator['tracks']),'supported_tracks':len(ap),
                       'failed_gate_counts_overlapping':dict(fail),'excluded_large_component_observations':estimator['excluded_large'],
                       'empty_samples':sum(not sample for sample in estimator['samples']),
                       'proposal_observations':sum(len(sample) for sample in estimator['samples']),
                       'maximum_track_duration':max((t['last']-t['first'] for t in estimator['tracks']),default=0)}
        supported[name]=ap
    assert d['turnover'] is False
    return summary,supported


def qualified(node):
    if isinstance(node,ast.Name):return node.id
    if isinstance(node,ast.Attribute):return qualified(node.value)+'.'+node.attr
    return ''


def calls(path,function):
    tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function)
    return collections.Counter(qualified(n.func) for n in ast.walk(node) if isinstance(n,ast.Call))


def replay_call_graph(root):
    expected=[('scripts/pilot_reporting.py','verify','pilot.verify_trace'),
              ('scripts/pilot_reporting.py','verify','audit_integration.analyze_environment'),
              ('scripts/pilot.py','verify_trace','audit.verify_case'),
              ('scripts/audit_integration.py','analyze_environment','detector.activity'),
              ('scripts/audit_detectors.py','activity','audit.verify_case'),
              ('scripts/audit_detectors.py','activity','audit.execute')]
    result=[]
    for path,function,target in expected:
        assert calls(root/path,function)[target]==1
        result.append({'file':path,'function':function,'call':target,'static_call_sites':1,'source_sha256':campaign.sha(root/path)})
    return result


def main():
    bundle=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest={'schema':'p01d-analysis-manifest-v1','execution_status':'running','scientific_status':'untested',
              'new_world_runs':0,'source_files':{},'processed_slots':0}
    def save():(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    try:
        campaign.check_freezes()
        for name in ('scripts/diagnose_p01.py','scripts/test_diagnose_p01.py','docs/p01d_analysis_plan.md'):
            source=campaign.ROOT/name;dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(source.read_bytes());manifest['source_files'][name]=campaign.sha(source)
        original=audit_campaign.verify(bundle);assert original['integrity_verified']
        write(out/'input_campaign_audit.json',original)
        m=json.loads((bundle/'manifest.json').read_text());inventory=json.loads((bundle/'checksums.json').read_text())
        assert len(m['runs'])==512
        p=json.loads((bundle/'source/docs/detector_protocol.json').read_text())
        rows=[];cases=[];events=collections.Counter();rule_forms=collections.Counter();laws=set()
        totals=collections.Counter();births=0;max_nodes=0;direction=collections.Counter();track_totals=collections.Counter()
        leaf=collections.Counter();guard_self=guard_all=0
        for row in m['runs']:
            for name,result in row['stages'].items():
                leaf[name]+=result.get('child_cpu_seconds',0);guard_self+=result.get('guard_self_cpu_seconds',0)
                guard_all+=result.get('guard_and_reaped_children_cpu_seconds',0)
            if not row['status'].startswith('verified_'):continue
            root=bundle/'runs'/str(row['slot']);req=json.loads((root/'request.json').read_text());initial=req['initial']['native']['world']
            assert not req['initial']['channels'] and req['initial']['injected']==req['initial']['extracted']==0
            forms={rule['id']:rule_form(rule) for rule in req['initial']['native']['rules']}
            if row['proposal'] not in laws:rule_forms.update(forms.values());laws.add(row['proposal'])
            report=json.loads((root/'rust/stdout.bin').read_text());summary,supported=report_diagnosis(report,p)
            d=report['prefix_detection'];direction[(row['coverage'],d['connected']['supported'],d['interaction']['supported'])]+=1
            if row['full_horizon_ap']=='inconclusive':
                cases.append({'slot':row['slot'],'proposal':row['proposal'],'initial_state':row['initial_state'],
                              'full_horizon_ap':'inconclusive','estimators':summary,'supported_tracks':supported,
                              'report_sha256':campaign.sha(root/'rust/stdout.bin')})
            for name,v in summary.items():track_totals[name+'_supported_tracks']+=v['supported_tracks']
            previous=initial;world_scope(initial,initial,initial);count=0;slot_events=collections.Counter();slot_births=0
            trace=root/'native/trace.jsonl';h=hashlib.sha256()
            with trace.open('rb') as stream:
                for line in stream:
                    h.update(line);frame=json.loads(line);world=frame['state']['native']['world']
                    assert frame['native_frame']['world']==world
                    added=world_scope(initial,world,previous);slot_births+=added
                    for event in frame['native_frame']['events']:
                        form=forms[event['candidate']['rule']];assert form!=7, 'DeleteNode bundle executed'
                        slot_events[str(form)]+=1
                    count+=1;previous=world;max_nodes=max(max_nodes,len(world['nodes']))
            assert h.hexdigest()==inventory[str(trace.relative_to(bundle))]
            assert count==row['observed_epochs'] and sum(slot_events.values())==row['events']
            births+=slot_births;totals['epochs']+=count;totals['events']+=row['events'];events.update(slot_events)
            rows.append({'slot':row['slot'],'proposal':row['proposal'],'initial_state':row['initial_state'],
                         'coverage':row['coverage'],'full_horizon_ap':row['full_horizon_ap'],'epochs':count,
                         'births':slot_births,'deaths':0,'event_forms':dict(slot_events),
                         'initial_nodes':8,'final_nodes':len(previous['nodes']),'node_bound':initial['matter_total']-8,
                         'estimators':summary})
            manifest['processed_slots']=len(rows);save()
        assert totals['epochs']==469935 and totals['events']==1655754 and len(rows)==470
        cpu=json.loads((bundle/'seal.json').read_text())['resource_usage']['total_process_cpu_seconds']
        costs={'leaf_child_cpu_seconds':dict(leaf),'leaf_child_cpu_total':sum(leaf.values()),
               'python_audit_fraction_of_leaf_cpu':leaf['audit']/sum(leaf.values()),
               'sum_guard_self_cpu_at_guard_observation':guard_self,'sum_guard_and_reaped_cpu_at_guard_observation':guard_all,
               'reaped_nonleaf_cpu_inferred_at_guard_boundaries':guard_all-guard_self-sum(leaf.values()),
               'aggregate_cpu_at_seal':cpu,'remaining_cpu_at_other_boundaries':cpu-guard_all,
               'limits':'boundary differences; residual is not an exact exclusive parent/ps profile; no speedup benchmark'}
        findings={'schema':'p01d-findings-v1','source_manifest_sha256':campaign.sha(bundle/'manifest.json'),
            'source_seal_sha256':campaign.sha(bundle/'seal.json'),'diagnostic_sha256':campaign.sha(Path(__file__)),
            'registered_slots':512,'started_slots_scanned':len(rows),'unstarted_slots_preserved':42,
            'epochs_scanned':totals['epochs'],'events_scanned':totals['events'],'unique_generated_laws':len(laws),
            'rule_forms_in_generated_laws':dict(rule_forms),'committed_event_forms':dict(events),
            'observed_node_births':births,'observed_node_deaths':0,'maximum_observed_nodes':max_nodes,
            'contact_and_newborn_invariants':'pass on all observed worlds',
            'detector_proposals_contain_newborns':False,'track_node_turnover':False,
            'estimator_directions':[{'coverage':k[0],'connected_supported':k[1],'interaction_supported':k[2],'states':v} for k,v in direction.items()],
            'supported_tracks':dict(track_totals),'inconclusive_cells_preserved':len(cases),'cost_attribution':costs,
            'replay_call_graph':replay_call_graph(bundle/'source'),'new_world_runs':0,'scientific_status':'untested','e01_authorized':False}
        write(out/'findings.json',findings);write(out/'slot_diagnoses.json',rows);write(out/'inconclusive_cases.json',cases)
        manifest.update(execution_status='complete',source_manifest_sha256=findings['source_manifest_sha256'])
    except BaseException as error:
        manifest.update(execution_status='failed',error=repr(error));raise
    finally:
        save();write(out/'checksums.json',{str(f.relative_to(out)):campaign.sha(f) for f in out.rglob('*') if f.is_file() and f!=out/'checksums.json'})
    print(json.dumps(findings,indent=2))


if __name__=='__main__':main()
