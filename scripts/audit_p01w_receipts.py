#!/usr/bin/env python3
"""P01w independent receipt audit; stdlib only, no replay or campaign imports.

Observation proof checks originate in the frozen P01q receipt algorithm.
Aggregation and inventory/guard verification below are separately implemented.
"""
import hashlib
import json
import math
import statistics
from collections import Counter
import sys
import time
from pathlib import Path

def need(ok,why):
    if not ok:raise ValueError(why)
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def load(p):
    def pairs(items):
        need(len(items)==len({k for k,v in items}),'duplicate keys');return dict(items)
    value=json.loads(Path(p).read_bytes(),object_pairs_hook=pairs);encoded(value);return value
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(encoded(x)).hexdigest()
def validate_observations(receipt):
    need(receipt['independent_events_pass'] is True, 'observation invariant')
    obs = receipt['prefix_observations']
    counts = {key: len(obs[key]) for key in ('births', 'recycling', 'visibility', 'additional_structural_funding', 'descendant_construction', 'orphaning', 'visible_birth_recycle_ids', 'cleanup_events')}
    counts['ordered_branch'] = len({(*r['roles'], r['cleanup_form']) for r in obs['ordered_branch']})
    need(counts['ordered_branch'] == obs['ordered_branch_count'], 'observation invariant')
    need(receipt['prefix_counts'] == counts, 'observation invariant')
    need(receipt['full_horizon_counts'] == (counts if receipt['full_horizon_verified'] else None), 'observation invariant')
    if not receipt['full_horizon_verified']:
        need(receipt['full_horizon_ap'] is None, 'observation invariant')
    born = {b['node']: b for b in obs['births']}
    clean = {c['event']: c for c in obs['cleanup_events']}
    funds = {f['event']: f for f in obs['additional_structural_funding']}
    for f in funds.values():
        need(f['recipient'] in born and born[f['recipient']]['birth_event'] == f['birth_event'] < f['event'], 'observation invariant')
    for d in obs['descendant_construction']:
        need(d['donor'] in born and born[d['donor']]['birth_event'] == d['donor_birth_event'] < d['event'], 'observation invariant')
        need(born[d['node']]['birth_event'] == d['event'] and born[d['node']]['donor'] == d['donor'], 'observation invariant')
    for c in clean.values():
        need(c['form'] in (6, 7) and c['donor'] != c['child'], 'observation invariant')
        recycle = c['form'] == 7
        need(c['child_survives'] is (not recycle) and c['burn'] == int(recycle), 'observation invariant')
        need(c['returned_matter'] == (c['child_before'][0] + 2 if recycle else 1), 'observation invariant')
        need(c['returned_activation'] == (c['child_before'][1] if recycle else 0), 'observation invariant')
        need([c['donor_after'][i] - c['donor_before'][i] for i in (0, 1)] == [c['returned_matter'], c['returned_activation'] - c['burn']], 'observation invariant')
    for b in obs['ordered_branch']:
        P, C, G = b['roles']
        need(len({P, C, G}) == 3, 'observation invariant')
        ids = b['events']
        need(len(ids) == 6 and all((a < c for a, c in zip(ids, ids[1:]))), 'observation invariant')
        need((born[C]['donor'], born[C]['birth_event']) == (P, ids[0]), 'observation invariant')
        need((born[G]['donor'], born[G]['birth_event']) == (C, ids[3]), 'observation invariant')
        for e in ids[1:3]:
            need((funds[e]['donor'], funds[e]['recipient'], funds[e]['matter']) == (P, C, 1), 'observation invariant')
        need((clean[ids[4]]['donor'], clean[ids[4]]['child'], clean[ids[4]]['form']) == (C, G, b['cleanup_form']), 'observation invariant')
        need((clean[ids[5]]['donor'], clean[ids[5]]['child'], clean[ids[5]]['form']) == (P, C, 7), 'observation invariant')
        need(b['creation_edges'] == [clean[ids[5]]['edge'], clean[ids[4]]['edge']], 'observation invariant')
        need([p['event'] for p in b['phase_balances']] == ids, 'observation invariant')
        need(all((ids[0] < e < ids[-1] and e not in ids for e in b['intervening_events'])), 'observation invariant')
    return counts

def gates(rows):
    need(len(rows)==128,'128 rows');tables={};visible=set();loops=set();eligible=0;stopped=False
    for slot,row in enumerate(rows):
        need([row[k] for k in ('slot','proposal','initial')]==[slot,6000+slot//4,slot%4],'ordered identity')
        need(all(type(row[k]) is int for k in ('slot','proposal','initial')),'identity types')
        need(row['status'] in ('complete','failed','censored','unstarted'),'terminal status')
        need(not stopped or row['status']=='unstarted','no execution after stop')
        stopped|=row['status']!='complete'
        if row.get('law_digest'):
            h=row['law_digest'];need(len(h)==64 and set(h)<=set('0123456789abcdef'),'table digest')
            need(tables.setdefault(row['proposal'],h)==h,'four initial table equality')
        if row['status']!='complete':continue
        obs=row['observation'];need(obs['full_horizon_verified'] is True and obs['observed_epochs']==128,'eligible horizon')
        b=set(obs['attached_funded_birth_ids']);v=set(obs['visible_birth_ids']);r=set(obs['recycled_ids'])
        need(v<=b and r<=b,'same-trajectory birth');eligible+=1
        if v:visible.add(row['law_digest'])
        if v&r:loops.add(row['law_digest'])
    return eligible,len(visible) if eligible else None,len(loops) if eligible else None

def verify(out,require_closure=True):
    started=time.monotonic();out=Path(out);clock_checks=0
    def tick():
        nonlocal clock_checks
        clock_checks+=1;need(time.monotonic()-started<=175,'audit wall reserve')
    inv=load(out/'checksums.json');seal=load(out/'seal.json');manifest=load(out/'manifest.json')
    need(seal['schema']=='p01w-campaign-seal-v1' and manifest['schema']=='p01w-saved-panel-dynamics-manifest-v1','schemas')
    files={str(p.relative_to(out)):p for p in out.rglob('*') if p.is_file()};need(set(files)==set(inv)|{'checksums.json','seal.json'},'complete inventory membership')
    for name,e in inv.items():
        tick();need(not Path(name).is_absolute() and '..' not in Path(name).parts,'inventory path')
        need(files[name].stat().st_size==e['size'] and sha(files[name])==e['sha256'],'inventory bytes '+name)
    need(sha(out/'checksums.json')==seal['checksums_sha256'] and sha(out/'manifest.json')==seal['manifest_sha256'],'seal links')
    total=sum(p.stat().st_size for p in files.values());need(seal['known_path_bytes']==total,'known output bytes')
    need(seal['usage_upper_bound_bytes']==total+seal['extra_bound_bytes'],'byte bound')
    need(seal['output_bytes']==(total if seal['exact_bytes'] else None),'exact byte label')
    p=load(out/'source/docs/p01w_protocol.json') if require_closure else load(out/'protocol.json')
    cap=p['campaign'];need(seal['usage_upper_bound_bytes']<=cap['artifact_bytes'],'artifact ceiling')
    need(seal['terminal_wall_upper_seconds']<=cap['wall_seconds'] and seal['terminal_cpu_upper_seconds']<=cap['total_process_cpu_seconds'],'aggregate limits')
    need(seal['terminal_wall_upper_seconds']==seal['usage_before_seal']['wall_seconds']+5 and seal['terminal_cpu_upper_seconds']==seal['usage_before_seal']['total_process_cpu_seconds']+5,'terminal reserves')
    if require_closure:
        source=out/'source';f=load(source/'docs/p01w_execution_freeze.json');a=load(source/'docs/p01w_execution_admission.json')
        need(a['schema']=='p01w-execution-admission-v1' and a['world_execution_admitted'] is True,'admission')
        for key in ('protocol','registration_freeze','execution_freeze'):
            need(sha(source/f'docs/p01w_{key}.json')==a[key+'_sha256'],'admission link')
        for name,h in f['files'].items():need(inv['source/'+name]['sha256']==h,'source snapshot')
        for section in ('saved_requests','production_binaries','prerequisite_receipts'):
            for name,h in p[section].items():need(f['files'].get(name)==h,'protocol snapshot coverage')
        for bundle,h in p['source_bundles'].items():
            need(inv['source/'+bundle+'/seal.json']['sha256']==h,'original source seal')
            old=load(source/bundle/'checksums.json');oldseal=load(source/bundle/'seal.json')
            need(inv['source/'+bundle+'/checksums.json']['sha256']==oldseal['checksums_sha256'] and inv['source/'+bundle+'/manifest.json']['sha256']==oldseal['manifest_sha256'],'original source links')
            need({n.removeprefix('source/'+bundle+'/') for n in inv if n.startswith('source/'+bundle+'/')}==set(old)|{'checksums.json','seal.json'},'original source membership')
            for n,h in old.items():need(inv['source/'+bundle+'/'+n]['sha256']==h,'original source bytes')
        for key in ('protocol','execution_freeze','execution_admission'):
            need(manifest['provenance'][key+'_sha256']==sha(source/f'docs/p01w_{key}.json'),'manifest provenance')
        allowed={'source/'+n for n in f['files']}|{'source/docs/p01w_execution_freeze.json','source/docs/p01w_execution_admission.json'}
        need({n for n in inv if n.startswith('source/')}==allowed,'snapshot membership')
        dep=load(out/'dependency_inventory.json')
        need({n:e['sha256'] for n,e in dep.items()}=={**f['dependencies'],**f['tools']},'dependency inventory')
        for n,e in dep.items():need(inv[e['file']]['sha256']==e['sha256'],'dependency snapshot')
        reg=load(source/'docs/p01w_registration_freeze.json')
        for section in ('files','inputs','prior_public_receipts'):
            for n,h in reg[section].items():need(f['files'].get(n)==h,'registered closure')
    initial=load(out/'initial_manifest.json')
    need(initial['schema']=='p01w-initial-manifest-v1' and len(initial['rows'])==128,'initialized denominator')
    for i,row in enumerate(initial['rows']):
        need(row==dict(slot=i,proposal=6000+i//4,initial=i%4,status='unstarted',stages=[dict(role=r,status='unstarted') for r in ('native','rust_report','python_audit')]),'initialized slots')
    rows=manifest['rows'];eligible,visible,loops=gates(rows);stages=0;child_cpu=0;physical_stages=0
    for row in rows:
        tick();slot=row['slot'];base=f'runs/{slot:03}'
        need([s['role'] for s in row['stages']]==['native','rust_report','python_audit'],'stage order')
        stopped=False
        for stage in row['stages']:
            role=stage['role'];need(stage['status'] in ('unstarted','complete','failed'),'stage status')
            need(not stopped or stage['status']=='unstarted','stage prefix');stopped|=stage['status']!='complete'
            g=stage.get('guard')
            if not g:
                need(stage['status']!='complete','missing successful guard');continue
            physical_stages+=int(g['launched'])
            need(g==load(out/base/role/'guard.json'),'guard receipt')
            for stream in ('stdout','stderr'):
                filename=f'{base}/{role}/{stream}.bin'
                need(g[stream+'_file']==filename and inv[filename]['size']==g[stream+'_bytes'],'stream bytes')
                need(inv[filename]['sha256']==stage[stream+'_sha256'],'stream digest')
            child_cpu+=g.get('child_cpu_seconds') or 0
            if stage['status']=='complete':
                s=p['per_process'][role];c=p['production_contracts'][role]
                need(g['launched'] is True and g['status']=='complete' and g['returncode']==0 and g['pre_input_sample'] is True and g['rss_samples']>0,'successful guard')
                need(0<=g['wall_seconds']<=s['wall_seconds'] and 0<=g['child_cpu_seconds'],'stage cost')
                need(max(g['peak_rss_bytes'],g['peak_sampled_rss_bytes'])<=s['sampled_rss_bytes'],'stage RSS')
                for stream in ('stdout','stderr'):need(g[stream+'_bytes']==g[stream+'_observed_bytes']<=c[stream+'_cap_bytes'],'stream cap')
                need(g['stdout_bytes']+g['stderr_bytes']<=s['output_bytes'],'combined cap');stages+=1
            if require_closure:
                req=str((out/base/'request.json').resolve());directory=str((out/base).resolve())
                commands={'native':[str((out/'source/target/release/pilot-worker').resolve()),'run',req],
                    'rust_report':[str((out/'source/target/release/pilot-report').resolve()),req,directory],
                    'python_audit':[f['interpreter'],'-I','-B',str((out/'source/scripts/p01w_cell.py').resolve()),req,directory]}
                need(g['argv']==commands[role],'exact production argv')
                expected={commands[role][0]:f['tools'][f['interpreter']] if role=='python_audit' else p['production_binaries']['target/release/pilot-worker' if role=='native' else 'target/release/pilot-report']}
                if role=='python_audit':expected[commands[role][3]]=f['files']['scripts/p01w_cell.py']
                need(g['identities']==expected,'executor identities')
        if row.get('law_digest'):
            request=load(out/base/'request.json')
            need(digest([{k:v for k,v in rule.items() if k!='id'} for rule in request['initial']['native']['rules']])==row['law_digest'],'all admitted table identities')
            need(inv[base+'/request.json']['sha256']==row['input_sha256'],'admitted request identity')
            if require_closure:need(row['input_sha256']==p['saved_requests'][p['request_bundle']+f'/requests/{slot:03}.json'],'registered request identity')
        if row['status'] in ('failed','unstarted'):need(not row.get('observation'),'unverified observations')
        if row['status'] in ('complete','censored'):
            proof=load(out/base/'python_audit/stdout.bin');need(proof['schema']=='p01w-cell-audit-v1','cell schema')
            need(all(proof[k]==row[k] for k in ('slot','proposal','initial','law_digest','status')),'cell binding')
            need(row['receipt_sha256']==inv[base+'/python_audit/stdout.bin']['sha256'],'cell receipt digest')
            need(proof['full_horizon_verified'] is (row['status']=='complete'),'coverage')
            validate_observations(proof)
            for key,v in row['observation'].items():need(proof[key]==v,'compact observation')
            for key,name in [('request','request.json'),('trace','trace.jsonl'),('summary','worker.json'),('report','report.json')]:
                need(proof['inputs_sha256'][key]==inv[base+'/'+name]['sha256'],'cell input chain')
            # Copies must match the guarded original streams, not merely each other.
            for dest,stage,stream in [('trace.jsonl','native','stdout'),('worker.json','native','stderr'),('report.json','rust_report','stdout')]:
                need(inv[base+'/'+dest]['sha256']==inv[f'{base}/{stage}/{stream}.bin']['sha256'],'stream copy')
            request=load(out/base/'request.json');law=digest([{k:v for k,v in r.items() if k!='id'} for r in request['initial']['native']['rules']])
            need(law==row['law_digest'],'law identity')
            obs=proof['prefix_observations'];report=load(out/base/'report.json');worker=load(out/base/'worker.json')
            need(report['request_digest']==digest(request) and report['worker_result_digest']==digest(worker),'canonical report digests')
            need(proof['observed_epochs']==worker['epochs']==report['observed_epochs'] and proof['observed_events']==worker['events'],'observed count binding')
            need(report['trace_bytes']==worker['trace_bytes']==inv[base+'/trace.jsonl']['size'],'trace byte binding')
            for key,records in [('attached_funded_birth_ids','births'),('visible_birth_ids','visibility'),('recycled_ids','recycling')]:
                need(proof[key]==obs[key]==sorted(x['node'] for x in obs[records]),'event ID proof')
            births={x['node']:x for x in obs['births']};deletions={x['node']:x for x in obs['recycling']}
            for v in obs['visibility']:
                need(v['node'] in births and v['sample']>=births[v['node']]['birth_sample'],'visibility birth')
                for estimator in ('connected','interaction'):need(v[estimator] in report['prefix_detection'][estimator]['samples'][v['sample']] and v['node'] in v[estimator]['members'],'visibility proof')
                if v['node'] in deletions:need(v['sample']<deletions[v['node']]['sample'],'visibility before recycle')
            for v in deletions.values():need(v['node'] in births and v['birth_event']==births[v['node']]['birth_event']<v['deletion_event'],'recycle birth')
            need(obs['visible_birth_recycle_ids']==sorted(set(proof['visible_birth_ids'])&set(proof['recycled_ids'])),'loop identity')
            need(proof['full_horizon_ap']==report['full_horizon_ap'],'detector AP unchanged')
    u=seal['usage_before_seal']
    need(u['live_cpu_upper_seconds']==0 and u['total_process_cpu_seconds']==u['controller_and_reaped_cpu_seconds']+u['failed_stage_cpu_upper_seconds'],'CPU components')
    need(child_cpu<=u['controller_and_reaped_cpu_seconds']+1e-9,'child CPU accounting')
    counts=seal['counts_before_seal'];need(counts['output_scans']==1 and counts['poll_scans']==counts['closeout_scans']==0,'no polling scans')
    need(counts['launches']==counts['reaped']==physical_stages,'stage launch/reap counts')
    need(counts['write_bytes']==sum(e['size'] for e in inv.values())+files['checksums.json'].stat().st_size,'emitted ledger bytes')
    a=manifest['assessment'];mechanism=None if not eligible else visible>=2 and loops>=1
    engineering=eligible==128 and stages==384 and manifest['first_error'] is None and not manifest['closeout_errors'] and seal['exact_bytes']
    need(a['eligible_trajectories']==eligible and a['distinct_tables_with_visible_birth']==visible and a['distinct_tables_with_same_trajectory_visible_birth_recycle_loop']==loops,'gate counts')
    need(a['engineering_gate_pass'] is engineering and a['mechanism_gate_pass'] is mechanism and a['continuation_gate_pass'] is (engineering and mechanism is True),'gates')
    decision='engineering_failure_or_incomplete' if not engineering else 'both_pass' if mechanism else 'engineering_pass_mechanism_fail'
    need(a['decision']==decision and manifest['e01_authorized'] is False and manifest['scientific_status']=='untested','decision')
    need(a['law_denominator']==32 and a['trajectory_denominator']==128,'reported denominators')
    need(a['status_counts']==dict(Counter(r['status'] for r in rows)),'reported status counts')
    need(a['full_horizon_ap_labels']==dict(Counter(r['observation']['full_horizon_ap'] for r in rows if r['status']=='complete')),'reported AP counts')
    need(len(a['laws'])==32,'reported law denominator')
    for pr,law in zip(range(6000,6032),a['laws']):
        group=[r for r in rows if r['proposal']==pr]
        need(law['proposal']==pr and law['law_digest']==next((r.get('law_digest') for r in group if r.get('law_digest')),None),'reported law identity')
        expected=[dict(initial=r['initial'],status=r['status'],prefix_counts=r.get('observation',{}).get('prefix_counts'),full_horizon_counts=r.get('observation',{}).get('full_horizon_counts') if r['status']=='complete' else None,full_horizon_ap=r.get('observation',{}).get('full_horizon_ap') if r['status']=='complete' else None,missing_reason=None if r['status']=='complete' else r.get('error',r['status'])) for r in group]
        need(law['initial_states']==expected,'reported missingness and metrics')
    need(set(a['stage_costs'])=={'native','rust_report','python_audit'},'complete stage cost roles')
    for role,metrics in a['stage_costs'].items():
        need(set(metrics)=={'wall_seconds','child_cpu_seconds','peak_sampled_rss_bytes','peak_rss_bytes','stdout_bytes','stderr_bytes'},'complete cost metrics')
        need(role in ('native','rust_report','python_audit'),'reported stage role')
        for metric,value in metrics.items():
            values=sorted(s['guard'][metric] for row in rows for s in row['stages'] if s['role']==role and s.get('guard',{}).get(metric) is not None)
            expected=None if not values else dict(count=len(values),sum=sum(values),median=statistics.median(values),p95_nearest_rank=values[math.ceil(.95*len(values))-1],maximum=values[-1])
            need(value==expected,'reported stage cost distribution')

    for field,metric in [('per_run_stage_child_cpu_seconds','child_cpu_seconds'),('per_run_stage_wall_seconds','wall_seconds')]:
        values=sorted(sum(s.get('guard',{}).get(metric) or 0 for s in row['stages']) for row in rows if any(s.get('guard') for s in row['stages']))
        expected=None if not values else dict(count=len(values),sum=sum(values),median=statistics.median(values),p95_nearest_rank=values[math.ceil(.95*len(values))-1],maximum=values[-1])
        need(a[field]==expected,'per-run cost distribution')
    need(manifest['status']==seal['status']==('pass' if manifest['first_error'] is None and seal['exact_bytes'] else 'fail'),'terminal status')
    return dict(schema='p01w-independent-receipt-audit-v1',status='pass',engineering_gate_pass=engineering,mechanism_gate_pass=mechanism,
        cells=128,verified_cell_receipts=sum(r['status'] in ('complete','censored') for r in rows),guarded_stages=physical_stages,
        inventory_files=len(files),retained_bytes=total,world_replay_executed=False,wall_seconds=time.monotonic()-started,clock_checks=clock_checks)

if __name__=='__main__':
    start=time.monotonic();result=verify(Path(sys.argv[1]));target=Path(sys.argv[2]);target.mkdir(exist_ok=False)
    raw=encoded(result);need(len(raw)<=134217728-1048576 and time.monotonic()-start<=175,'audit output reserve')
    (target/'audit.json').write_bytes(raw);need(time.monotonic()-start<=180,'audit terminal wall')
    print(raw.decode())
