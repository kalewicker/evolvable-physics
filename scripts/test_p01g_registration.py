"""Mock fields and synthetic bookkeeping only: no hash-keyed laws or transitions."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_p01g_registration as checker
import generator_v2


def fields(p,i,field,index,n):
    if field=='form':return index
    if field in ('route','structural'):return 1
    if field in ('state0','state1'):return 3
    return n-1


class SamplerStructure(unittest.TestCase):
    def test_optimized_python_rejected_before_arguments_or_draws(self):
        for script in ('generator_v2.py','check_p01g_registration.py'):
            result=subprocess.run([sys.executable,'-O',str(checker.ROOT/'scripts'/script)],
                                  capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('requires assertions',result.stderr)

    def test_all_templates_resources_and_no_hash_draw(self):
        with patch('generator_v2.draw',side_effect=AssertionError('Hash-keyed draw forbidden')):
            e=generator_v2.construct(0,0,fields)
        rules=e['native']['rules'];world=e['native']['world']
        self.assertEqual(world['matter_total'],88)
        self.assertEqual(world['next_edge'],16)
        self.assertEqual([r['id'] for r in rules],list(range(8)))
        self.assertEqual([o['op'] for o in rules[4]['ops']],['CreateNode','CreateEdge','Transfer','Burn'])
        self.assertEqual(rules[4]['ops'][1]['ends'],[0,1])
        self.assertEqual(rules[4]['ops'][2],{'op':'Transfer','from':0,'to':1,'matter':1,'activation':1})
        self.assertEqual(rules[4]['ops'][3],{'op':'Burn','node':0,'amount':1})
        self.assertEqual(rules[7]['ops'],[{'op':'DeleteEdge','account':0,'kind':0,'ends':[0,1]},
                         {'op':'DeleteNode','node':1,'recipient':0},{'op':'Burn','node':0,'amount':1}])
        self.assertEqual(rules[3]['edges'][0]['class'],'Structural')
        self.assertEqual(rules[3]['ops'][0]['activation'],2)
        self.assertTrue(all(n['state'] is None for r in rules for n in r['nodes']))
        self.assertEqual(sum(n['matter']+1 for n in world['nodes'].values())+len(world['edges']),88)
        self.assertEqual(sum(n['activation'] for n in world['nodes'].values()),64)

    def test_field_domains_and_law_initial_index_separation(self):
        calls=[]
        def spy(p,i,field,index,n):
            calls.append((p,i,field,index,n));return fields(p,i,field,index,n)
        e=generator_v2.construct(0,3,spy)
        self.assertEqual(e['native']['seed'],2**64-2)
        for p,i,field,index,n in calls:
            self.assertEqual(i,3 if field in ('node_kind','node_state','structural','scheduler') else 0)
        self.assertIn((0,0,'route',3,2),calls)
        self.assertNotIn('route',[f for _,_,f,j,_ in calls if j!=3])

    def test_zero_boundaries_and_negative_sign(self):
        def zero(p,i,field,index,n): return index if field=='form' else 0
        e=generator_v2.construct(0,0,zero);rules=e['native']['rules']
        self.assertEqual(e['native']['world']['matter_total'],80)
        self.assertEqual(rules[3]['edges'][0]['class'],'Contact')
        self.assertEqual(rules[1]['ops'][0]['delta'],-1)
        self.assertTrue(all(n['state']==0 and n['kind']==1 for r in rules for n in r['nodes']))

    def test_invalid_initial_and_mock_domain_rejected(self):
        with patch('generator_v2.draw',side_effect=AssertionError('Hash-keyed draw forbidden')):
            with self.assertRaises(AssertionError):generator_v2.construct(0,4)
        with self.assertRaises(AssertionError):generator_v2.construct(0,0,lambda p,i,f,j,n:n)

    def test_cli_admission_rejected_without_generation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'p.json';a=Path(td)/'a.json'
            p.write_text((checker.ROOT/'docs/p01g_protocol.json').read_text())
            admission={'schema':'p01g-execution-admission-v1','law_sampling_admitted':False,'fixed_slots':64,
                       'protocol_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'e01_authorized':False}
            a.write_text(json.dumps(admission))
            with self.assertRaises(AssertionError):generator_v2.admitted_slot(p,a,0)
            admission['law_sampling_admitted']=True;a.write_text(json.dumps(admission))
            self.assertEqual(generator_v2.admitted_slot(p,a,63),(4015,3))
            with self.assertRaises(AssertionError):generator_v2.admitted_slot(p,a,64)
            p.write_text(p.read_text()+'\n')
            with self.assertRaises(AssertionError):generator_v2.admitted_slot(p,a,0)


class RegistrationAndDecision(unittest.TestCase):
    def setUp(self):
        self.p=checker.load(checker.ROOT/'docs/p01g_protocol.json')
        self.cases=[dict(row,status='complete',full_horizon_verified=True,law_digest='a'*64,
                        attached_funded_birth_ids=[],visible_birth_ids=[],recycled_ids=[])
                    for row in checker.planned_slots(self.p)]

    def test_fixed_contract_and_tampering(self):
        self.assertEqual(checker.validate(self.p)['maximum_requested_epochs'],8192)
        for field,value in [('proposal_ids',list(range(4001,4017))),('epochs',256),('trajectory_denominator',60),
                            ('execution_admitted_now',True),('law_sampling_admitted_now',True)]:
            p=copy.deepcopy(self.p);p[field]=value
            with self.assertRaises(AssertionError):checker.validate(p)

    def test_no_pooling_different_children_initial_states_or_duplicate_laws(self):
        for case in self.cases:
            case['attached_funded_birth_ids']=[8,9];case['visible_birth_ids']=[8];case['recycled_ids']=[9]
        r=checker.assess_mechanisms(self.p,self.cases)
        self.assertEqual(r['distinct_tables_with_visible_birth'],1)
        self.assertEqual(r['distinct_tables_with_same_trajectory_visible_birth_recycle_loop'],0)
        self.assertFalse(r['mechanism_gate_pass'])
        self.cases[1]['visible_birth_ids']=[];self.cases[1]['recycled_ids']=[8]
        self.assertFalse(checker.assess_mechanisms(self.p,self.cases)['mechanism_gate_pass'])

    def test_distinct_tables_and_same_child_loop_pass(self):
        for row in (0,4):
            self.cases[row].update(attached_funded_birth_ids=[8],visible_birth_ids=[8])
        for row in range(4,8):self.cases[row]['law_digest']='b'*64
        self.cases[4]['recycled_ids']=[8]
        self.assertTrue(checker.assess_mechanisms(self.p,self.cases)['mechanism_gate_pass'])
        self.cases[4]['status']='censored'
        self.assertFalse(checker.assess_mechanisms(self.p,self.cases)['mechanism_gate_pass'])

    def test_unborn_ids_missing_and_reordered_cases_rejected(self):
        self.cases[0]['visible_birth_ids']=[8]
        with self.assertRaises(AssertionError):checker.assess_mechanisms(self.p,self.cases)
        with self.assertRaises(AssertionError):checker.assess_mechanisms(self.p,self.cases[:-1])
        self.cases[0]['visible_birth_ids']=[]
        self.cases[0],self.cases[1]=self.cases[1],self.cases[0]
        with self.assertRaises(AssertionError):checker.assess_mechanisms(self.p,self.cases)

    def test_law_identity_cannot_change_across_initial_states(self):
        self.cases[1]['law_digest']='b'*64
        with self.assertRaisesRegex(AssertionError,'Law identity'):
            checker.assess_mechanisms(self.p,self.cases)

if __name__=='__main__':unittest.main()
