import copy
import hashlib
import json
import sys
import shutil
import tempfile
from pathlib import Path
import audit_generalization as checker
ROOT=Path(__file__).resolve().parents[1]

def check_freeze():
    frozen=json.loads((ROOT/'docs/p00f_freeze.json').read_text())
    assert frozen['schema']=='p00f-source-freeze-v1'
    for name,expected in frozen['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,f'frozen source drift: {name}'
    # The registered receipt records the P00e baseline identity. Runtime validation
    # must not depend on ignored historical artifact directories being present.
    return frozen

def portable_freeze_check():
    global ROOT
    original=ROOT
    frozen=check_freeze()
    with tempfile.TemporaryDirectory(prefix='p00f-source-freeze-') as temp:
        clean=Path(temp)
        for name in [*frozen['files'], 'docs/p00f_freeze.json']:
            target=clean/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(original/name,target)
        try:
            ROOT=clean
            assert not (ROOT/'artifacts').exists()
            assert check_freeze()==frozen
        finally:
            ROOT=original

def admission(out,panel):
    requirements=json.loads((ROOT/'docs/p00_admission_requirements.json').read_text())
    rows=[]
    for req in requirements['requirements']:
        row=copy.deepcopy(req);source=ROOT/req['source'];assert source.is_file()
        row['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
        row['evidence_hashes']={}
        for name in req['evidence']:
            path=out/('source/'+name if name.startswith('docs/') else name)
            assert path.is_file(),name
            row['evidence_hashes'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
        if row['id']=='detector_generalization_panel':
            row['status']='passed_with_explicit_scope_limits' if panel['panel_accepted'] else 'failed_registered_panel'
            row['blocks_p00']=not panel['panel_accepted']
        rows.append(row)
    blockers=[r['id'] for r in rows if r['blocks_p00']]
    receipt={'schema':'p00f-admission-audit-v1','requirements':rows,'blocking_requirements':blockers,'p00_admitted':not blockers,
             'p01_execution_readiness':requirements['p01_execution_readiness'],'p01_started':False,'e01_started':False,
             'scientific_status':'untested','decision':requirements['decision']}
    (out/'p00_admission_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

def validate(binary,out,run):
    frozen=check_freeze();portable_freeze_check();directory=out/'generalization'
    run([str(binary),'generalization-panel',str(directory)],out/'generalization.txt')
    suite=json.loads((directory/'suite.json').read_text());receipt=checker.audit_suite(suite)
    p=suite['protocol'];base=json.loads(checker.detector.REGISTRY.read_text())
    rejected=[]
    for mutation in ('generator','scope','summary','fingerprint','expected_label','event_omission','encoding'):
        c=copy.deepcopy(next(c for c in suite['cases'] if c['family']=='chain4'))
        if mutation=='generator':c['initial']['world']['nodes']['0']['kind']=999
        elif mutation=='scope':c['scope']='negative_control'
        elif mutation=='summary':c['detection']['active_persistence']='not_supported'
        elif mutation=='fingerprint':c['initial_fingerprint']='0'*64
        elif mutation=='expected_label':c['expected_ap']='not_supported'
        elif mutation=='event_omission':c['frames'][0]['events']=[]
        else:c['encoding']='unknown'
        try:checker.verify_case(c,p,base)
        except AssertionError:rejected.append(mutation)
        else:raise AssertionError(f'Generalization checker accepted {mutation}')
    receipt['tamper_rejections']=rejected;receipt['source_freeze']=frozen;receipt['source_only_freeze_check']='pass'
    (out/'generalization_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    run([sys.executable,str(Path(checker.__file__)),str(directory/'suite.json')],out/'generalization-fresh-process.txt')
    receipt['admission']=admission(out,receipt)
    check_freeze()
    return receipt
