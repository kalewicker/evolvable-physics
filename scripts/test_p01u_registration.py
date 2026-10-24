"""P01u registration mutations; no native implementation or input parsing."""
import copy
import unittest
import check_p01u_registration as c
class Registration(unittest.TestCase):
    def setUp(self):self.p=c.load(c.ROOT/'docs/p01u_protocol.json')
    def reject(self,k,v):
        q=copy.deepcopy(self.p);q[k]=v
        with self.assertRaises(ValueError):c.validate(q)
    def test_valid(self):self.assertEqual(c.validate(self.p)['requests_pinned'],128)
    def test_fixed_panel(self):
        self.assertEqual(c.cells(self.p)[-1],(127,6031,3))
        for k,v in [('proposal_ids',[6011]),('initial_ids',[False,1,2,3]),('request_denominator',127),('epochs_executed',1)]:self.reject(k,v)
    def test_no_execution_expansion(self):
        for k in ('implementation_started','native_validation_executed_now','world_execution_admitted','original_worker_run_admitted','candidate_matching_admitted','keyed_evaluation_admitted','campaign_integration_admitted','performance_assay_admitted','consumed_attempt_repair_admitted','e01_authorized'):self.reject(k,True)
        self.reject('validator_implementation_admitted_after_commit_push',1)
    def test_exact_controls(self):
        q=copy.deepcopy(self.p['controls']);q.pop(next(iter(q)));self.reject('controls',q)
        q=copy.deepcopy(self.p['controls']);q['world_size_limits'].pop();self.reject('controls',q)
    def test_caps_and_work(self):
        for k in ('limits','work_contract'):
            for n,v in self.p[k].items():self.reject(k,dict(self.p[k],**{n:v+1}))
    def test_input_source_and_binary_boundary(self):
        self.reject('saved_requests',{})
        self.reject('semantic_sources',{})
        self.reject('source_bundles',{})
        self.reject('future_paths',dict(self.p['future_paths'],native_source='src/bin/pilot-worker.rs'))
    def test_native_vs_panel_contract(self):
        self.reject('request_contract',dict(self.p['request_contract'],epochs=0))
        self.reject('request_contract',dict(self.p['request_contract'],max_events=1))
    def test_failure_and_unknowns(self):
        self.reject('failure_policy','repair failed requests')
        self.reject('behavioral_outcomes',{'births':0})
        self.reject('scientific_status','accepted')
if __name__=='__main__':unittest.main()
