#!/usr/bin/env python3
"""Post-run descriptive accounting only; never changes or resumes a campaign."""
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
import audit_campaign
import campaign


def distribution(values):
    if not values: return None
    values=sorted(values)
    return {'n':len(values),'mean':statistics.mean(values),'median':statistics.median(values),
            'p95_nearest_rank':values[math.ceil(.95*len(values))-1],'maximum':values[-1]}


def describe(manifest):
    p=manifest['protocol'];rows=manifest['runs']
    assert len(rows)==p['denominator']==512
    assert [(r['proposal'],r['initial_state']) for r in rows]==[(p,i) for p in range(3000,3128) for i in range(4)]
    labels=Counter();statuses=Counter();laws=defaultdict(list);stage_values=defaultdict(lambda:defaultdict(list))
    costs=defaultdict(list);started=0;verified_epochs=events=candidates=0
    for row in rows:
        statuses[row['status']]+=1;laws[row['proposal']].append(row)
        if row['status']=='verified_complete':
            assert row['coverage']=='complete' and row['full_horizon_ap'] in ('supported','not_supported','inconclusive')
            assert row['observed_epochs']==p['epochs']
            labels[row['full_horizon_ap']]+=1
        elif row['status']=='verified_censored':
            assert row['coverage']=='censored_prefix' and row['full_horizon_ap'] is None;labels['censored']+=1
        else:
            assert row['coverage']=='unmeasured' and row['full_horizon_ap'] is None
            labels['not_started' if row['status'].startswith('not_started_') else 'unmeasured_started']+=1
        if row['status'].startswith('verified_'):
            verified_epochs+=row['observed_epochs'];events+=row['events'];candidates+=row['applicable_candidates']
        if row['stages']:
            started+=1
            for key in ('wall_seconds','child_cpu_seconds'):
                costs[key].append(sum(s.get(key,0) for s in row['stages'].values()))
        for name,result in row['stages'].items():
            for key in ('wall_seconds','child_cpu_seconds','peak_rss_bytes','peak_sampled_rss_bytes','stdout_bytes','stderr_bytes'):
                if key in result:stage_values[name][key].append(result[key])
    assert sum(labels.values())==512 and len(laws)==128
    law_labels=Counter()
    for states in laws.values():
        assert len(states)==4
        ap=[r['full_horizon_ap'] for r in states]
        if 'supported' in ap: law_labels['at_least_one_verified_supported_state']+=1
        elif all(a=='not_supported' for a in ap):law_labels['all_four_not_supported']+=1
        elif all(a in ('not_supported','inconclusive') for a in ap):law_labels['inconclusive_without_verified_support']+=1
        else:law_labels['censored_or_unmeasured_without_verified_support']+=1
    assert sum(law_labels.values())==128
    return {'registered_laws':128,'registered_states':512,'requested_epochs_per_state':p['epochs'],
            'started_slots':started,'status_counts':dict(statuses),
            'endpoint_counts_all_512':{k:labels[k] for k in ('supported','not_supported','inconclusive','censored','unmeasured_started','not_started')},
            'complete_case_endpoint_counts':{k:labels[k] for k in ('supported','not_supported','inconclusive')},
            'law_outcomes_all_128':{k:law_labels[k] for k in ('at_least_one_verified_supported_state','all_four_not_supported',
                'inconclusive_without_verified_support','censored_or_unmeasured_without_verified_support')},
            'independently_verified_prefix_epochs':verified_epochs,'independently_verified_events':events,
            'independently_verified_applicable_candidates':candidates,
            'started_slot_costs_including_censored_lower_observations':{k:distribution(v) for k,v in costs.items()},
            'stage_distributions_started_including_censored_lower_observations':{
                name:{k:distribution(v) for k,v in values.items()} for name,values in stage_values.items()},
            'scope':'descriptive development observations; nested initial states; no hypothesis test or confirmatory prevalence',
            'maintenance_status':'not_assessed','scientific_status':'untested','e01_authorized':False}


def declared_native(bundle,row):
    if row['stages'].get('native',{}).get('status')!='exited':return None
    try:
        declared=json.loads((bundle/'runs'/str(row['slot'])/'native/worker.json').read_bytes())
        assert declared['schema']=='p01-worker-result-v1' and isinstance(declared['status'],str)
        assert all(type(declared[key]) is int and declared[key]>=0 for key in ('epochs','events','applicable_candidates'))
        return declared
    except (OSError,ValueError,KeyError,TypeError,AssertionError):
        return {'status':'missing_or_invalid_summary'}


def write_new(path,obj):
    with path.open('x') as out:json.dump(obj,out,indent=2);out.write('\n')


def main():
    bundle=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
    receipt=audit_campaign.verify(bundle)
    assert receipt['integrity_verified'], 'Unsealed campaign cannot supply accepted endpoints'
    manifest=json.loads((bundle/'manifest.json').read_text());seal=json.loads((bundle/'seal.json').read_text())
    assert manifest['mode']=='full'
    summary=describe(manifest)
    summary.update(schema='p01-development-findings-v1',execution_status=manifest['execution_status'],
                   stop_reason=manifest['stop_reason'],resource_usage=seal['resource_usage'],overshoots=seal['overshoots'],
                   duplicate_laws_among_generated_proposals=manifest['summary']['duplicate_laws_among_generated_proposals'],
                   source_manifest_sha256=campaign.sha(bundle/'manifest.json'),source_seal_sha256=campaign.sha(bundle/'seal.json'),
                   source_checksums_sha256=campaign.sha(bundle/'checksums.json'),summarizer_sha256=campaign.sha(Path(__file__)))
    declared_unverified={'slots':0,'epochs':0,'events':0,'applicable_candidates':0,'invalid_summaries':0}
    for row in manifest['runs']:
        if row['status'].startswith('verified_') or row['stages'].get('native',{}).get('status')!='exited':continue
        declared=declared_native(bundle,row)
        declared_unverified['slots']+=1
        if declared['status']=='missing_or_invalid_summary':
            declared_unverified['invalid_summaries']+=1;continue
        for target,source in [('epochs','epochs'),('events','events'),('applicable_candidates','applicable_candidates')]:
            declared_unverified[target]+=declared[source]
    summary['native_work_declared_but_not_independently_verified']=declared_unverified
    write_new(out/'campaign_audit.json',receipt);write_new(out/'findings.json',summary)
    fields=['slot','proposal','initial_state','status','coverage','full_horizon_ap','observed_epochs','events','applicable_candidates','worker_status',
            'native_declared_epochs','native_declared_events','native_summary_status','trace_bytes','native_peak_rss_bytes','stage_wall_seconds','stage_child_cpu_seconds']
    with (out/'slot_outcomes.csv').open('x',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for row in manifest['runs']:
            result={k:row.get(k) for k in fields if k in row};native=row['stages'].get('native',{})
            result.update(trace_bytes=native.get('stdout_bytes'),native_peak_rss_bytes=native.get('peak_rss_bytes'),
                          stage_wall_seconds=sum(s.get('wall_seconds',0) for s in row['stages'].values()),
                          stage_child_cpu_seconds=sum(s.get('child_cpu_seconds',0) for s in row['stages'].values()))
            if native.get('status')=='exited':
                declared=declared_native(bundle,row)
                result.update(native_declared_epochs=declared.get('epochs'),native_declared_events=declared.get('events'),native_summary_status=declared['status'])
            writer.writerow(result)
    write_new(out/'report_checksums.json',{p.name:campaign.sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps({k:summary[k] for k in ('execution_status','stop_reason','started_slots','endpoint_counts_all_512','law_outcomes_all_128','resource_usage','overshoots')},indent=2))


if __name__=='__main__':main()
