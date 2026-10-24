"""Registration checks; no recovery implementation or retained conversion."""
import copy
import unittest
import check_p01s_registration as c
class Registration(unittest.TestCase):
    def setUp(self):self.p=c.load(c.ROOT/'docs/p01s_protocol.json')
    def reject(self,k,v):
        p=copy.deepcopy(self.p);p[k]=v
        with self.assertRaises(ValueError):c.validate(p)
    def test_valid(self):self.assertEqual(c.validate(self.p)['planned_controls'],24)
    def test_panel(self):
        self.assertEqual(len(c.cells(self.p)),128)
        for k,v in [('proposal_ids',[6000]),('initial_ids',[False,1,2,3]),('epochs',1),('saved_streams',128)]:self.reject(k,v)
    def test_scope(self):
        for k in ('implementation_started','world_execution_admitted','keyed_evaluation_admitted','performance_assay_admitted','retained_request_construction_admitted','consumed_attempt_repair_admitted','e01_authorized'):self.reject(k,True)
        self.reject('engineering_admitted_after_commit_push',1)
    def test_exact_controls(self):
        self.reject('controls',self.p['controls'][:-1])
        self.reject('controls',self.p['controls'][:-1]+['different_control'])
    def test_reserves_and_work_limits(self):
        for k in ('limits','work_contract','request_contract'):
            for n in self.p[k]:self.reject(k,dict(self.p[k],**{n:self.p[k][n]+1}))
    def test_old_paths_and_seals(self):
        self.reject('future_paths',dict(self.p['future_paths'],boundary='scripts/p01q_cell.py'))
        self.reject('source_bundles',{})
    def test_unknowns(self):
        self.reject('behavioral_outcomes',{'births':0})
        self.reject('scientific_status','supported')
if __name__=='__main__':unittest.main()
