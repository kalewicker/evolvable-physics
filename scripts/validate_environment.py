import copy
import json
import subprocess
import audit_environment as checker

def validate(binary,out,run):
    directory=out/'environment'
    run([str(binary),'environment-fixtures',str(directory)],out/'environment.txt')
    suite=json.loads((directory/'suite.json').read_text())
    receipt=checker.audit_suite(suite)
    base=next(c for c in suite['cases'] if c['mode']=='driven')
    rejected=[]
    for name in ('ledger','order','contact','parent','prepared','schedule','native','skip'):
        c=copy.deepcopy(base)
        if name=='ledger': c['epochs'][0]['state']['injected']+=1
        elif name=='order': c['epochs'][0]['environment_events'].reverse()
        elif name=='contact': c['initial']['channels'][1]['action']['to']=3
        elif name=='parent': c['epochs'][0]['environment_events'][1]['parents']=[]
        elif name=='prepared': c['epochs'][0]['prepared']['world']['nodes']['1']['activation']=99
        elif name=='schedule': c['initial']['channels'][0]['period']=2
        elif name=='native': c['epochs'][0]['native_frame']['events']=[]
        else: c['epochs'][0]['environment_events'][0]['status']='insufficient_resource'
        try: checker.verify_case(c)
        except AssertionError: rejected.append(name)
        else: raise AssertionError(f'Environment auditor accepted {name}')
    for mode in checker.MODES:
        cp=directory/f'{mode}-checkpoint.json';original=cp.read_bytes()
        resumed=out/f'{mode}-environment-resumed.json'
        run([str(binary),'environment-resume',str(cp),'5',str(resumed)],out/f'{mode}-environment-resume.txt')
        assert json.loads(resumed.read_text())==json.loads((directory/f'{mode}-expected.json').read_text())
        assert cp.read_bytes()==original
    cp=directory/'driven-checkpoint.json'
    valid=json.loads(cp.read_text())
    for name in ('truncated','digest','profile'):
        bad=out/f'environment-{name}.json'
        altered=copy.deepcopy(valid)
        if name=='truncated': bad.write_bytes(cp.read_bytes()[:99])
        else:
            if name=='digest': altered['payload']['injected']+=1
            else:
                altered['payload']['profile']='unknown'
                altered['digest']=checker.audit.digest(altered['payload'])
            bad.write_text(json.dumps(altered))
        dest=out/f'environment-{name}-accepted.json'
        p=subprocess.run([str(binary),'environment-resume',str(bad),'1',str(dest)],capture_output=True,text=True)
        (out/f'environment-{name}-rejected.txt').write_text(p.stdout+p.stderr)
        assert p.returncode!=0 and not dest.exists()
    # Prevent silently resuming only the embedded native world, losing its environment.
    p=subprocess.run([str(binary),'resume',str(cp),'1',str(out/'wrong-profile.json')],capture_output=True,text=True)
    assert p.returncode!=0 and not (out/'wrong-profile.json').exists()
    (out/'environment-native-loader-rejected.txt').write_text(p.stdout+p.stderr)
    receipt.update(tamper_rejections=rejected,fresh_process_continuation='pass',damaged_checkpoint_rejections='pass',native_loader_profile_separation='pass')
    (out/'environment_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
