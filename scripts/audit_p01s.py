"""Independent P01s fixture oracle; imports no implementation or runner."""
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def need(ok, why):
    if not ok:raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def signature(v):
    if type(v) is dict:return ('object',sorted((k,signature(x)) for k,x in v.items()))
    if type(v) is list:return ('array',[signature(x) for x in v])
    if type(v) is float:need(math.isfinite(v),'nonfinite')
    return (type(v).__name__,v)


def parse(text):
    def pairs(items):
        need(len({k for k,v in items})==len(items),'duplicate')
        return dict(items)
    v=json.loads(text,object_pairs_hook=pairs)
    signature(v)
    return v


def interface_oracle(case):
    try:
        need(len(case['streams'])==len(case['hashes'])==2,'two streams')
        values=[]
        for s,h in zip(case['streams'],case['hashes']):
            need(sha(s.encode())==h,'hash')
            v=parse(s);need(type(v) is dict,'object')
            need(v.get('schema')=='p01o-generated-environment-v1','schema')
            need(signature([v.get(k) for k in ('slot','proposal','initial')])==signature([0,6000,0]),'ids')
            need(type(v.get('environment')) is dict and type(v['environment'].get('native')) is dict,'nested objects')
            values.append(v)
        need(signature(values[0])==signature(values[1]),'pair mismatch')
        expected=dict(envelope=values[0],request=dict(schema='p01-worker-request-v1',initial=values[0]['environment'],epochs=128,max_events=16384,max_trace_bytes=4194304))
    except (ValueError,TypeError,KeyError):
        need(case['accepted'] is False and case['expected_accept'] is False and case['result'] is None and bool(case['error']),'rejection receipt')
    else:
        need(case['accepted'] is True and case['expected_accept'] is True and case['error'] is None,'acceptance receipt')
        need(signature(case['result'])==signature(expected),'request/envelope changed')


def replay_events(case):
    sizes={}
    for event in case['events']:
        op=event['op']
        if op in ('write','stage'):
            need(event['old']==sizes.get(event['name'],0),'event old size')
            sizes[event['name']]=event['new']
        elif op=='rename':
            value=sizes.pop(event['source'])
            need(sizes.pop(event['target'],0)==event['removed'],'rename transient')
            sizes[event['target']]=value
        elif op=='delete':need(sizes.pop(event['name'])==event['removed'],'delete')
        else:raise ValueError('unknown event')
        need(sum(sizes.values())==event['total'],'event total')
    need(sizes=={n:v['size'] for n,v in case['files'].items()} and sum(sizes.values())==case['total'],'ledger replay')
    need(len(case['events'])==case['counters']['ledger_updates'],'update counter')


def check_case(control,case,root):
    if case['kind']=='interface':interface_oracle(case);return
    sub=case['subcase'];base=root/case['root']
    replay_events(case)
    for key in ('stat_calls','hash_read_bytes','write_bytes','discovered_entries'):
        need(type(case['counters'][key]) is int and case['counters'][key]>=0 and case['counters'][key]==case['spy'][key],'counter mismatch '+key)
    need(case['counters']['output_full_scans'] in (1,2),'scan bound')
    need(case['counters']['stage_reconciliations'] in (0,1),'stage bound')
    need(case['rejected']==case['expected_rejection'],'rejection agreement')
    expected_reject=control in ('failed_partial_write_is_retained','inventory_mismatch_and_unlisted_file','path_escape_symlink_and_external_mutation_rejected')
    if control=='bounded_stage_reconciliation':expected_reject=sub!='valid'
    if case['kind']=='budget':
        a=case['args']
        expected_reject=not(a['wall']<a['wall_cap']-a['seconds_reserve'] and a['cpu']<a['cpu_cap']-a['seconds_reserve'] and case['total']+case['reserved']<case['cap']-case['reserve'])
    need(case['rejected']==expected_reject,'independent rejection')
    mismatched=sub in ('equal_size_mutation','unlisted','missing','external_mutation')
    for n,entry in case['files'].items():
        p=base/n
        if sub=='missing' and n=='a':need(not p.exists(),'missing fixture');continue
        data=p.read_bytes()
        if mismatched and n=='a' and sub!='unlisted':need(data==b'xyz' and entry['sha256']==sha(b'abc'),'preserved external mutation')
        else:need(len(data)==entry['size'] and sha(data)==entry['sha256'],'file ledger '+n)
    # Independently fixed operation outcomes, not merely receipt self-consistency.
    expected={
        'create_and_append':{'a':b'x'},
        'atomic_replace_counts_old_and_temporary_until_rename':{'a':b'newer'},
        'failed_partial_write_is_retained':dict(a=b'abc',**({'source':b'abcdef'} if sub=='partial_copy' else {})),
        'duplicate_path_not_double_counted':{'a':b'abc'},
        'snapshot_bytes_included':{'source':b'invented source snapshot','snapshot':b'invented source snapshot'},
        'budget_poll_has_zero_filesystem_work':{'a':b'abc'},
    }.get(control)
    if expected is not None:
        need(set(case['files'])==set(expected),'expected file set')
        for n,v in expected.items():need((base/n).read_bytes()==v,'expected file bytes')
    if control=='atomic_replace_counts_old_and_temporary_until_rename':need(case['transient_bytes']==8,'transient bytes')
    if control=='metadata_and_seal_bytes_included':
        inv=json.loads((base/'checksums.json').read_bytes());seal=json.loads((base/'completion.json').read_bytes())
        need(inv=={'data':dict(size=3,sha256=sha(b'abc'))},'fixture inventory')
        need(seal['checksums_sha256']==sha((base/'checksums.json').read_bytes()),'fixture seal')
        need(set(case['files'])=={'data','checksums.json','completion.json'},'seal counted')
    if control=='budget_poll_has_zero_filesystem_work':
        need(case['counters']['budget_polls']==100 and not any(case['poll_spy_delta'].values()),'zero work polls')
    if case['kind']=='terminal':
        t=case['terminal']
        expected_rows=[dict(slot=i,proposal=6000+i//4,initial=i%4,status='failed' if i==0 else 'unstarted') for i in range(128)]
        need(t['rows']==expected_rows and t['first_error']==case['first_error'],'terminal denominator/original error')
        need(t['reconciliation']=='incomplete' and t['inventory_scope']=='maintained_ledger','partial scope')
        need(case['counters']['output_full_scans']==1,'terminal no scan')
        if sub=='terminal_io_error':need(t['terminal_receipt']=='missing' and len(t['closeout_errors'])==1 and not (base/'terminal.json').exists(),'terminal I/O failure')
        else:need(t['terminal_receipt']=='written' and not t['closeout_errors'] and json.loads((base/'terminal.json').read_bytes())==t,'terminal written')
    if control=='bounded_stage_reconciliation':
        if sub=='valid':need(case['reserved']==0 and case['files']=={'stage/a':dict(size=3,sha256=sha(b'abc'))},'stage success')
        if sub in ('unknown','oversize'):need(case['invalid'] and case['reserved']==4,'failed stage reservation')
        if sub!='too_many':need(case['reserved_before']==4 and case['counters']['stage_reconciliations']==1,'single bounded stage')
    if sub=='external_mutation':need(case['invalid'],'external mutation invalidates accounting')
    if sub=='unlisted':need((base/'unknown').read_bytes()==b'x','unlisted retained')
    if sub=='symlink':need((base/'link').is_symlink() and os.readlink(base/'link')=='a','symlink retained')


def verify_results(records,declared,root):
    protocol=json.loads((ROOT/'docs/p01s_protocol.json').read_bytes())
    need([r['control'] for r in records]==protocol['controls'],'all24 ordered controls')
    need(set(declared['controls'])==set(protocol['controls']),'packet controls')
    for record in records:
        need([c['subcase'] for c in record['cases']]==declared['controls'][record['control']],'all prescribed subcases')
        for case in record['cases']:check_case(record['control'],case,root)
    return dict(controls=len(records),subcases=sum(len(r['cases']) for r in records),terminal_rows=sum(len(c['terminal']['rows']) for r in records for c in r['cases'] if c['kind']=='terminal'))


def inventory(root):
    found={}
    for folder,dirs,files in os.walk(root,followlinks=False):
        for name in files:
            p=Path(folder)/name;n=str(p.relative_to(root))
            if p.is_symlink():found[n]=dict(symlink=os.readlink(p),size=0)
            else:
                data=p.read_bytes();found[n]=dict(size=len(data),sha256=sha(data))
        need(not any((Path(folder)/n).is_symlink() for n in dirs),'unexpected directory symlink')
    return found


def verify_bundle(source):
    source=Path(source)
    inv=json.loads((source/'checksums.json').read_bytes());completion=json.loads((source/'completion.json').read_bytes())
    actual=inventory(source)
    need(set(actual)==set(inv)|{'checksums.json','completion.json'},'inventory membership')
    need(all(actual[n]==v for n,v in inv.items()),'inventory bytes')
    need(sha((source/'checksums.json').read_bytes())==completion['checksums_sha256'],'seal link')
    need(sum(v['size'] for v in actual.values())==completion['output_bytes']<134217728,'total bytes')
    need(completion['status']=='pass' and completion['wall_seconds']<120,'completion')
    return actual


def main(out,source,test_receipt):
    def no_process(event,args):
        if event.startswith(('subprocess.','os.exec','os.spawn')) or event in ('os.system','os.fork','os.posix_spawn'):raise RuntimeError('audit forbids processes')
    sys.addaudithook(no_process)
    start=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=False);source=Path(source)
    result=dict(status='fail',world_transitions=0,keyed_evaluations=0,retained_payloads_parsed=0)
    try:
        freeze=json.loads((ROOT/'docs/p01s_registration_freeze.json').read_bytes());seen={}
        for section in ('files','inputs','prior_public_receipts'):
            for n,h in freeze[section].items():
                need(time.monotonic()-start<115,'custody deadline')
                if n not in seen:
                    b=(ROOT/n).read_bytes();need(sha(b)==h,'custody '+n);seen[n]=len(b)
        tests=json.loads(Path(test_receipt).read_bytes())
        protocol=json.loads((ROOT/'docs/p01s_protocol.json').read_bytes())
        need(tests['status']=='pass' and tests['returncodes']==[0,0],'test gate')
        need(tests['sources']=={n:sha((ROOT/n).read_bytes()) for n in protocol['future_paths'].values()},'tested sources')
        for n,h in tests['sources'].items():need(sha((source/'sources'/n).read_bytes())==h,'snapshot')
        need((source/'tests.json').read_bytes()==Path(test_receipt).read_bytes(),'test receipt')
        need(sha((source/'packet.json').read_bytes())==tests['packet_sha256'],'packet identity')
        actual=verify_bundle(source)
        counts=verify_results(json.loads((source/'results.json').read_bytes()),json.loads((source/'packet.json').read_bytes()),source/'fixtures')
        result.update(status='pass',**counts,inventory_entries=len(actual),output_bytes=sum(v['size'] for v in actual.values()),input_unique_reads=len(seen),input_hash_read_bytes=sum(seen.values()),output_full_scans=1)
    except Exception as error:result['error']=repr(error)
    data=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode();(out/'audit.json').write_bytes(data)
    closure=dict(status=result['status'],audit_sha256=sha(data),wall_seconds=time.monotonic()-start,output_bytes=0)
    while True:
        tail=(json.dumps(closure,sort_keys=True,indent=2)+'\n').encode();total=len(data)+len(tail)
        if closure['output_bytes']==total:break
        closure['output_bytes']=total
    need(total<134217728 and time.monotonic()-start<120,'audit limits')
    (out/'completion.json').write_bytes(tail)
    print(json.dumps(result));return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3]))
