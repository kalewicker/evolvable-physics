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
    require(p['schema']=='p01s-recovery-engineering-v1','schema')
    require(equal(p['proposal_ids'],list(range(6000,6032))) and equal(p['initial_ids'],list(range(4))),'fixed panel')
    require(equal([p[k] for k in ('law_denominator','cell_denominator','saved_streams','epochs')],[32,128,256,0]),'denominators')
    for k in ('registration_only_now','engineering_admitted_after_commit_push'):require(p[k] is True,'scope: '+k)
    for k in ('implementation_started','world_execution_admitted','keyed_evaluation_admitted','performance_assay_admitted','retained_request_construction_admitted','consumed_attempt_repair_admitted','e01_authorized'):require(p[k] is False,'scope: '+k)
    require(p['scientific_status']=='untested' and p['behavioral_outcomes'] is None and p['behavioral_missing_reason']=='not_executed','unknown outcomes')
    require(equal(p['source_bundles'],{'artifacts/p01o-001': 'fa6fb28cefdf3f253227fc1de2096246a9c1bf30bd6c7ce2d1b8deef72fdfd00', 'artifacts/p01q-001': 'eabecddbe5ea1a14d537a56af96a2bd9516bf9dca6d1998137e7cc277df7dcf4'}),'source_bundles')
    require(equal(p['controls'],['complete_wrapper_preserves_all_fields', 'already_unwrapped_fixture_is_wrong_boundary', 'missing_environment', 'missing_native', 'wrong_schema', 'wrong_cell_ids', 'bool_vs_integer_mismatch', 'stream_disagreement', 'extra_metadata_preserved', 'nested_resource_or_rule_mutation_rejected', 'create_and_append', 'atomic_replace_counts_old_and_temporary_until_rename', 'failed_partial_write_is_retained', 'duplicate_path_not_double_counted', 'snapshot_bytes_included', 'metadata_and_seal_bytes_included', 'cpu_reserve_boundary', 'wall_and_byte_reserve_boundaries', 'terminal_failure_preserves_all_cells', 'inventory_mismatch_and_unlisted_file', 'budget_poll_has_zero_filesystem_work', 'bounded_stage_reconciliation', 'terminal_reserve_exhaustion_preserves_first_error', 'path_escape_symlink_and_external_mutation_rejected']),'controls')
    require(equal(p['future_paths'],{'boundary': 'scripts/p01s_boundary.py', 'accounting': 'scripts/p01s_accounting.py', 'readiness': 'scripts/p01s_readiness.py', 'audit': 'scripts/audit_p01s.py', 'tests': 'scripts/test_p01s.py'}),'future_paths')
    require(equal(p['limits'],{'wall_seconds_per_tool': 120, 'output_bytes_per_tool': 134217728, 'terminal_reserve_bytes': 1048576, 'terminal_reserve_seconds': 5}),'limits')
    require(equal(p['request_contract'],{'epochs': 128, 'max_events': 16384, 'max_trace_bytes': 4194304}),'request_contract')
    require(equal(p['work_contract'],{'full_output_scans_per_attempt': 2, 'full_output_scans_per_budget_poll': 0, 'full_output_scans_during_failure_closeout': 0, 'stage_reconciliations_per_stage': 1, 'stage_declared_file_cap': 16, 'stage_declared_byte_cap': 8388608}),'work_contract')
    require(equal(p['plan'],'docs/p01s_engineering_plan.md'),'plan')
    return dict(schema='p01s-registration-review-v1',status='pass',fixed_laws=32,fixed_cells=128,saved_streams=256,planned_controls=24,retained_payloads_parsed=0,worker_requests=0,world_transitions=0,keyed_evaluations=0,implementation_started=False,scientific_status='untested')

def review():
    p=load(ROOT/'docs/p01s_protocol.json');result=validate(p);f=load(ROOT/'docs/p01s_registration_freeze.json')
    for section in ('files','inputs','prior_public_receipts'):
        for n,h in f[section].items():require(sha(ROOT/n)==h,section+': '+n)
    expected=set(load(ROOT/'docs/p01r_analysis_freeze.json')['inputs'])|set(load(ROOT/'docs/p01r_closure.json')['receipts'])
    require(set(f['inputs'])==expected,'complete recovery custody input set')
    for _,pr,i in cells(p):
        slot=(pr-6000)*4+i
        for lang in ('rust_generation','python_generation'):require(f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin' in f['inputs'],'saved stream omitted')
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
    result.update(frozen_files=len(f['files']),analysis_inputs=len(f['inputs']),prior_public_receipts=len(f['prior_public_receipts']),original_inventory_counts=counts,freeze_sha256=sha(ROOT/'docs/p01s_registration_freeze.json'))
    return result
if __name__=='__main__':
    result=review();out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    (out/'static_review.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
