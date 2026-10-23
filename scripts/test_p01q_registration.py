"""Descriptor/custody controls; no saved-world execution or generator imports."""
import copy
import hashlib
import unittest
from unittest.mock import patch
import check_p01q_registration as c

class Registration(unittest.TestCase):
    def setUp(self): self.p=c.load(c.ROOT/'docs/p01q_protocol.json')
    def reject(self,path,value):
        p=copy.deepcopy(self.p); d=p
        for k in path[:-1]: d=d[k]
        d[path[-1]]=value
        with self.assertRaises(ValueError): c.validate(p)
    def test_valid_without_hashes_or_execution(self):
        with patch.object(hashlib,'sha256',side_effect=RuntimeError('no hashing')):
            self.assertEqual(c.validate(self.p)['world_transitions'],0)
    def test_unfiltered_cartesian_order(self):
        rows=c.cells(self.p)
        self.assertEqual(len(rows),128)
        self.assertEqual(rows[0],dict(slot=0,proposal=6000,initial=0))
        self.assertEqual(rows[-1],dict(slot=127,proposal=6031,initial=3))
        self.assertEqual(len({(x['proposal'],x['initial']) for x in rows}),128)
    def test_panel_horizon_and_bool_mutations(self):
        for k,v in [('proposal_ids',[6011]),('initial_ids',[False,1,2,3]),('epochs',256),('law_denominator',1),('trajectory_denominator',127)]:
            with self.subTest(k=k): self.reject([k],v)
    def test_no_early_admission_or_observed_zero(self):
        for k,v in [('world_execution_admitted_now',True),('keyed_evaluation_admitted',True),('e01_authorized',True),('behavioral_outcomes',{'births':0})]:
            with self.subTest(k=k): self.reject([k],v)
    def test_threshold_and_historical_decision_unchanged(self):
        self.reject(['mechanism_gate','min_distinct_rule_tables_with_visible_birth'],1)
        self.reject(['decision','engineering_pass_mechanism_fail'],'continue')
    def test_budgets_and_output_cannot_expand(self):
        self.reject(['campaign','wall_seconds'],1201)
        self.reject(['per_process','native','wall_seconds'],11)
        self.reject(['execution_output'],'artifacts/p01q-retry')
    def test_missing_controls_or_observables_rejected(self):
        self.reject(['verification_controls'],self.p['verification_controls'][:-1])
        self.reject(['observables','visible_birth'],'rule available')
    def test_source_and_path_identity(self):
        self.reject(['source_seal_sha256'],'0'*64)
        self.reject(['future_paths','cell'],'scripts/p01g_cell.py')

if __name__=='__main__': unittest.main()
