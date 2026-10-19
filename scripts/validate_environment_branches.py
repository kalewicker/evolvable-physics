import copy
import json
import shutil
import subprocess
import audit_environment_branches as checker

def validate(binary,out,run):
    directory=out/'environment_branches'
    run([str(binary),'environment-branch-fixtures',str(directory)],out/'environment_branches.txt')
    suite=json.loads((directory/'suite.json').read_text());receipt=checker.audit_suite(suite)
    rejected=[]
    for name in ('source','schedule','ledger','operations','receipt','rescue','native','phase'):
        c=copy.deepcopy(suite['cases'][0]);target=c['arms'][2]['chain'][0]
        if name=='source':target['request']['expected_source']='0'*64
        elif name=='schedule':target['environment']['channels'][0]['period']=2
        elif name=='ledger':target['environment']['initial_activation']+=1;target['environment']['extracted']+=1
        elif name=='operations':target['request']['operations'][0]['value']=8
        elif name=='receipt':target['native_branch']['receipt']['parents']=[]
        elif name=='rescue':c['arms'][4]['chain'].pop()
        elif name=='native':c['arms'][2]['epochs'][0]['native_frame']['events']=[]
        else:c['arms'][2]['epochs'][0]['environment_events']=[]
        try:checker.verify_case(c)
        except AssertionError:rejected.append(name)
        else:raise AssertionError(f'Integrated auditor accepted {name}')
    for family in checker.FAMILIES:
        c=next(c for c in suite['cases'] if c['family']==family and c['initial']['native']['seed']==0)
        source=directory/f'{family}-source.json';original=source.read_bytes();bundle=out/f'{family}-environment-branch'
        run([str(binary),'environment-branch',str(source),str(directory/f'{family}-request.json'),str(bundle)],out/f'{family}-environment-branch.txt')
        assert checker.verify_bundle(bundle)==c['arms'][2]['chain'][0]['environment']
        resumed=out/f'{family}-integrated-resumed.json'
        run([str(binary),'environment-branch-resume',str(bundle),'6',str(resumed)],out/f'{family}-integrated-resume.txt')
        assert json.loads(resumed.read_text())==json.loads((directory/f'{family}-expected.json').read_text())
        req=out/f'{family}-environment-rescue-request.json';req.write_text(json.dumps(c['arms'][4]['chain'][1]['request']))
        rescue=out/f'{family}-environment-rescue'
        run([str(binary),'environment-branch',str(bundle/'checkpoint.json'),str(req),str(rescue)],out/f'{family}-environment-rescue.txt')
        assert checker.verify_bundle(rescue)==c['arms'][4]['chain'][1]['environment']
        resumed=out/f'{family}-integrated-rescue-resumed.json'
        run([str(binary),'environment-branch-resume',str(rescue),'6',str(resumed)],out/f'{family}-integrated-rescue-resume.txt')
        assert json.loads(resumed.read_text())['payload']==c['arms'][4]['epochs'][-1]['state']
        assert source.read_bytes()==original
    good=out/'state_arrest-environment-branch'
    rejected_bundles=[]
    for name in ('no_manifest','no_record','truncated_record','forged_receipt','schedule_drift','not_complete'):
        bad=out/f'incomplete-{name}';bad.mkdir()
        for p in good.iterdir():
            if (name=='no_manifest' and p.name=='manifest.json') or (name=='no_record' and p.name=='branch.json'):continue
            shutil.copyfile(p,bad/p.name)
        if name=='truncated_record':(bad/'branch.json').write_text('{partial')
        if name in ('forged_receipt','schedule_drift'):
            r=json.loads((bad/'branch.json').read_text())
            if name=='forged_receipt':r['native_branch']['receipt']['parents']=[]
            else:r['environment']['channels'][0]['period']=2
            (bad/'branch.json').write_text(json.dumps(r))
            # A matching declared record hash alone must not bypass semantic replay.
            m=json.loads((bad/'manifest.json').read_text());m['branch_digest']=checker.audit.digest(r);(bad/'manifest.json').write_text(json.dumps(m))
        if name=='not_complete':
            m=json.loads((bad/'manifest.json').read_text());m['execution_status']='running';(bad/'manifest.json').write_text(json.dumps(m))
        dest=out/f'{name}-wrongly-resumed.json'
        p=subprocess.run([str(binary),'environment-branch-resume',str(bad),'1',str(dest)],capture_output=True,text=True)
        (out/f'{name}-bundle-rejected.txt').write_text(p.stdout+p.stderr)
        assert p.returncode!=0 and not dest.exists();rejected_bundles.append(name)
        try:checker.verify_bundle(bad)
        except (AssertionError,FileNotFoundError,json.JSONDecodeError):pass
        else:raise AssertionError(f'Python accepted {name}')
    # A schedule-only source edit must invalidate an otherwise valid request.
    cp=json.loads((directory/'state_arrest-source.json').read_text());cp['payload']['channels'][0]['period']=2;cp['digest']=checker.audit.digest(cp['payload'])
    drift=out/'changed-schedule-source.json';drift.write_text(json.dumps(cp));dest=out/'stale-environment-branch'
    p=subprocess.run([str(binary),'environment-branch',str(drift),str(directory/'state_arrest-request.json'),str(dest)],capture_output=True,text=True)
    (out/'stale-wrapper-rejected.txt').write_text(p.stdout+p.stderr);assert p.returncode!=0 and not dest.exists()
    before={p.name:p.read_bytes() for p in good.iterdir()}
    p=subprocess.run([str(binary),'environment-branch',str(directory/'state_arrest-source.json'),str(directory/'state_arrest-request.json'),str(good)],capture_output=True,text=True)
    assert p.returncode!=0 and before=={p.name:p.read_bytes() for p in good.iterdir()}
    receipt.update(tamper_rejections=rejected,bundle_rejections=rejected_bundles,fresh_process_target_and_rescue='pass',stale_schedule_request_rejected='pass',no_overwrite='pass')
    (out/'environment_branch_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
