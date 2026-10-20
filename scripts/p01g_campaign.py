#!/usr/bin/env python3
"""Single fixed P01g batch using the existing worker, reporter and watchdog."""
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
import audit
import campaign
import generator_v2
import check_p01g_registration as registration
import p01g_cell
from campaign_guard import atomic_json

if not __debug__: raise RuntimeError('Campaign requires assertions')
ROOT=Path(__file__).resolve().parents[1]
load,sha=registration.load,registration.sha
STAGES=('generation','native','rust_report','python_audit')
class ReservationStop(Exception): pass


def check_execution(root=ROOT):
    freeze=load(root/'docs/p01g_execution_freeze.json'); admission=load(root/'docs/p01g_execution_admission.json')
    assert admission['schema']=='p01g-execution-admission-v1'
    assert admission['protocol_sha256']==sha(root/'docs/p01g_protocol.json')
    assert admission['execution_freeze_sha256']==sha(root/'docs/p01g_execution_freeze.json')
    assert admission['registration_freeze_sha256']==sha(root/'docs/p01g_registration_freeze.json')
    assert admission['admitted_output']=='artifacts/p01g-001' and admission['fixed_slots']==64
    assert admission['law_sampling_admitted'] is True and admission['e01_authorized'] is False
    for name,expected in freeze['files'].items():assert sha(root/name)==expected,name
    for name,expected in load(root/'docs/p01g_registration_freeze.json')['files'].items():assert sha(root/name)==expected,name
    for item in freeze['binaries'].values():assert sha(root/item['path'])==item['sha256']
    for section in ('dependencies','tools'):
        for name,expected in freeze[section].items():assert sha(Path(name))==expected,name
    registration.validate(load(root/'docs/p01g_protocol.json'))
    return freeze,admission


def stream_limits(protocol,name):
    p=protocol['per_process'][name]
    stderr=262144 if name=='native' else 65536
    return {'wall_seconds':p['wall_seconds'],'rss_bytes':p['sampled_rss_bytes'],
            'poll_seconds':protocol['campaign']['poll_seconds'],
            'stdout_bytes':p['output_bytes']-stderr,'stderr_bytes':stderr}


def launch_fits(protocol,usage,name):
    p=protocol['per_process'][name]; cap=protocol['campaign']
    return (usage['wall_seconds']+p['wall_seconds']+5<=cap['wall_seconds']
        and usage['total_process_cpu_seconds']+2*p['wall_seconds']+5<=cap['total_process_cpu_seconds']
        and usage['artifact_bytes']+p['output_bytes']+cap['metadata_reserve_bytes']<=cap['artifact_bytes'])


def stats(values):
    values=sorted(values)
    return {'count':len(values),'sum':sum(values),'median':statistics.median(values),
            'p95_nearest_rank':values[math.ceil(.95*len(values))-1],'maximum':values[-1]} if values else None


def summarize(protocol,rows,usage,execution_status):
    assert len(rows)==64
    for plan,row in zip(registration.planned_slots(protocol),rows):assert all(row[k]==v for k,v in plan.items())
    gate_rows=[{**{k:r[k] for k in ('slot','proposal','initial_state')},
                'status':r['status'],'full_horizon_verified':r.get('observation',{}).get('full_horizon_verified',False),
                'law_digest':r.get('law_digest'),**{k:r.get('observation',{}).get(k,[]) for k in
                ('attached_funded_birth_ids','visible_birth_ids','recycled_ids')}} for r in rows]
    mechanisms=registration.assess_mechanisms(protocol,gate_rows)
    resources=all(usage[k]<=protocol['campaign'][k] for k in ('wall_seconds','total_process_cpu_seconds','artifact_bytes'))
    full=all(r['status']=='complete' and r.get('observation',{}).get('full_horizon_verified')
             and set(r['stages'])==set(STAGES) and all(s['status']=='exited' for s in r['stages'].values()) for r in rows)
    engineering=execution_status=='complete' and full and resources
    decision='engineering_failure_or_incomplete' if not engineering else 'both_pass' if mechanisms['mechanism_gate_pass'] else 'engineering_pass_mechanism_fail'
    laws=[]
    for p in protocol['proposal_ids']:
        group=[r for r in rows if r['proposal']==p]
        digest=next((r.get('law_digest') for r in group if r.get('law_digest')),None)
        verified=[r for r in group if r['status'] in ('complete','censored')]
        laws.append({'proposal':p,'law_digest':digest,'initial_states':[
            {'initial_state':r['initial_state'],'status':r['status'],'full_horizon_ap':r.get('observation',{}).get('full_horizon_ap'),
             'prefix_counts':r.get('observation',{}).get('prefix_counts'),
             'full_horizon_counts':r.get('observation',{}).get('full_horizon_counts'),
             'missing_reason':None if r['status']=='complete' else r.get('reason',r['status'])} for r in group],
             'all_four_horizons_complete':all(r['status']=='complete' for r in group),
             'observed_trajectories_with_visible_birth':sum(bool(r['observation']['visible_birth_ids']) for r in verified),
             'observed_trajectories_with_visible_recycling':sum(bool(set(r['observation']['visible_birth_ids']) & set(r['observation']['recycled_ids'])) for r in verified)})
    stages={name:{key:stats([r['stages'][name].get(key,0) for r in rows if name in r['stages']])
                  for key in ('wall_seconds','child_cpu_seconds','guard_and_reaped_children_cpu_seconds',
                              'peak_sampled_rss_bytes','peak_rss_bytes','stdout_bytes','stderr_bytes')} for name in STAGES}
    return {'schema':'p01g-assessment-v1','law_denominator':16,'trajectory_denominator':64,
            'status_counts':dict(Counter(r['status'] for r in rows)),
            'full_horizon_ap_labels':dict(Counter(r['observation']['full_horizon_ap'] for r in rows if r['status']=='complete')),
            'distinct_observed_tables':len({r['law_digest'] for r in rows if r.get('law_digest')}),
            'engineering_gate_pass':engineering,**mechanisms,'continuation_gate_pass':engineering and mechanisms['mechanism_gate_pass'],
            'decision':decision,'laws':laws,'stage_costs':stages,
            'per_run_stage_child_cpu_seconds':stats([sum(r['stages'][n].get('child_cpu_seconds',0) for n in STAGES if n in r['stages']) for r in rows if r['stages']]),
            'per_run_stage_wall_seconds':stats([sum(r['stages'][n].get('wall_seconds',0) for n in STAGES if n in r['stages']) for r in rows if r['stages']]),
            'resource_usage_before_seal':usage,'scientific_status':'untested','e01_authorized':False}


def main():
    out=Path(sys.argv[1]).resolve();freeze,admission=check_execution()
    assert out==ROOT/admission['admitted_output']
    probe=subprocess.run(['ps','-o','rss=','-p',str(os.getpid())],capture_output=True,text=True,check=True)
    assert int(probe.stdout.strip())>0
    out.mkdir(parents=True,exist_ok=False)
    started,cpu_start=time.monotonic(),campaign.process_cpu()
    protocol=load(ROOT/'docs/p01g_protocol.json')
    manifest={'schema':'p01g-campaign-manifest-v1','execution_status':'preparing',
        'protocol_sha256':sha(ROOT/'docs/p01g_protocol.json'),
        'execution_freeze_sha256':sha(ROOT/'docs/p01g_execution_freeze.json'),
        'execution_admission_sha256':sha(ROOT/'docs/p01g_execution_admission.json'),
        'registration_freeze_sha256':sha(ROOT/'docs/p01g_registration_freeze.json'),
        'rows':[{**r,'status':'pending','stages':{}} for r in registration.planned_slots(protocol)],
        'scientific_status':'untested','e01_authorized':False}
    def save():atomic_json(out/'manifest.json',manifest)
    def usage():return {'wall_seconds':time.monotonic()-started,'total_process_cpu_seconds':campaign.process_cpu()-cpu_start,
                         'artifact_bytes':campaign.file_bytes(out)}
    def stage(row,name,command):
        if not launch_fits(protocol,usage(),name):raise ReservationStop(name)
        directory=out/'runs'/str(row['slot'])/name; directory.mkdir(parents=True)
        descriptor={'command':command,'cwd':str(out/'source'),'directory':str(directory),
                    'parent_pid':os.getpid(),'campaign_deadline':started+protocol['campaign']['wall_seconds'],
                    'limits':stream_limits(protocol,name)}
        if name=='native':descriptor['output_names']={'stdout':'trace.jsonl','stderr':'worker.json'}
        atomic_json(directory/'descriptor.json',descriptor)
        row['stages'][name]={'status':'running'};save()
        guard=subprocess.Popen([sys.executable,str(out/'source/scripts/campaign_guard.py'),
                                str(directory/'descriptor.json')],start_new_session=True)
        try:guard.wait()
        except BaseException:
            guard.terminate()
            try:guard.wait(timeout=3)
            except subprocess.TimeoutExpired:guard.kill();guard.wait()
            if (directory/'result.json').exists():
                row['stages'][name]=load(directory/'result.json');save()
            raise
        result=load(directory/'result.json');row['stages'][name]=result;save()
        assert guard.returncode==0 and result['status']=='exited',(name,result)
        assert max(result.get('peak_rss_bytes',0),result['peak_sampled_rss_bytes'])<=protocol['per_process'][name]['sampled_rss_bytes'], 'Reaped RSS'
        return directory
    save();current=None
    try:
        for name,expected in freeze['files'].items():
            dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
            assert sha(dest)==expected,name
        for name in ('p01g_execution_freeze.json','p01g_execution_admission.json'):
            shutil.copyfile(ROOT/'docs'/name,out/'source/docs'/name)
        deps={};(out/'dependencies').mkdir();(out/'bin').mkdir()
        for i,(name,expected) in enumerate(freeze['dependencies'].items()):
            dest=out/'dependencies'/str(i);shutil.copyfile(name,dest);assert sha(dest)==expected
            deps[str(i)]={'origin':name,'sha256':expected}
        atomic_json(out/'dependency_inventory.json',deps)
        for name,item in freeze['binaries'].items():
            dest=out/'bin'/name;shutil.copyfile(ROOT/item['path'],dest);dest.chmod(0o755);assert sha(dest)==item['sha256']
        manifest['execution_status']='running';save()
        proto=str(out/'source/docs/p01g_protocol.json');adm=str(out/'source/docs/p01g_execution_admission.json')
        tables={}
        for row in manifest['rows']:
            current=row;row['status']='generating';save()
            generated=stage(row,'generation',[str(out/'bin/generator-v2'),proto,adm,str(row['slot'])])
            initial=load(generated/'stdout.bin')
            assert initial==generator_v2.construct(row['proposal'],row['initial_state']), 'Independent pre-native sampler'
            table=audit.digest([{k:v for k,v in r.items() if k!='id'} for r in initial['native']['rules']])
            assert tables.setdefault(row['proposal'],table)==table, 'Same law across initial states'
            row.update(law_digest=table,status='generated');save()
            request=out/'runs'/str(row['slot'])/'request.json'
            atomic_json(request,{'schema':'p01-worker-request-v1','initial':initial,'epochs':protocol['epochs'],**protocol['worker_request']})
            native=stage(row,'native',[str(out/'bin/pilot-worker'),'run',str(request)])
            row['status']='native_measured';save()
            report=stage(row,'rust_report',[str(out/'bin/pilot-report'),str(request),str(native)])
            row['status']='reported';save()
            audited=stage(row,'python_audit',[sys.executable,str(out/'source/scripts/p01g_cell.py'),proto,adm,
                str(row['slot']),str(request),str(native),str(report/'stdout.bin')])
            receipt=load(audited/'stdout.bin')
            assert all(receipt[k]==row[k] for k in ('slot','proposal','initial_state','law_digest'))
            assert receipt['status'] in ('complete','censored')
            row.update(status=receipt['status'],observation=p01g_cell.compact(receipt),receipt_sha256=sha(audited/'stdout.bin'))
            if row['status']=='censored':row['reason']=receipt['worker_status']
            save();current=None
        manifest['execution_status']='complete'
    except ReservationStop as error:
        manifest.update(execution_status='budget_stopped',reason=str(error))
        if current:current.update(status='incomplete_budget' if current['stages'] else 'unstarted_budget',reason=str(error))
    except BaseException as error:
        manifest.update(execution_status='failed',error=repr(error))
        if current:current.update(status='failed',reason=repr(error))
        raise
    finally:
        for row in manifest['rows']:
            if row['status']=='pending':row.update(status='unstarted',reason=manifest.get('reason',manifest.get('error','preparation stopped')))
        try:check_execution()
        except BaseException as error:manifest.update(execution_status='failed',provenance_error=repr(error))
        assessment=summarize(protocol,manifest['rows'],usage(),manifest['execution_status'])
        manifest['assessment']=assessment;save();atomic_json(out/'assessment.json',assessment)
        inventory={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        atomic_json(out/'checksums.json',inventory)
        seal={'schema':'p01g-campaign-seal-v1','manifest_sha256':sha(out/'manifest.json'),'checksums_sha256':sha(out/'checksums.json'),
              'resource_usage':usage(),'engineering_gate_pass':assessment['engineering_gate_pass'],
              'mechanism_gate_pass':assessment['mechanism_gate_pass'],'continuation_gate_pass':assessment['continuation_gate_pass'],
              'decision':assessment['decision'],'overshoot':[],'scientific_status':'untested'}
        base=campaign.file_bytes(out)
        while True:
            before=json.dumps(seal,sort_keys=True,indent=2)+'\n'
            seal['resource_usage']['artifact_bytes']=base+len(before.encode())
            seal['overshoot']=[k for k,v in seal['resource_usage'].items() if v>protocol['campaign'][k]]
            if seal['overshoot']:
                seal.update(engineering_gate_pass=False,continuation_gate_pass=False,decision='engineering_failure_or_incomplete')
            if before==json.dumps(seal,sort_keys=True,indent=2)+'\n':break
        atomic_json(out/'seal.json',seal)
    print(json.dumps({k:seal[k] for k in ('engineering_gate_pass','mechanism_gate_pass','continuation_gate_pass','decision')}))

if __name__=='__main__':main()
