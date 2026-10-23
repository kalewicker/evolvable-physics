#!/usr/bin/env python3
"""Read-only P01q closure check; no worker, sampler or interpreter imports."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)


def review(root=ROOT):
    f=load(root/'docs/p01q_execution_freeze.json');a=load(root/'docs/p01q_execution_admission.json')
    p=load(root/'docs/p01q_protocol.json');r=load(root/'docs/p01q_registration_freeze.json')
    require(a['schema']=='p01q-execution-admission-v1' and a['world_execution_admitted'] is True and
        a['keyed_evaluation_admitted'] is False and a['e01_authorized'] is False,'admission scope')
    require(a['fixed_slots']==128 and a['fixed_laws']==32 and a['epochs']==128 and p['epochs']==128,'denominators')
    require(a['admitted_output']=='artifacts/p01q-001' and a['output_absolute']==str(root/'artifacts/p01q-001'),'fixed output')
    require(not (root/'artifacts/p01q-001').exists(),'attempt exists; no resume')
    require(a['no_retries_or_replacements'] is True and a['world_transitions_so_far']==0 and
        a['scientific_status']=='untested' and a['required_environment']=={'PYTHONDONTWRITEBYTECODE':'1'},'scope/environment')
    for key in ('protocol','registration_freeze','execution_freeze'):
        require(sha(root/'docs'/('p01q_'+key+'.json'))==a[key+'_sha256'],'linked '+key)
    for section in ('files','inputs','prior_public_receipts'):
        for name,h in r[section].items():require(f['files'].get(name)==h,'registration coverage: '+name)
    for section in ('files','dependencies','tools'):
        require(f[section], 'empty '+section)
        for name,h in f[section].items():require(sha(root/name)==h,'identity: '+name)
    require(f['membership'],'membership roots')
    for item in f['membership']:
        base=Path(item['root']);actual={str(x.relative_to(base)) for x in base.rglob('*') if x.is_file()}
        require(actual==set(item['files']),'membership: '+str(base))
        require(all(str(base/n) in f['dependencies'] for n in actual),'membership hash coverage')
    require(set(f['binaries'])=={'pilot-worker','pilot-report'},'binary set')
    old=load(root/'docs/p01g_execution_freeze.json')
    for name,row in f['binaries'].items():
        require(row==old['binaries'][name] and sha(root/row['path'])==row['sha256'],'tested binary: '+name)
    readiness=load(root/'docs/p01q_implementation_readiness.json')
    require(readiness['implementation_complete'] is True and readiness['invented_mock_checks_pass'] is True and
        readiness['world_execution_admitted'] is False,'implementation readiness')
    require(sha(root/'docs/p01q_implementation_readiness.json')==a['implementation_readiness_sha256'],'readiness identity')
    receipt=load(root/readiness['readiness_receipt'])
    require(sha(root/readiness['readiness_receipt'])==readiness['readiness_sha256'],'readiness receipt')
    for name,h in receipt['sources'].items():require(f['files'].get(name)==h and sha(root/name)==h,'tested implementation')
    metadata=load(root/f['cargo_metadata']);packages=[x for x in metadata['packages'] if x['source'] is not None]
    require(packages and all(x['manifest_path'] in f['dependencies'] for x in packages),'manifest coverage')
    for name,h in f['prior_public_receipts'].items():require(sha(root/name)==h and f['files'].get(name)==h,'receipt identity')
    return dict(schema='p01q-pre-execution-readiness-v1',status='pass',source_files=len(f['files']),
        dependency_files=len(f['dependencies']),tool_files=len(f['tools']),membership_roots=len(f['membership']),
        prior_public_receipts_verified=len(f['prior_public_receipts']),cargo_dependency_packages=len(packages),
        binary_sha256={n:x['sha256'] for n,x in f['binaries'].items()},fixed_laws=32,fixed_environments=128,
        epochs_per_cell=128,world_transitions=0,keyed_evaluations=0,scientific_status='untested',
        execution_freeze_sha256=sha(root/'docs/p01q_execution_freeze.json'),
        execution_admission_sha256=sha(root/'docs/p01q_execution_admission.json'))

if __name__=='__main__':
    result=review();out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    (out/'readiness.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
