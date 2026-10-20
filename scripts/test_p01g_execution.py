"""Invented event records and bookkeeping only; no sampled law or transition."""
import copy
import json
import subprocess
import sys
import unittest
import check_p01g_registration as registration
import p01g_campaign as runner
import p01g_cell as cell


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


class EventObservations(unittest.TestCase):
    def test_birth_funding_descendant_and_same_child_recycle_proofs(self):
        records=cell.empty_records();before=initial();after=birth(before,42)
        cell.observe_event(rule(4),[42],10,1,before,after,records)
        self.assertFalse(records['additional_structural_funding'])
        worlds=[before,after]
        for event,sample in ((11,2),(12,3)):
            before=after;after=copy.deepcopy(before)
            for key in ('matter','activation'):
                after['nodes']['42'][key]-=1;after['nodes']['100'][key]+=1
            cell.observe_event(rule(3),[42,100],event,sample,before,after,records);worlds.append(after)
        before=after;after=birth(before,100)
        cell.observe_event(rule(4),[100],13,4,before,after,records);worlds.append(after)
        before=after;after=copy.deepcopy(before)
        del after['nodes']['101'];del after['edges']['301']
        after['nodes']['100']['matter']+=3
        cell.observe_event(rule(7),[100,101],14,5,before,after,records);worlds.append(after)
        self.assertEqual(len(records['additional_structural_funding']),2)
        self.assertEqual(records['descendant_construction'][0]['donor_birth_event'],10)
        self.assertEqual(records['recycling'][101]['birth_event'],13)
        samples=[[]]+[[{'members':[42,100],'features':{}}] for _ in range(5)]
        samples[4]=[{'members':[100,101],'features':{}}]
        detection={name:{'samples':copy.deepcopy(samples)} for name in ('connected','interaction')}
        visible=cell.visibility(records,worlds,detection)
        self.assertEqual(visible[101]['sample'],4)
        self.assertEqual(set(visible)&set(records['recycling']),{101})

    def test_unfunded_and_unattached_birth_rejected(self):
        before=initial();after=birth(before,42)
        after['nodes']['100']['activation']=0
        with self.assertRaisesRegex(AssertionError,'Unfunded'):
            cell.observe_event(rule(4),[42],10,1,before,after,cell.empty_records())
        after=birth(before,42);after['edges']={}
        with self.assertRaisesRegex(AssertionError,'Unattached'):
            cell.observe_event(rule(4),[42],10,1,before,after,cell.empty_records())

    def test_contact_transfer_not_structural_funding(self):
        before=initial();after=birth(before,42);records=cell.empty_records()
        cell.observe_event(rule(4),[42],10,1,before,after,records)
        before=after;after=copy.deepcopy(before)
        for key in ('matter','activation'):
            after['nodes']['42'][key]-=1;after['nodes']['100'][key]+=1
        cell.observe_event(rule(3,'Contact'),[42,100],11,2,before,after,records)
        self.assertFalse(records['additional_structural_funding'])

    def test_synthetic_preexisting_node_not_a_birth_or_recycle(self):
        before=birth(initial(),42);after=copy.deepcopy(before);records=cell.empty_records()
        del after['nodes']['100'];del after['edges']['300'];after['nodes']['42']['matter']+=3
        cell.observe_event(rule(7),[42,100],11,1,before,after,records)
        self.assertFalse(records['recycling'])

    def test_estimator_disagreement_does_not_supply_visibility(self):
        before=initial();after=birth(before,42);records=cell.empty_records()
        cell.observe_event(rule(4),[42],10,1,before,after,records)
        d={'connected':{'samples':[[],[{'members':[42,100]}]]},'interaction':{'samples':[[],[]]}}
        self.assertEqual(cell.visibility(records,[before,after],d),{})

    def test_orphan_observations_compressed_without_inflating_unique_nodes(self):
        before=initial();after=birth(before,42);records=cell.empty_records()
        cell.observe_event(rule(4),[42],10,1,before,after,records)
        before=after;after=copy.deepcopy(before);after['edges']={}
        cell.observe_event(rule(6),[42,100],11,2,before,after,records)
        cell.observe_event(rule(0),[42],12,3,after,after,records)
        self.assertEqual(records['orphaning'][100],{'node':100,'first_event':11,'last_event':12,'observed_events':2})


class CampaignBookkeeping(unittest.TestCase):
    def setUp(self):
        self.p=registration.load(registration.ROOT/'docs/p01g_protocol.json')
        self.usage={'wall_seconds':1,'total_process_cpu_seconds':1,'artifact_bytes':100}
        self.rows=[]
        for plan in registration.planned_slots(self.p):
            counts={k:0 for k in ('births','recycling','visibility','additional_structural_funding',
                    'descendant_construction','orphaning','visible_birth_recycle_ids')}
            self.rows.append({**plan,'law_digest':f'{plan["proposal"]:064x}','status':'complete',
                'stages':{name:{'status':'exited','child_cpu_seconds':.01,'wall_seconds':.02} for name in runner.STAGES},
                'observation':{'full_horizon_verified':True,'full_horizon_ap':'not_supported',
                    'attached_funded_birth_ids':[],'visible_birth_ids':[],'recycled_ids':[],
                    'prefix_counts':counts,'full_horizon_counts':counts}})

    def test_negative_engineering_success_retained_as_mechanism_failure(self):
        result=runner.summarize(self.p,self.rows,self.usage,'complete')
        self.assertTrue(result['engineering_gate_pass'])
        self.assertFalse(result['mechanism_gate_pass'])
        self.assertEqual(result['decision'],'engineering_pass_mechanism_fail')
        self.assertEqual(len(result['laws']),16)

    def test_positive_gate_needs_two_distinct_tables_and_full_completion(self):
        for i in (0,4):
            self.rows[i]['observation'].update(attached_funded_birth_ids=[8],visible_birth_ids=[8],recycled_ids=[8])
        self.assertTrue(runner.summarize(self.p,self.rows,self.usage,'complete')['continuation_gate_pass'])
        self.rows[4]['status']='censored'
        self.rows[4]['observation'].update(full_horizon_verified=False,full_horizon_ap=None,full_horizon_counts=None)
        r=runner.summarize(self.p,self.rows,self.usage,'complete')
        self.assertFalse(r['engineering_gate_pass']);self.assertFalse(r['mechanism_gate_pass'])
        self.assertIsNone(r['laws'][1]['initial_states'][0]['full_horizon_counts'])

    def test_missing_cells_have_null_endpoints_and_all_denominators(self):
        for row in self.rows:
            row['status']='unstarted';row['stages']={};row.pop('observation');row.pop('law_digest')
        r=runner.summarize(self.p,self.rows,self.usage,'budget_stopped')
        self.assertEqual(r['status_counts'],{'unstarted':64})
        self.assertFalse(r['engineering_gate_pass'])
        self.assertEqual(len(r['laws']),16)
        self.assertTrue(all(c['full_horizon_counts'] is None for law in r['laws'] for c in law['initial_states']))

    def test_budget_reservation_and_native_stream_split(self):
        self.assertTrue(runner.launch_fits(self.p,self.usage,'python_audit'))
        u=dict(self.usage,total_process_cpu_seconds=236)
        self.assertFalse(runner.launch_fits(self.p,u,'python_audit'))
        u=dict(self.usage,artifact_bytes=self.p['campaign']['artifact_bytes']-self.p['campaign']['metadata_reserve_bytes'])
        self.assertFalse(runner.launch_fits(self.p,u,'native'))
        self.assertEqual(runner.stream_limits(self.p,'native')['stdout_bytes'],4194304)
        self.assertEqual(runner.stream_limits(self.p,'native')['stderr_bytes'],262144)

    def test_cost_summary_independent_of_json_dictionary_order(self):
        for name,cpu in zip(runner.STAGES,(.1,.2,.3,1e-16)):
            self.rows[0]['stages'][name]['child_cpu_seconds']=cpu
        before=runner.summarize(self.p,self.rows,self.usage,'complete')
        after=runner.summarize(self.p,json.loads(json.dumps(self.rows,sort_keys=True)),self.usage,'complete')
        self.assertEqual(before,after)

    def test_optimized_python_rejected(self):
        for script in ('p01g_cell.py','p01g_campaign.py','audit_p01g_receipts.py'):
            p=subprocess.run([sys.executable,'-O',str(registration.ROOT/'scripts'/script)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('requires assertions',p.stderr)

if __name__=='__main__':unittest.main()
