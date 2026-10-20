#!/usr/bin/env python3
"""P01h: saved-record algebra and footprint diagnosis; no evolution or sampling."""
import collections
import contextlib
import json
import sys
from pathlib import Path
from unittest.mock import patch
import audit
import audit_p01g_receipts
import generator_v2
import pilot_reporting
import subprocess
from check_p01f_registration import template
from check_p01g_registration import load, sha
from diagnose_p01 import failed_gates

if not __debug__:raise RuntimeError('Read-only diagnosis requires assertions')
ROOT=Path(__file__).resolve().parents[1]
U64=2**64-1
KINDS=('funding','recycling','descendant_birth')


def forbidden(*args,**kwargs):raise RuntimeError('Read-only diagnosis forbids sampling, evolution and subprocesses')


@contextlib.contextmanager
def read_only():
    with contextlib.ExitStack() as stack:
        for module,name in [(audit,'execute'),(audit,'enumerate_candidates'),
                            (generator_v2,'construct'),(generator_v2,'draw'),
                            (pilot_reporting,'next_epoch'),(subprocess,'Popen'),(subprocess,'run')]:
            stack.enter_context(patch.object(module,name,forbidden))
        yield


def state_frozen(rules,kind,state):
    """No first unary state change is possible from this kind/state.

    This is a sufficient static invariance test, not a reachability simulator.
    False means unresolved; it does not establish that a change will occur.
    """
    for r in rules:
        form=template(r)
        if form not in (0,1):continue
        p=r['nodes'][0]
        if p['kind']==kind and p['state'] in (None,state):
            if form==1 or r['ops'][0]['value']!=state:return False
    return True


def compatibility(rules,birth,other):
    donor,child=birth['nodes'][0],birth['ops'][0]
    left,right=other['nodes'];reasons=[]
    if left['kind']!=donor['kind']:reasons.append('donor_kind')
    if right['kind']!=child['kind']:reasons.append('target_kind')
    if donor['state'] is not None and left['state'] not in (None,donor['state']) and state_frozen(rules,donor['kind'],donor['state']):
        reasons.append('invariant_donor_state')
    if right['state'] not in (None,child['state']) and state_frozen(rules,child['kind'],child['state']):
        reasons.append('invariant_child_state')
    return {'birth_rule':birth['id'],'other_rule':other['id'],'excluded_by':reasons,
            'not_excluded_by_kind_or_proved_state_invariance':not reasons}


def law_diagnosis(rules):
    forms={r['id']:template(r) for r in rules}
    groups={kind:[r for r in rules if forms[r['id']]==form and (form!=3 or r['edges'][0]['class']=='Structural')]
            for kind,form in [('birth',4),('funding',3),('recycling',7)]}
    pairs={kind:[compatibility(rules,b,r) for b in groups['birth'] for r in groups[kind]] for kind in ('funding','recycling')}
    return {'rule_forms':dict(collections.Counter(str(f) for f in forms.values())),
            'contact_transfer_rules':[r['id'] for r in rules if forms[r['id']]==3 and r['edges'][0]['class']=='Contact'],
            'birth_rules':[r['id'] for r in groups['birth']],
            'structural_funding_rules':[r['id'] for r in groups['funding']],
            'matter_funding_rules':[r['id'] for r in groups['funding'] if r['ops'][0]['matter']>0],
            'recycling_rules':[r['id'] for r in groups['recycling']],
            'birth_pair_compatibility':pairs,
            'birth_child_state_invariance':[{'birth_rule':r['id'],'kind':r['ops'][0]['kind'],
                'state':r['ops'][0]['state'],'proved_invariant':state_frozen(rules,r['ops'][0]['kind'],r['ops'][0]['state'])} for r in groups['birth']]}


def conditions(kind,rule,binding,w):
    """Closed-form applicability for the fixed v2 bundles, with no state edits."""
    failures=[]
    for slot,label in enumerate(('donor','target')[:len(binding)]):
        n=w['nodes'][str(binding[slot])];p=rule['nodes'][slot]
        if n['kind']!=p['kind']:failures.append(label+'_kind')
    for slot,label in enumerate(('donor','target')[:len(binding)]):
        n=w['nodes'][str(binding[slot])];p=rule['nodes'][slot]
        if p['state'] is not None and n['state']!=p['state']:failures.append(label+'_state')
    donor=w['nodes'][str(binding[0])]
    if kind=='descendant_birth':
        if donor['matter']<3:failures.append('matter')
        if donor['activation']<2:failures.append('activation')
        if max(w['next_node'],w['next_edge'],w['dissipated'])>=U64:failures.append('integer_bounds')
    else:
        target=w['nodes'][str(binding[1])]
        edge={'class':'Structural','kind':0,'ends':binding}
        matches=[key for key,e in w['edges'].items() if e==edge]
        assert len(matches)==1,'Exposure must have its ordered Structural edge'
        if kind=='recycling':
            if any(key!=matches[0] and binding[1] in e['ends'] for key,e in w['edges'].items()):failures.append('target_other_incidence')
            if donor['activation']+target['activation']<1:failures.append('activation')
            if donor['matter']+target['matter']+2>U64 or donor['activation']+target['activation']>U64 or w['dissipated']>=U64:
                failures.append('integer_bounds')
        else:
            assert kind=='funding'
            op=rule['ops'][0]
            if donor['matter']<op['matter']:failures.append('matter')
            if donor['activation']<op['activation']:failures.append('activation')
            if any(target[k]+op[k]>U64 for k in ('matter','activation')):failures.append('integer_bounds')
    return failures


def key(c):return c['rule'],tuple(c['binding'])
def conflict(a,b):return sorted((set(a['writes'])&(set(b['reads'])|set(b['writes']))) | (set(a['reads'])&set(b['writes'])))


def scheduler(frame):
    candidates=frame['candidates'];assert candidates==sorted(candidates,key=lambda c:(c['priority'],c['rule'],c['binding']))
    assert len({key(c) for c in candidates})==len(candidates)
    winners=[];losses={}
    for c in candidates:
        other=next((w for w in winners if conflict(c,w)),None)
        if other is None:winners.append(c)
        else:losses[key(c)]={'winner':key(other),'conflicting_keys':conflict(c,other)}
    assert sorted(winners,key=lambda c:(c['rule'],c['binding']))==[e['candidate'] for e in frame['events']], 'Recorded scheduler partition'
    events={key(e['candidate']):e['id'] for e in frame['events']}
    for row in losses.values():row['winner_event']=events[row['winner']]
    return {key(c):c for c in candidates},losses,events


def counter():return {'exposures':0,'first_blocker':collections.Counter(),'failed_conditions_overlapping':collections.Counter(),'examples':{}}


def exposure(count,kind,r,binding,w,candidates,losses,events,epoch):
    failed=conditions(kind,r,binding,w);ident=(r['id'],tuple(binding));present=ident in candidates
    assert present==(not failed), ('Algebra/candidate mismatch',kind,ident,failed)
    reason=failed[0] if failed else 'scheduler_conflict' if ident in losses else 'committed'
    if not failed:assert (ident in losses) != (ident in events)
    count['exposures']+=1;count['first_blocker'][reason]+=1;count['failed_conditions_overlapping'].update(failed)
    if reason not in count['examples']:
        count['examples'][reason]={'epoch':epoch,'rule':r['id'],'binding':binding,'failed_conditions':failed,
            **({'conflict':losses[ident]} if ident in losses else {})}
    return ident if present else None


def componentsize(w,node):
    group={node}
    while True:
        old=len(group)
        for e in w['edges'].values():
            if e['class']=='Structural' and group.intersection(e['ends']):group.update(e['ends'])
        if len(group)==old:return len(group)


def world_scope(initial,w,births,sample):
    audit.validate(w)
    contacts={k:e for k,e in initial['edges'].items() if e['class']=='Contact'}
    assert {k:e for k,e in w['edges'].items() if e['class']=='Contact'}==contacts
    for n in range(8):assert w['nodes'][str(n)]['kind']==initial['nodes'][str(n)]['kind']
    for key in w['nodes']:
        if int(key)>=8:assert int(key) in births and births[int(key)]['birth_sample']<=sample
    for e in w['edges'].values():
        if e['class']!='Structural':continue
        donor,child=e['ends'];assert e['kind']==0
        if child>=8:assert child in births and donor==births[child]['donor']
        else:assert donor<8 and any(c['ends']==e['ends'] for c in contacts.values())


def report_diagnosis(report,protocol):
    d=report['prefix_detection'];out={}
    for name in ('connected','interaction'):
        e=d[name];reasons=collections.Counter();supported=[]
        for i,t in enumerate(e['tracks']):
            failed=failed_gates(t,protocol);reasons.update(failed)
            if not failed:supported.append({'track':i,**t})
        assert e['supported']==bool(supported)
        out[name]={'supported':e['supported'],'tracks':len(e['tracks']),'supported_tracks':supported,
            'failed_track_conditions_overlapping':dict(reasons),'empty_samples':sum(not s for s in e['samples']),
            'proposal_observations':sum(len(s) for s in e['samples']),'excluded_large_observations':e['excluded_large']}
    return out


def cell_diagnosis(bundle,row,detector):
    directory=bundle/'runs'/str(row['slot']);request=load(directory/'request.json');initial=request['initial']['native']['world']
    receipt=load(directory/'python_audit/stdout.bin');report=load(directory/'rust_report/stdout.bin')
    rules=request['initial']['native']['rules'];forms={r['id']:template(r) for r in rules}
    grouped={k:[r for r in rules if forms[r['id']]==f and (f!=3 or r['edges'][0]['class']=='Structural')]
             for k,f in [('funding',3),('recycling',7),('descendant_birth',4)]}
    births={b['node']:b for b in receipt['prefix_observations']['births']};byevent={b['birth_event']:b for b in births.values()}
    history={};counts={k:counter() for k in KINDS};base=collections.Counter();events=collections.Counter();birth_visibility=[]
    before=initial;frames=0;contacts={k:e for k,e in initial['edges'].items() if e['class']=='Contact'}
    with (directory/'native/trace.jsonl').open('rb') as stream:
        for line in stream:
            frame=json.loads(line);native=frame['native_frame'];after=frame['state']['native']['world'];frames+=1
            assert frame['prepared']['world']==before and native['world']==after
            world_scope(initial,before,births,frames-1);world_scope(initial,after,births,frames)
            assert {k:e for k,e in after['edges'].items() if e['class']=='Contact'}==contacts
            for n in range(8):assert after['nodes'][str(n)]['kind']==initial['nodes'][str(n)]['kind']
            live=[int(i) for i in before['nodes'] if int(i)>=8]
            assert all(i in births and births[i]['birth_sample']<frames for i in live)
            base['live_newborn_pre_epochs']+=len(live)
            edges=[e for e in before['edges'].values() if e['class']=='Structural' and e['ends'][1]>=8]
            base['newborn_edge_epochs']+=len(edges)
            for e in edges:
                donor,child=e['ends'];assert e['kind']==0 and child in births and donor==births[child]['donor']
            base['newborn_without_incoming_edge_pre_epochs']+=sum(not any(e['ends'][1]==n for e in edges) for n in live)
            candidates,losses,selected=scheduler(native);covered={k:set() for k in KINDS}
            for kind in KINDS:
                bindings=[[n] for n in live] if kind=='descendant_birth' else [e['ends'] for e in edges]
                if not grouped[kind]:base[kind+'_base_opportunities_without_rule']+=len(bindings)
                for r in grouped[kind]:
                    for binding in bindings:
                        got=exposure(counts[kind],kind,r,binding,before,candidates,losses,selected,before['epoch'])
                        if got is not None:covered[kind].add(got)
                relevant={key(c) for c in native['candidates'] if
                    (kind=='descendant_birth' and forms[c['rule']]==4 and c['binding'][0]>=8) or
                    (kind=='recycling' and forms[c['rule']]==7 and c['binding'][1]>=8) or
                    (kind=='funding' and forms[c['rule']]==3 and rules[c['rule']]['edges'][0]['class']=='Structural' and c['binding'][1]>=8)}
                assert covered[kind]==relevant, 'Relevant candidate coverage'
            for n in live:
                node=before['nodes'][str(n)]
                h=history[n];assert node['kind']==h['kind']
                h['states'].add(node['state']);h['matter'].add(node['matter']);h['activation'].add(node['activation'])
                h['pre_epochs']+=1;h['construction_resources_pre_epochs']+=node['matter']>=3 and node['activation']>=2
            allocated=before['next_node']
            for event in native['events']:
                r=rules[event['candidate']['rule']];form=forms[r['id']];events[str(form)]+=1
                if form==4:
                    b=byevent[event['id']];assert b['node']==allocated and b['birth_sample']==frames
                    donor=event['candidate']['binding'][0];assert b['donor']==donor
                    node=after['nodes'][str(allocated)]
                    assert node=={'kind':r['ops'][0]['kind'],'state':r['ops'][0]['state'],'matter':1,'activation':1}
                    history[allocated]={'node':allocated,'birth_rule':r['id'],'donor':donor,'kind':node['kind'],
                        'birth_state':node['state'],'states':{node['state']},'matter':{1},'activation':{1},'pre_epochs':0,'construction_resources_pre_epochs':0}
                    connected=any(allocated in p['members'] for p in report['prefix_detection']['connected']['samples'][frames])
                    interaction=any(allocated in p['members'] for p in report['prefix_detection']['interaction']['samples'][frames])
                    size=componentsize(after,allocated)
                    assert connected==(detector['min_nodes']<=size<=detector['max_nodes'])
                    birth_visibility.append({'node':allocated,'birth_rule':r['id'],'birth_sample':frames,
                        'connected_at_birth':connected,'interaction_at_birth':interaction,
                        'connected_component_size_at_birth':size,
                        'ever_jointly_visible':allocated in receipt['visible_birth_ids']})
                    allocated+=1
            assert after['next_node']==allocated
            assert set(after['nodes'])-set(before['nodes'])=={str(n) for n in history if births[n]['birth_sample']==frames}
            assert not set(before['nodes'])-set(after['nodes']), 'Unexpected deletion contradicts original zero-death receipt'
            for n,h in history.items():
                node=after['nodes'][str(n)];assert node['kind']==h['kind']
                h['states'].add(node['state']);h['matter'].add(node['matter']);h['activation'].add(node['activation'])
            before=after
    assert frames==128 and sum(events.values())==row['observation']['observed_events']
    assert len(history)==receipt['prefix_counts']['births']==len(births)
    assert sum(v['ever_jointly_visible'] for v in birth_visibility)==receipt['prefix_counts']['visibility']
    for c in counts.values():assert sum(c['first_blocker'].values())==c['exposures']
    for h in history.values():
        for field in ('states','matter','activation'):h[field]=sorted(h[field])
    return {'slot':row['slot'],'proposal':row['proposal'],'initial_state':row['initial_state'],
        'full_horizon_ap':row['observation']['full_horizon_ap'],'epochs':frames,'event_forms':dict(events),
        'base_opportunities':dict(base),'mechanism_exposures':counts,
        'newborn_histories':list(history.values()),'birth_visibility':birth_visibility,
        'estimators':report_diagnosis(report,detector),'rules':rules,'law_digest':row['law_digest']}


def write(path,value):
    with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')


def run(bundle,out):
    out.mkdir(parents=True,exist_ok=False)
    manifest={'schema':'p01h-read-only-manifest-v1','execution_status':'running','processed_cells':0,
              'new_world_runs':0,'sampler_calls':0,'transition_applications':0,'scientific_status':'untested'}
    def save():(out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    save()
    try:
        sources=['scripts/diagnose_p01g.py','scripts/test_diagnose_p01g.py','docs/p01h_analysis_plan.md']
        manifest['source_files']={name:sha(ROOT/name) for name in sources}
        for name in sources:
            dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
        original=audit_p01g_receipts.verify(bundle);write(out/'input_receipt_audit.json',original)
        assert original['engineering_gate_pass'] and not original['mechanism_gate_pass']
        for name,h in load(bundle/'source/docs/p01g_execution_freeze.json')['files'].items():
            assert sha(ROOT/name)==h, 'Imported/frozen source changed: '+name
        source=load(bundle/'manifest.json');detector=load(bundle/'source/docs/detector_protocol.json')
        rows=[];laws={};totals=collections.Counter();events=collections.Counter()
        combined={k:counter() for k in KINDS}
        for row in source['rows']:
            cell=cell_diagnosis(bundle,row,detector);rules=cell.pop('rules');rows.append(cell)
            totals.update(cell['base_opportunities']);totals['epochs']+=cell['epochs'];events.update(cell['event_forms'])
            p=str(row['proposal'])
            if p not in laws:laws[p]={'proposal':row['proposal'],'law_digest':row['law_digest'],**law_diagnosis(rules),'cells':[]}
            assert laws[p]['law_digest']==row['law_digest'];laws[p]['cells'].append(row['slot'])
            for kind,c in cell['mechanism_exposures'].items():
                agg=combined[kind];agg['exposures']+=c['exposures'];agg['first_blocker'].update(c['first_blocker'])
                agg['failed_conditions_overlapping'].update(c['failed_conditions_overlapping'])
                for reason,example in c['examples'].items():agg['examples'].setdefault(reason,{'slot':row['slot'],**example})
            manifest['processed_cells']=len(rows);save()
        assert len(rows)==64 and len(laws)==16 and totals['epochs']==8192 and sum(events.values())==7453
        for law in laws.values():
            selected=[c for c in rows if c['proposal']==law['proposal']]
            law['newborns']=sum(len(c['newborn_histories']) for c in selected)
            law['mechanism_exposures']={kind:{'exposures':sum(c['mechanism_exposures'][kind]['exposures'] for c in selected),
                'first_blocker':dict(sum((collections.Counter(c['mechanism_exposures'][kind]['first_blocker']) for c in selected),collections.Counter()))}
                for kind in KINDS}
        rule_census=sum((collections.Counter(law['rule_forms']) for law in laws.values()),collections.Counter())
        assert sum(rule_census.values())==128
        histories=[h for c in rows for h in c['newborn_histories']];visibility=[v for c in rows for v in c['birth_visibility']]
        assert len(histories)==142 and sum(v['ever_jointly_visible'] for v in visibility)==104
        findings={'schema':'p01h-read-only-findings-v1','input_manifest_sha256':sha(bundle/'manifest.json'),
            'input_seal_sha256':sha(bundle/'seal.json'),'analysis_plan_sha256':sha(ROOT/'docs/p01h_analysis_plan.md'),
            'law_cells':16,'trajectory_cells':64,'totals':dict(totals),'committed_event_forms':dict(events),
            'rule_forms_across_16_tables':dict(rule_census),
            'mechanism_exposures':combined,'newborns':len(histories),
            'newborn_matter_values':sorted({m for h in histories for m in h['matter']}),
            'newborn_activation_values':sorted({a for h in histories for a in h['activation']}),
            'newborns_observed_state_change':sum(len(h['states'])>1 for h in histories),
            'newborns_with_construction_resources':sum(h['construction_resources_pre_epochs']>0 for h in histories),
            'birth_visibility_categories':dict(collections.Counter(f'connected={v["connected_at_birth"]},interaction={v["interaction_at_birth"]},ever_joint={v["ever_jointly_visible"]}' for v in visibility)),
            'inconclusive_slots':[c['slot'] for c in rows if c['full_horizon_ap']=='inconclusive'],
            'original_mechanism_gate_pass':False,'new_world_runs':0,'sampler_calls':0,'transition_applications':0,
            'scientific_status':'untested','e01_authorized':False}
        write(out/'findings.json',findings);write(out/'law_diagnoses.json',list(laws.values()));write(out/'cell_diagnoses.json',rows)
        write(out/'inconclusive_cases.json',[c for c in rows if c['full_horizon_ap']=='inconclusive'])
        manifest.update(execution_status='complete',input_manifest_sha256=findings['input_manifest_sha256'],input_seal_sha256=findings['input_seal_sha256'])
    except BaseException as error:manifest.update(execution_status='failed',error=repr(error));raise
    finally:
        save();write(out/'checksums.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'checksums.json'})
    return findings

if __name__=='__main__':
    with read_only():result=run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
    print(json.dumps(result,indent=2))
