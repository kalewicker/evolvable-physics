#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path
import audit
import audit_environment as environment
import audit_interventions as interventions

if not __debug__:
    raise RuntimeError('Audit requires assertions enabled')
ARMS=('baseline','sham','target','unrelated','rescue')
FAMILIES=('state_arrest','replenished_activation')

def replay_branch(source,record):
    assert set(record)=={'request','receipt','native_branch','environment'}
    req=record['request']
    assert set(req)=={'schema','expected_source','operations'}
    assert req['schema']=='environment-intervention-v1' and req['expected_source']==audit.digest(source)
    assert record['native_branch']['request']['operations']==req['operations']
    out=copy.deepcopy(source)
    out['native']=interventions.replay_branch(source['native'],record['native_branch'])
    environment.validate(out)
    assert record['environment']==out, 'entire wrapper must be preserved'
    assert record['receipt']=={'schema':'environment-intervention-receipt-v1','request_digest':audit.digest(req),'before':audit.digest(source),'after':audit.digest(out)}
    return out

def replay_epochs(source,frames):
    e=copy.deepcopy(source);native=external=0
    for f in frames:
        assert f['before']==audit.digest(e)
        e,events=environment.apply_environment(e)
        assert f['environment_events']==events
        external+=sum(x['event_id'] is not None for x in events)
        assert f['prepared']==e['native']
        native+=audit.verify_case({'name':'integrated','initial':e['native'],'frames':[f['native_frame']]})
        e['native']['world']=f['native_frame']['world'];environment.validate(e)
        assert f['state']==e and f['after']==audit.digest(e)
    return e,native,external

def physical(e):
    e=copy.deepcopy(e)
    for k in ('next_event','writers'): del e['native']['world'][k]
    return e

def verify_case(c):
    family=c['family'];assert family in FAMILIES
    initial=c['initial'];environment.validate(initial)
    w=initial['native']['world']
    assert initial['initial_activation']==4 and initial['injected']==initial['extracted']==0
    assert w['epoch']==w['next_event']==w['dissipated']==0 and w['writers']=={}
    assert w['matter_total']==34 and w['activation_total']==4 and w['next_node']==6 and w['next_edge']==4
    assert w['nodes']=={str(i):{'kind':1 if i%3==1 else 2,'state':0,'matter':[8,4,0][i%3],'activation':2 if i%3==0 else 0} for i in range(6)}
    assert w['edges']=={str(i):{'class':'Contact','kind':0,'ends':ends} for i,ends in enumerate(([0,1],[1,2],[3,4],[4,5]))}
    channels=environment.registered_channels('driven');other=copy.deepcopy(channels)
    for ch in other:
        ch['id']+=100;a=ch['action']
        if a['op']=='Transport':a['edge']+=2;a['from']+=3;a['to']+=3
        else:a['node']+=3
    assert initial['channels']==channels+other
    assert initial['native']['rules']==[{'id':s,'nodes':[{'kind':1,'state':s}],'edges':[],'absent':[],'ops':[{'op':'SetState','node':0,'value':1-s},{'op':'Burn','node':0,'amount':1}]} for s in (0,1)]
    assert len(c['warmup'])==2
    source,_,_=replay_epochs(initial,c['warmup']);assert c['source']==source
    for i in range(3):assert source['native']['world']['nodes'][str(i)]==source['native']['world']['nodes'][str(i+3)]
    assert [a['name'] for a in c['arms']]==list(ARMS)
    total=external=0;outcomes={}
    for arm in c['arms']:
        name=arm['name'];offset=3 if name=='unrelated' else 0
        op=({'op':'SetState','node':1+offset,'expected':0,'value':0 if name=='sham' else 9} if family=='state_arrest' else
            {'op':'MoveResources','from':offset,'to':2+offset,'matter':0,'activation':0 if name=='sham' else source['native']['world']['nodes'][str(offset)]['activation']})
        assert len(arm['chain'])==(2 if name=='rescue' else 1)
        assert arm['chain'][0]['request']['operations']==([] if name=='baseline' else [op])
        if name=='rescue':
            restore=({'op':'SetState','node':1,'expected':9,'value':0} if family=='state_arrest' else
                     {'op':'MoveResources','from':2,'to':0,'matter':0,'activation':source['native']['world']['nodes']['0']['activation']})
            assert arm['chain'][1]['request']['operations']==[restore]
        current=copy.deepcopy(source)
        for record in arm['chain']:current=replay_branch(current,record)
        if name=='baseline':assert current==source
        assert len(arm['epochs'])==6
        final,native,env=replay_epochs(current,arm['epochs']);total+=native;external+=env
        assert final['injected']==32 and final['extracted']==16
        counts={i:sum(ev['candidate']['binding']==[i] for f in arm['epochs'] for ev in f['native_frame']['events']) for i in (1,4)}
        assert counts[1]==(0 if family=='state_arrest' and name=='target' else 6)
        assert counts[4]==(0 if family=='state_arrest' and name=='unrelated' else 6)
        outcomes[name]={'focal_events':counts[1],'control_events':counts[4]}
        if name in ('sham','rescue'):
            for f,b in zip(arm['epochs'],c['arms'][0]['epochs']):assert physical(f['state'])==physical(b['state'])
    return total,external,outcomes

def audit_suite(suite):
    assert suite['schema']=='p00d-environment-branch-suite-v1' and suite['scientific_status']=='untested'
    assert len(suite['cases'])==32 and {(c['family'],c['initial']['native']['seed']) for c in suite['cases']}=={(f,s) for f in FAMILIES for s in range(16)}
    native=external=0;outcomes={}
    for c in suite['cases']:
        n,e,o=verify_case(c);native+=n;external+=e
        if c['family'] in outcomes:assert outcomes[c['family']]==o
        outcomes[c['family']]=o
    return {'status':'pass','cases':32,'arms':160,'continuation_epochs':960,'native_events':native,'environment_events':external,'outcomes':outcomes,'scientific_status':'untested'}

def verify_bundle(path):
    p=Path(path);m=json.loads((p/'manifest.json').read_text())
    assert m['schema']=='environment-branch-bundle-v1' and m['execution_status']=='complete' and m['scientific_status']=='untested'
    def cp(name):
        x=json.loads((p/name).read_text());assert x['schema']=='environment-checkpoint-v1' and x['digest']==audit.digest(x['payload']);environment.validate(x['payload']);return x['payload']
    source=cp('source.json');r=json.loads((p/'branch.json').read_text());out=replay_branch(source,r)
    assert cp('checkpoint.json')==out and m['source_digest']==audit.digest(source) and m['branch_digest']==audit.digest(r) and m['checkpoint_digest']==audit.digest(out)
    return out
if __name__=='__main__':print(json.dumps(audit_suite(json.loads(Path(sys.argv[1]).read_text())),indent=2))
