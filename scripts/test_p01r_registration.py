"""Registration mutation checks only; no saved-payload diagnosis."""
import copy
import hashlib
import unittest
from unittest.mock import patch
import check_p01r_registration as c
class Registration(unittest.TestCase):
    def setUp(self):self.p=c.load(c.ROOT/'docs/p01r_protocol.json')
    def reject(self,key,value):
        p=copy.deepcopy(self.p);p[key]=value
        with self.assertRaises(ValueError):c.validate(p)
    def test_valid_without_hash_or_execution(self):
        with patch.object(hashlib,'sha256',side_effect=RuntimeError('no hashing')):self.assertEqual(c.validate(self.p)['retained_payloads_parsed'],0)
    def test_all128_cells(self):
        rows=c.cells(self.p);self.assertEqual(len(rows),128);self.assertEqual(rows[0],(0,6000,0));self.assertEqual(rows[-1],(127,6031,3))
    def test_panel_types_and_horizon(self):
        for k,v in [('proposal_ids',[6000]),('initial_ids',[False,1,2,3]),('saved_streams',128),('epochs',1)]:
            with self.subTest(k=k):self.reject(k,v)
    def test_no_repair_performance_or_world_admission(self):
        for k in ('repair_admitted','performance_assay_admitted','world_execution_admitted','keyed_evaluation_admitted','diagnosis_executed_now','e01_authorized'):
            with self.subTest(k=k):self.reject(k,True)
    def test_controls_and_unknowns_cannot_disappear(self):
        for k in ('invented_interface_controls','invented_accounting_controls'):self.reject(k,self.p[k][:-1])
        self.reject('classification',['confirmed_from_saved_records','source_derived'])
        self.reject('behavioral_outcomes',{'births':0})
    def test_seals_paths_and_limits_unchanged(self):
        self.reject('source_bundles',{})
        self.reject('future_paths',dict(self.p['future_paths'],review='scripts/p01q_campaign.py'))
        self.reject('limits',dict(self.p['limits'],wall_seconds_per_tool=121))
if __name__=='__main__':unittest.main()
