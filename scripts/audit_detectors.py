#!/usr/bin/env python3
"""Independent offline proposals, temporal metrics, and intervention endpoint audit."""
import collections
import copy
import itertools
import json
import sys
from pathlib import Path
import audit
import audit_interventions
if not __debug__: raise RuntimeError('Detector audit requires assertions')
REGISTRY=Path(__file__).resolve().parents[1]/'docs/detector_protocol.json'

def components(nodes,links):
    remaining=set(nodes);groups=[]
    while remaining:
        group={min(remaining)}
        while True:
            joined=group|set().union(*(edge for edge in links if edge&group))
            joined &= set(nodes)
            if joined==group:break
            group=joined
        groups.append(group);remaining-=group
    return groups

def structural(w):
    return [set(e['ends']) for e in w['edges'].values() if e['class']=='Structural']

def features(w,members):
    f=collections.Counter(f"n:{w['nodes'][str(i)]['kind']}" for i in members)
    for e in w['edges'].values():
        if e['class']=='Structural' and set(e['ends'])<=members:
            kinds=[w['nodes'][str(i)]['kind'] for i in e['ends']]
            f[f"e:{e['kind']}:{kinds}"]+=1
    return dict(f)

def fingerprint(w,members):
    choices=[]
    for order in itertools.permutations(sorted(members)):
        kinds=[w['nodes'][str(i)]['kind'] for i in order]
        edges=sorted([e['kind'],[order.index(i) for i in e['ends']]] for e in w['edges'].values() if e['class']=='Structural' and set(e['ends'])<=members)
        choices.append(audit.canonical([kinds,edges]))
    # The Rust fingerprint hashes the canonical byte vector as a JSON integer array.
    return audit.digest(list(min(choices)))

def changed(a,b):
    ids=set(a['nodes'])|set(b['nodes']);out=set()
    for i in ids:
        x,y=a['nodes'].get(i),b['nodes'].get(i)
        if x is None or y is None or (x['kind'],x['state'])!=(y['kind'],y['state']):out.add(int(i))
    for i in set(a['edges'])|set(b['edges']):
        x,y=a['edges'].get(i),b['edges'].get(i)
        if x!=y:
            for edge in (x,y):
                if edge is not None and edge['class']=='Structural':out.update(edge['ends'])
    return out

def activity(initial,frames):
    audit.verify_case({'name':'detector_trace','initial':initial,'frames':frames})
    w=initial['world'];result=[]
    for frame in frames:
        events=[]
        for event in frame['events']:
            rule=next(r for r in initial['rules'] if r['id']==event['candidate']['rule'])
            after,_=audit.execute(w,rule,event['candidate']['binding'])
            events.append(changed(w,after));w=after
        result.append(events);w=frame['world']
    return result

def similarity(a,b,p):
    keys=set(a)|set(b)
    return sum(min(a.get(k,0),b.get(k,0)) for k in keys)*p['feature_similarity_denominator']>=sum(max(a.get(k,0),b.get(k,0)) for k in keys)*p['feature_similarity_numerator']

def estimator(worlds,events,interaction,p):
    samples=[];excluded=0
    for t,w in enumerate(worlds):
        nodes={int(i) for i in w['nodes']}
        if interaction:
            links=[s&nodes for epoch in events[max(0,t-p['interaction_lookback']):t] for s in epoch]
            eligible=set().union(*links) if links else set()
        else:links=structural(w);eligible=nodes
        proposals=[]
        for group in components(eligible,links):
            if len(group)>p['max_nodes']:excluded+=1
            elif len(group)>=p['min_nodes']:proposals.append({'members':sorted(group),'features':features(w,group)})
        samples.append(proposals)
    tracks=[];previous=[];ambiguous_links=0
    def identity(a,b):
        return len(a&b)*p['identity_jaccard_denominator']>=len(a|b)*p['identity_jaccard_numerator']
    for t,proposals in enumerate(samples):
        links=[[i for i in previous if identity(set(tracks[i]['members']),set(q['members']))] for q in proposals];current=[]
        for j,q in enumerate(proposals):
            possible=links[j];continuation=None;ambiguous=False
            if len(possible)==1:
                if sum(possible[0] in x for x in links)==1:continuation=possible[0]
                else:ambiguous=True
            elif possible:ambiguous=True
            if ambiguous:
                ambiguous_links+=1
                for i in possible:tracks[i]['ambiguous']=True
            if continuation is None:
                i=len(tracks)
                tracks.append({'first':t,'last':t,'observations':0,'members':q['members'],'all_members':[],
                               'active_members':[],'active_epochs':0,'births':0,'deaths':0,'initial_features':q['features'],
                               'similar_observations':0,'ambiguous':ambiguous,'active_persistence':False})
            else:i=continuation
            tr=tracks[i];old=set(tr['members']);members=set(q['members'])
            if t>tr['first']:
                tr['births']+=sum(str(i) not in worlds[t-1]['nodes'] for i in members-old)
                tr['deaths']+=sum(str(i) not in worlds[t]['nodes'] for i in old-members)
            affected=set().union(*events[t-1]) if t>0 and events[t-1] else set()
            active=(old|members)&affected
            if t>tr['first'] and active:tr['active_epochs']+=1
            tr['active_members']=sorted(set(tr['active_members'])|active)
            tr['all_members']=sorted(set(tr['all_members'])|members);tr['members']=q['members'];tr['last']=t;tr['observations']+=1
            if similarity(tr['initial_features'],q['features'],p):tr['similar_observations']+=1
            current.append(i)
        previous=current
    for tr in tracks:
        duration=tr['last']-tr['first']
        tr['active_persistence']=(not tr['ambiguous'] and duration>=p['min_duration'] and tr['observations']==duration+1
            and tr['similar_observations']==tr['observations'] and tr['active_epochs']*p['min_active_epoch_denominator']>=duration*p['min_active_epoch_numerator']
            and set(tr['all_members'])<=set(tr['active_members']))
    return {'samples':samples,'tracks':tracks,'excluded_large':excluded,'ambiguous_links':ambiguous_links,'supported':any(t['active_persistence'] for t in tracks)}

def analyze(initial,frames,p):
    events=activity(initial,frames);worlds=[initial['world']]+[f['world'] for f in frames]
    conn=estimator(worlds,events,False,p);inter=estimator(worlds,events,True,p)
    pairs=[[i,j] for i,a in enumerate(conn['tracks']) for j,b in enumerate(inter['tracks']) if a['active_persistence'] and b['active_persistence'] and a['last']==b['last'] and len(set(a['members'])&set(b['members']))*p['identity_jaccard_denominator']>=len(set(a['members'])|set(b['members']))*p['identity_jaccard_numerator']]
    disagreement=conn['supported']!=inter['supported'] or (conn['supported'] and inter['supported'] and not pairs)
    return {'protocol_digest':audit.digest(p),'connected':conn,'interaction':inter,'active_persistence':('inconclusive' if disagreement else 'supported' if conn['supported'] else 'not_supported'),
            'disagreement':disagreement,'agreement_pairs':pairs,'turnover':any(all(min(t['births'],t['deaths'])>=p['min_replacement_pairs'] for t in (conn['tracks'][i],inter['tracks'][j])) for i,j in pairs)}

def occupancy(frames,root,reference,p):
    result=0
    for f in frames:
        w=f['world'];nodes={int(i) for i in w['nodes']}
        if any(root in group and p['min_nodes']<=len(group)<=p['max_nodes'] and fingerprint(w,group)==reference for group in components(nodes,structural(w))):result+=1
    return result

def verify_case(c,p):
    assert c['family'] in p['expected'] and len(c['frames'])==12
    seed=c['initial']['seed'];assert c['split']==('development' if seed in p['development_seeds'] else 'validation')
    detection=analyze(c['initial'],c['frames'],p);assert detection==c['detection'],'independent detector summary'
    m=c['maintenance'];supported=False
    if c['family'] in ('renewal','passive_turnover'):
        assert m is not None and m['root']==0 and len(m['warmup'])==2
        audit.verify_case({'name':'maintenance_warmup','initial':c['initial'],'frames':m['warmup']})
        source=copy.deepcopy(c['initial']);source['world']=m['warmup'][-1]['world'];assert source==m['source']
        reference=fingerprint(c['initial']['world'],{0,1,2});assert m['reference_fingerprint']==reference
        assert [a['name'] for a in m['arms']]==['baseline','sham','target','unrelated','rescue']
        counts=[]
        for arm in m['arms']:
            name=arm['name'];node=3 if name=='unrelated' else 0;expected=source['world']['nodes'][str(node)]['state']
            prescribed=[] if name=='baseline' else [{'op':'SetState','node':node,'expected':expected,'value':expected if name=='sham' else 9}]
            assert len(arm['chain'])==(2 if name=='rescue' else 1) and arm['chain'][0]['request']['operations']==prescribed
            if name=='rescue':assert arm['chain'][1]['request']['operations']==[{'op':'SetState','node':0,'expected':9,'value':source['world']['nodes']['0']['state']}]
            current=copy.deepcopy(source)
            for b in arm['chain']:current=audit_interventions.replay_branch(current,b)
            assert len(arm['frames'])==p['maintenance_horizon']
            audit.verify_case({'name':'maintenance_arm','initial':current,'frames':arm['frames']})
            count=occupancy(arm['frames'],0,reference,p);assert count==arm['occupancy'];counts.append(count)
        supported=(detection['active_persistence']=='supported' and any(all(0 in t['members'] and min(t['births'],t['deaths'])>=p['min_replacement_pairs'] for t in (detection['connected']['tracks'][i],detection['interaction']['tracks'][j])) for i,j in detection['agreement_pairs'])
            and max(0,counts[0]-counts[2])*p['min_occupancy_drop_denominator']>=p['maintenance_horizon']*p['min_occupancy_drop_numerator']
            and all(abs(counts[i]-counts[0])<=p['control_occupancy_tolerance'] for i in (1,3,4)))
        assert supported==m['supported']
        assert counts==([8,8,0,8,8] if c['family']=='renewal' else [12,12,12,12,12]),'physical endpoint fixture expectation'
    else:assert m is None
    maintenance='supported' if supported else 'not_supported'
    assert c['maintenance_status']==maintenance
    assert [detection['active_persistence'],maintenance]==p['expected'][c['family']],'registered expected labels'
    return detection['disagreement']

def audit_suite(suite):
    p=json.loads(REGISTRY.read_text());assert suite['protocol']==p and suite['protocol_digest']==audit.digest(p)
    assert suite['schema']=='p00e-detector-suite-v1' and suite['scientific_status']=='untested'
    assert len(suite['cases'])==144 and {(c['family'],c['initial']['seed']) for c in suite['cases']}=={(f,s) for f in p['expected'] for s in range(16)}
    disagreements=0;counts={}
    for c in suite['cases']:
        disagreements+=verify_case(c,p)
        key=c['split'];counts[key]=counts.get(key,0)+1
    return {'status':'pass','cases':144,'splits':counts,'detector_epochs':1728,'maintenance_arms':160,'maintenance_epochs':1920,
            'retained_disagreements':disagreements,'registered_label_mismatches':0,'protocol_digest':audit.digest(p),'scientific_status':'untested'}
if __name__=='__main__':print(json.dumps(audit_suite(json.loads(Path(sys.argv[1]).read_text())),indent=2))
