"""Invented descriptors/mock stages only; never interprets or samples a world."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import audit
import audit_single_pass
import pilot_reporting
import p01q_cell as cell
import audit_p01q_events as independent
import p01q_campaign as runner
import audit_p01q_receipts as receipts

def rule(form,route='Structural'):
    node={'kind':1,'state':None}
    edge={'class':route,'kind':0,'ends':[0,1]}
    ops={0:[{'op':'SetState','node':0,'value':0}],
         4:[{'op':'CreateNode','account':0,'kind':2,'state':0},
            {'op':'CreateEdge','account':0,'kind':0,'ends':[0,1]},
            {'op':'Transfer','from':0,'to':1,'matter':1,'activation':1},{'op':'Burn','node':0,'amount':1}],
         3:[{'op':'Transfer','from':0,'to':1,'matter':1,'activation':1}],
         7:[{'op':'DeleteEdge','account':0,'kind':0,'ends':[0,1]},
            {'op':'DeleteNode','node':1,'recipient':0},{'op':'Burn','node':0,'amount':1}],
         6:[{'op':'DeleteEdge','account':0,'kind':0,'ends':[0,1]}]}
    return {'id':0,'nodes':[node]*(1 if form in (0,4) else 2),'edges':[] if form in (0,4) else [edge],
            'absent':[],'ops':ops[form]}


def node(m,a,kind=1):return {'kind':kind,'state':0,'matter':m,'activation':a}
def initial():return {'nodes':{'42':node(8,8)},'edges':{},'next_node':100}
def birth(before,donor):
    # Directly authored record, not a kernel operation or interpreter.
    after=copy.deepcopy(before);child=before['next_node'];after['next_node']+=1
    after['nodes'][str(donor)]['matter']-=3;after['nodes'][str(donor)]['activation']-=2
    after['nodes'][str(child)]=node(1,1,2)
    after['edges'][str(200+child)]={'class':'Structural','kind':0,'ends':[donor,child]}
    return after


def branch(form=7, extra=False):
    """Literal expected records, with arithmetic, not calls into any interpreter."""
    events=[];worlds=[initial()];worlds[0]['nodes']['42']['kind']=2
    def add(form,ids,after):
        events.append(dict(rule=rule(form),binding=ids,event=10+len(events),sample=len(worlds),before=worlds[-1],after=after))
        worlds.append(after)
    add(4,[42],birth(worlds[-1],42))
    for _ in range(2):
        a=copy.deepcopy(worlds[-1])
        for k in ('matter','activation'):a['nodes']['42'][k]-=1;a['nodes']['100'][k]+=1
        add(3,[42,100],a)
    if extra:
        a=copy.deepcopy(worlds[-1]);a['nodes']['42']['state']=1;rr=rule(0);rr['ops'][0]['value']=1
        add(0,[42],a);events[-1]['rule']=rr
    add(4,[100],birth(worlds[-1],100))
    a=copy.deepcopy(worlds[-1]);del a['edges']['301']
    if form==7:del a['nodes']['101'];a['nodes']['100']['matter']+=3
    else:a['nodes']['100']['matter']+=1
    add(form,[100,101],a)
    a=copy.deepcopy(worlds[-1]);old=a['nodes'].pop('100');del a['edges']['300']
    a['nodes']['42']['matter']+=old['matter']+2;a['nodes']['42']['activation']+=old['activation']-1
    add(7,[42,100],a)
    samples=[[dict(members=[int(n) for n in w['nodes']])] for w in worlds]
    detection={k:dict(samples=copy.deepcopy(samples)) for k in ('connected','interaction')}
    return events,worlds,detection


def receipt(obs,complete=True):
    counts={k:len(obs[k]) for k in ('births','recycling','visibility','additional_structural_funding',
        'descendant_construction','orphaning','visible_birth_recycle_ids','cleanup_events')}
    counts['ordered_branch']=obs['ordered_branch_count']
    return dict(independent_events_pass=True,prefix_observations=obs,prefix_counts=counts,
                full_horizon_counts=counts if complete else None,full_horizon_verified=complete,
                full_horizon_ap='not_supported' if complete else None)


class ForbiddenExecution(unittest.TestCase):
    def setUp(self):
        real_sha=hashlib.sha256
        def file_only(data=b'', *args, **kwargs):
            if data.startswith(b'p01-generator-v'):raise AssertionError('keyed generation forbidden')
            return real_sha(data,*args,**kwargs)
        guard=patch.object(hashlib,'sha256',side_effect=file_only);guard.start();self.addCleanup(guard.stop)
        for module,name in [(audit,'execute'),(audit,'enumerate_candidates'),(pilot_reporting,'next_epoch'),
                            (pilot_reporting,'verify'),(audit_single_pass,'verify'),(runner.subprocess,'Popen')]:
            p=patch.object(module,name,side_effect=AssertionError('unadmitted execution'));p.start();self.addCleanup(p.stop)


class ObservationControls(ForbiddenExecution):
    def test_reused_body_same_kind_distinct_nodes_and_cleanup7(self):
        e,w,d=branch();obs=cell.observations(e,w,d)
        self.assertEqual(obs['ordered_branch_count'],1)
        b=obs['ordered_branch'][0]
        self.assertEqual(b['roles'],[42,100,101]);self.assertEqual(b['parent_net'],[0,-4])
        self.assertEqual(b['total_burns'],4)
        self.assertEqual(len(obs['additional_structural_funding']),2)
        self.assertEqual(obs['descendant_construction'][0]['donor_birth_event'],10)
        receipts.validate_observations(receipt(obs))
    def test_cleanup6_preserves_orphan_and_spends_activation(self):
        e,w,d=branch(6);obs=cell.observations(e,w,d)
        self.assertIn('101',w[-1]['nodes']);self.assertEqual(obs['ordered_branch'][0]['parent_net'],[-2,-4])
        self.assertEqual(obs['ordered_branch'][0]['total_burns'],3)
        self.assertEqual(obs['recycled_ids'],[100]);self.assertEqual(obs['orphaning'][0]['node'],101)
    def test_availability_and_initial_nodes_are_not_births(self):
        e,w,d=branch();self.assertEqual(cell.observations([],w[:1],{k:{'samples':[[]]} for k in d})['births'],[])
        self.assertNotIn(42,cell.observations(e,w,d)['attached_funded_birth_ids'])
    def test_birth_internal_transfer_not_additional_funding(self):
        e,w,d=branch();out=cell.observations(e[:1],w[:2],{k:{'samples':v['samples'][:2]} for k,v in d.items()})
        self.assertEqual(out['additional_structural_funding'],[])
    def test_birth_must_be_funded_attached_and_paid(self):
        for kind in ('unfunded','unattached','unpaid'):
            e,w,d=branch();x=e[0]
            if kind=='unfunded':x['after']['nodes']['100']['matter']=0
            elif kind=='unattached':x['after']['edges']={}
            else:x['after']['nodes']['42']['matter']+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):cell.observations(e,w,d)
    def test_visibility_needs_both_proposals_same_live_sample(self):
        e,w,d=branch();d['interaction']['samples']=[[] for _ in w]
        self.assertEqual(cell.observations(e,w,d)['visible_birth_ids'],[])
        e,w,d=branch()
        for k in d:d[k]['samples']=[[] for _ in w]
        d['connected']['samples'][1]=[dict(members=[100])];d['interaction']['samples'][2]=[dict(members=[100])]
        self.assertEqual(cell.observations(e,w,d)['visibility'],[])
    def test_funding_donor_and_same_node_cannot_be_pooled(self):
        e,w,d=branch();obs=cell.observations(e,w,d)
        altered=copy.deepcopy(obs);altered['additional_structural_funding'][0]['recipient']=101
        with self.assertRaises(AssertionError):receipts.validate_observations(receipt(altered))
        altered=copy.deepcopy(obs);altered['descendant_construction'][0]['donor']=42
        with self.assertRaises(AssertionError):receipts.validate_observations(receipt(altered))
    def test_wrong_edge_nonleaf_and_refund_rejected(self):
        for kind in ('direction','missing','nonleaf','refund'):
            e,w,d=branch();x=e[-2]
            if kind=='direction':x['before']['edges']['301']['ends'].reverse()
            elif kind=='missing':del x['before']['edges']['301']
            elif kind=='nonleaf':x['after']['edges']['777']={'class':'Structural','kind':0,'ends':[101,42]}
            else:x['after']['nodes']['100']['activation']+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):cell.observations(e,w,d)
    def test_order_and_unrelated_intervening_events(self):
        e,w,d=branch(extra=True);o=cell.observations(e,w,d)
        self.assertEqual(o['ordered_branch'][0]['intervening_events'],[13])
        e[1]['event']=e[0]['event']
        with self.assertRaises(AssertionError):cell.observations(e,w,d)
    def test_censored_and_disagreement_keep_null_or_inconclusive(self):
        o=cell.observations(*branch());r=receipt(o,False);receipts.validate_observations(r)
        r['full_horizon_counts']=r['prefix_counts']
        with self.assertRaises(AssertionError):receipts.validate_observations(r)
        r=receipt(o);r['full_horizon_ap']='inconclusive';receipts.validate_observations(r)
        self.assertEqual(r['full_horizon_ap'],'inconclusive')
    def test_independent_oracle_and_receipt_mutations(self):
        e,w,d=branch();o=cell.observations(e,w,d)
        with patch.object(cell,'branch_records',return_value=[]):
            with self.assertRaisesRegex(AssertionError,'independent'):cell.observations(e,w,d)
        for field in ('events','roles','creation_edges'):
            a=copy.deepcopy(o);a['ordered_branch'][0][field][0]+=1
            with self.subTest(field=field),self.assertRaises((AssertionError,KeyError)):receipts.validate_observations(receipt(a))
        a=copy.deepcopy(o);a['cleanup_events'][0]['returned_matter']+=1
        with self.assertRaises(AssertionError):receipts.validate_observations(receipt(a))


class PipelineControls(ForbiddenExecution):
    def setUp(self):
        super().setUp();self.p=runner.load(runner.ROOT/'docs/p01q_protocol.json')
        self.u=dict(wall_seconds=1,total_process_cpu_seconds=1,artifact_bytes=100)
    def rows(self):
        return [{**p,'status':'pending','stages':{}} for p in runner.planned_slots(self.p)]
    def full(self):
        rows=self.rows()
        for r in rows:r.update(status='complete',law_digest=f'{r["proposal"]:064x}',stages={n:dict(status='exited') for n in runner.STAGES},
            observation=dict(full_horizon_verified=True,full_horizon_ap='not_supported',attached_funded_birth_ids=[],visible_birth_ids=[],recycled_ids=[],prefix_counts={},full_horizon_counts={}))
        return rows
    def test_negative_full_panel_and_duplicates_and_no_pooling(self):
        rows=self.full();a=runner.summarize(self.p,rows,self.u,'complete')
        self.assertTrue(a['engineering_gate_pass']);self.assertFalse(a['continuation_gate_pass']);self.assertEqual(len(a['laws']),32)
        for i in (0,4):rows[i]['observation'].update(attached_funded_birth_ids=[8],visible_birth_ids=[8],recycled_ids=[8])
        self.assertTrue(runner.summarize(self.p,rows,self.u,'complete')['continuation_gate_pass'])
        for r in rows:r['law_digest']='a'*64
        self.assertFalse(runner.summarize(self.p,rows,self.u,'complete')['mechanism_gate_pass'])
        rows=self.full();rows[0]['observation'].update(attached_funded_birth_ids=[8],visible_birth_ids=[8]);rows[1]['observation'].update(attached_funded_birth_ids=[8],recycled_ids=[8])
        self.assertEqual(runner.summarize(self.p,rows,self.u,'complete')['distinct_tables_with_same_trajectory_visible_birth_recycle_loop'],0)
    def test_reservation_watchdog_and_missingness(self):
        self.assertTrue(runner.launch_fits(self.p,self.u,'native'))
        for field,value in [('wall_seconds',1190),('total_process_cpu_seconds',590),('artifact_bytes',2147483648-67108864)]:
            with self.subTest(field=field):self.assertFalse(runner.launch_fits(self.p,dict(self.u,**{field:value}),'native'))
        m={'rows':self.rows()};m['rows'][0].update(status='reported',stages={'native':{'status':'wall_budget_exceeded'}})
        runner.terminalize(m,'watchdog');a=runner.summarize(self.p,m['rows'],self.u,'failed')
        self.assertEqual(a['status_counts'],{'failed':1,'unstarted':127})
        self.assertTrue(all(x['full_horizon_counts'] is None for law in a['laws'] for x in law['initial_states']))
    def test_saved_input_hash_types_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);base=root/'artifacts/p01o-001/runs/0';inputs={}
            for lang,value in [('rust_generation',{'value':1}),('python_generation',{'value':True})]:
                path=base/lang/'stdout.bin';path.parent.mkdir(parents=True);path.write_text(json.dumps(value));inputs[str(path.relative_to(root))]=runner.sha(path)
            (root/'docs').mkdir();runner.atomic_json(root/'docs/p01q_registration_freeze.json',dict(inputs=inputs))
            with self.assertRaisesRegex(AssertionError,'streams disagree'):cell.saved_initial(root,0,self.p)
            (base/'python_generation/stdout.bin').write_text('{}')
            with self.assertRaisesRegex(AssertionError,'identity'):cell.saved_initial(root,0,self.p)
    def test_all128_mock_pipeline_and_stage_failure_stop(self):
        for fail in (False,True):
            with tempfile.TemporaryDirectory() as td:
                out=Path(td);m={'rows':self.rows()};calls=[]
                def saved(source,slot,p):return dict(slot=slot,proposal=6000+slot//4,initial=slot%4),dict(native=dict(rules=[dict(id=1,label=slot//4)]))
                def stage(row,name,command):
                    calls.append((row['slot'],name));path=out/'runs'/str(row['slot'])/name;path.mkdir(parents=True)
                    row['stages'][name]={'status':'exited'}
                    if fail and row['slot']==1 and name=='native':raise runner.ReservationStop('mock stage failure')
                    if name=='python_audit':
                        proof={**{k:row[k] for k in ('slot','proposal','initial_state','law_digest')},'status':'complete',
                            'full_horizon_verified':True,'attached_funded_birth_ids':[],'visible_birth_ids':[],'recycled_ids':[],
                            'full_horizon_ap':'inconclusive','observed_epochs':128,'observed_events':0,'worker_status':'complete',
                            'prefix_counts':{},'full_horizon_counts':{},'independent_events_pass':True}
                        runner.atomic_json(path/'stdout.bin',proof)
                    return path
                with patch.object(cell,'saved_initial',side_effect=saved):
                    if fail:
                        with self.assertRaises(runner.ReservationStop):runner.execute_pipeline(out,self.p,m,stage,lambda:None)
                        runner.terminalize(m,'mock reserve',True)
                        self.assertEqual(m['rows'][0]['status'],'complete');self.assertEqual(m['rows'][2]['status'],'unstarted')
                        self.assertEqual(len(calls),4)
                    else:
                        runner.execute_pipeline(out,self.p,m,stage,lambda:None)
                        self.assertEqual(len(calls),384);self.assertTrue(all(r['status']=='complete' for r in m['rows']))
                        self.assertTrue(all(r['observation']['full_horizon_ap']=='inconclusive' for r in m['rows']))
    def test_no_execution_without_admission_and_seal_failure_retained(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaises(FileNotFoundError):runner.check_execution(root)
            out=root/'attempt'
            def fail():out.mkdir();raise RuntimeError('mock seal failure')
            with patch.object(runner.sys,'argv',['runner',str(out)]),patch.object(runner,'run',side_effect=fail):
                with self.assertRaises(RuntimeError):runner.main()
            self.assertEqual(runner.load(out/'terminal_failure.json')['integrity'],'unsealed')
            before=(out/'terminal_failure.json').read_bytes()
            with patch.object(runner.sys,'argv',['runner',str(out)]),patch.object(runner,'run',side_effect=RuntimeError('existing')):
                with self.assertRaises(RuntimeError):runner.main()
            self.assertEqual(before,(out/'terminal_failure.json').read_bytes())

    def test_complete_unstarted_receipt_bundle_and_inventory_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);source=out/'source';(source/'docs').mkdir(parents=True);(out/'bin').mkdir()
            runner.atomic_json(source/'docs/p01q_protocol.json',self.p)
            reg={'files':{'docs/p01q_protocol.json':runner.sha(source/'docs/p01q_protocol.json')},'inputs':{},'prior_public_receipts':{}}
            runner.atomic_json(source/'docs/p01q_registration_freeze.json',reg)
            freeze={'files':reg['files'],'dependencies':{},'binaries':{}}
            runner.atomic_json(source/'docs/p01q_execution_freeze.json',freeze)
            adm=dict(schema='p01q-execution-admission-v1',world_execution_admitted=True,keyed_evaluation_admitted=False,e01_authorized=False,fixed_slots=128,admitted_output='artifacts/p01q-001',
                **{k+'_sha256':runner.sha(source/'docs'/('p01q_'+k+'.json')) for k in ('protocol','registration_freeze','execution_freeze')})
            runner.atomic_json(source/'docs/p01q_execution_admission.json',adm)
            runner.atomic_json(out/'dependency_inventory.json',{})
            m=dict(schema='p01q-campaign-manifest-v1',execution_status='budget_stopped',rows=self.rows(),scientific_status='untested',e01_authorized=False,
                **{k+'_sha256':runner.sha(source/'docs'/('p01q_'+k+'.json')) for k in ('protocol','registration_freeze','execution_freeze','execution_admission')})
            runner.terminalize(m,'invented reservation stop',True)
            m['assessment']=runner.summarize(self.p,m['rows'],dict(self.u,artifact_bytes=0),'budget_stopped')
            runner.atomic_json(out/'manifest.json',m);runner.atomic_json(out/'assessment.json',m['assessment'])
            inventory={str(p.relative_to(out)):runner.sha(p) for p in out.rglob('*') if p.is_file()}
            runner.atomic_json(out/'checksums.json',inventory)
            seal=dict(schema='p01q-campaign-seal-v1',manifest_sha256=runner.sha(out/'manifest.json'),checksums_sha256=runner.sha(out/'checksums.json'),
                resource_usage=dict(self.u),overshoot=[],engineering_gate_pass=False,mechanism_gate_pass=False,continuation_gate_pass=False,
                decision='engineering_failure_or_incomplete',scientific_status='untested')
            base=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
            while True:
                data=json.dumps(seal,sort_keys=True,indent=2)+'\n';n=base+len(data.encode())
                if seal['resource_usage']['artifact_bytes']==n:break
                seal['resource_usage']['artifact_bytes']=n
            runner.atomic_json(out/'seal.json',seal)
            result=receipts.verify(out)
            self.assertEqual(result['verified_trajectory_receipts'],0);self.assertFalse(result['engineering_gate_pass'])
            (out/'extra').write_text('unlisted')
            with self.assertRaises(AssertionError):receipts.verify(out)

if __name__=='__main__':unittest.main()
