"""Registration mutation checks only; no runtime imports or retained payloads."""
import copy
import unittest
import check_p01w_registration as c

class Registration(unittest.TestCase):
    def setUp(self):
        self.p=c.load(c.ROOT/'docs/p01w_protocol.json')
    def reject(self,key,value):
        p=copy.deepcopy(self.p);p[key]=value
        with self.assertRaises(ValueError):c.validate(p)
    def test_valid(self):
        r=c.validate(self.p)
        self.assertEqual((r['fixed_cells'],r['planned_production_stages'],r['named_control_cases']),(128,384,68))
    def test_panel_and_types(self):
        self.assertEqual(c.cells(self.p)[-1],(127,6031,3))
        for k,v in [('proposal_ids',[6011]),('initial_ids',[False,1,2,3]),('epochs',0),('trajectory_denominator',127),('law_denominator',True)]:self.reject(k,v)
    def test_no_execution_now(self):
        for k in ('implementation_started','world_execution_admitted_now','candidate_matching_admitted_now','keyed_evaluation_admitted','performance_assay_admitted','consumed_attempt_repair_admitted','e01_authorized'):self.reject(k,True)
        self.reject('implementation_admitted_after_commit_push',1)
        self.reject('requirements_before_execution',[])
    def test_unchanged_primary_criteria(self):
        for k,v in self.p['mechanism_gate'].items():
            if isinstance(v,int):self.reject('mechanism_gate',dict(self.p['mechanism_gate'],**{k:v+1}))
        self.reject('engineering_gate',self.p['engineering_gate'][:-1])
        self.reject('verification_controls',self.p['verification_controls'][:-1])
    def test_observation_and_decision_not_redefined(self):
        for key in ('observables','decision','reporting'):
            for field in self.p[key]:
                bad=copy.deepcopy(self.p[key]);bad[field]='relaxed';self.reject(key,bad)
    def test_caps_reserves_and_no_scans(self):
        for key in ('campaign','per_process','accounting_contract','request_contract'):
            bad=copy.deepcopy(self.p[key]);first=next(iter(bad));bad[first]=None;self.reject(key,bad)
        bad=copy.deepcopy(self.p['campaign']);bad['total_process_cpu_seconds']=601;self.reject('campaign',bad)
        bad=copy.deepcopy(self.p['accounting_contract']);bad['stage_retries']=1;self.reject('accounting_contract',bad)
    def test_production_contract_and_scope(self):
        for key in ('native','rust_report','python_audit'):
            bad=copy.deepcopy(self.p['production_contracts']);bad[key]['argv']=['stub'];self.reject('production_contracts',bad)
        self.reject('stage_order',['native_stub','report_stub','audit_stub'])
        self.reject('failure_policy','repeat after repairing inputs')
    def test_exact_identity_and_new_paths(self):
        for key in ('saved_requests','source_bundles','semantic_sources','additional_semantic_sources','production_binaries','prerequisite_receipts'):self.reject(key,{})
        self.reject('original_protocol_sha256','0'*64)
        self.reject('future_paths',dict(self.p['future_paths'],cell='scripts/p01q_cell.py'))
        self.reject('execution_output','artifacts/p01q-001')
    def test_controls_preserved(self):
        for family in self.p['controls']:
            bad=copy.deepcopy(self.p['controls']);bad[family].pop();self.reject('controls',bad)
    def test_unknown_and_missing_fields(self):
        p=copy.deepcopy(self.p);p['unregistered']=True
        with self.assertRaises(ValueError):c.validate(p)
        del p['unregistered'];del p['failure_policy']
        with self.assertRaises(ValueError):c.validate(p)
    def test_no_fabricated_observations(self):
        self.reject('behavioral_outcomes',{'births':0});self.reject('behavioral_missing_reason','observed_zero')
        self.reject('scientific_status','accepted');self.reject('epochs_executed',1)

if __name__=='__main__':unittest.main()
