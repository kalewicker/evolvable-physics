"""Pre-execution structural/tamper checks. Never evaluate witness transitions."""
import copy
import subprocess
import sys
import unittest
from unittest.mock import patch
import audit_p01f_receipts
import check_p01f_registration as registration
import p01f_audit
import validate_p01f


class ExecutionContract(unittest.TestCase):
    def setUp(self):
        self.protocol=registration.load(registration.ROOT/'docs/p01f_protocol.json')
        self.registry=registration.load(registration.ROOT/'docs/p01f_witnesses.json')
        self.rows=[]
        for i,(family,seed) in enumerate(p01f_audit.slots(self.protocol,self.registry)):
            initial=copy.deepcopy(family['initial']); initial['native']['seed']=seed
            self.rows.append({'schema':'p01f-witness-slot-v1','slot':i,'family':family['id'],
                              'seed':seed,'initial':initial,'results':{'Reference':{},'Indexed':{}}})

    def test_denominator_and_seed_order(self):
        self.assertEqual(len(self.rows),48)
        self.assertEqual([(r['slot'],r['seed']) for r in self.rows[:4]],list(enumerate(range(4))))
        with self.assertRaisesRegex(AssertionError,'denominator'):
            p01f_audit.verify_panel(self.protocol,self.registry,self.rows[:-1])

    def test_swapped_identity_rejected_before_replay(self):
        self.rows[0],self.rows[1]=self.rows[1],self.rows[0]
        with patch('p01f_audit.verify_result',return_value={}) as replay:
            result=p01f_audit.verify_panel(self.protocol,self.registry,self.rows)
        self.assertEqual(result['status'],'failed')
        self.assertIn('Fixed slot identity',result['cases'][0]['error'])
        self.assertEqual(replay.call_count,92)

    def test_matcher_mismatch_rejected(self):
        self.rows[0]['results']['Indexed']={'changed':True}
        with patch('p01f_audit.verify_result',return_value={}):
            result=p01f_audit.verify_panel(self.protocol,self.registry,self.rows)
        self.assertIn('Exact matcher',result['cases'][0]['error'])
        self.assertEqual(len(result['cases']),48)

    def test_initial_substitution_rejected(self):
        self.rows[0]['initial']['native']['seed']=99
        with patch('p01f_audit.verify_result',return_value={}):
            result=p01f_audit.verify_panel(self.protocol,self.registry,self.rows)
        self.assertIn('Fixed initial state',result['cases'][0]['error'])

    def test_budget_reservation(self):
        usage={'wall_seconds':0,'total_process_cpu_seconds':0,'artifact_bytes':0}
        execution=self.protocol['future_execution']
        self.assertTrue(validate_p01f.launch_fits(usage,execution['python_audit_process'],execution['campaign']))
        usage['total_process_cpu_seconds']=116
        self.assertFalse(validate_p01f.launch_fits(usage,execution['python_audit_process'],execution['campaign']))

    def test_optimized_python_cannot_disable_audits(self):
        for script in ('p01f_audit.py','audit_p01f_receipts.py','validate_p01f.py'):
            result=subprocess.run([sys.executable,'-O',str(registration.ROOT/'scripts'/script)],
                                  capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('requires assertions',result.stderr)

    def test_sealed_resource_tamper_rejected(self):
        seal={'resource_usage':{'artifact_bytes':12,'wall_seconds':1,'total_process_cpu_seconds':1},'overshoot':[]}
        manifest={'resource_usage_before_seal':dict(seal['resource_usage']),'stages':{}}
        with self.assertRaisesRegex(AssertionError,'Artifact size'):
            audit_p01f_receipts.resources(manifest,seal,self.protocol,13)
        seal['resource_usage']['wall_seconds']=241
        with self.assertRaisesRegex(AssertionError,'wall_seconds'):
            audit_p01f_receipts.resources(manifest,seal,self.protocol,12)

if __name__=='__main__': unittest.main()
