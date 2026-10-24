"""Registration mutation checks only; no retained transport implementation."""
import copy
import unittest
import check_p01t_registration as c
class Registration(unittest.TestCase):
    def setUp(self):self.p=c.load(c.ROOT/'docs/p01t_protocol.json')
    def reject(self,k,v):
        p=copy.deepcopy(self.p);p[k]=v
        with self.assertRaises(ValueError):c.validate(p)
    def test_valid(self):self.assertEqual(c.validate(self.p)['planned_requests'],128)
    def test_panel_and_types(self):
        self.assertEqual(c.cells(self.p)[-1],(127,6031,3))
        for k,v in [('proposal_ids',[6011]),('initial_ids',[False,1,2,3]),('saved_streams',128),('planned_requests',127),('epochs',128)]:self.reject(k,v)
    def test_scope(self):
        for k in ('implementation_started','retained_conversion_executed_now','world_execution_admitted','native_worker_execution_admitted','performance_assay_admitted','campaign_integration_admitted','consumed_attempt_repair_admitted','keyed_evaluation_admitted','e01_authorized'):self.reject(k,True)
        self.reject('readiness_admitted_after_commit_push',1)
    def test_controls(self):
        self.reject('controls',self.p['controls'][:-1])
        self.reject('controls',self.p['controls'][:-1]+['replacement'])
    def test_request_contract(self):
        for n in ('epochs','max_events','max_trace_bytes'):self.reject('request_contract',dict(self.p['request_contract'],**{n:self.p['request_contract'][n]+1}))
        self.reject('request_contract',dict(self.p['request_contract'],schema='wrong'))
    def test_limits_and_work(self):
        for k in ('limits','work_contract'):
            for n,v in self.p[k].items():self.reject(k,dict(self.p[k],**{n:v+1}))
    def test_paths_and_custody(self):
        self.reject('frozen_reuse',{})
        self.reject('source_bundles',{})
        self.reject('future_paths',dict(self.p['future_paths'],readiness='scripts/p01q_campaign.py'))
    def test_outcomes_and_failure_policy(self):
        self.reject('behavioral_outcomes',{'births':0})
        self.reject('failure_policy','retry with repaired inputs')
        self.reject('scientific_status','supported')
if __name__=='__main__':unittest.main()
