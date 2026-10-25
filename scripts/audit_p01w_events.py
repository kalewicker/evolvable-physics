#!/usr/bin/env python3
"""P01w oracle copied unchanged from frozen P01q. Independent observation oracle over supplied committed before/after records.

No primary-extractor imports, candidate enumeration or transition application.
"""
import itertools

if not __debug__: raise RuntimeError('Event audit requires assertions')


def observe(events, worlds, detection):
    births={};deletions={};orphans={};funds=[];descendants=[];clean=[];edges_at_birth={}
    previous=-1
    for x in events:
        e,s=x['event'],x['sample'];assert e>previous;previous=e
        a,b=x['before'],x['after'];rule=x['rule'];ids=x['binding']
        tags=tuple(op['op'] for op in rule['ops'])
        added=set(b['nodes'])-set(a['nodes']);removed=set(a['nodes'])-set(b['nodes'])
        if tags==('CreateNode','CreateEdge','Transfer','Burn'):
            n=a['next_node'];p=ids[0]
            assert added=={str(n)} and not removed and n not in births
            assert b['next_node']==n+1
            node=b['nodes'][str(n)];account=a['nodes'][str(p)];after=b['nodes'][str(p)]
            assert node['kind']==rule['ops'][0]['kind'] and node['state']==rule['ops'][0]['state']
            assert node['matter']==node['activation']==1
            assert [after[k]-account[k] for k in ('matter','activation')]==[-3,-2]
            new_edges=set(b['edges'])-set(a['edges']);assert len(new_edges)==1
            edge=new_edges.pop();assert b['edges'][edge]==dict(ends=[p,n],kind=0,**{'class':'Structural'})
            edges_at_birth[n]=int(edge)
            births[n]=dict(node=n,birth_event=e,donor=p,birth_sample=s)
            if p in births:
                assert births[p]['birth_event']<e
                descendants.append(dict(event=e,node=n,donor=p,donor_birth_event=births[p]['birth_event'],sample=s))
        elif tags==('DeleteEdge','DeleteNode','Burn'):
            assert removed=={str(ids[1])} and not added
        else: assert not added and not removed
        if tags==('Transfer',) and rule['edges'][0]['class']=='Structural':
            p,n=ids;op=rule['ops'][0]
            assert p!=n
            for k in ('matter','activation'):
                assert b['nodes'][str(n)][k]-a['nodes'][str(n)][k]==op[k]
                assert a['nodes'][str(p)][k]-b['nodes'][str(p)][k]==op[k]
            if n in births:
                assert births[n]['birth_event']<e
                funds.append(dict(event=e,recipient=n,birth_event=births[n]['birth_event'],donor=p,
                                  matter=op['matter'],activation=op['activation'],sample=s))
        if tags in (('DeleteEdge',),('DeleteEdge','DeleteNode','Burn')):
            p,n=ids;assert p!=n
            lost=set(a['edges'])-set(b['edges']);assert len(lost)==1
            edge=lost.pop();assert a['edges'][edge]=={'class':'Structural','kind':0,'ends':[p,n]}
            old=a['nodes'][str(n)];before=a['nodes'][str(p)];after=b['nodes'][str(p)]
            recycle=len(tags)==3
            if recycle:
                assert not any(n in edge['ends'] for edge in b['edges'].values())
                assert [after[k]-before[k] for k in ('matter','activation')]==[old['matter']+2,old['activation']-1]
                if n in births:
                    assert n not in deletions and births[n]['birth_event']<e
                    deletions[n]=dict(node=n,birth_event=births[n]['birth_event'],deletion_event=e,recipient=p,sample=s,
                        returned_matter=old['matter']+2,returned_activation=old['activation'],burn=1)
            else:
                assert b['nodes'][str(n)]==old
                assert [after[k]-before[k] for k in ('matter','activation')]==[1,0]
            clean.append(dict(event=e,sample=s,form=7 if recycle else 6,edge=int(edge),donor=p,child=n,
                child_survives=not recycle,returned_matter=old['matter']+2 if recycle else 1,
                returned_activation=old['activation'] if recycle else 0,burn=int(recycle),
                donor_before=[before['matter'],before['activation']],donor_after=[after['matter'],after['activation']],
                child_before=[old['matter'],old['activation']]))
        for n in births:
            if str(n) in b['nodes'] and not any(v['class']=='Structural' and n in v['ends'] for v in b['edges'].values()):
                if n not in orphans:orphans[n]=dict(node=n,first_event=e,last_event=e,observed_events=0)
                orphans[n]['last_event']=e;orphans[n]['observed_events']+=1
    visible={}
    assert all(len(detection[k]['samples'])==len(worlds) for k in ('connected','interaction'))
    for sample,w in enumerate(worlds):
        for n,birth in births.items():
            if n in visible or sample<birth['birth_sample'] or str(n) not in w['nodes']:continue
            found={}
            for k in ('connected','interaction'):
                candidates=[v for v in detection[k]['samples'][sample] if n in v['members']]
                if candidates:found[k]=candidates[0]
            if len(found)==2:
                assert n not in deletions or sample<deletions[n]['sample']
                visible[n]=dict(node=n,sample=sample,**found)
    branches=[]
    # Index by parent/child creation identity; join only evidence in this cell.
    for G,gb in births.items():
        C=gb['donor']
        if C not in births:continue
        cb=births[C];P=cb['donor']
        if len({P,C,G})!=3:continue
        candidates=[f for f in funds if (f['donor'],f['recipient'],f['matter'])==(P,C,1)
                    and cb['birth_event']<f['event']<gb['birth_event']]
        for c in clean:
            if (c['donor'],c['child'],c['edge'])!=(C,G,edges_at_birth[G]) or c['event']<=gb['birth_event']:continue
            for r in clean:
                if (r['donor'],r['child'],r['edge'],r['form'])!=(P,C,edges_at_birth[C],7) or r['event']<=c['event']:continue
                segment=[x for x in events if cb['birth_event']<=x['event']<=r['event']]
                if any(str(edges_at_birth[C]) not in x['after']['edges'] for x in segment[:-1]):continue
                if any(str(edges_at_birth[G]) not in x['after']['edges'] for x in segment if gb['birth_event']<=x['event']<c['event']):continue
                for f1,f2 in itertools.combinations(candidates,2):
                    chosen=[cb['birth_event'],f1['event'],f2['event'],gb['birth_event'],c['event'],r['event']]
                    phases=[]
                    for x in segment:
                        if x['event'] in chosen:
                            balances=[]
                            for n in (P,C,G):
                                v=x['after']['nodes'].get(str(n));balances.append([v['matter'],v['activation']] if v else None)
                            phases.append(dict(event=x['event'],balances=balances))
                    first,last=segment[0]['before']['nodes'][str(P)],segment[-1]['after']['nodes'][str(P)]
                    branches.append(dict(roles=[P,C,G],cleanup_form=c['form'],events=chosen,
                        creation_edges=[edges_at_birth[C],edges_at_birth[G]],
                        intervening_events=[x['event'] for x in segment if x['event'] not in chosen],phase_balances=phases,
                        parent_net=[last['matter']-first['matter'],last['activation']-first['activation']],
                        total_burns=sum(op['amount'] for x in segment for op in x['rule']['ops'] if op['op']=='Burn')))
    branches.sort(key=lambda x:(x['roles'],x['cleanup_form'],x['events']))
    return dict(births=[births[k] for k in sorted(births)],recycling=[deletions[k] for k in sorted(deletions)],
        orphaning=[orphans[k] for k in sorted(orphans)],additional_structural_funding=funds,
        descendant_construction=descendants,visibility=[visible[k] for k in sorted(visible)],
        attached_funded_birth_ids=sorted(births),visible_birth_ids=sorted(visible),recycled_ids=sorted(deletions),
        visible_birth_recycle_ids=sorted(visible.keys() & deletions.keys()),cleanup_events=clean,ordered_branch=branches,
        ordered_branch_count=len({(*x['roles'],x['cleanup_form']) for x in branches}))
