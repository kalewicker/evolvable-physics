import json,subprocess,time,hashlib
from pathlib import Path
out=Path('artifacts/p01n-readiness-driver-001'); out.mkdir(exist_ok=False)
(out/'driver.py').write_bytes(Path(__file__).read_bytes())
start=time.monotonic(); stages=[]
commands=[['python3','scripts/validate_p01n.py','artifacts/p01n-readiness-001'],['python3','scripts/audit_p01n_readiness.py','artifacts/p01n-readiness-001',str(out/'receipt_audit.json')]]
for i,command in enumerate(commands):
 with (out/f'stage-{i}.log').open('x') as log:
  try:
   result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=max(0.001,300-(time.monotonic()-start)))
   code=result.returncode
  except subprocess.TimeoutExpired:
   code='aggregate_timeout'
 stages.append(dict(command=command,returncode=code))
 print(stages[-1],flush=True)
 if code: break
elapsed=time.monotonic()-start
receipt=dict(stages=stages,wall_seconds_including_readonly_custody_audit=elapsed,aggregate_ceiling_seconds=300,aggregate_pass=elapsed<=300 and len(stages)==2 and all(s['returncode']==0 for s in stages),scientific_status='untested')
(out/'completion.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
raise SystemExit(not receipt['aggregate_pass'])
