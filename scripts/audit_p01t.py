"""Independent P01t transport oracle; no producer or P01s imports."""
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def encoded(v):return json.dumps(v,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode('utf-8')


def identity(value):
    if type(value) is dict:return ('object',sorted((k,identity(v)) for k,v in value.items()))
    if type(value) is list:return ('array',[identity(v) for v in value])
    if type(value) is float:need(math.isfinite(value),'nonfinite value')
    return (type(value).__name__,value)


def parse(data):
    def pairs(items):
        need(len(items)==len({k for k,v in items}),'duplicate key')
        return dict(items)
    value=json.loads(data,object_pairs_hook=pairs);identity(value);return value


def paths(slot):return [f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin' for lang in ('rust_generation','python_generation')]


def oracle(streams,hashes,cell):
    need(len(streams)==len(hashes)==2,'two streams')
    need(all(type(v) is int for v in cell) and len(cell)==3,'cell types')
    slot,proposal,initial=cell
    need(0<=slot<128 and proposal==6000+slot//4 and initial==slot%4,'cell identity')
    values=[]
    for data,h in zip(streams,hashes):
        need(len(data)<1048576 and sha(data)==h,'stream bytes')
        env=parse(data)
        need(type(env) is dict and env.get('schema')=='p01o-generated-environment-v1','schema')
        need(identity([env.get(k) for k in ('slot','proposal','initial')])==identity(list(cell)),'envelope identity')
        need(type(env.get('environment')) is dict and type(env['environment'].get('native')) is dict,'environment/native')
        values.append(env)
    need(identity(values[0])==identity(values[1]),'typed stream agreement')
    expected=dict(schema='p01-worker-request-v1',initial=values[0]['environment'],epochs=128,max_events=16384,max_trace_bytes=4194304)
    return expected,values[0]


def verify_request(data,streams,hashes,cell,row=None):
    expected,envelope=oracle(streams,hashes,cell)
    actual=parse(data)
    need(len(data)<524288 and identity(actual)==identity(expected),'exact request')
    need(data==encoded(expected),'canonical serialization')
    if row is not None:
        expected_fields=dict(input_sha256=hashes,typed_pair_equal=True,
            envelope_canonical_sha256=sha(encoded(envelope)),environment_canonical_sha256=sha(encoded(envelope['environment'])),
            request_sha256=sha(data),request_bytes=len(data))
        for k,v in expected_fields.items():need(identity(row[k])==identity(v),'row '+k)
    return True


def validate_rows(rows):
    expected=[[i,6000+i//4,i%4] for i in range(128)]
    actual=[[r['slot'],r['proposal'],r['initial']] for r in rows]
    need(identity(actual)==identity(expected),'all128 cell order')
    need(all(r['status']=='complete' and r['request_file']==f'requests/{i:03}.json' for i,r in enumerate(rows)),'all128 complete requests')


def output_inventory(root,tick=lambda:None):
    root=Path(root);data={};stats=0;reads=0
    for folder,dirs,names in os.walk(root,followlinks=False):
        for n in dirs+names:
            p=Path(folder)/n;stats+=1;need(not p.is_symlink(),'output symlink')
        for n in names:
            tick();p=Path(folder)/n;name=str(p.relative_to(root));data[name]=p.read_bytes();reads+=1
    return data,dict(output_full_scans=1,output_reads=reads,output_stat_calls=stats,output_read_bytes=sum(map(len,data.values())))


def verify_inventory(data):
    inv=parse(data['checksums.json']);completion=parse(data['completion.json'])
    need(set(data)==set(inv)|{'checksums.json','completion.json'},'exact file membership')
    for n,entry in inv.items():need(entry==dict(size=len(data[n]),sha256=sha(data[n])),'inventory '+n)
    need(sha(data['checksums.json'])==completion['checksums_sha256'],'seal link')
    need(type(completion['output_bytes']) is int and completion['output_bytes']==sum(map(len,data.values()))<134217728,'exact byte total')
    need(completion['status']=='pass' and completion['first_error'] is None and completion['closeout_errors']==[],'completion status')
    need(completion['wall_seconds']<120 and completion['count_scope']=='all_output_except_completion','completion limits/scope')
    c=completion['counts_before_completion'];names=set(data)-{'completion.json'}
    expected=dict(output_full_scans=1,input_full_scans=0,stage_reconciliations=0,discovered_entries=0,
        hash_read_bytes=0,write_bytes=sum(len(data[n]) for n in names),ledger_updates=len(names),
        stat_calls=sum(len(Path(n).parts)+2 for n in names))
    for k,v in expected.items():need(c[k]==v,'counter '+k)
    input_reads=parse(data['custody.json'])['input_reads'] if 'custody.json' in data else 0
    need(type(c['budget_polls']) is int and c['budget_polls']==input_reads+len(data)-3+128,'budget polls')
    return inv,completion


def verify_panel(data,cache,hashes):
    inv,completion=verify_inventory(data)
    manifest=parse(data['manifest.json']);validate_rows(manifest['rows'])
    need(manifest['status']=='pass' and manifest['first_error'] is None and not manifest['closeout_errors'],'manifest status')
    need(manifest['world_transitions']==manifest['keyed_evaluations']==0 and manifest['behavioral_outcomes'] is None,'scope')
    requests={n for n in data if n.startswith('requests/')}
    need(requests=={f'requests/{i:03}.json' for i in range(128)},'request membership')
    for row in manifest['rows']:
        names=paths(row['slot'])
        verify_request(data[row['request_file']],[cache[n] for n in names],[hashes[n] for n in names],(row['slot'],row['proposal'],row['initial']),row)
    return dict(cells=128,streams=256,requests=128,exact_typed_requests=128,output_bytes=completion['output_bytes'],inventory_entries=len(data))


def custody(test_path, tick):
    """One deduplicated pass; retain stream bytes and small source/receipt snapshots."""
    protocol_path='docs/p01t_protocol.json';freeze_path='docs/p01t_registration_freeze.json'
    seen={};cached={};cost=dict(input_reads=0,hash_read_bytes=0,stat_calls=0,input_bundle_scans=0)
    streams={n for i in range(128) for n in paths(i)}
    def read(name, keep=False):
        name=str(name);tick()
        if name not in seen:
            p=Path(name) if Path(name).is_absolute() else ROOT/name
            cost['stat_calls']+=1
            if name in streams:need(p.stat().st_size<1048576,'input stream cap')
            else:p.stat()
            data=p.read_bytes();cost['input_reads']+=1;cost['hash_read_bytes']+=len(data)
            seen[name]=sha(data)
            if keep or name in streams:cached[name]=data
            return data
        need(name in cached,'unexpected repeated input read: '+name)
        return cached[name]
    protocol=json.loads(read(protocol_path,True));freeze=json.loads(read(freeze_path,True))
    tests=json.loads(read(str(test_path),True))
    expected={}
    for section in ('files','inputs','prior_public_receipts'):
        for name,h in freeze[section].items():
            need(name not in expected or expected[name]==h,'conflicting freeze');expected[name]=h
    for bundle,h in protocol['source_bundles'].items():
        invname=bundle+'/checksums.json';sealname=bundle+'/seal.json'
        inv=json.loads(read(invname,True));seal=json.loads(read(sealname,True))
        need(seen[sealname]==h and seen[invname]==seal['checksums_sha256'],'original seal')
        cost['input_bundle_scans']+=1
        actual={str(p.relative_to(ROOT/bundle)) for p in (ROOT/bundle).rglob('*') if p.is_file()}
        need(actual==set(inv)|{'checksums.json','seal.json'},'original membership')
        expected[bundle+'/manifest.json']=seal['manifest_sha256']
        for name,d in inv.items():
            full=bundle+'/'+name;need(full not in expected or expected[full]==d,'conflicting original');expected[full]=d
    sources=list(protocol['future_paths'].values())+list(protocol['frozen_reuse'])
    need(tests['status']=='pass' and tests['returncodes']==[0,0] and tests['controls']==protocol['controls'],'invented test gate')
    for name in sources:
        content=read(name,True);need(sha(content)==tests['sources'][name],'tested source identity')
    for name,h in protocol['frozen_reuse'].items():need(seen[name]==h,'frozen reuse')
    for name,h in expected.items():
        if name not in seen:read(name)
        need(seen[name]==h,'custody '+name)
    for name in streams:need(name in cached and seen[name]==freeze['inputs'][name],'complete stream closure')
    snapshots={name:cached[name] for name in sources+[protocol_path,freeze_path]}
    snapshots['test_receipt.json']=cached[str(test_path)]
    return cached,seen,snapshots,dict(**cost,unique_files=len(seen),stream_count=len(streams),
        sources={n:seen[n] for n in sources},freeze_sha256=seen[freeze_path],test_receipt_sha256=seen[str(test_path)])



def main(output,source,test_path):
    def forbid(event,args):
        if event.startswith(('subprocess.','os.exec','os.spawn')) or event in ('os.system','os.fork','os.posix_spawn'):raise RuntimeError('P01t audit forbids processes')
    sys.addaudithook(forbid)
    start=time.monotonic();out=Path(output);out.mkdir(parents=True,exist_ok=False);written={}
    def tick():need(time.monotonic()-start<115,'audit ordinary deadline')
    def emit(name,value,terminal=False):
        need(time.monotonic()-start<(120 if terminal else 115),'audit deadline')
        data=value if isinstance(value,bytes) else encoded(value)
        need(sum(v['size'] for v in written.values())+len(data)<134217728-(0 if terminal else 1048576),'audit byte reserve')
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
        # Record actual progress even when a write fails.
        actual=bytearray()
        try:
            with p.open('xb') as f:
                while len(actual)<len(data):
                    count=f.write(data[len(actual):]);need(count>0,'short write');actual.extend(data[len(actual):len(actual)+count])
        finally:written[name]=dict(size=len(actual),sha256=sha(actual))
    result=dict(status='fail',world_transitions=0,keyed_evaluations=0,scientific_status='untested',behavioral_outcomes=None)
    try:
        cache,hashes,snapshots,receipt=custody(test_path,tick)
        for n,b in snapshots.items():emit('sources/'+n,b)
        emit('custody.json',receipt)
        data,counters=output_inventory(source,tick)
        for n,b in snapshots.items():need(data['sources/'+n]==b,'source/test snapshot '+n)
        need(parse(data['custody.json'])==receipt,'independent input custody/counts')
        result.update(verify_panel(data,cache,hashes),status='pass',output_work=counters,
                      source_completion_sha256=sha(data['completion.json']))
    except Exception as error:result['error']=repr(error)
    try:
        emit('audit.json',result,True)
        emit('checksums.json',written,True)
        final=dict(status=result['status'],checksums_sha256=written['checksums.json']['sha256'],wall_seconds=time.monotonic()-start,output_bytes=0)
        while True:
            raw=encoded(final);total=sum(v['size'] for v in written.values())+len(raw)
            if total==final['output_bytes']:break
            final['output_bytes']=total
        emit('completion.json',raw,True)
    except Exception as error:
        result.update(status='fail',terminal_error=repr(error),terminal_receipt='missing')
    print(json.dumps(result));return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3]))
