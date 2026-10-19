import copy
import hashlib
import json
import sys
from pathlib import Path
import audit_integration as checker
ROOT=Path(__file__).resolve().parents[1]

def admission(out,receipt):
    addon=json.loads((ROOT/'docs/p00g_admission_addendum.json').read_text())
    assert hashlib.sha256((ROOT/addon['base_requirements']).read_bytes()).hexdigest()==addon['base_requirements_sha256']
    prior=json.loads((out/'p00_admission_audit.json').read_text());rows=copy.deepcopy(prior['requirements'])
    good=receipt['status']=='pass' and receipt['logging_equivalent_epochs']==4256 and receipt['external_only_activity_rejected'] and receipt['mixed_islands_not_pooled'] and receipt['environment_maintenance_controls']=='pass' and receipt['native_engine_equivalence_cases']==320 and receipt['fresh_process_mode_switch']=='pass'
    for row in rows:
        if row['id'] in addon['updates']:
            update=addon['updates'][row['id']];row.update(status='supported_in_registered_profiles' if good else 'not_supported',blocks_p00=not good,source=update['source'],limit=update['limit'],evidence=[update['required_evidence']])
            row['source_sha256']=hashlib.sha256((ROOT/row['source']).read_bytes()).hexdigest()
            row['evidence_hashes']={update['required_evidence']:hashlib.sha256((out/update['required_evidence']).read_bytes()).hexdigest()}
    blockers=[r['id'] for r in rows if r['blocks_p00']]
    result={'schema':'p00g-admission-audit-v1','base_assessment':'p00_admission_audit.json','addendum_digest':checker.audit.digest(addon),'requirements':rows,
            'blocking_requirements':blockers,'p00_admitted':not blockers,'admission_scope':'bounded engineering profiles and disclosed fixture panels',
            'p01_execution_readiness':prior['p01_execution_readiness'],'p01_ready':False,'p01_started':False,'e01_started':False,'scientific_status':'untested'}
    (out/'p00g_admission_audit.json').write_text(json.dumps(result,indent=2)+'\n');return result

def validate(binary,out,run):
    directory=out/'integration';run([str(binary),'integration-fixtures',str(directory)],out/'integration.txt')
    suite=json.loads((directory/'suite.json').read_text());receipt=checker.audit_suite(suite);p=suite['protocol']
    mutations=('prepared','environment','ledger','quiet_digest','external_activity','native','occupancy','rescue')
    rejected=[]
    for name in mutations:
        family='driven_renewal' if name in ('occupancy','rescue') else 'external_flux'
        c=copy.deepcopy(next(c for c in suite['cases'] if c['family']==family))
        if name=='prepared':c['epochs'][0]['prepared']['world']['nodes']['1']['state']=9
        elif name=='environment':c['epochs'][0]['environment_events']=[]
        elif name=='ledger':c['epochs'][0]['state']['injected']+=1
        elif name=='quiet_digest':c['disabled_digests'][0]='0'*64
        elif name=='external_activity':c['detection']['active_persistence']='supported'
        elif name=='native':c['epochs'][0]['native_frame']['events']=[{'id':0,'candidate':{'rule':0,'binding':[1,2],'priority':'0'*64,'reads':[],'writes':[]},'parents':[]}]
        elif name=='occupancy':c['maintenance']['arms'][2]['occupancy']=8
        else:c['maintenance']['arms'][4]['chain'].pop()
        try:checker.verify_case(c,p)
        except AssertionError:rejected.append(name)
        else:raise AssertionError(f'Integration checker accepted {name}')
    receipt['tamper_rejections']=rejected
    run([sys.executable,str(Path(checker.__file__)),str(directory/'suite.json')],out/'integration-fresh-process-audit.txt')
    for family in p['families']:
        cp=directory/f'{family}-checkpoint.json';expected=json.loads((directory/f'{family}-expected.json').read_text());source_bytes=cp.read_bytes()
        for mode in ('environment-resume','environment-resume-quiet'):
            dest=out/f'{family}-{mode}.json'
            run([str(binary),mode,str(cp),'9',str(dest)],out/f'{family}-{mode}.txt')
            assert json.loads(dest.read_text())==expected
        quiet=out/f'{family}-quiet-midpoint.json'
        run([str(binary),'environment-resume-quiet',str(cp),'4',str(quiet)],out/f'{family}-quiet-midpoint.txt')
        mixed=out/f'{family}-mixed.json';run([str(binary),'environment-resume',str(quiet),'5',str(mixed)],out/f'{family}-mixed.txt')
        assert json.loads(mixed.read_text())==expected and cp.read_bytes()==source_bytes
    # Native checkpoint continuation with exported output disabled is the same state too.
    cp=out/'fixtures/checkpoint.json';dest=out/'native-quiet-resumed.json'
    run([str(binary),'resume-quiet',str(cp),'7',str(dest)],out/'native-quiet-resume.txt')
    assert json.loads(dest.read_text())==json.loads((out/'fixtures/expected.json').read_text())
    cases=0
    for name,want in (('detectors',144),('generalization',176)):
        dest=out/f'{name}-engine-equivalence.json'
        run([str(binary),'analysis-equivalence',str(out/name/'suite.json'),str(dest)],out/f'{name}-engine-equivalence.txt')
        r=json.loads(dest.read_text());assert r['all_outputs_equal'] and r['cases']==want;cases+=r['cases']
    receipt['native_engine_equivalence_cases']=cases;receipt['fresh_process_mode_switch']='pass'
    (out/'integration_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    receipt['admission']=admission(out,receipt)
    return receipt
