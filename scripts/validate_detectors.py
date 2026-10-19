import copy
import json
import subprocess
import sys
import audit_detectors as checker

def validate(binary,out,run):
    directory=out/'detectors';run([str(binary),'detector-fixtures',str(directory)],out/'detectors.txt')
    suite=json.loads((directory/'suite.json').read_text());receipt=checker.audit_suite(suite);p=suite['protocol']
    rejected=[]
    for mutation in ('label','activity','membership','turnover','occupancy','intervention','fingerprint','disagreement'):
        c=copy.deepcopy(next(c for c in suite['cases'] if c['family']=='renewal'))
        if mutation=='label':c['maintenance_status']='not_supported'
        elif mutation=='activity':c['detection']['connected']['tracks'][0]['active_epochs']=0
        elif mutation=='membership':c['detection']['connected']['samples'][0][0]['members']=[0]
        elif mutation=='turnover':c['detection']['turnover']=False
        elif mutation=='occupancy':c['maintenance']['arms'][2]['occupancy']=8
        elif mutation=='intervention':c['maintenance']['arms'][2]['chain'][0]['request']['operations'][0]['value']=1
        elif mutation=='fingerprint':c['maintenance']['reference_fingerprint']='0'*64
        else:c['detection']['disagreement']=True
        try:checker.verify_case(c,p)
        except AssertionError:rejected.append(mutation)
        else:raise AssertionError(f'Detector audit accepted {mutation}')
    # New interpreter process: no Rust analysis functions are called by the checker.
    run([sys.executable,str(checker.Path(checker.__file__)),str(directory/'suite.json')],out/'detector-fresh-process-audit.txt')
    summary=[]
    for family,expected in p['expected'].items():
        group=[c for c in suite['cases'] if c['family']==family]
        summary.append({'family':family,'cases':len(group),'active_persistence':expected[0],'maintenance':expected[1],
                        'connected_supported':sum(c['detection']['connected']['supported'] for c in group),
                        'interaction_supported':sum(c['detection']['interaction']['supported'] for c in group)})
    receipt['families']=summary;receipt['tamper_rejections']=rejected
    (out/'detector_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
