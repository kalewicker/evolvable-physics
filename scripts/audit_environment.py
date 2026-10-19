#!/usr/bin/env python3
"""Independent accounting, environment scheduling, transport, and native replay."""
import copy
import json
import sys
from pathlib import Path
import audit

if not __debug__:
    raise RuntimeError('Audit requires assertions enabled')
MODES = ('closed', 'local_transport', 'driven', 'blocked')

def validate(e):
    assert e['profile'] == 'p00c-local-driven-v1'
    audit.validate(e['native']['world'])
    assert all(0 <= e[k] <= audit.U64 for k in ('initial_activation','injected','extracted'))
    assert e['initial_activation'] + e['injected'] == e['native']['world']['activation_total'] + e['extracted']
    assert len(e['channels']) <= 32
    assert len({c['id'] for c in e['channels']}) == len(e['channels'])
    w = e['native']['world']
    for c in e['channels']:
        assert c['period'] > 0 and (c['end'] is None or c['end'] > c['start'])
        a = c['action']
        if a['op'] in ('Supply','Extract'):
            assert str(a['node']) in w['nodes'] and 0 < a['amount'] <= audit.U64
        else:
            assert a['op'] == 'Transport'
            contact = w['edges'][str(a['edge'])]
            assert contact['class'] == 'Contact' and contact['ends'] == [a['from'],a['to']]
            assert a['matter'] + a['activation'] > 0

def apply_environment(source):
    e = copy.deepcopy(source); validate(e)
    epoch = e['native']['world']['epoch']; records = []
    for c in sorted(e['channels'], key=lambda c:c['id']):
        if epoch < c['start'] or (c['end'] is not None and epoch >= c['end']) or (epoch-c['start']) % c['period']:
            continue
        before = audit.digest(e)
        a = c['action']; w = e['native']['world']; reads=set(); writes=set(); enabled=True
        if a['op'] == 'Supply':
            key = f"node:{a['node']}"; reads.add(key); writes.add(key)
            w['nodes'][str(a['node'])]['activation'] += a['amount']
            w['activation_total'] += a['amount']; e['injected'] += a['amount']
        elif a['op'] == 'Extract':
            key = f"node:{a['node']}"; reads.add(key)
            n = w['nodes'][str(a['node'])]; enabled = n['activation'] >= a['amount']
            if enabled:
                n['activation'] -= a['amount']; w['activation_total'] -= a['amount']; e['extracted'] += a['amount']; writes.add(key)
        else:
            reads.update(f'{prefix}:{i}' for i in (a['from'],a['to']) for prefix in ('node','adj'))
            n, m = w['nodes'][str(a['from'])], w['nodes'][str(a['to'])]
            enabled = all(n[k] >= a[k] for k in ('matter','activation'))
            if enabled:
                for k in ('matter','activation'):
                    n[k] -= a[k]; m[k] += a[k]
                writes.update((f"node:{a['from']}",f"node:{a['to']}"))
        parents = sorted({w['writers'][k] for k in reads if k in w['writers']})
        event_id = None
        if enabled:
            event_id=w['next_event']; w['next_event'] += 1
            for k in writes: w['writers'][k]=event_id
        validate(e)
        records.append({'channel':c['id'],'event_id':event_id,'status':'applied' if enabled else 'insufficient_resource',
                        'reads':sorted(reads),'writes':sorted(writes),'parents':parents,'before':before,'after':audit.digest(e)})
    return e, records

def registered_channels(mode):
    def ch(i, action): return {'id':i,'start':0,'end':None,'period':1,'action':action}
    channels=[]
    if mode in ('driven','blocked'): channels.append(ch(10,{'op':'Supply','node':0,'amount':2}))
    if mode in ('driven','local_transport'):
        channels.append(ch(20,{'op':'Transport','edge':0,'from':0,'to':1,'matter':0,'activation':2 if mode=='driven' else 1}))
        channels.append({'id':40,'start':1,'end':7,'period':2,'action':{'op':'Transport','edge':1,'from':1,'to':2,'matter':1,'activation':0}})
    if mode == 'driven': channels.append(ch(30,{'op':'Extract','node':1,'amount':1}))
    return channels

def verify_case(case):
    mode=case['mode']; assert mode in MODES
    e=copy.deepcopy(case['initial']);validate(e)
    assert e['channels']==registered_channels(mode)
    assert e['initial_activation']==2 and e['injected']==e['extracted']==0
    assert e['native']['world']=={
        'nodes':{'0':{'kind':2,'state':0,'matter':8,'activation':2},'1':{'kind':1,'state':0,'matter':4,'activation':0},
                 '2':{'kind':2,'state':0,'matter':0,'activation':0},'3':{'kind':1,'state':0,'matter':4,'activation':0}},
        'edges':{'0':{'class':'Contact','kind':0,'ends':[0,1]},'1':{'class':'Contact','kind':0,'ends':[1,2]}},
        'next_node':4,'next_edge':2,'epoch':0,'dissipated':0,'matter_total':22,'activation_total':2,'next_event':0,'writers':{}}
    assert e['native']['rules']==[{'id':s,'nodes':[{'kind':1,'state':s}],'edges':[],'absent':[],
                                   'ops':[{'op':'SetState','node':0,'value':1-s},{'op':'Burn','node':0,'amount':1}]} for s in (0,1)]
    assert len(case['epochs'])==8
    applied=skipped=native=0
    for frame in case['epochs']:
        assert frame['before']==audit.digest(e)
        e,events=apply_environment(e)
        assert frame['environment_events']==events, 'environment receipts'
        applied+=sum(x['status']=='applied' for x in events);skipped+=sum(x['status']=='insufficient_resource' for x in events)
        assert frame['prepared']==e['native'], 'environment before native ordering'
        native+=audit.verify_case({'name':'environment_native','initial':e['native'],'frames':[frame['native_frame']]})
        e['native']['world']=frame['native_frame']['world']
        validate(e)
        assert frame['state']==e and frame['after']==audit.digest(e), 'epoch continuation identity'
        assert e['native']['world']['nodes']['3']==case['initial']['native']['world']['nodes']['3'], 'disconnected component'
    assert native=={'closed':0,'local_transport':2,'driven':8,'blocked':0}[mode]
    assert e['injected']==(16 if mode in ('driven','blocked') else 0)
    assert e['extracted']==(8 if mode=='driven' else 0)
    assert e['native']['world']['nodes']['2']['matter']==(3 if mode in ('driven','local_transport') else 0)
    return {'native_events':native,'environment_events':applied,'skipped_attempts':skipped,'injected':e['injected'],'extracted':e['extracted']}

def audit_suite(suite):
    assert suite['schema']=='p00c-environment-suite-v1' and suite['scientific_status']=='untested'
    assert len(suite['cases'])==64
    assert {(c['mode'],c['initial']['native']['seed']) for c in suite['cases']}=={(m,s) for m in MODES for s in range(16)}
    outcomes={};native=environment=skipped=0
    for c in suite['cases']:
        result=verify_case(c)
        if c['mode'] in outcomes: assert outcomes[c['mode']]==result
        outcomes[c['mode']]=result
        native+=result['native_events'];environment+=result['environment_events'];skipped+=result['skipped_attempts']
    return {'status':'pass','cases':64,'epochs':512,'native_events':native,'environment_events':environment,
            'skipped_attempts':skipped,'outcomes':outcomes,'scientific_status':'untested'}
if __name__=='__main__':
    print(json.dumps(audit_suite(json.loads(Path(sys.argv[1]).read_text())),indent=2))
