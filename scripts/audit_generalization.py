#!/usr/bin/env python3
"""Independent panel generation, trace replay and frozen-detector comparison."""
import copy
import json
import sys
from pathlib import Path
import audit
import audit_detectors as detector
if not __debug__: raise RuntimeError('Audit requires assertions')
ROOT=Path(__file__).resolve().parents[1]

def initial(family,seed,encoding,p):
    n=p['families'][family]['nodes'];kinds=list(range(100,100+n))
    if family in ('ring6','async_ring4'):shape=[[i,(i+1)%n] for i in range(n)]
    elif family=='star5':shape=[[0,i] for i in range(1,n)]
    elif family in ('hyperedge3','hyperedge4'):shape=[list(range(n))]
    elif family=='templated_births':shape=[]
    else:shape=[[i,i+1] for i in range(n-1)]
    nodes={str(i):{'kind':kind,'state':0,'matter':2,'activation':0} for i,kind in enumerate(kinds)}
    edges={str(i):{'class':'Structural','kind':3,'ends':ends} for i,ends in enumerate(shape)}
    def rule(i,ks,states,es,ops):return {'id':i,'nodes':[{'kind':k,'state':s} for k,s in zip(ks,states)],'edges':[{'class':'Structural','kind':3,'ends':ends} for ends in es],'absent':[],'ops':ops}
    def setstate(i,v):return {'op':'SetState','node':i,'value':v}
    def transfer(a,b):return {'op':'Transfer','from':a,'to':b,'matter':1,'activation':0}
    rules=[]
    if family=='frozen6':pass
    elif family=='resource_cycle3':rules=[rule(0,kinds,[None]*n,shape,[transfer(0,1),transfer(1,2),transfer(2,0)])]
    elif family in ('async_ring4','oversize7'):
        rules=[rule(i,[kind],[None],[],[{'op':'AddState','node':0,'delta':1}]) for i,kind in enumerate(kinds)]
    elif family=='fragmentation4':
        rules=[rule(0,kinds,[0]*n,shape,[setstate(i,1) for i in range(n)]),rule(1,kinds,[1]*n,shape,[setstate(i,2) for i in range(n)]+[{'op':'DeleteEdge','account':0,'kind':3,'ends':[1,2]}])]
        for j,start in enumerate((0,2)):
            for state in (2,3):rules.append(rule(2+j*2+state-2,kinds[start:start+2],[state]*2,[[0,1]],[setstate(0,5-state),setstate(1,5-state)]))
    elif family=='templated_births':
        for node in nodes.values():node['kind']=99;node['matter']=3
        rules=[rule(0,[99],[0],[],[{'op':'CreateNode','account':0,'kind':100,'state':0},{'op':'CreateNode','account':0,'kind':101,'state':0},{'op':'CreateEdge','account':0,'kind':3,'ends':[1,2]},setstate(0,1)])]
    else:rules=[rule(0,kinds,[None]*n,shape,[{'op':'AddState','node':i,'delta':1} for i in range(n)])]
    e={'profile':'p00a-local-closed-v1','seed':seed,'rules':rules,'limits':{'max_candidates':10000,'max_bindings':100000,'max_nodes':128,'max_edges':256},
       'world':{'nodes':nodes,'edges':edges,'next_node':n,'next_edge':len(edges),'epoch':0,'dissipated':0,'matter_total':sum(x['matter']+1 for x in nodes.values())+len(edges),'activation_total':0,'next_event':0,'writers':{}}}
    if encoding=='relabeled':
        def mapping(n,offset):return {i:offset+17*((n-1-i+seed%n)%n) for i in range(n)}
        nm=mapping(n,1000);em=mapping(len(edges),10000)
        w=e['world'];w['nodes']={str(nm[int(i)]):node for i,node in nodes.items()}
        w['edges']={str(em[int(i)]):dict(edge,ends=[nm[j] for j in edge['ends']]) for i,edge in edges.items()}
        w['next_node']=max(map(int,w['nodes']))+1;w['next_edge']=max(map(int,w['edges']),default=-1)+1
        e['rules'].reverse()
    else:assert encoding=='identity'
    audit.validate(e['world']);return e

def verify_case(c,p,base):
    family=c['family'];seed=c['initial']['seed'];encoding=c['encoding'];cfg=p['families'][family]
    assert seed in p['seeds'] and encoding in p['encodings']
    assert c['initial']==initial(family,seed,encoding,p),'independent initial generator'
    assert c['scope']==cfg['scope'] and c['expected_ap']==cfg['expected_ap']
    assert len(c['frames'])==p['epochs']
    observed=detector.analyze(c['initial'],c['frames'],base)
    assert observed==c['detection'],'independent detector output'
    w=c['initial']['world'];members={int(i) for i in w['nodes']}
    expected_fp=detector.fingerprint(w,members) if len(members)<=6 else None
    assert expected_fp==c['initial_fingerprint'],'exact initial fingerprint'
    return observed

def audit_suite(suite):
    p=json.loads((ROOT/'docs/generalization_panel.json').read_text());base=json.loads(detector.REGISTRY.read_text())
    assert suite['schema']=='p00f-generalization-suite-v1' and suite['scientific_status']=='untested'
    assert suite['protocol']==p and suite['protocol_digest']==audit.digest(p)
    assert audit.digest(base)==p['base_protocol_digest']
    all_keys={(f,s,e) for f in p['families'] for s in p['seeds'] for e in p['encodings']}
    assert len(suite['cases'])==len(all_keys)==176
    assert {(c['family'],c['initial']['seed'],c['encoding']) for c in suite['cases']}==all_keys
    mismatches=[];invariance_failures=[];counts={};lookup={};scope_counts={};ambiguities=excluded=0
    for c in suite['cases']:
        observed=verify_case(c,p,base);family=c['family'];scope_counts[c['scope']]=scope_counts.get(c['scope'],0)+1
        row=counts.setdefault(family,{'cases':0,'expected':c['expected_ap'],'scope':c['scope'],'supported':0,'not_supported':0,'inconclusive':0,'excluded_large_samples':0,'ambiguous_links':0})
        row['cases']+=1;row[observed['active_persistence']]+=1
        x=sum(observed[k]['excluded_large'] for k in ('connected','interaction'));a=sum(observed[k]['ambiguous_links'] for k in ('connected','interaction'))
        row['excluded_large_samples']+=x;row['ambiguous_links']+=a;excluded+=x;ambiguities+=a
        if observed['active_persistence']!=c['expected_ap']:mismatches.append({'family':family,'seed':c['initial']['seed'],'encoding':c['encoding'],'expected':c['expected_ap'],'observed':observed['active_persistence']})
        lookup[(family,c['initial']['seed'],c['encoding'])]=c
    for f in p['families']:
        for seed in p['seeds']:
            a,b=lookup[(f,seed,'identity')],lookup[(f,seed,'relabeled')]
            if a['detection']['active_persistence']!=b['detection']['active_persistence'] or a['initial_fingerprint']!=b['initial_fingerprint']:
                invariance_failures.append({'family':f,'seed':seed})
    return {'execution_status':'complete','independent_replay':'pass','panel_accepted':not mismatches and not invariance_failures,
            'cases':176,'epochs':2112,'family_count':11,'matched_identifier_pairs':88,'outcomes':counts,'scope_counts':scope_counts,
            'registered_label_mismatches':mismatches,'identifier_invariance_failures':invariance_failures,'ambiguous_links':ambiguities,'excluded_large_samples':excluded,
            'detector_unchanged':True,'p00_admitted':False,'scientific_status':'untested'}
if __name__=='__main__':print(json.dumps(audit_suite(json.loads(Path(sys.argv[1]).read_text())),indent=2))
