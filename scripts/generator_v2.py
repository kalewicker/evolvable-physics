#!/usr/bin/env python3
"""Independent generator-v2 construction; mock-field tests do not draw laws."""
import hashlib
import json
import sys
from pathlib import Path

if not __debug__:
    raise RuntimeError('Generator audit requires assertions')
NAMESPACE = 'p01-generator-v2'


def draw(proposal, initial, field, index, n):
    raw = json.dumps([NAMESPACE, proposal, initial, field, index],
                     sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return int(hashlib.sha256(raw).hexdigest()[:16], 16) % n


def construct(proposal, initial, field_source=None):
    assert type(proposal) is int and 0 <= proposal < 2**64
    assert type(initial) is int and 0 <= initial < 4
    source = draw if field_source is None else field_source
    def bounded(p, i, field, index, n):
        value = source(p, i, field, index, n)
        assert type(value) is int and 0 <= value < n, (field, value, n)
        return value
    rules = []
    for rule_id in range(8):
        def d(field, n): return bounded(proposal, 0, field, rule_id, n)
        form = d('form', 8)
        nodes = []
        for slot in range(2 if form in (3, 5, 6, 7) else 1):
            state = d('state'+str(slot), 4)
            nodes.append({'kind':1+d('kind'+str(slot),3),'state':None if state == 3 else state})
        pair = {'class':'Structural','kind':0,'ends':[0,1]}
        edges = []
        if form in (3,5,6,7):
            route = 'Structural' if form >= 6 or (form == 3 and d('route',2)) else 'Contact'
            edges = [dict(pair, **{'class':route})]
        if form == 0:
            ops = [{'op':'SetState','node':0,'value':d('value',3)}]
        elif form == 1:
            ops = [{'op':'AddState','node':0,'delta':-1 if d('sign',2)==0 else 1}]
        elif form == 2:
            ops = [{'op':'Burn','node':0,'amount':1+d('amount',2)}]
        elif form == 3:
            ops = [{'op':'Transfer','from':0,'to':1,'matter':d('matter',2),'activation':1+d('amount',2)}]
        elif form == 4:
            ops = [{'op':'CreateNode','account':0,'kind':1+d('new_kind',3),'state':d('value',3)},
                   {'op':'CreateEdge','account':0,'kind':0,'ends':[0,1]},
                   {'op':'Transfer','from':0,'to':1,'matter':1,'activation':1},
                   {'op':'Burn','node':0,'amount':1}]
        elif form in (5,6):
            ops = [{'op':'CreateEdge' if form==5 else 'DeleteEdge','account':0,'kind':0,'ends':[0,1]}]
        else:
            ops = [{'op':'DeleteEdge','account':0,'kind':0,'ends':[0,1]},
                   {'op':'DeleteNode','node':1,'recipient':0}, {'op':'Burn','node':0,'amount':1}]
        rules.append({'id':rule_id,'nodes':nodes,'edges':edges,'absent':[pair] if form==5 else [],'ops':ops})
    nodes = {str(i):{'kind':1+bounded(proposal,initial,'node_kind',i,3),
                     'state':bounded(proposal,initial,'node_state',i,3),'matter':8,'activation':8}
             for i in range(8)}
    edges = {str(i):{'class':'Contact','kind':0,'ends':[i,(i+1)%8]} for i in range(8)}
    for i in range(8):
        if bounded(proposal,initial,'structural',i,2):
            edges[str(len(edges))] = {'class':'Structural','kind':0,'ends':[i,(i+1)%8]}
    return {'profile':'p00c-local-driven-v1','channels':[],'initial_activation':64,'injected':0,'extracted':0,
            'native':{'profile':'p00a-local-closed-v1','seed':bounded(proposal,initial,'scheduler',0,2**64-1),
                      'rules':rules,'limits':{'max_candidates':4096,'max_bindings':65536,'max_nodes':128,'max_edges':256},
                      'world':{'nodes':nodes,'edges':edges,'next_node':8,'next_edge':len(edges),'epoch':0,
                               'dissipated':0,'matter_total':72+len(edges),'activation_total':64,
                               'next_event':0,'writers':{}}}}


def admitted_slot(protocol_path, admission_path, slot):
    raw = protocol_path.read_bytes()
    protocol = json.loads(raw)
    admission = json.loads(admission_path.read_bytes())
    assert protocol['schema']=='p01g-generator-v2-feasibility-registration-v1'
    assert protocol['proposal_ids']==list(range(4000,4016)) and protocol['initial_state_ids']==list(range(4))
    assert protocol['trajectory_denominator']==64 and type(slot) is int and 0<=slot<64
    assert admission['schema']=='p01g-execution-admission-v1'
    assert admission['law_sampling_admitted'] is True and admission['fixed_slots']==64
    assert admission['protocol_sha256']==hashlib.sha256(raw).hexdigest()
    assert admission['e01_authorized'] is False
    return 4000+slot//4, slot%4


if __name__=='__main__':
    p, i = admitted_slot(Path(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3]))
    print(json.dumps(construct(p,i),sort_keys=True,separators=(',',':')))
