#!/usr/bin/env python3
"""Registration descriptors, inventories and hashes only; no payload diagnosis."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def equal(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def cells(p):return [(n,pr,i) for n,(pr,i) in enumerate((pr,i) for pr in p['proposal_ids'] for i in p['initial_ids'])]
def validate(p):
    require(equal(p['schema'],'p01t-saved-input-readiness-v1'),'schema')
    require(equal(p['date'],'2026-10-24'),'date')
    require(equal(p['scope'],'Register unfiltered saved-envelope-to-request transport readiness; no native semantic validation or execution.'),'scope')
    require(equal(p['registration_only_now'],True),'registration_only_now')
    require(equal(p['readiness_admitted_after_commit_push'],True),'readiness_admitted_after_commit_push')
    require(equal(p['implementation_started'],False),'implementation_started')
    require(equal(p['retained_conversion_executed_now'],False),'retained_conversion_executed_now')
    require(equal(p['world_execution_admitted'],False),'world_execution_admitted')
    require(equal(p['native_worker_execution_admitted'],False),'native_worker_execution_admitted')
    require(equal(p['keyed_evaluation_admitted'],False),'keyed_evaluation_admitted')
    require(equal(p['performance_assay_admitted'],False),'performance_assay_admitted')
    require(equal(p['campaign_integration_admitted'],False),'campaign_integration_admitted')
    require(equal(p['consumed_attempt_repair_admitted'],False),'consumed_attempt_repair_admitted')
    require(equal(p['e01_authorized'],False),'e01_authorized')
    require(equal(p['scientific_status'],'untested'),'scientific_status')
    require(equal(p['behavioral_outcomes'],None),'behavioral_outcomes')
    require(equal(p['behavioral_missing_reason'],'not_executed'),'behavioral_missing_reason')
    require(equal(p['epochs'],0),'epochs')
    require(equal(p['proposal_ids'],[6000, 6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6010, 6011, 6012, 6013, 6014, 6015, 6016, 6017, 6018, 6019, 6020, 6021, 6022, 6023, 6024, 6025, 6026, 6027, 6028, 6029, 6030, 6031]),'proposal_ids')
    require(equal(p['initial_ids'],[0, 1, 2, 3]),'initial_ids')
    require(equal(p['law_denominator'],32),'law_denominator')
    require(equal(p['cell_denominator'],128),'cell_denominator')
    require(equal(p['saved_streams'],256),'saved_streams')
    require(equal(p['planned_requests'],128),'planned_requests')
    require(equal(p['source_bundles'],{'artifacts/p01o-001': 'fa6fb28cefdf3f253227fc1de2096246a9c1bf30bd6c7ce2d1b8deef72fdfd00', 'artifacts/p01q-001': 'eabecddbe5ea1a14d537a56af96a2bd9516bf9dca6d1998137e7cc277df7dcf4'}),'source_bundles')
    require(equal(p['controls'],['complete_envelope_to_exact_request', 'all128_identity_order_and_no_selection', 'typed_equality_bool_int_float', 'malformed_duplicate_nonfinite_json', 'wrong_digest_schema_or_cell', 'missing_or_unwrapped_environment', 'extra_metadata_and_draws_preserved', 'resource_rule_and_request_cap_mutation', 'relative_and_absolute_output_paths', 'partial_request_write_preserved', 'terminal_write_failure_preserves_first_error', 'reserve_boundaries_and_zero_filesystem_polls', 'missing_duplicate_extra_cell_receipts', 'inventory_and_counter_mutation']),'controls')
    require(equal(p['future_paths'],{'readiness': 'scripts/p01t_readiness.py', 'audit': 'scripts/audit_p01t.py', 'tests': 'scripts/test_p01t.py'}),'future_paths')
    require(equal(p['frozen_reuse'],{'scripts/p01s_boundary.py': 'b989fe16f989f27df6050fe144fb11965e6343f2ea7d33da836e5a4f385beef0', 'scripts/p01s_accounting.py': 'be42dd72ff13ab9d51bc6086a8ede99747e810a7c8599ee3c34e2ba04a012e2a'}),'frozen_reuse')
    require(equal(p['request_contract'],{'schema': 'p01-worker-request-v1', 'epochs': 128, 'max_events': 16384, 'max_trace_bytes': 4194304}),'request_contract')
    require(equal(p['limits'],{'wall_seconds_per_tool': 120, 'output_bytes_per_tool': 134217728, 'terminal_reserve_bytes': 1048576, 'terminal_reserve_seconds': 5, 'input_stream_bytes': 1048576, 'request_bytes_per_cell': 524288}),'limits')
    require(equal(p['work_contract'],{'input_custody_passes_per_tool': 1, 'output_root_scans_per_producer': 1, 'output_root_scans_per_auditor': 1, 'filesystem_operations_per_budget_poll': 0, 'full_scans_during_failure_closeout': 0}),'work_contract')
    require(equal(p['plan'],'docs/p01t_readiness_plan.md'),'plan')
    require(equal(p['failure_policy'],'Retain every test/readiness/audit attempt, partial output and all128 statuses. Stop at first retained-cell failure; later cells stay unstarted. Implementation-only corrections may repeat this unchanged transport panel in fresh directories. Never repair saved inputs, change thresholds, select cells, resume P01q or launch dynamics.'),'failure_policy')
    require(equal(p['decision'],'Stop after independently audited transport readiness. Native semantic validation, campaign integration, performance assay and dynamics each remain outside this registration.'),'decision')
    require(equal(p['prior_knowledge'],'P01r found all128 stream pairs typed-equal with nested environment.native. P01s invented fixtures passed after preserved path and failure-accounting corrections. These are disclosed prior observations, not blind predictions.'),'prior_knowledge')
    return dict(schema='p01t-registration-review-v1',status='pass',fixed_laws=32,fixed_cells=128,saved_streams=256,planned_requests=128,planned_controls=14,retained_payloads_parsed=0,worker_requests=0,world_transitions=0,keyed_evaluations=0,implementation_started=False,scientific_status='untested')

def review():
    p=load(ROOT/'docs/p01t_protocol.json');result=validate(p);f=load(ROOT/'docs/p01t_registration_freeze.json')
    for section in ('files','inputs','prior_public_receipts'):
        for n,h in f[section].items():require(sha(ROOT/n)==h,section+': '+n)
    expected=set(load(ROOT/'docs/p01s_registration_freeze.json')['inputs'])|set(load(ROOT/'docs/p01s_closure.json')['receipts'])
    require(set(f['inputs'])==expected,'complete recovery custody input set')
    for _,pr,i in cells(p):
        slot=(pr-6000)*4+i
        for lang in ('rust_generation','python_generation'):require(f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin' in f['inputs'],'saved stream omitted')
    for n,h in p['frozen_reuse'].items():require(sha(ROOT/n)==h,'frozen reuse: '+n)
    require(load(ROOT/'docs/p01s_closure.json')['independent_audit_pass'] is True,'P01s engineering gate')
    counts={}
    for bundle,h in p['source_bundles'].items():
        b=ROOT/bundle;inv=load(b/'checksums.json');seal=load(b/'seal.json')
        require(sha(b/'seal.json')==h,'original seal')
        require({str(x.relative_to(b)) for x in b.rglob('*') if x.is_file()}==set(inv)|{'checksums.json','seal.json'},'inventory membership')
        for n,digest in inv.items():require(sha(b/n)==digest,'inventory: '+n)
        require(sha(b/'manifest.json')==seal['manifest_sha256'] and sha(b/'checksums.json')==seal['checksums_sha256'],'seal links')
        counts[bundle]=len(inv)
    m=load(ROOT/'artifacts/p01q-001/manifest.json')
    require(len(m['rows'])==128 and m['execution_status']=='failed' and m['error']=="KeyError('native')" and m['provenance_error']=="AssertionError('aggregate CPU reserve')",'preserved failure')
    for plan,row in zip(cells(p),m['rows']):require((row['slot'],row['proposal'],row['initial_state'])==plan and not row['stages'],'fixed cells/no stages')
    require(m['rows'][0]['status']=='failed' and all(x['status']=='unstarted' for x in m['rows'][1:]),'failed/unstarted denominator')
    for n in p['future_paths'].values():require(not (ROOT/n).exists(),'implementation before registration: '+n)
    result.update(frozen_files=len(f['files']),analysis_inputs=len(f['inputs']),prior_public_receipts=len(f['prior_public_receipts']),original_inventory_counts=counts,freeze_sha256=sha(ROOT/'docs/p01t_registration_freeze.json'))
    return result
if __name__=='__main__':
    result=review();out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    (out/'static_review.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
