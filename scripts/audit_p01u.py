"""P01u independent report/value and custody audit. Never invokes the validator."""
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def encoded(v):return json.dumps(v,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()


def identity(v):
    if type(v) is dict:return ('object',sorted((k,identity(x)) for k,x in v.items()))
    if type(v) is list:return ('array',[identity(x) for x in v])
    if type(v) is float:need(math.isfinite(v),'nonfinite')
    return (type(v).__name__,v)


def parse(data):
    def pairs(items):
        need(len(items)==len({k for k,v in items}),'duplicate key')
        return dict(items)
    v=json.loads(data,object_pairs_hook=pairs);identity(v);return v


def verify_report(data,report,panel_required=False):
    request=parse(data)
    need(report['schema']=='p01u-validation-result-v1' and report['input_sha256']==sha(data),'report identity')
    need(type(report['accepted']) is bool,'native acceptance bool')
    if report['rejection_stage']=='parse':
        need(report['accepted'] is False and report['roundtrip_request'] is None and type(report['error']) is str,'parse stage')
        return False
    need(identity(request)==identity(report['roundtrip_request']),'exact roundtrip')
    need(report['request_before_sha256']==report['request_after_sha256']==sha(encoded(request)),'immutable request')
    need(report['world_before_sha256']==report['world_after_sha256']==sha(encoded(request['initial']['native']['world'])),'immutable world')
    need((report['accepted'] is True and report['rejection_stage'] is None and report['error'] is None) or
         (report['accepted'] is False and report['rejection_stage'] in ('worker_prefix','initial_validate') and type(report['error']) is str),'native stage/acceptance')
    prefix=(request['schema']=='p01-worker-request-v1' and request['epochs']<=1000)
    need((report['rejection_stage']=='worker_prefix')==(not prefix),'worker prefix')
    contract=dict(schema='p01-worker-request-v1',epochs=128,max_events=16384,max_trace_bytes=4194304)
    policy=set(request)==set(contract)|{'initial'} and all(identity(request[k])==identity(v) for k,v in contract.items())
    if panel_required:need(policy and report['accepted'] is True,'native/panel acceptance')
    return policy


def validate_rows(rows):
    need(identity([[r['slot'],r['proposal'],r['initial']] for r in rows])==identity([[i,6000+i//4,i%4] for i in range(128)]),'all128 ordered rows')
    need(all(r['status']=='complete' and r['native_accepted'] is True and r['panel_policy'] is True and r['roundtrip_equal'] is True and r['world_unchanged'] is True and r['rejection_stage'] is None for r in rows),'all128 acceptance')


def inventory(root,tick=lambda:None):
    data={};stats=0
    for folder,dirs,names in os.walk(root,followlinks=False):
        for n in dirs+names:stats+=1;need(not (Path(folder)/n).is_symlink(),'output symlink')
        for n in names:
            tick();p=Path(folder)/n;data[str(p.relative_to(root))]=p.read_bytes()
    return data,dict(output_scans=1,reads=len(data),read_bytes=sum(map(len,data.values())),lstat_calls=stats)


def verify_inventory(data):
    inv=parse(data['checksums.json']);c=parse(data['completion.json'])
    need(set(data)==set(inv)|{'checksums.json','completion.json'},'complete membership')
    for n,e in inv.items():need(e==dict(size=len(data[n]),sha256=sha(data[n])),'file '+n)
    need(c['checksums_sha256']==sha(data['checksums.json']),'inventory link')
    need(type(c['output_bytes']) is int and c['output_bytes']==sum(map(len,data.values()))<134217728,'exact output total')
    need(c['status']=='pass' and c['wall_seconds']<180,'completion')
    counts=c['counts_before_completion'];names=set(data)-{'completion.json'}
    manifest=parse(data['manifest.json']);stages=[r['stage'] for r in manifest['rows']]
    chunks=sum(sum(s['chunks'].values()) for s in stages)
    streamfiles={s[k] for s in stages for k in ('stdout_file','stderr_file')}
    need(counts['output_scans']==1 and counts['write_bytes']==sum(len(data[n]) for n in names),'scan/write counter')
    need(counts['ledger_updates']==len(names)+chunks,'ledger update counter')
    need(counts['write_calls']==chunks+sum(bool(data[n]) for n in names-streamfiles),'write call counter')
    return manifest,c


def verify_panel(data,request_cache,protocol,binary_hash):
    manifest,c=verify_inventory(data);validate_rows(manifest['rows'])
    need(manifest['status']=='pass' and manifest['first_error'] is None and not manifest['closeout_errors'],'manifest')
    need(manifest['world_transitions']==manifest['keyed_evaluations']==0 and manifest['behavioral_outcomes'] is None,'scope')
    expected_stage_names=set()
    for row,(name,h) in zip(manifest['rows'],sorted(protocol['saved_requests'].items())):
        s=row['stage'];slot=row['slot'];prefix=f'stages/{slot:03}'
        need(s['stdout_file']==prefix+'/stdout.bin' and s['stderr_file']==prefix+'/stderr.bin','stage paths')
        expected_stage_names|={prefix+'/'+n for n in ('stdout.bin','stderr.bin','stage.json')}
        need(parse(data[prefix+'/stage.json'])==s,'stage receipt')
        need(s['status']=='complete' and s['returncode']==0 and s['guard_error'] is None and s['kills']==0,'guard status')
        need(s['wall_seconds']<2 and s['output_bytes']<1048576 and s['binary_sha256']==binary_hash,'guard limits/identity')
        need(s['rss_samples']>0 and 0<s['max_sampled_rss_bytes']<268435456 and s['rss_sample_interval_seconds']==0.005,'sampled rss')
        stdout=data[s['stdout_file']];stderr=data[s['stderr_file']];request=request_cache[name]
        need(not stderr and len(stdout)+len(stderr)==s['output_bytes'] and len(request)==s['stdin_bytes'],'stage byte counts')
        need(sha(request)==h==row['input_sha256'] and sha(stdout)==row['report_sha256'],'input/report hashes')
        verify_report(request,parse(stdout),True)
    need({n for n in data if n.startswith('stages/')}==expected_stage_names,'exact stage membership')
    need(sha(data['binary/validator'])==binary_hash,'executed binary snapshot')
    return dict(cells=128,native_acceptances=128,typed_roundtrips=128,unchanged_worlds=128,inventory_entries=len(data),output_bytes=c['output_bytes'])


def custody(test_path,closure_path,tick):
    protocol_path='docs/p01u_protocol.json';freeze_path='docs/p01u_registration_freeze.json'
    cost=dict(input_reads=0,input_hash_bytes=0,input_stats=0,input_bundle_scans=0);seen={};cache={}
    def read(name,keep=False,limit=None):
        name=str(name);tick()
        if name not in seen:
            path=Path(name) if Path(name).is_absolute() else ROOT/name
            size=path.stat().st_size;cost['input_stats']+=1
            if limit is not None:need(size<limit,'input cap')
            data=path.read_bytes();cost['input_reads']+=1;cost['input_hash_bytes']+=len(data);seen[name]=sha(data)
            if keep:cache[name]=data
            return data
        need(name in cache,'duplicate uncached read '+name);return cache[name]
    protocol=json.loads(read(protocol_path,True));freeze=json.loads(read(freeze_path,True))
    tests=json.loads(read(str(test_path),True));closure=json.loads(read(str(closure_path),True));expected={}
    for group in ('files','inputs','prior_public_receipts'):
        for n,h in freeze[group].items():
            need(n not in expected or expected[n]==h,'conflicting freeze');expected[n]=h
    need(tests['status']=='pass' and tests['returncodes']==[0,0] and tests['controls']==protocol['controls'],'fixed invented test gate')
    need(tests['closure_sha256']==seen[str(closure_path)] and tests['binary_sha256']==closure['binary_sha256'],'tested binary closure')
    for n,h in protocol['saved_requests'].items():
        data=read(n,True,524288);need(sha(data)==h,'saved request identity')
    for n,h in tests['sources'].items():need(sha(read(n,True))==h,'tested implementation')
    for n,h in closure['files'].items():
        if n not in seen:read(n,n==closure['binary'])
        need(seen[n]==h,'build dependency closure '+n)
    binary=closure['binary'];binary_data=read(binary,True)
    need(seen[binary]==closure['binary_sha256'],'binary closure')
    for bundle,seal_hash in protocol['source_bundles'].items():
        invname=bundle+'/checksums.json';sealname=bundle+'/seal.json'
        inv=json.loads(read(invname,True));seal=json.loads(read(sealname,True))
        need(seen[sealname]==seal_hash and seen[invname]==seal['checksums_sha256'],'original seal')
        cost['input_bundle_scans']+=1
        need({str(p.relative_to(ROOT/bundle)) for p in (ROOT/bundle).rglob('*') if p.is_file()}==set(inv)|{'checksums.json','seal.json'},'original membership')
        expected[bundle+'/manifest.json']=seal['manifest_sha256']
        for n,h in inv.items():
            full=bundle+'/'+n;need(full not in expected or expected[full]==h,'conflicting original');expected[full]=h
    bundle=protocol['request_bundle'];invname=bundle+'/checksums.json';completion_name=bundle+'/completion.json'
    inv=json.loads(read(invname,True));complete=json.loads(read(completion_name,True))
    need(seen[completion_name]==protocol['request_bundle_completion_sha256'] and seen[invname]==complete['checksums_sha256'],'request seal')
    cost['input_bundle_scans']+=1
    need({str(p.relative_to(ROOT/bundle)) for p in (ROOT/bundle).rglob('*') if p.is_file()}==set(inv)|{'checksums.json','completion.json'},'request membership')
    for n,e in inv.items():expected[bundle+'/'+n]=e['sha256']
    for n,h in expected.items():
        if n not in seen:read(n)
        need(seen[n]==h,'custody '+n)
    snapshots={n:cache[n] for n in tests['sources']}
    snapshots.update({protocol_path:cache[protocol_path],freeze_path:cache[freeze_path],
                      'tests.json':cache[str(test_path)],'build_closure.json':cache[str(closure_path)]})
    receipt=dict(**cost,unique_inputs=len(seen),binary_sha256=closure['binary_sha256'],
                 sources=tests['sources'],closure_sha256=seen[str(closure_path)],test_receipt_sha256=seen[str(test_path)])
    return protocol,cache,snapshots,receipt,closure



def main(output,source,test_path,closure_path):
    def forbid(event,args):
        if event.startswith(('subprocess.','os.exec','os.spawn')) or event in ('os.system','os.fork','os.posix_spawn'):raise RuntimeError('P01u auditor forbids processes')
    sys.addaudithook(forbid)
    start=time.monotonic();out=Path(output);out.mkdir(parents=True,exist_ok=False);written={}
    def tick():need(time.monotonic()-start<175,'audit reserve')
    def emit(name,value,terminal=False):
        need(time.monotonic()-start<(180 if terminal else 175),'audit deadline')
        raw=value if isinstance(value,bytes) else encoded(value)
        need(sum(e['size'] for e in written.values())+len(raw)<134217728-(0 if terminal else 1048576),'audit byte reserve')
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);actual=bytearray()
        try:
            with p.open('xb') as handle:
                while len(actual)<len(raw):
                    n=handle.write(raw[len(actual):]);need(n>0,'short write');actual.extend(raw[len(actual):len(actual)+n])
        finally:written[name]=dict(size=len(actual),sha256=sha(actual))
    result=dict(status='fail',world_transitions=0,keyed_evaluations=0,scientific_status='untested',behavioral_outcomes=None)
    try:
        protocol,cache,snapshots,receipt,closure=custody(test_path,closure_path,tick)
        for n,b in snapshots.items():emit('sources/'+n,b)
        emit('custody.json',receipt)
        data,work=inventory(Path(source),tick)
        for n,b in snapshots.items():need(data['sources/'+n]==b,'snapshot '+n)
        need(parse(data['custody.json'])==receipt,'independent input work')
        gate=parse(data['source_gate.json']);source_text=cache[protocol['future_paths']['native_source']].decode()
        need(gate['status']=='pass' and gate['native_source_sha256']==sha(source_text.encode()),'native source gate identity')
        stripped=re.sub(r'//[^\n]*|"(?:\\.|[^"\\])*"','',source_text)
        need(not re.search(r'\b(bounded_step|step|generate|Matcher|runtime|Command|spawn|unsafe|include|apply|commit)\b',stripped),'forbidden call')
        for span in gate['validator_spans']:
            raw=(ROOT/span['file']).read_text();begin=sum(len(line) for line in raw.splitlines(keepends=True)[:span['line']-1]);part=raw[begin:]
            match=re.search(r'(?:pub )?fn validate(?:_ends)?\(',part);need(match is not None and not part[:match.start()].strip(),'validator line')
            begin+=match.start();brace=raw.index('{',begin);end=brace+1;depth=1
            while depth:depth+=(raw[end]=='{')-(raw[end]=='}');end+=1
            need(sha(raw[begin:end].encode())==span['sha256'],'validator span identity')
        need(len(gate['validator_spans'])==5,'all validation spans')
        result.update(verify_panel(data,cache,protocol,closure['binary_sha256']),status='pass',output_work=work,
                      completion_sha256=sha(data['completion.json']))
    except Exception as error:result['error']=repr(error)
    try:
        emit('audit.json',result,True);emit('checksums.json',written,True)
        c=dict(status=result['status'],checksums_sha256=written['checksums.json']['sha256'],wall_seconds=time.monotonic()-start,output_bytes=0)
        while True:
            raw=encoded(c);total=sum(e['size'] for e in written.values())+len(raw)
            if total==c['output_bytes']:break
            c['output_bytes']=total
        emit('completion.json',raw,True)
    except Exception as error:result.update(status='fail',terminal_receipt='missing',terminal_error=repr(error))
    print(json.dumps(result));return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]))
