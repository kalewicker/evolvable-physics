#!/usr/bin/env python3
"""Saved-input replay and primary committed-event P01q observations."""
import copy
import json
import sys
from pathlib import Path
import audit
import audit_single_pass
import pilot_reporting
import itertools
import audit_p01q_events
from check_p01f_registration import template
from check_p01q_registration import load, sha, equal, cells

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


def cleanup(rule, binding, event, sample, before, after):
    form=template(rule)
    if form not in (6,7): return None
    donor,child=binding
    target={'class':'Structural','kind':0,'ends':[donor,child]}
    removed=[k for k,e in before['edges'].items() if e==target and k not in after['edges']]
    assert len(removed)==1 and set(before['edges'])-set(after['edges'])==set(removed), 'cleanup edge'
    edge=removed[0]
    assert not any(e['class']=='Structural' and child in e['ends'] for e in after['edges'].values()) if form==7 else True
    a,b=before['nodes'][str(donor)],after['nodes'][str(donor)]
    old=before['nodes'][str(child)]
    assert donor!=child
    if form==6:
        assert after['nodes'][str(child)]==old and set(before['nodes'])==set(after['nodes'])
        assert b['matter']-a['matter']==1 and b['activation']==a['activation'], 'edge refund'
    else:
        assert set(before['nodes'])-set(after['nodes'])=={str(child)}
        assert not any(child in e['ends'] for e in after['edges'].values()), 'leaf deletion'
        assert b['matter']-a['matter']==old['matter']+2 and b['activation']-a['activation']==old['activation']-1, 'node refund'
    return dict(event=event,sample=sample,form=form,edge=int(edge),donor=donor,child=child,
        child_survives=form==6,returned_matter=1 if form==6 else old['matter']+2,
        returned_activation=0 if form==6 else old['activation'],burn=0 if form==6 else 1,
        donor_before=[a['matter'],a['activation']],donor_after=[b['matter'],b['activation']],
        child_before=[old['matter'],old['activation']])


def branch_records(events, births, funding, cleanups):
    branches=[]
    for c in births:
        P,C=c['donor'],c['node']
        for g in births:
            G=g['node']
            if g['donor']!=C or len({P,C,G})!=3 or g['birth_event']<=c['birth_event']:continue
            transfers=[f for f in funding if f['donor']==P and f['recipient']==C and f['matter']==1
                       and c['birth_event']<f['event']<g['birth_event']]
            for first,second in itertools.combinations(transfers,2):
                for clean in cleanups:
                    if not (clean['donor']==C and clean['child']==G and clean['event']>g['birth_event']):continue
                    for recycle in cleanups:
                        if not (recycle['form']==7 and recycle['donor']==P and recycle['child']==C and recycle['event']>clean['event']):continue
                        ev={x['event']:x for x in events}
                        cb=ev[c['birth_event']];gb=ev[g['birth_event']]
                        def creation(x,donor,child):
                            return next(int(k) for k,v in x['after']['edges'].items() if k not in x['before']['edges'] and v=={'class':'Structural','kind':0,'ends':[donor,child]})
                        ce,ge=creation(cb,P,C),creation(gb,C,G)
                        if clean['edge']!=ge or recycle['edge']!=ce:continue
                        if not all(str(ce) in x['after']['edges'] for x in events if c['birth_event']<=x['event']<recycle['event']):continue
                        if not all(str(ge) in x['after']['edges'] for x in events if g['birth_event']<=x['event']<clean['event']):continue
                        ids=[c['birth_event'],first['event'],second['event'],g['birth_event'],clean['event'],recycle['event']]
                        interval=[x for x in events if ids[0]<=x['event']<=ids[-1]]
                        def balance(w,n):
                            v=w['nodes'].get(str(n));return None if v is None else [v['matter'],v['activation']]
                        start,end=interval[0]['before'],interval[-1]['after']
                        branches.append(dict(roles=[P,C,G],cleanup_form=clean['form'],events=ids,
                            creation_edges=[ce,ge],intervening_events=[x['event'] for x in interval if x['event'] not in ids],
                            phase_balances=[dict(event=i,balances=[balance(ev[i]['after'],n) for n in (P,C,G)]) for i in ids],
                            parent_net=[end['nodes'][str(P)][k]-start['nodes'][str(P)][k] for k in ('matter','activation')],
                            total_burns=sum(sum(op.get('amount',0) for op in x['rule']['ops'] if op['op']=='Burn') for x in interval)))
    return sorted(branches,key=lambda x:(x['roles'],x['cleanup_form'],x['events']))


def observations(events, worlds, detection):
    records=empty_records();cleanups=[]
    assert all(a['event']<b['event'] for a,b in zip(events,events[1:])), 'event order'
    for x in events:
        observe_event(x['rule'],x['binding'],x['event'],x['sample'],x['before'],x['after'],records)
        proof=cleanup(x['rule'],x['binding'],x['event'],x['sample'],x['before'],x['after'])
        if proof:cleanups.append(proof)
    visible=visibility(records,worlds,detection)
    result={**{name:sorted(rows.values(),key=lambda r:r['node']) for name,rows in records.items()
               if name in ('births','recycling','orphaning')},
            'additional_structural_funding':records['additional_structural_funding'],
            'descendant_construction':records['descendant_construction'],
            'visibility':sorted(visible.values(),key=lambda r:r['node']),
            'attached_funded_birth_ids':sorted(records['births']),
            'visible_birth_ids':sorted(visible),'recycled_ids':sorted(records['recycling']),
            'visible_birth_recycle_ids':sorted(set(visible)&set(records['recycling'])), 'cleanup_events':cleanups}
    result['ordered_branch']=branch_records(events,result['births'],result['additional_structural_funding'],cleanups)
    result['ordered_branch_count']=len({(*x['roles'],x['cleanup_form']) for x in result['ordered_branch']})
    independent=audit_p01q_events.observe(events,worlds,detection)
    assert equal(result,independent), 'independent event observations'
    return result


def extract(initial, frames, detection):
    events=[];worlds=[initial['native']['world']]
    for sample,frame in enumerate(frames,1):
        world=copy.deepcopy(frame['prepared']['world'])
        pilot_reporting.matching_cap(frame['prepared'])
        for event in frame['native_frame']['events']:
            candidate=event['candidate']
            rule=next(r for r in initial['native']['rules'] if r['id']==candidate['rule'])
            after,writes=audit.execute(world,rule,candidate['binding'])
            events.append(dict(rule=rule,binding=candidate['binding'],event=event['id'],sample=sample,before=world,after=after))
            after['next_event']+=1
            for key in writes:after['writers'][key]=event['id']
            world=after
        world['epoch']+=1
        assert world==frame['native_frame']['world'], 'Extraction recurrence'
        worlds.append(world)
    return observations(events,worlds,detection)


def compact(receipt):
    keys=('status','full_horizon_verified','law_digest','attached_funded_birth_ids',
          'visible_birth_ids','recycled_ids','full_horizon_ap','observed_epochs','observed_events',
          'worker_status','full_horizon_counts','prefix_counts')
    return {key:receipt[key] for key in keys}


def saved_initial(source, slot, protocol):
    assert type(slot) is int and 0<=slot<128, 'saved slot'
    plan=cells(protocol)[slot]
    freeze=load(source/'docs/p01q_registration_freeze.json')
    base=source/protocol['source_bundle']/'runs'/str(slot)
    values=[]
    for language in ('rust_generation','python_generation'):
        path=base/language/'stdout.bin'
        name=str(path.relative_to(source))
        assert sha(path)==freeze['inputs'][name], 'saved input identity'
        values.append(load(path))
    assert equal(*values), 'saved streams disagree'
    return plan,values[0]


def verify(protocol_path, admission_path, slot, request_path, native, report_path):
    protocol=load(protocol_path);request=load(request_path);report=load(report_path)
    source=protocol_path.parent.parent
    admission=load(admission_path)
    assert admission['schema']=='p01q-execution-admission-v1' and admission['world_execution_admitted'] is True
    assert admission['protocol_sha256']==sha(protocol_path) and admission['fixed_slots']==128
    plan,initial=saved_initial(source,slot,protocol)
    assert equal(request,{'schema':'p01-worker-request-v1','initial':initial,'epochs':protocol['epochs'],**protocol['worker_request']}), 'saved request'
    original=pilot_reporting.verify(request,native,report)
    assert audit_single_pass.verify(request,native,report)==original, 'Single-pass full report'
    frames=[json.loads(line) for line in (native/'trace.jsonl').read_bytes().splitlines()]
    obs=extract(request['initial'],frames,report['prefix_detection'])
    counts={key:len(obs[key]) for key in ('births','recycling','visibility','additional_structural_funding',
        'descendant_construction','orphaning','visible_birth_recycle_ids','cleanup_events')}
    counts['ordered_branch']=obs['ordered_branch_count']
    complete=report['coverage']=='complete';summary=load(native/'worker.json')
    return {'schema':'p01q-cell-audit-v1','slot':slot,'proposal':plan['proposal'],'initial_state':plan['initial'],
        'status':'complete' if complete else 'censored','full_horizon_verified':complete,
        'worker_status':summary['status'],'full_horizon_ap':original,
        'observed_epochs':len(frames),'observed_events':summary['events'],
        'law_digest':audit.digest([{k:v for k,v in r.items() if k!='id'} for r in initial['native']['rules']]),
        **{k:obs[k] for k in ('attached_funded_birth_ids','visible_birth_ids','recycled_ids')},
        'prefix_counts':counts,'full_horizon_counts':counts if complete else None,
        'prefix_observations':obs,'observed_lower_bound_only':not complete,'independent_events_pass':True,
        'inputs_sha256':{'request':sha(request_path),'trace':sha(native/'trace.jsonl'),
        'summary':sha(native/'worker.json'),'report':sha(report_path)},'scientific_status':'untested'}

if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3]),Path(sys.argv[4]),Path(sys.argv[5]),Path(sys.argv[6])),sort_keys=True))
