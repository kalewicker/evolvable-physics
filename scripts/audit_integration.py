#!/usr/bin/env python3
"""Independent full-environment detector integration and log-mode evidence audit."""
import copy
import json
import sys
from pathlib import Path
import audit
import audit_detectors as detector
import audit_environment as env_audit
import audit_environment_branches as env_replay
ROOT=Path(__file__).resolve().parents[1]
if not __debug__:raise RuntimeError('Audit requires assertions')

def registry():return json.loads((ROOT/'docs/p00g_protocol.json').read_text())
def channel(i,action):return {'id':i,'start':0,'end':None,'period':1,'action':action}
def channels(flux):
    out=[channel(10,{'op':'Supply','node':0,'amount':2}),channel(20,{'op':'Transport','edge':0,'from':0,'to':1,'matter':0,'activation':2})]
    if flux:out.append(channel(25,{'op':'Transport','edge':2,'from':1,'to':2,'matter':0,'activation':1}))
    out.append(channel(30,{'op':'Extract','node':1,'amount':1}))
    if flux:out.append(channel(40,{'op':'Extract','node':2,'amount':1}))
    return out

def renewal_native(seed):
    def node(k,m=0):return {'kind':k,'state':0,'matter':m,'activation':0}
    def pattern(k,s=None):return {'kind':k,'state':s}
    def edge(k,ends):return {'class':'Structural','kind':k,'ends':ends}
    def rule(i,ns,es,ops):return {'id':i,'nodes':ns,'edges':es,'absent':[],'ops':ops}
    def state(i,s):return {'op':'SetState','node':i,'value':s}
    nodes={str(i):node([10,11,12][i%3],8 if i%3==0 else 0) for i in range(6)}
    edges={'0':edge(3,[0,1]),'1':edge(4,[0,2]),'2':edge(3,[3,4]),'3':edge(4,[3,5])}
    rules=[rule(0,[pattern(12,0)],[],[state(0,1)]),
           rule(1,[pattern(10,0),pattern(11),pattern(12,1)],[edge(3,[0,1]),edge(4,[0,2])],
                [{'op':'DeleteEdge','account':0,'kind':4,'ends':[0,2]},{'op':'DeleteNode','node':2,'recipient':0},state(0,1),state(1,1)]),
           rule(2,[pattern(10,1),pattern(11)],[edge(3,[0,1])],
                [{'op':'CreateNode','account':0,'kind':12,'state':0},{'op':'CreateEdge','account':0,'kind':4,'ends':[0,2]},state(0,0),state(1,0)])]
    return native(seed,nodes,edges,rules,26,0)

def native(seed,nodes,edges,rules,matter,activation):
    return {'profile':'p00a-local-closed-v1','seed':seed,'rules':rules,'limits':{'max_candidates':10000,'max_bindings':100000,'max_nodes':128,'max_edges':256},
            'world':{'nodes':nodes,'edges':edges,'next_node':len(nodes),'next_edge':len(edges),'epoch':0,'dissipated':0,'matter_total':matter,'activation_total':activation,'next_event':0,'writers':{}}}

def initial(family,seed):
    if family=='driven_renewal':
        return {'profile':'p00c-local-driven-v1','channels':[channel(10+i,{'op':'Supply','node':n,'amount':1}) for i,n in enumerate((0,3))],
                'initial_activation':0,'injected':0,'extracted':0,'native':renewal_native(seed)}
    nodes={str(i):{'kind':k,'state':0,'matter':m,'activation':a} for i,k,m,a in ((0,2,8,2),(1,10,4,0),(2,11,0,0),(3,2,0,0))}
    edges={str(i):{'class':cl,'kind':3,'ends':ends} for i,cl,ends in ((0,'Contact',[0,1]),(1,'Contact',[1,3]),(2,'Contact',[1,2]),(3,'Structural',[1,2]))}
    rules=[{'id':s,'nodes':[{'kind':10,'state':s},{'kind':11,'state':s}],'edges':[{'class':'Structural','kind':3,'ends':[0,1]}],'absent':[],
            'ops':[{'op':'SetState','node':0,'value':1-s},{'op':'SetState','node':1,'value':1-s},{'op':'Burn','node':0,'amount':1}]} for s in (0,1)]
    if family=='external_flux':rules=[]
    if family=='no_op_pair':rules=[dict(rules[0],nodes=[{'kind':10,'state':None},{'kind':11,'state':None}],ops=[{'op':'SetState','node':0,'value':0},{'op':'SetState','node':1,'value':0},{'op':'Burn','node':0,'amount':1}])]
    e={'profile':'p00c-local-driven-v1','channels':channels(family=='external_flux'),'initial_activation':2,'injected':0,'extracted':0,'native':native(seed,nodes,edges,rules,20,2)}
    if family=='unfunded_pair':e['channels']=[c for c in e['channels'] if c['id']!=10]
    if family=='mixed_islands':
        for i in range(4):
            n=copy.deepcopy(nodes[str(i)])
            if n['kind'] in (10,11):n['kind']+=100
            nodes[str(i+4)]=n
            ed=copy.deepcopy(edges[str(i)]);ed['ends']=[n+4 for n in ed['ends']];edges[str(i+4)]=ed
        for c in channels(True):
            c['id']+=100;a=c['action']
            if a['op']=='Transport':a['edge']+=4;a['from']+=4;a['to']+=4
            else:a['node']+=4
            e['channels'].append(c)
        e['native']['world'].update(next_node=8,next_edge=8,matter_total=40,activation_total=4);e['initial_activation']=4
    return e

def detection(worlds,activity):
    p=json.loads(detector.REGISTRY.read_text())
    conn=detector.estimator(worlds,activity,False,p);inter=detector.estimator(worlds,activity,True,p)
    pairs=[[i,j] for i,a in enumerate(conn['tracks']) for j,b in enumerate(inter['tracks']) if a['active_persistence'] and b['active_persistence'] and a['last']==b['last'] and len(set(a['members'])&set(b['members']))*p['identity_jaccard_denominator']>=len(set(a['members'])|set(b['members']))*p['identity_jaccard_numerator']]
    disagreement=conn['supported']!=inter['supported'] or (conn['supported'] and inter['supported'] and not pairs)
    return {'protocol_digest':audit.digest(p),'connected':conn,'interaction':inter,'active_persistence':'inconclusive' if disagreement else 'supported' if conn['supported'] else 'not_supported',
            'disagreement':disagreement,'agreement_pairs':pairs,'turnover':any(all(min(t['births'],t['deaths'])>=p['min_replacement_pairs'] for t in (conn['tracks'][i],inter['tracks'][j])) for i,j in pairs)}

def analyze_environment(initial,epochs,quiet):
    assert len(quiet)==len(epochs)
    e=copy.deepcopy(initial);worlds=[e['native']['world']];activities=[]
    for f,disabled in zip(epochs,quiet):
        assert f['before']==audit.digest(e)
        e,events=env_audit.apply_environment(e)
        assert f['environment_events']==events,'environment phase'
        assert f['prepared']==e['native'],'prepared state'
        # This validates and extracts native changes only; external records are never activity groups.
        native=detector.activity(e['native'],[f['native_frame']]);assert len(native)==1;activities.append(native[0])
        e['native']['world']=f['native_frame']['world'];env_audit.validate(e)
        assert f['state']==e and f['after']==audit.digest(e) and disabled==audit.digest(e),'whole state/logging prefix'
        worlds.append(e['native']['world'])
    return detection(worlds,activities)

def verify_case(c,p):
    family=c['family'];cfg=p['families'][family];seed=c['initial']['native']['seed'];assert seed in p['seeds']
    assert c['initial']==initial(family,seed),'independent integration generator'
    assert len(c['epochs'])==p['epochs']
    d=analyze_environment(c['initial'],c['epochs'],c['disabled_digests']);assert d==c['detection'],'environment detector output'
    assert d['active_persistence']==cfg['expected_ap'],'registered AP label'
    native_events=sum(len(f['native_frame']['events']) for f in c['epochs']);assert native_events==cfg['expected_native_events']
    if family in ('external_flux','no_op_pair'):
        assert not d['interaction']['tracks'] and all(not t['active_members'] for t in d['connected']['tracks'])
    if family=='mixed_islands':assert all(not t['active_members'] and not t['active_persistence'] for t in d['connected']['tracks'] if 5 in t['members'])
    if family==p['maintenance_family']:
        m=c['maintenance'];assert m is not None and len(m['warmup'])==p['maintenance_warmup_epochs']
        analyze_environment(c['initial'],m['warmup'],m['disabled_warmup_digests'])
        source=m['warmup'][-1]['state'];assert m['source']==source
        ref=detector.fingerprint(c['initial']['native']['world'],{0,1,2});assert m['reference_fingerprint']==ref
        assert [a['name'] for a in m['arms']]==p['maintenance_arms']
        counts=[]
        for arm in m['arms']:
            name=arm['name'];n=3 if name=='unrelated' else 0;value=source['native']['world']['nodes'][str(n)]['state']
            expected=[] if name=='baseline' else [{'op':'SetState','node':n,'expected':value,'value':value if name=='sham' else 9}]
            assert len(arm['chain'])==(2 if name=='rescue' else 1) and arm['chain'][0]['request']['operations']==expected
            if name=='rescue':assert arm['chain'][1]['request']['operations']==[{'op':'SetState','node':0,'expected':9,'value':source['native']['world']['nodes']['0']['state']}]
            current=copy.deepcopy(source)
            for b in arm['chain']:current=env_replay.replay_branch(current,b)
            assert len(arm['epochs'])==p['epochs'];analyze_environment(current,arm['epochs'],arm['disabled_digests'])
            frames=[{'world':f['state']['native']['world']} for f in arm['epochs']]
            count=detector.occupancy(frames,0,ref,json.loads(detector.REGISTRY.read_text()));assert count==arm['occupancy'];counts.append(count)
        assert counts==p['maintenance_expected_occupancy']
        base=json.loads(detector.REGISTRY.read_text())
        support=(d['active_persistence']=='supported' and any(all(0 in t['members'] and min(t['births'],t['deaths'])>=base['min_replacement_pairs'] for t in (d['connected']['tracks'][i],d['interaction']['tracks'][j])) for i,j in d['agreement_pairs'])
                 and (counts[0]-counts[2])*base['min_occupancy_drop_denominator']>=p['epochs']*base['min_occupancy_drop_numerator'] and all(abs(counts[i]-counts[0])<=base['control_occupancy_tolerance'] for i in (1,3,4)))
        assert support and m['supported']==support
    else:assert c['maintenance'] is None
    return native_events

def audit_suite(suite):
    p=registry();assert suite['schema']=='p00g-integration-suite-v1' and suite['protocol']==p and suite['protocol_digest']==audit.digest(p) and suite['scientific_status']=='untested'
    assert p['base_detector_protocol_digest']==audit.digest(json.loads(detector.REGISTRY.read_text()))
    assert len(suite['native_logging'])==112 and {(c['family'],c['initial']['seed']) for c in suite['native_logging']}=={(f,s) for f in ('frozen','oscillator','attach_detach','growth_recycling','transfer','absence_conflict','resource_exhaustion') for s in p['seeds']}
    for c in suite['native_logging']:
        assert len(c['frames'])==len(c['disabled_digests'])==p['epochs']
        audit.verify_case({'name':c['family'],'initial':c['initial'],'frames':c['frames']})
        assert c['disabled_digests']==[f['after'] for f in c['frames']]
    assert len(suite['environment_logging'])==64 and {(c['family'],c['initial']['native']['seed']) for c in suite['environment_logging']}=={(f,s) for f in ('closed','local_transport','driven','blocked') for s in p['seeds']}
    for c in suite['environment_logging']:
        assert len(c['epochs'])==12
        env_audit.verify_case({'mode':c['family'],'initial':c['initial'],'epochs':c['epochs'][:8]})
        analyze_environment(c['initial'],c['epochs'],c['disabled_digests'])
    assert len(suite['cases'])==96 and {(c['family'],c['initial']['native']['seed']) for c in suite['cases']}=={(f,s) for f in p['families'] for s in p['seeds']}
    native=sum(verify_case(c,p) for c in suite['cases'])
    return {'status':'pass','environment_detector_cases':96,'environment_detector_epochs':1152,'native_events_in_primary_cases':native,
            'native_logging_cases':112,'legacy_environment_logging_cases':64,'maintenance_arms':80,'maintenance_epochs':960,'logging_equivalent_epochs':4256,
            'external_only_activity_rejected':True,'mixed_islands_not_pooled':True,'environment_maintenance_controls':'pass','scientific_status':'untested'}
if __name__=='__main__':print(json.dumps(audit_suite(json.loads(Path(sys.argv[1]).read_text())),indent=2))
