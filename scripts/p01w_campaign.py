#!/usr/bin/env python3
"""Single P01w attempt; original worker/reporter and admission-gated Python replay."""
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path
if __name__=='__main__':
    sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
from p01w_guard import Output,ROLES,need,parse,encoded,sha,typed,run_stage,probe
ROOT=Path(__file__).resolve().parents[1]

def summary(rows,p,integrity):
    need(len(rows)==128,'fixed denominator');visible=set();loops=set();tables={};eligible=0
    for slot,row in enumerate(rows):
        need(typed([row[k] for k in ('slot','proposal','initial')])==typed([slot,6000+slot//4,slot%4]),'fixed row')
        table=row.get('law_digest')
        if table is not None:need(tables.setdefault(row['proposal'],table)==table,'four-initial table')
        if row['status']!='complete':continue
        obs=row['observation'];need(obs['full_horizon_verified'] is True and obs['observed_epochs']==128,'complete horizon')
        born=set(obs['attached_funded_birth_ids']);vis=set(obs['visible_birth_ids']);recycled=set(obs['recycled_ids'])
        need(vis<=born and recycled<=born,'same newborn identity');eligible+=1
        if vis:visible.add(table)
        if vis&recycled:loops.add(table)
    mechanism=None if not eligible else len(visible)>=2 and len(loops)>=1
    engineering=integrity and eligible==128 and all(all(s['status']=='complete' for s in r['stages']) for r in rows)
    def distribution(values):
        values=sorted(values)
        return None if not values else dict(count=len(values),sum=sum(values),median=statistics.median(values),p95_nearest_rank=values[math.ceil(.95*len(values))-1],maximum=max(values))
    stage_costs={role:{metric:distribution([s['guard'][metric] for r in rows for s in r['stages'] if s['role']==role and s.get('guard',{}).get(metric) is not None])
        for metric in ('wall_seconds','child_cpu_seconds','peak_sampled_rss_bytes','peak_rss_bytes','stdout_bytes','stderr_bytes')} for role in ROLES}
    return dict(schema='p01w-assessment-v1',law_denominator=32,trajectory_denominator=128,
        status_counts=dict(Counter(r['status'] for r in rows)),eligible_trajectories=eligible,
        distinct_tables_with_visible_birth=len(visible) if eligible else None,
        distinct_tables_with_same_trajectory_visible_birth_recycle_loop=len(loops) if eligible else None,
        mechanism_evidence='assessed_complete_trajectories' if eligible else 'not_assessed_no_eligible_trajectories',
        engineering_gate_pass=engineering,mechanism_gate_pass=mechanism,continuation_gate_pass=engineering and mechanism is True,
        decision='engineering_failure_or_incomplete' if not engineering else 'both_pass' if mechanism else 'engineering_pass_mechanism_fail',
        stage_costs=stage_costs,per_run_stage_child_cpu_seconds=distribution([sum(s.get('guard',{}).get('child_cpu_seconds') or 0 for s in r['stages']) for r in rows if any(s.get('guard') for s in r['stages'])]),
        per_run_stage_wall_seconds=distribution([sum(s.get('guard',{}).get('wall_seconds') or 0 for s in r['stages']) for r in rows if any(s.get('guard') for s in r['stages'])]),full_horizon_ap_labels=dict(Counter(r['observation']['full_horizon_ap'] for r in rows if r['status']=='complete')),
        laws=[dict(proposal=pr,law_digest=tables.get(pr),initial_states=[dict(initial=r['initial'],status=r['status'],prefix_counts=r.get('observation',{}).get('prefix_counts'),
            full_horizon_counts=r.get('observation',{}).get('full_horizon_counts') if r['status']=='complete' else None,
            full_horizon_ap=r.get('observation',{}).get('full_horizon_ap') if r['status']=='complete' else None,
            missing_reason=None if r['status']=='complete' else r.get('error',r['status'])) for r in rows if r['proposal']==pr]) for pr in range(6000,6032)],
        scientific_status='untested',e01_authorized=False)

def command(role,pins,request,directory):
    if role=='native':return [pins['worker'],'run',str(request)]
    if role=='rust_report':return [pins['reporter'],str(request),str(directory)]
    need(role=='python_audit','role');return [pins['python'],'-I','-B',pins['cell'],str(request),str(directory)]

def canonical(raw):
    need(raw.endswith(b'\n'),'complete JSON newline');value=parse(raw)
    need(encoded(value)+b'\n'==raw,'canonical JSON');return value

def check_stage(role,stdout,stderr,raw,prior,row):
    if role=='native':
        result=canonical(stderr);need(result['schema']=='p01-worker-result-v1','worker schema')
        need(set(result)==set('schema status epochs events native_events applicable_candidates trace_bytes step_ns serialize_ns write_ns final_state'.split()),'worker fields')
        frames=stdout.splitlines(keepends=True)
        for line in frames:canonical(line)
        need(result['trace_bytes']==len(stdout) and result['epochs']==len(frames)<=128,'worker trace binding')
        need(result['status']!='complete' or len(frames)==128,'worker complete horizon')
        return result
    if role=='rust_report':
        need(not stderr,'report diagnostics');result=canonical(stdout)
        need(result['schema']=='p01-detector-report-v1','report schema')
        need(set(result)==set('schema request_digest worker_result_digest trace_bytes worker_status requested_epochs observed_epochs coverage full_horizon_ap prefix_detection maintenance_status scientific_status'.split()),'report fields')
        need(result['worker_status']==prior['worker']['status'] and result['maintenance_status']=='not_assessed' and result['scientific_status']=='untested','report labels')
        need(result['request_digest']==sha(encoded(parse(raw))) and result['worker_result_digest']==sha(encoded(prior['worker'])),'report input digests')
        need(result['trace_bytes']==len(prior['trace_raw']) and result['observed_epochs']==prior['worker']['epochs'] and result['requested_epochs']==128,'report coverage binding')
        need(result['coverage'] in ('complete','censored_prefix'),'coverage')
        if result['coverage']=='complete':need(result['observed_epochs']==128 and prior['worker']['status']=='complete','complete report')
        else:need(result['full_horizon_ap'] is None,'censored AP')
        return result
    need(not stderr,'audit diagnostics');result=canonical(stdout)
    need('inert' not in result and 'plumbing_complete' not in result.values(),'inert audit forbidden')
    need(result['schema']=='p01w-cell-audit-v1' and result['scientific_status']=='untested','audit schema')
    for k in ('slot','proposal','initial','law_digest'):need(typed(result[k])==typed(row[k]),'audit identity '+k)
    complete=prior['report']['coverage']=='complete'
    need(result['status']==('complete' if complete else 'censored') and result['full_horizon_verified'] is complete,'audit coverage')
    need(result['observed_epochs']==prior['report']['observed_epochs'] and result['observed_events']==prior['worker']['events'],'audit observations')
    need(result['full_horizon_ap']==prior['report']['full_horizon_ap'] and result['independent_events_pass'] is True,'independent checks')
    need(result['inputs_sha256']==dict(request=sha(raw),trace=sha(prior['trace_raw']),summary=sha(prior['worker_raw']),report=sha(prior['report_raw'])),'audit input chain')
    need(result['full_horizon_counts']==(result['prefix_counts'] if complete else None),'full horizon counts')
    return result

def pipeline(out,descriptors,reader,native_rows,pins,invoke=None):
    need(__debug__,'assert-enabled campaign required')
    from p01w_cell import admit_request,compact
    invoke=invoke or run_stage;tables={}
    try:
        need(len(descriptors)==len(native_rows)==128,'all128 descriptors')
        for row,desc,native in zip(out.rows,descriptors,native_rows):
            current=None
            try:
                out.poll();row['status']='admitting_input'
                need(typed([desc[k] for k in ('slot','proposal','initial')])==typed([row[k] for k in ('slot','proposal','initial')]),'descriptor order')
                raw=reader(desc['file']);streams=[reader(n) for n in desc['streams']]
                request,law=admit_request(raw,desc['sha256'],streams,desc['stream_hashes'],row,native)
                rules=request['initial']['native']['rules'];need(typed(tables.setdefault(row['proposal'],rules))==typed(rules),'ordered table across initials')
                row.update(law_digest=law,input_sha256=sha(raw));base=f"runs/{row['slot']:03}";directory=out.root/base
                out.write(base+'/request.json',raw);out.write(base+'/identity.json',encoded({k:row[k] for k in ('slot','proposal','initial','law_digest')}))
                previous={}
                for current,role in zip(row['stages'],ROLES):
                    current['status']='running';argv=command(role,pins,directory/'request.json',directory)
                    identities={argv[0]:pins['hashes'][argv[0]]}
                    if role=='python_audit':identities[pins['cell']]=pins['hashes'][pins['cell']]
                    guard,stdout,stderr=invoke(out,role,argv,base+'/'+role,identities)
                    current.update(guard=guard,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
                    need(guard['status']=='complete','stage guard')
                    result=check_stage(role,stdout,stderr,raw,previous,row)
                    if role=='native':
                        previous.update(worker=result,trace_raw=stdout,worker_raw=stderr)
                        out.write(base+'/trace.jsonl',stdout);out.write(base+'/worker.json',stderr)
                    elif role=='rust_report':
                        previous.update(report=result,report_raw=stdout);out.write(base+'/report.json',stdout)
                    else:row.update(status=result['status'],observation=compact(result),receipt_sha256=sha(stdout))
                    current['status']='complete'
                if row['status']=='censored':raise ValueError('censored trajectory; preserve prefix and stop')
            except Exception as error:
                if current is not None and current['status']=='running':current.update(status='failed',error=repr(error))
                if row['status']!='censored':row['status']='failed'
                row['error']=repr(error);out.first_error=repr(error);break
    except Exception as error:out.first_error=repr(error)

def main(output):
    need(__debug__,'assert-enabled campaign required')
    from check_p01w_execution import review,publication_check
    p=parse((ROOT/'docs/p01w_protocol.json').read_bytes())
    need(Path(output).resolve()==ROOT/p['execution_output'],'fixed output')
    review(ROOT);publication_check(ROOT);capability=probe()
    # This mkdir consumes the attempt; no retry or deletion path exists.
    out=Output(output,p);provenance={}
    try:
        freeze=parse((ROOT/'docs/p01w_execution_freeze.json').read_bytes());admission=parse((ROOT/'docs/p01w_execution_admission.json').read_bytes())
        provenance=dict(protocol_sha256=sha((ROOT/'docs/p01w_protocol.json').read_bytes()),execution_freeze_sha256=sha((ROOT/'docs/p01w_execution_freeze.json').read_bytes()),execution_admission_sha256=sha((ROOT/'docs/p01w_execution_admission.json').read_bytes()),capability=capability)
        cache={};seen={}
        # One inside-attempt custody pass; all snapshots and writes charged.
        for section in ('files','dependencies','tools'):
            for name,h in freeze[section].items():
                out.poll();path=Path(name) if Path(name).is_absolute() else ROOT/name
                if str(path) in seen:need(seen[str(path)]==h,'closure conflict');continue
                raw=path.read_bytes();need(sha(raw)==h,'within-attempt custody '+name);seen[str(path)]=h
                if not Path(name).is_absolute():cache[name]=raw;dest='source/'+name
                else:dest='dependencies/'+sha(name.encode())
                out.write(dest,raw)
        for name in ('docs/p01w_execution_freeze.json','docs/p01w_execution_admission.json'):
            if name not in cache:out.write('source/'+name,(ROOT/name).read_bytes())
        out.write('dependency_inventory.json',encoded({n:dict(file='dependencies/'+sha(n.encode()),sha256=h) for n,h in {**freeze['dependencies'],**freeze['tools']}.items()}))
        reg=parse(cache['docs/p01w_registration_freeze.json']);descriptors=[]
        for row in out.rows:
            slot=row['slot'];name=f'artifacts/p01t-002/requests/{slot:03}.json'
            streams=[f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin' for lang in ('rust_generation','python_generation')]
            descriptors.append({**{k:row[k] for k in ('slot','proposal','initial')},'file':name,'sha256':p['saved_requests'][name],
                'streams':streams,'stream_hashes':[reg['inputs'][n] for n in streams]})
        pins={k:str((out.root/'source'/v).resolve()) for k,v in [('worker','target/release/pilot-worker'),('reporter','target/release/pilot-report'),('cell','scripts/p01w_cell.py')]}
        pins['python']=freeze['interpreter'];pins['hashes']={pins['worker']:p['production_binaries']['target/release/pilot-worker'],pins['reporter']:p['production_binaries']['target/release/pilot-report'],pins['cell']:freeze['files']['scripts/p01w_cell.py'],pins['python']:freeze['tools'][pins['python']]}
        # Snapshots preserve bytes; executable permissions are set only on owned copies.
        for key in ('worker','reporter'):(Path(pins[key])).chmod(0o500)
        native=parse(cache['artifacts/p01u-001/manifest.json'])['rows']
        pipeline(out,descriptors,cache.__getitem__,native,pins)
    except Exception as error:out.first_error=repr(error)
    assessment=summary(out.rows,p,out.first_error is None and out.exact)
    result=out.finish(assessment,provenance);print(encoded(result).decode());return int(result['status']!='pass')

if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
