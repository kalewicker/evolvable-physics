#!/usr/bin/env python3
"""Original independent replay plus committed-event P01g mechanism observations."""
import copy
import json
import sys
from pathlib import Path
import audit
import audit_single_pass
import generator_v2
import pilot_reporting
from check_p01f_registration import template
from check_p01g_registration import load, sha

if not __debug__:
    raise RuntimeError('Cell audit requires assertions')


def observe_event(rule, binding, event, sample, before, after, records):
    """Observe supplied before/after worlds. Never applies or matches a rule."""
    form=template(rule)
    born=set(after['nodes'])-set(before['nodes'])
    dead=set(before['nodes'])-set(after['nodes'])
    births=records['births']
    if form==4:
        child=before['next_node']; donor=binding[0]
        assert born=={str(child)} and not dead and after['next_node']==child+1
        assert child not in births
        node=after['nodes'][str(child)]
        assert node['matter']>=1 and node['activation']>=1, 'Unfunded birth'
        assert node['kind']==rule['ops'][0]['kind'] and node['state']==rule['ops'][0]['state']
        edge={'class':'Structural','kind':0,'ends':[donor,child]}
        assert any(e==edge and key not in before['edges'] for key,e in after['edges'].items()), 'Unattached birth'
        births[child]={'node':child,'birth_event':event,'donor':donor,'birth_sample':sample}
        if donor in births:
            parent=births[donor]
            assert parent['birth_event']<event
            records['descendant_construction'].append({'event':event,'node':child,'donor':donor,
                'donor_birth_event':parent['birth_event'],'sample':sample})
    elif form==7:
        child=binding[1]; donor=binding[0]
        assert dead=={str(child)} and not born
        if child in births:
            assert births[child]['birth_event']<event
            a,b=before['nodes'][str(donor)],after['nodes'][str(donor)]
            old=before['nodes'][str(child)]
            assert b['matter']-a['matter']==old['matter']+2
            assert b['activation']-a['activation']==old['activation']-1
            assert child not in records['recycling'], 'Repeated deletion'
            records['recycling'][child]={'node':child,'birth_event':births[child]['birth_event'],
                'deletion_event':event,'recipient':donor,'sample':sample,
                'returned_matter':old['matter']+2,'returned_activation':old['activation'],'burn':1}
    else:
        assert not born and not dead, 'Unexpected topology operation'
    if form==3 and rule['edges'][0]['class']=='Structural':
        child=binding[1]
        if child in births:
            assert births[child]['birth_event']<event
            op=rule['ops'][0]
            for key in ('matter','activation'):
                assert after['nodes'][str(child)][key]-before['nodes'][str(child)][key]==op[key]
            records['additional_structural_funding'].append({'event':event,'recipient':child,
                'birth_event':births[child]['birth_event'],'donor':binding[0],
                'matter':op['matter'],'activation':op['activation'],'sample':sample})
    for child in births:
        if str(child) in after['nodes'] and not any(e['class']=='Structural' and child in e['ends'] for e in after['edges'].values()):
            row=records['orphaning'].setdefault(child,{'node':child,'first_event':event,'last_event':event,'observed_events':0})
            row['last_event']=event; row['observed_events']+=1


def empty_records():
    return {'births':{},'recycling':{},'additional_structural_funding':[],
            'descendant_construction':[],'orphaning':{}}


def visibility(records, worlds, detection):
    assert len(detection['connected']['samples'])==len(detection['interaction']['samples'])==len(worlds)
    found={}
    for child,birth in records['births'].items():
        for sample in range(birth['birth_sample'],len(worlds)):
            if str(child) not in worlds[sample]['nodes']:continue
            proposals={name:next((p for p in detection[name]['samples'][sample] if child in p['members']),None)
                       for name in ('connected','interaction')}
            if all(p is not None for p in proposals.values()):
                if child in records['recycling']: assert sample<records['recycling'][child]['sample']
                found[child]={'node':child,'sample':sample,**proposals};break
    return found


def extract(initial, frames, detection):
    records=empty_records(); worlds=[initial['native']['world']]
    for sample,frame in enumerate(frames,1):
        world=copy.deepcopy(frame['prepared']['world'])
        pilot_reporting.matching_cap(frame['prepared'])
        for event in frame['native_frame']['events']:
            candidate=event['candidate']
            rule=next(r for r in initial['native']['rules'] if r['id']==candidate['rule'])
            after,writes=audit.execute(world,rule,candidate['binding'])
            observe_event(rule,candidate['binding'],event['id'],sample,world,after,records)
            after['next_event']+=1
            for key in writes:after['writers'][key]=event['id']
            world=after
        world['epoch']+=1
        assert world==frame['native_frame']['world'], 'Extraction recurrence'
        worlds.append(world)
    visible=visibility(records,worlds,detection)
    return {**{name:sorted(rows.values(),key=lambda r:r['node']) for name,rows in records.items()
               if name in ('births','recycling','orphaning')},
            'additional_structural_funding':records['additional_structural_funding'],
            'descendant_construction':records['descendant_construction'],
            'visibility':sorted(visible.values(),key=lambda r:r['node']),
            'attached_funded_birth_ids':sorted(records['births']),
            'visible_birth_ids':sorted(visible),'recycled_ids':sorted(records['recycling']),
            'visible_birth_recycle_ids':sorted(set(visible)&set(records['recycling']))}


def compact(receipt):
    keys=('status','full_horizon_verified','law_digest','attached_funded_birth_ids',
          'visible_birth_ids','recycled_ids','full_horizon_ap','observed_epochs','observed_events',
          'worker_status','full_horizon_counts','prefix_counts')
    return {key:receipt[key] for key in keys}


def verify(protocol_path, admission_path, slot, request_path, native, report_path):
    p,i=generator_v2.admitted_slot(protocol_path,admission_path,slot)
    protocol=load(protocol_path); request=load(request_path); report=load(report_path)
    assert request=={'schema':'p01-worker-request-v1','initial':generator_v2.construct(p,i),
                     'epochs':protocol['epochs'],**protocol['worker_request']}, 'Independent generator'
    original=pilot_reporting.verify(request,native,report)
    assert audit_single_pass.verify(request,native,report)==original, 'Single-pass full report'
    frames=[json.loads(line) for line in (native/'trace.jsonl').read_bytes().splitlines()]
    observations=extract(request['initial'],frames,report['prefix_detection'])
    counts={key:len(observations[key]) for key in ('births','recycling','visibility',
           'additional_structural_funding','descendant_construction','orphaning','visible_birth_recycle_ids')}
    complete=report['coverage']=='complete'; summary=load(native/'worker.json')
    return {'schema':'p01g-cell-audit-v1','slot':slot,'proposal':p,'initial_state':i,
            'status':'complete' if complete else 'censored','full_horizon_verified':complete,
            'worker_status':summary['status'],'full_horizon_ap':original,
            'observed_epochs':len(frames),'observed_events':summary['events'],
            'law_digest':audit.digest([{k:v for k,v in r.items() if k!='id'} for r in request['initial']['native']['rules']]),
            **{k:observations[k] for k in ('attached_funded_birth_ids','visible_birth_ids','recycled_ids')},
            'prefix_counts':counts,'full_horizon_counts':counts if complete else None,
            'prefix_observations':observations,'observed_lower_bound_only':not complete,
            'inputs_sha256':{'request':sha(request_path),'trace':sha(native/'trace.jsonl'),
                            'summary':sha(native/'worker.json'),'report':sha(report_path)},
            'scientific_status':'untested'}

if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3]),Path(sys.argv[4]),
                            Path(sys.argv[5]),Path(sys.argv[6])),sort_keys=True))
