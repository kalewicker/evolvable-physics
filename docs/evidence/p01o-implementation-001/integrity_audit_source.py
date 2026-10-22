import hashlib,itertools,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from audit_p01n_readiness import registered_input
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
registry=load(Path('docs/p01n_literal_fields.json'))
receipts=[]
for attempt in (1,2):
 bundle=Path(f'artifacts/p01o-implementation-{attempt:03d}'); inventory=load(bundle/'checksums.json'); completion=load(bundle/'completion.json'); assessment=load(bundle/'assessment.json')
 require({str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file()}==set(inventory)|{'checksums.json','completion.json'},'inventory membership')
 for name,digest in inventory.items():require(sha(bundle/name)==digest,'artifact identity '+name)
 require(completion['checksums_sha256']==sha(bundle/'checksums.json'),'completion link')
 require(completion['wall_seconds_including_inventory']<=300 and assessment['literal_gate_pass'] is True,'preflight gate')
 for name,digest in assessment['source_sha256'].items():
  require(sha(bundle/'source'/name)==digest,'snapshot '+name)
  if attempt==2:require(sha(Path(name))==digest,'current source '+name)
 require(sha(bundle/'rust_binary')==assessment['rust_binary_sha256'],'binary snapshot')
 require(assessment['keyed_hash_evaluations']==assessment['world_transitions']==0 and assessment['sampling_admitted'] is False,'scope')
 counts={}
 for panel in ('literal','recorded'):
  count=0
  with (bundle/(panel+'-inputs.jsonl')).open() as ins,(bundle/('python-'+panel+'.jsonl')).open() as py,(bundle/('rust-'+panel+'.jsonl')).open() as rs:
   for ordinal,rows in enumerate(itertools.zip_longest(ins,py,rs)):
    require(all(row is not None for row in rows),'record census')
    req,a,b=map(json.loads,rows)
    require(json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True),'differential')
    if panel=='recorded':
     cell=req.pop('cell');slot=ordinal%128
     require(cell==dict(slot=slot,proposal=6000+slot//4,initial=ordinal%4),'mock coordinates')
     registered_input(req,14337+ordinal,registry)
     require(len(a['draws'])==119,'mock draws')
    else:registered_input(req,ordinal,registry)
    count+=1
  require(count==(17727 if panel=='literal' else 2916),'fixed count')
  counts[panel]=count
 for name,stage in assessment['stages'].items():
  total=(bundle/(name+'.jsonl')).stat().st_size+(bundle/(name+'.stderr')).stat().st_size
  require(stage['status']=='complete' and stage['returncode']==0 and stage['output_bytes']==total<=268435456 and stage['wall_seconds']<=60,'stage ceiling')
 receipts.append(dict(attempt=attempt,status='pass',inventory_entries=len(inventory),records=counts,checksums_sha256=sha(bundle/'checksums.json'),current_sources_verified=attempt==2))
for name in ('literal-inputs.jsonl','recorded-inputs.jsonl','rust_binary'):
 require(sha(Path('artifacts/p01o-implementation-001')/name)==sha(Path('artifacts/p01o-implementation-002')/name),'unchanged readiness input/binary')
for freeze in ['docs/p01o_registration_freeze.json','docs/p01n_registration_freeze.json','docs/p01k_execution_freeze.json']:
 for name,digest in load(Path(freeze))['files'].items():require(sha(Path(name))==digest,'frozen '+name)
prior=load(Path('docs/evidence/publication_inventory.json'))['files']
for row in prior:require(sha(Path(row['file']))==row['sha256'],'prior receipt')
result=dict(schema='p01o-implementation-integrity-audit-v1',status='pass',attempts=receipts,prior_public_receipts_verified=len(prior),keyed_hash_evaluations=0,adapter_executions=0,world_transitions=0,scope='read-only byte custody, independent registered-input coordinates, differential streams and ceilings; operation/static oracle remains implementation preflight',scientific_status='untested')
out=Path('artifacts/p01o-implementation-integrity-001');out.mkdir(exist_ok=False)
(out/'audit.py').write_bytes(Path(__file__).read_bytes());(out/'receipt.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result))
