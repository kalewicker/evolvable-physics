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
    require(p['schema']=='p01r-read-only-engineering-diagnosis-v1','schema')
    require(equal(p['proposal_ids'],list(range(6000,6032))) and equal(p['initial_ids'],list(range(4))),'fixed panel')
    require(equal([p[k] for k in ('law_denominator','cell_denominator','saved_streams','epochs')],[32,128,256,0]),'denominators')
    for k,v in [('registration_only_now',True),('read_only_diagnosis_admitted_after_commit_push',True),('diagnosis_executed_now',False),('repair_admitted',False),('performance_assay_admitted',False),('world_execution_admitted',False),('keyed_evaluation_admitted',False),('e01_authorized',False),('scientific_status','untested'),('behavioral_outcomes',None),('behavioral_missing_reason','not_executed')]:require(equal(p[k],v),'scope: '+k)
    require(p['source_bundles']=={'artifacts/p01o-001':'fa6fb28cefdf3f253227fc1de2096246a9c1bf30bd6c7ce2d1b8deef72fdfd00','artifacts/p01q-001':'eabecddbe5ea1a14d537a56af96a2bd9516bf9dca6d1998137e7cc277df7dcf4'},'original seals')
    require(len(p['questions'])==4,'four questions')
    for k in ('invented_interface_controls','invented_accounting_controls'):require(len(p[k])==len(set(p[k]))==10,'complete controls')
    require(p['classification']==['confirmed_from_saved_records','source_derived','unresolved'],'evidence classes')
    require(equal([p['limits'][k] for k in ('wall_seconds_per_tool','output_bytes_per_tool','terminal_reserve_bytes')],[120,134217728,1048576]),'budgets')
    require(p['future_paths']==dict(review='scripts/review_p01r.py',audit='scripts/audit_p01r.py',tests='scripts/test_p01r.py'),'separate paths')
    return dict(schema='p01r-registration-review-v1',status='pass',fixed_laws=32,fixed_cells=128,saved_streams=256,planned_interface_controls=10,planned_accounting_controls=10,retained_payloads_parsed=0,world_transitions=0,keyed_evaluations=0,diagnosis_executed=False,scientific_status='untested')

def review():
    p=load(ROOT/'docs/p01r_protocol.json');result=validate(p);f=load(ROOT/'docs/p01r_analysis_freeze.json')
    for section in ('files','inputs','prior_public_receipts'):
        for n,h in f[section].items():require(sha(ROOT/n)==h,section+': '+n)
    expected=set(load(ROOT/'docs/p01q_registration_freeze.json')['inputs'])|set(load(ROOT/'docs/p01q_closure.json')['receipts'])
    require(set(f['inputs'])==expected,'complete diagnosis input set')
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
    for n in p['future_paths'].values():require(not (ROOT/n).exists(),'diagnosis before registration: '+n)
    result.update(frozen_files=len(f['files']),analysis_inputs=len(f['inputs']),prior_public_receipts=len(f['prior_public_receipts']),original_inventory_counts=counts,freeze_sha256=sha(ROOT/'docs/p01r_analysis_freeze.json'))
    return result
if __name__=='__main__':
    result=review();out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    (out/'static_review.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
