#!/usr/bin/env python3
"""One guarded fixed witness batch, reusing the frozen campaign guard."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import campaign
import check_p01f_registration as registration
from campaign_guard import atomic_json

if not __debug__:
    raise RuntimeError('Validation requires assertions')
ROOT = Path(__file__).resolve().parents[1]
sha, load = registration.sha, registration.load


def check_execution(root=ROOT):
    freeze = load(root/'docs/p01f_execution_freeze.json')
    admission = load(root/'docs/p01f_execution_admission.json')
    assert admission['execution_freeze_sha256']==sha(root/'docs/p01f_execution_freeze.json')
    assert admission['registration_freeze_sha256']==sha(root/'docs/p01f_registration_freeze.json')
    assert admission['admitted_output']=='artifacts/p01f-001' and admission['fixed_slots']==48
    assert admission['native_execution_admitted'] is True
    assert not admission['law_sampling_admitted'] and not admission['e01_authorized']
    for name, expected in freeze['files'].items(): assert sha(root/name)==expected, name
    assert sha(root/freeze['binary']['path'])==freeze['binary']['sha256'], 'Binary'
    for section in ('dependencies','tools'):
        for name, expected in freeze[section].items(): assert sha(Path(name))==expected, name
    for name, expected in load(root/'docs/p01f_registration_freeze.json')['files'].items():
        assert sha(root/name)==expected, name
    campaign.check_freezes()
    for name, expected in load(root/'docs/p01e_freeze.json')['files'].items():
        assert sha(root/name)==expected, name
    registration.validate(load(root/'docs/p01f_protocol.json'),load(root/'docs/p01f_witnesses.json'))
    return freeze, admission


def launch_fits(usage, limits, cap):
    # Single-threaded fixed children; reserve guard/serial ps CPU and sealing.
    return (usage['wall_seconds']+limits['wall_seconds']+5 <= cap['wall_seconds']
            and usage['total_process_cpu_seconds']+2*limits['wall_seconds']+5 <= cap['total_process_cpu_seconds']
            and usage['artifact_bytes']+limits['output_bytes']+2*1024**2 <= cap['artifact_bytes'])


def main():
    out = Path(sys.argv[1]).resolve()
    # Check access/source identities before consuming the single output path.
    freeze, admission = check_execution()
    assert out==ROOT/admission['admitted_output'], 'Only registered attempt path'
    probe = subprocess.run(['ps','-o','rss=','-p',str(os.getpid())],capture_output=True,text=True,check=True)
    assert int(probe.stdout.strip())>0, 'RSS access'
    out.mkdir(parents=True,exist_ok=False)
    started, cpu_start = time.monotonic(), campaign.process_cpu()
    protocol=load(ROOT/'docs/p01f_protocol.json'); execution=protocol['future_execution']
    manifest={'schema':'p01f-execution-manifest-v1','execution_status':'preparing',
              'execution_freeze_sha256':sha(ROOT/'docs/p01f_execution_freeze.json'),
              'execution_admission_sha256':sha(ROOT/'docs/p01f_execution_admission.json'),
              'registration_freeze_sha256':sha(ROOT/'docs/p01f_registration_freeze.json'),
              'slots':[{'slot':i,'family':f['id'],'seed':s,'status':'pending'}
                       for i,(f,s) in enumerate((f,s) for f in load(ROOT/'docs/p01f_witnesses.json')['families']
                                                for s in protocol['scheduler_seeds'])],
              'stages':{},'gate_pass':False,'scientific_status':'untested','law_sampling_admitted':False}
    def save(): atomic_json(out/'manifest.json',manifest)
    def usage():
        return {'wall_seconds':time.monotonic()-started,
                'total_process_cpu_seconds':campaign.process_cpu()-cpu_start,
                'artifact_bytes':campaign.file_bytes(out)}
    def stage(name, command, limits):
        assert launch_fits(usage(),limits,execution['campaign']), 'Launch reservation'
        directory=out/'stages'/name; directory.mkdir(parents=True)
        descriptor={'command':command,'cwd':str(out/'source'),'directory':str(directory),
                    'parent_pid':os.getpid(),'campaign_deadline':started+execution['campaign']['wall_seconds'],
                    'limits':{'wall_seconds':limits['wall_seconds'],'rss_bytes':limits['sampled_rss_bytes'],
                              'poll_seconds':execution['poll_seconds'],
                              'stdout_bytes':limits['output_bytes']-65536,'stderr_bytes':65536}}
        atomic_json(directory/'descriptor.json',descriptor)
        manifest['stages'][name]={'status':'running'}; save()
        guard=subprocess.Popen([sys.executable,str(out/'source/scripts/campaign_guard.py'),
                                str(directory/'descriptor.json')],start_new_session=True)
        try: guard.wait()
        except BaseException:
            guard.terminate()
            try: guard.wait(timeout=3)
            except subprocess.TimeoutExpired: guard.kill(); guard.wait()
            raise
        result=load(directory/'result.json'); manifest['stages'][name]=result; save()
        assert guard.returncode==0 and result['status']=='exited', (name,result)
        assert max(result.get('peak_rss_bytes',0),result['peak_sampled_rss_bytes'])<=limits['sampled_rss_bytes'], 'Reaped peak RSS'
        return directory/'stdout.bin'
    save()
    try:
        for name in freeze['files']:
            dest=out/'source'/name; dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        for name in ('p01f_execution_freeze.json','p01f_execution_admission.json'):
            shutil.copyfile(ROOT/'docs'/name,out/'source/docs'/name)
        # Copy the complete pinned crate-source closure and tool identities as
        # retained provenance, outside the public compact evidence selection.
        dep_inventory={}
        for i,(name,expected) in enumerate(freeze['dependencies'].items()):
            dest=out/'dependencies'/str(i); dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(name,dest); assert sha(dest)==expected
            dep_inventory[str(i)]={'origin':name,'sha256':expected}
        atomic_json(out/'dependency_inventory.json',dep_inventory)
        binary=out/'bin/reachability-witness'; binary.parent.mkdir()
        shutil.copyfile(ROOT/freeze['binary']['path'],binary); binary.chmod(0o755)
        assert sha(binary)==freeze['binary']['sha256']
        for name,expected in freeze['files'].items(): assert sha(out/'source'/name)==expected, name
        manifest['execution_status']='running'; save()
        protocol_path=str(out/'source/docs/p01f_protocol.json')
        registry_path=str(out/'source/docs/p01f_witnesses.json')
        trace=stage('native',[str(binary),protocol_path,registry_path],execution['native_panel_process'])
        rows=[json.loads(line) for line in trace.read_bytes().splitlines()]
        for row in rows:
            index=row['slot']
            assert 0<=index<48 and manifest['slots'][index]['status']=='pending', 'Slot identity'
            manifest['slots'][index]['status']='measured'
        save()
        receipt_path=stage('audit',[sys.executable,str(out/'source/scripts/p01f_audit.py'),
                                   protocol_path,registry_path,str(trace)],execution['python_audit_process'])
        receipt=load(receipt_path)
        atomic_json(out/'panel_audit.json',receipt)
        for row in receipt['cases']: manifest['slots'][row['slot']]['status']=row['status']
        manifest['gate_pass']=receipt['status']=='pass' and all(r['status']=='pass' for r in manifest['slots'])
        manifest['execution_status']='complete'
    except BaseException as error:
        manifest.update(execution_status='failed',error=repr(error))
        raise
    finally:
        # Check original sources again; a changing source invalidates admission.
        try: check_execution()
        except BaseException as error:
            manifest.update(execution_status='failed',gate_pass=False,provenance_error=repr(error))
        manifest['resource_usage_before_seal']=usage(); save()
        inventory={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        atomic_json(out/'checksums.json',inventory)
        seal={'schema':'p01f-execution-seal-v1','manifest_sha256':sha(out/'manifest.json'),
              'checksums_sha256':sha(out/'checksums.json'),'resource_usage':usage(),
              'gate_pass':manifest['gate_pass'],'overshoot':[],'scientific_status':'untested'}
        base_bytes=campaign.file_bytes(out)
        while True:
            before=json.dumps(seal,sort_keys=True,indent=2)+'\n'
            seal['resource_usage']['artifact_bytes']=base_bytes+len(before.encode())
            seal['overshoot']=[key for key,value in seal['resource_usage'].items() if value>execution['campaign'][key]]
            seal['gate_pass']=manifest['gate_pass'] and not seal['overshoot']
            if before==json.dumps(seal,sort_keys=True,indent=2)+'\n': break
        atomic_json(out/'seal.json',seal)
    print(json.dumps({'gate_pass':seal['gate_pass'],'status':manifest['execution_status']}))

if __name__=='__main__': main()
