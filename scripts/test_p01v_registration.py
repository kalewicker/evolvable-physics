"""P01v registration descriptors only; no integration execution."""
import copy
import unittest
import check_p01v_registration as c
class Registration(unittest.TestCase):
    def setUp(self):self.p=c.load(c.ROOT/'docs/p01v_protocol.json')
    def reject(self,key,value):
        p=copy.deepcopy(self.p);p[key]=value
        with self.assertRaises(ValueError):c.validate(p)
    def test_valid(self):self.assertEqual(c.validate(self.p)['planned_inert_stages'],384)
    def test_all128_and_types(self):
        self.assertEqual(c.cells(self.p)[-1],(127,6031,3))
        for k,v in [('proposal_ids',[6011]),('initial_ids',[False,1,2,3]),('cell_denominator',127),('inert_stage_denominator',128),('epochs_executed',1)]:self.reject(k,v)
    def test_roles_and_inert_schema(self):
        self.reject('stage_order',self.p['stage_order'][::-1]);self.reject('fixture_schema','p01-worker-result-v1')
        self.reject('manifest_schema','p01u-manifest-v1')
    def test_scope(self):
        for k in ('implementation_started','integration_executed_now','world_execution_admitted','original_worker_run_admitted','new_native_validation_admitted','candidate_matching_admitted','keyed_evaluation_admitted','productive_campaign_admitted','performance_assay_admitted','consumed_attempt_repair_admitted','e01_authorized'):self.reject(k,True)
        self.reject('integration_implementation_admitted_after_commit_push',1)
    def test_controls_and_failures(self):
        q=copy.deepcopy(self.p['controls']);q['early_and_midpoint_failures'].pop();self.reject('controls',q)
        self.reject('failure_policy','resume after a failed cell')
    def test_budgets_and_work(self):
        for k in ('limits','work_contract'):
            for n,v in self.p[k].items():self.reject(k,dict(self.p[k],**{n:v+1}))
    def test_identity_and_new_paths(self):
        for k in ('saved_requests','semantic_sources','source_bundles','frozen_reuse'):self.reject(k,{})
        self.reject('prior_independent_audit_sha256','0'*64)
        self.reject('future_paths',dict(self.p['future_paths'],pipeline='scripts/p01q_campaign.py'))
    def test_exact_request_contract(self):
        for n in ('epochs','max_events','max_trace_bytes'):self.reject('request_contract',dict(self.p['request_contract'],**{n:self.p['request_contract'][n]+1}))
    def test_unknown_behavior(self):
        self.reject('behavioral_outcomes',{'births':0});self.reject('scientific_status','accepted')
if __name__=='__main__':unittest.main()
