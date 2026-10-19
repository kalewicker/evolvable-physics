#!/usr/bin/env python3
"""Bounded control campaigns; never evaluates IDs 3000..3127."""
import copy
import json
import os
import signal
import subprocess
import shutil
from unittest.mock import patch
import sys
import time
from pathlib import Path
import audit_campaign
import audit_integration
import campaign
from campaign_guard import atomic_json


def protocol():
    p=json.loads((campaign.ROOT/'docs/p01_protocol.json').read_text())
    p.update(schema='p01c-engineering-controls-v1',proposal_ids={'start':2000,'count':1},denominator=4,epochs=12)
    p['worker']['max_trace_bytes']=1024**2
    p['supervisor']['wall_seconds']=2
    p['rust_analysis']['wall_seconds']=3;p['python_audit']['wall_seconds']=5
    p['campaign'].update(wall_seconds=120,total_process_cpu_seconds=120,trace_bytes=8*1024**2,
                         total_artifact_bytes=64*1024**2,metadata_reserve_bytes=1024**2)
    return p


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest={'schema':'p01c-readiness-v1','execution_status':'running','full_p01_started':False,
              'scientific_status':'untested','p01_ready':False,'checks':{}}
    atomic_json(out/'manifest.json',manifest)
    def save():atomic_json(out/'manifest.json',manifest)
    try:
        campaign.check_freezes()
        for name,cmd in [('tests',['cargo','test','--locked','--offline']),
                         ('python_tests',[sys.executable,'-m','unittest','discover','-s','scripts','-p','test_*.py']),
                         ('clippy',['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings']),
                         ('format',['cargo','fmt','--check']),
                         ('build',['cargo','build','--release','--locked','--offline','--bin','pilot-worker','--bin','pilot-report'])]:
            with (out/(name+'.txt')).open('x') as log:
                subprocess.run(cmd,cwd=campaign.ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        p=protocol();initial=audit_integration.initial('driven_pair',0)
        def run(name,configuration=None,faults=None,generated=False):
            config=configuration or copy.deepcopy(p)
            bundle=out/name
            m=campaign.run_campaign(bundle,config,mode='engineering_control',
                                    controls=None if generated else [initial]*config['denominator'],faults=faults)
            receipt=audit_campaign.verify(bundle);atomic_json(out/(name+'_audit.json'),receipt)
            manifest['checks'][name]={'manifest_sha256':campaign.sha(bundle/'manifest.json'),
                                     'seal_sha256':campaign.sha(bundle/'seal.json'),
                                     'execution_status':m['execution_status'],'summary':m['summary']}
            save();return m,receipt
        m,receipt=run('complete')
        assert receipt['accepted_endpoints']==4 and all(r['full_horizon_ap']=='supported' for r in m['runs'])
        assert not any(receipt['overshoots'].values())
        for name in ('event_cap','trace_cap'):
            c=copy.deepcopy(p);c['worker']['max_events' if name=='event_cap' else 'max_trace_bytes']=0
            m,_=run(name,c);assert all(r['status']=='verified_censored' and r['full_horizon_ap'] is None for r in m['runs'])
        for kind,key in [('wall','wall_seconds'),('cpu','total_process_cpu_seconds'),('trace','trace_bytes'),('artifact','total_artifact_bytes')]:
            c=copy.deepcopy(p);c['campaign'][key]=0
            m,_=run('campaign_'+kind,c);assert all(r['status']=='not_started_campaign_budget' for r in m['runs'])
        for stage in ('generate','native','rust','audit'):
            m,_=run('failure_'+stage,faults={(1,stage):'fail'},generated=stage=='generate')
            assert m['runs'][0]['status']=='verified_complete'
            assert m['runs'][1]['full_horizon_ap'] is None
            assert all(r['status']=='not_started_infrastructure' for r in m['runs'][2:])
            for stream in ('stdout','stderr'):
                m,_=run('overflow_'+stage+'_'+stream,faults={(0,stage):stream},generated=stage=='generate')
                assert m['runs'][0]['status']==stage+'_'+stream+'_budget_exceeded'
                assert m['runs'][0]['full_horizon_ap'] is None
        for fault in ('rss','sleep','bad_summary','bad_report'):
            stage='rust' if fault=='bad_report' else 'native'
            m,_=run('forced_'+fault,faults={(0,stage):fault})
            assert m['runs'][0]['full_horizon_ap'] is None
            if fault in ('rss','sleep'):assert m['runs'][0]['status']==stage+('_rss_budget_exceeded' if fault=='rss' else '_wall_budget_exceeded')
            else:assert m['execution_status']=='failed'
        for checkpoint,answers in [('before_rust',[True,True,False]),('before_audit',[True,True,True,False])]:
            with patch.object(campaign,'can_launch',side_effect=answers):
                m,_=run('injected_budget_'+checkpoint)
            assert m['runs'][0]['status']=='campaign_budget_'+checkpoint
            assert m['runs'][0]['full_horizon_ap'] is None
            assert all(r['status']=='not_started_campaign_budget' for r in m['runs'][1:])
        for name,path in [('manifest','manifest.json'),('trace','runs/0/native/trace.jsonl')]:
            duplicate=out/('tamper_'+name);shutil.copytree(out/'complete',duplicate)
            with (duplicate/path).open('ab') as f:f.write(b' ')
            try:audit_campaign.verify(duplicate)
            except (AssertionError,ValueError):pass
            else:raise AssertionError('Tampered sealed bundle accepted')
            manifest['checks']['tamper_'+name]='rejected; original retained'
        # Existing output paths cannot be reopened, including after successful sealing.
        before=campaign.sha(out/'complete/seal.json')
        try:campaign.run_campaign(out/'complete',p,mode='engineering_control',controls=[initial]*4)
        except FileExistsError:pass
        else:raise AssertionError('Reopened output')
        assert campaign.sha(out/'complete/seal.json')==before
        manifest['checks']['exclusive_output']='pass'
        cancellation=out/'cancel_guard';cancellation.mkdir()
        descriptor={'command':[sys.executable,'-c','import time; time.sleep(10)'],
                    'directory':str(cancellation),'cwd':str(cancellation),'parent_pid':os.getpid(),
                    'campaign_deadline':time.monotonic()+10,
                    'limits':dict(campaign.stage_limits(p,'native'),wall_seconds=5)}
        atomic_json(cancellation/'descriptor.json',descriptor)
        cancelled=subprocess.Popen([sys.executable,str(campaign.ROOT/'scripts/campaign_guard.py'),str(cancellation/'descriptor.json')])
        deadline=time.monotonic()+5
        while not (cancellation/'live.json').exists() and time.monotonic()<deadline:time.sleep(.02)
        assert (cancellation/'live.json').exists()
        cancelled.terminate();cancelled.wait(timeout=3)
        assert json.loads((cancellation/'result.json').read_text())['status']=='parent_cancelled'
        manifest['checks']['guard_cancellation']='child killed and reaped'
        config=out/'crash-protocol.json';atomic_json(config,p)
        process=subprocess.Popen([sys.executable,str(campaign.ROOT/'scripts/campaign_control_child.py'),str(out/'parent_loss'),str(config)])
        assert process.wait(timeout=15)==91
        guard_result=out/'parent_loss/runs/0/native/result.json'
        deadline=time.monotonic()+5
        while not guard_result.exists() and time.monotonic()<deadline:time.sleep(.05)
        result=json.loads(guard_result.read_text());assert result['status']=='parent_lost'
        if (guard_result.parent/'live.json').exists():
            child=json.loads((guard_result.parent/'live.json').read_text())['child_pid']
            try:os.kill(child,0)
            except ProcessLookupError:pass
            else:raise AssertionError('Orphan worker remains alive')
        crash_receipt=audit_campaign.verify(out/'parent_loss')
        assert crash_receipt['registered_slots']==4 and crash_receipt['accepted_endpoints']==0
        assert crash_receipt['execution_status']=='interrupted_unsealed'
        atomic_json(out/'parent_loss_audit.json',crash_receipt)
        manifest['checks']['parent_loss']='guard reaped child; unsealed endpoints rejected'
        manifest.update(execution_status='complete',p01_ready=True,full_campaign_slots_launched=0,
                        source_freeze_sha256=campaign.sha(campaign.ROOT/'docs/p01c_freeze.json'))
        receipt={k:manifest[k] for k in ('schema','execution_status','p01_ready','full_p01_started','scientific_status',
                                        'source_freeze_sha256','full_campaign_slots_launched','checks')}
        atomic_json(out/'readiness_audit.json',receipt)
    except BaseException as error:
        manifest.update(execution_status='failed',error=repr(error));raise
    finally:
        save()
        inventory={str(f.relative_to(out)):campaign.sha(f) for f in out.rglob('*') if f.is_file() and f!=out/'checksums.json'}
        atomic_json(out/'checksums.json',inventory)
    print(json.dumps({'execution_status':manifest['execution_status'],'p01_ready':manifest['p01_ready'],'checks':len(manifest['checks'])},indent=2))


if __name__=='__main__':main()
