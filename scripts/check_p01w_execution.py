"""Read-only P01w admission checks. No worker, matcher, replay or generator imports."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())

def validate(root,f,a,p,r):
    need(a['schema']=='p01w-execution-admission-v1','admission schema')
    need(a['world_execution_admitted'] is True and a['keyed_evaluation_admitted'] is False and a['e01_authorized'] is False,'scope')
    need(a['admitted_output']=='artifacts/p01w-001' and a['fixed_slots']==128 and a['epochs']==128,'fixed attempt')
    need(a['no_retries_or_replacements'] is True,'no retries')
    for name in ('protocol','registration_freeze','execution_freeze'):
        need(sha(root/f'docs/p01w_{name}.json')==a[name+'_sha256'],'linked '+name)
    for section in ('files','inputs','prior_public_receipts'):
        for name,h in r[section].items():need(f['files'].get(name)==h,'registered coverage '+name)
    for name in p['future_paths'].values():need(name in f['files'],'implementation closure '+name)
    for name,h in p['saved_requests'].items():need(f['files'].get(name)==h,'unchanged request '+name)
    for name,h in p['production_binaries'].items():need(f['files'].get(name)==h,'unchanged binary '+name)
    need(str(Path(sys.executable).resolve())==f['interpreter'] and f['tools'].get(f['interpreter'])==sha(f['interpreter']),'interpreter identity')
    for section in ('files','dependencies','tools'):
        need(f[section],'empty closure '+section)
        for name,h in f[section].items():need(sha(Path(name) if Path(name).is_absolute() else root/name)==h,'identity '+name)
    need(f['membership'],'complete dependency membership')
    for item in f['membership']:
        base=Path(item['root']);names={str(x.relative_to(base)) for x in base.rglob('*') if x.is_file()}
        need(names==set(item['files']),'dependency membership')
        need(all(str(base/n) in f['dependencies'] for n in names),'dependency coverage')
    actual_scripts={str(x.relative_to(root)) for x in (root/'scripts').rglob('*') if x.is_file()}
    need(actual_scripts=={n for n in f['files'] if n.startswith('scripts/')},'project source membership')
    # Project bytecode must never be accidentally executed without a pin.
    for file in (root/'scripts').rglob('*.pyc'):
        need(f['files'].get(str(file.relative_to(root)))==sha(file),'project bytecode')
    need(f['existing_bytecode_included'] is True,'bytecode policy')
    ready=load(root/'docs/p01w_implementation_readiness.json')
    need(ready['implementation_complete'] is True and ready['invented_controls_pass'] is True and ready['world_execution_admitted'] is False,'implementation readiness')
    need(sha(root/'docs/p01w_implementation_readiness.json')==a['readiness_sha256'],'readiness link')
    tests=load(root/ready['test_receipt']);need(sha(root/ready['test_receipt'])==ready['test_receipt_sha256'],'tested receipt')
    need(tests['status']=='pass' and tests['controls']==p['controls'],'registered controls passed')
    for n,h in tests['sources'].items():need(f['files'].get(n)==h,'tested source '+n)
    for n,h in tests['runtime_files'].items():need(f['dependencies'].get(n,f['tools'].get(n))==h,'tested runtime '+n)
    # Every original bundle inventory member must be in the snapshot closure.
    for bundle,h in p['source_bundles'].items():
        b=root/bundle;need(sha(b/'seal.json')==h,'original seal')
        inv=load(b/'checksums.json');seal=load(b/'seal.json')
        need(sha(b/'checksums.json')==seal['checksums_sha256'] and sha(b/'manifest.json')==seal['manifest_sha256'],'original links')
        need({str(x.relative_to(b)) for x in b.rglob('*') if x.is_file()}==set(inv)|{'checksums.json','seal.json'},'original membership')
        for n,d in inv.items():need(f['files'].get(bundle+'/'+n)==d,'original snapshot closure')
    for name,h in p['prerequisite_receipts'].items():need(f['files'].get(name)==h,'prerequisite receipt')
    return dict(schema='p01w-execution-review-v1',status='pass',world_transitions=0,files=len(f['files']),dependencies=len(f['dependencies']))

def review(root=ROOT):
    root=Path(root).resolve();p=load(root/'docs/p01w_protocol.json')
    need(not (root/p['execution_output']).exists(),'consumed attempt exists')
    return validate(root,load(root/'docs/p01w_execution_freeze.json'),load(root/'docs/p01w_execution_admission.json'),p,load(root/'docs/p01w_registration_freeze.json'))

def publication_check(root):
    for name in ('protocol','registration_freeze','execution_freeze','execution_admission'):
        file=f'docs/p01w_{name}.json'
        need(subprocess.check_output(['git','show','HEAD:'+file],cwd=root)==(root/file).read_bytes(),'uncommitted '+name)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=root).decode().split()
    need(remote and remote[0]==head,'execution freeze not pushed')

def check_cell_admission(root,request,directory):
    need(__debug__,'assert-enabled replay');a=load(root/'docs/p01w_execution_admission.json');f=load(root/'docs/p01w_execution_freeze.json')
    need(a['schema']=='p01w-execution-admission-v1' and a['world_execution_admitted'] is True,'cell admission')
    for name in ('protocol','registration_freeze','execution_freeze'):
        need(sha(root/f'docs/p01w_{name}.json')==a[name+'_sha256'],'cell admission '+name)
    run=root.parent;directory=directory.resolve();request=request.resolve()
    need(directory.parent==run/'runs' and directory.name.isdecimal() and request==directory/'request.json','cell output binding')
    slot=int(directory.name);need(0<=slot<128,'cell slot')
    p=load(root/'docs/p01w_protocol.json');need(sha(request)==p['saved_requests'][f'artifacts/p01t-002/requests/{slot:03}.json'],'cell request')
    identity=load(directory/'identity.json');need([identity[k] for k in ('slot','proposal','initial')]==[slot,6000+slot//4,slot%4],'cell identity')
    for name,h in f['files'].items():
        if name.startswith('scripts/'):need(sha(root/name)==h,'cell frozen imports')
    need(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','bytecode write prohibition')
