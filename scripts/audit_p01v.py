"""Independent P01v chain, guard, manifest and byte audit; no child invocations."""
import ast
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROLES=('native_stub','report_stub','audit_stub')


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


def expected(role,row,request_hash,previous):
    return dict(schema='p01v-inert-stage-receipt-v1',inert=True,role=role,slot=row['slot'],proposal=row['proposal'],initial=row['initial'],
                input_request_sha256=request_hash,previous_stdout_sha256=None if previous is None else sha(previous))


def verify_receipt(raw,role,row,request_hash,previous):
    value=parse(raw);wanted=expected(role,row,request_hash,previous)
    need(identity(value)==identity(wanted),'inert receipt identity/chain')
    need(raw==encoded(wanted)+b'\n','inert stdout bytes')


def verify_rows(rows):
    need(identity([[r['slot'],r['proposal'],r['initial']] for r in rows])==identity([[i,6000+i//4,i%4] for i in range(128)]),'all128 identity/order')
    need(all(r['status']=='plumbing_complete' and [s['role'] for s in r['stages']]==list(ROLES) and
             [s['status'] for s in r['stages']]==['fixture_complete']*3 for r in rows),'all128/384 complete')


def inventory(root,tick=lambda:None):
    data={};stats=0
    for folder,dirs,names in os.walk(root,followlinks=False):
        for name in dirs+names:stats+=1;need(not (Path(folder)/name).is_symlink(),'output symlink')
        for name in names:
            tick();p=Path(folder)/name;data[str(p.relative_to(root))]=p.read_bytes()
    return data,dict(output_scans=1,reads=len(data),read_bytes=sum(map(len,data.values())),lstat_calls=stats)


def verify_inventory(data,success=True):
    inv=parse(data['checksums.json']);completion=parse(data['completion.json']);manifest=parse(data['manifest.json'])
    need(set(data)==set(inv)|{'checksums.json','completion.json'},'exact inventory membership')
    for name,entry in inv.items():need(entry==dict(size=len(data[name]),sha256=sha(data[name])),'inventory bytes '+name)
    need(completion['checksums_sha256']==sha(data['checksums.json']),'inventory link')
    total=sum(map(len,data.values()))
    need(type(completion['output_bytes']) is int and completion['output_bytes']==completion['known_path_bytes']==completion['usage_upper_bound_bytes']==total<134217728,'exact complete byte total')
    need(completion['extra_bound_bytes']==0 and completion['wall_seconds']<180,'completion limits')
    if success:need(completion['status']=='pass' and manifest['status']=='pass' and completion['reconciliation']=='pending_independent_audit','success status')
    else:need(completion['status']=='fail' and manifest['status']=='fail' and completion['reconciliation']=='incomplete','failure status')
    count=completion['counts_before_completion'];names=set(data)-{'completion.json'}
    guards=[stage['guard'] for row in manifest['rows'] for stage in row['stages'] if 'guard' in stage]
    chunks=sum(sum(g['chunks'].values()) for g in guards)
    streams={g[k] for g in guards for k in ('stdout_file','stderr_file')}
    need(count['output_scans']==1 and count['write_bytes']==sum(len(data[n]) for n in names),'scan/write byte counter')
    need(count['ledger_updates']==len(names)+chunks,'ledger updates')
    need(count['write_calls']==chunks+sum(bool(data[n]) for n in names-streams),'write syscall counter')
    need(manifest['executor_counts']['invocations']==len(guards),'invocations')
    return manifest,completion


def verify_panel(data,descriptors,reader,native_rows,pins):
    manifest,completion=verify_inventory(data);verify_rows(manifest['rows'])
    need(manifest['schema']=='p01v-inert-campaign-manifest-v1' and manifest['first_error'] is None and not manifest['closeout_errors'],'inert manifest')
    need(manifest['world_transitions']==manifest['keyed_evaluations']==0 and manifest['behavioral_outcomes'] is None and manifest['behavioral_missing_reason']=='not_executed','behavior scope')
    allowed_stages=set();ordinal=0
    for row,descriptor,prior in zip(manifest['rows'],descriptors,native_rows):
        request=reader(descriptor['file']);request_hash=sha(request);parsed=parse(request)
        need(request_hash==descriptor['sha256']==row['input_sha256']==prior['input_sha256'],'request hashes')
        need(len(request)==row['request_bytes']<524288,'request bytes')
        need(identity([descriptor[k] for k in ('slot','proposal','initial')])==identity([row[k] for k in ('slot','proposal','initial')]),'descriptor cell')
        need(identity([prior[k] for k in ('slot','proposal','initial')])==identity([row[k] for k in ('slot','proposal','initial')]) and prior['status']=='complete' and prior['native_accepted'] is True and row['prior_native_accepted'] is True,'prior native acceptance')
        contract=dict(schema='p01-worker-request-v1',epochs=128,max_events=16384,max_trace_bytes=4194304)
        need(set(parsed)==set(contract)|{'initial'} and all(identity(parsed[k])==identity(v) for k,v in contract.items()),'panel policy')
        previous=None
        for stage,role in zip(row['stages'],ROLES):
            ordinal+=1;guard=stage['guard'];prefix=f"stages/{row['slot']:03}/{role}"
            allowed_stages|={prefix+'/'+n for n in ('stdout.bin','stderr.bin','stage.json','binding.json')}
            need(parse(data[prefix+'/binding.json'])==guard,'binding receipt')
            original=parse(data[prefix+'/stage.json']);need(all(guard[k]==v for k,v in original.items()),'frozen guard receipt')
            need(guard['status']=='complete' and guard['returncode']==0 and guard['guard_error'] is None and guard['kills']==0,'guard complete')
            need(guard['wall_seconds']<2 and guard['output_bytes']<1048576 and guard['rss_samples']>0 and 0<guard['max_sampled_rss_bytes']<268435456 and guard['rss_sample_interval_seconds']==0.005,'guard caps')
            argv=[pins['interpreter'],'-I','-B',pins['fixture'],role,str(row['slot']),str(row['proposal']),str(row['initial']),request_hash]
            need(guard['argv']==argv and guard['interpreter_sha256']==pins['interpreter_sha256'] and guard['fixture_sha256']==pins['fixture_sha256'],'executor identity')
            need(guard['invocation_ordinal']==ordinal and guard['stdout_file']==prefix+'/stdout.bin' and guard['stderr_file']==prefix+'/stderr.bin','stage order/paths')
            stdin=request if previous is None else encoded(dict(schema='p01v-stage-input-v1',request_utf8=request.decode(),previous_stdout_utf8=previous.decode()))
            need(guard['stdin_sha256']==stage['stdin_sha256']==sha(stdin) and guard['stdin_bytes']==len(stdin),'exact stdin chain')
            stdout=data[prefix+'/stdout.bin'];stderr=data[prefix+'/stderr.bin']
            need(not stderr and stage['stderr_bytes']==0 and guard['output_bytes']==len(stdout) and stage['stdout_sha256']==sha(stdout),'stdout/stderr accounting')
            verify_receipt(stdout,role,row,request_hash,previous);previous=stdout
    need({n for n in data if n.startswith('stages/')}==allowed_stages and ordinal==384,'exact384 stages')
    counts=manifest['executor_counts'];need(counts['invocations']==384,'three invocations per cell')
    need(counts['interpreter_recheck_bytes']==384*len(data['provenance/interpreter.bin']),'interpreter recheck counter')
    fixture_key='sources/scripts/p01v_fixture.py'
    need(counts['fixture_recheck_bytes']==384*len(data[fixture_key]),'fixture recheck counter')
    need(sha(data['provenance/interpreter.bin'])==pins['interpreter_sha256'] and sha(data[fixture_key])==pins['fixture_sha256'],'executor snapshot hashes')
    return dict(cells=128,inert_stages=384,identity_chains=128,inventory_entries=len(data),output_bytes=completion['output_bytes'])


def verify_failure(data,cell,role):
    manifest,completion=verify_inventory(data,False);rows=manifest['rows']
    need(manifest['first_error'] is not None and len(rows)==128,'failure first error/denominator')
    need(identity([[r['slot'],r['proposal'],r['initial']] for r in rows])==identity([[i,6000+i//4,i%4] for i in range(128)]),'failure rows')
    expected_invocations=0 if cell is None else cell*3+(ROLES.index(role)+1 if role is not None else 0)
    for index,row in enumerate(rows):
        wanted='unstarted' if cell is None or index>cell else ('failed' if index==cell else 'plumbing_complete')
        need(row['status']==wanted,'failure prefix/suffix')
        expected_states=['unstarted']*3
        if cell is not None and index<cell:expected_states=['fixture_complete']*3
        elif cell is not None and index==cell and role is not None:
            before=ROLES.index(role);expected_states=['fixture_complete']*before+['failed']+['unstarted']*(2-before)
        need([s['role'] for s in row['stages']]==list(ROLES) and [s['status'] for s in row['stages']]==expected_states,'failure stage prefix')
    need(manifest['executor_counts']['invocations']==expected_invocations,'no later stage/cell invocations')
    return dict(status='pass',expected_invocations=expected_invocations,rows=128)


def custody(test_path,closure_path,tick):
    protocol_name='docs/p01v_protocol.json';freeze_name='docs/p01v_registration_freeze.json'
    seen={};cache={};cost=dict(input_reads=0,input_hash_bytes=0,input_stats=0,input_bundle_scans=0)
    def read(name,keep=False,limit=None):
        name=str(name);tick()
        if name not in seen:
            file=Path(name) if Path(name).is_absolute() else ROOT/name;size=file.stat().st_size;cost['input_stats']+=1
            if limit is not None:need(size<limit,'input cap')
            data=file.read_bytes();seen[name]=sha(data);cost['input_reads']+=1;cost['input_hash_bytes']+=len(data)
            if keep:cache[name]=data
            return data
        need(name in cache,'duplicate uncached read '+name);return cache[name]
    protocol=json.loads(read(protocol_name,True));freeze=json.loads(read(freeze_name,True))
    tests=json.loads(read(str(test_path),True));closure=json.loads(read(str(closure_path),True))
    need(tests['status']=='pass' and tests['returncodes']==[0,0] and tests['controls']==protocol['controls'],'fixed test gate')
    need(tests['closure_sha256']==seen[str(closure_path)],'tested execution closure')
    expected={}
    for section in ('files','inputs','prior_public_receipts'):
        for name,h in freeze[section].items():
            need(name not in expected or expected[name]==h,'conflicting freeze');expected[name]=h
    for name,h in protocol['saved_requests'].items():need(sha(read(name,True,524288))==h,'saved request identity')
    for name,h in tests['sources'].items():need(sha(read(name,True))==h,'tested source')
    for name,h in protocol['frozen_reuse'].items():need(sha(read(name,True))==h,'frozen helper')
    for name,h in closure['files'].items():
        if name not in seen:read(name,name==closure['interpreter'])
        need(seen[name]==h,'execution dependency '+name)
    if closure['interpreter'] not in cache:read(closure['interpreter'],True)
    for bundle,seal_hash in protocol['source_bundles'].items():
        invname=bundle+'/checksums.json';sealname=bundle+'/seal.json'
        inv=json.loads(read(invname,True));seal=json.loads(read(sealname,True))
        need(seen[sealname]==seal_hash and seen[invname]==seal['checksums_sha256'],'original seal')
        cost['input_bundle_scans']+=1
        need({str(p.relative_to(ROOT/bundle)) for p in (ROOT/bundle).rglob('*') if p.is_file()}==set(inv)|{'checksums.json','seal.json'},'original membership')
        for name,h in inv.items():expected[bundle+'/'+name]=h
        expected[bundle+'/manifest.json']=seal['manifest_sha256']
    for bundle,completion_hash in [(protocol['request_bundle'],protocol['request_bundle_completion_sha256']),
                                    (protocol['prior_validation_bundle'],protocol['prior_validation_completion_sha256'])]:
        invname=bundle+'/checksums.json';completion_name=bundle+'/completion.json'
        inv=json.loads(read(invname,True));completion=json.loads(read(completion_name,True))
        need(seen[completion_name]==completion_hash and seen[invname]==completion['checksums_sha256'],'prior bundle completion')
        cost['input_bundle_scans']+=1
        need({str(p.relative_to(ROOT/bundle)) for p in (ROOT/bundle).rglob('*') if p.is_file()}==set(inv)|{'checksums.json','completion.json'},'prior bundle membership')
        for name,e in inv.items():expected[bundle+'/'+name]=e['sha256']
    native_name=protocol['prior_validation_bundle']+'/manifest.json';native=json.loads(read(native_name,True))
    audit_name=protocol['prior_independent_audit'];audit=json.loads(read(audit_name,True))
    need(seen[audit_name]==protocol['prior_independent_audit_sha256'] and audit['status']=='pass','prior independent native audit')
    need(native['status']=='pass' and len(native['rows'])==128,'prior native manifest')
    for name,h in expected.items():
        if name not in seen:read(name)
        need(seen[name]==h,'custody '+name)
    snapshots={name:cache[name] for name in tests['sources']}
    snapshots.update({protocol_name:cache[protocol_name],freeze_name:cache[freeze_name],
                      'tests.json':cache[str(test_path)],'execution_closure.json':cache[str(closure_path)]})
    receipt=dict(**cost,unique_inputs=len(seen),sources=tests['sources'],closure_sha256=seen[str(closure_path)],
                 test_receipt_sha256=seen[str(test_path)],interpreter_sha256=closure['interpreter_sha256'])
    return protocol,cache,snapshots,receipt,closure,native['rows']



def main(output,source,test_path,closure_path):
    def forbid(event,args):
        if event.startswith(('subprocess.','os.exec','os.spawn')) or event in ('os.system','os.fork','os.posix_spawn'):raise RuntimeError('P01v auditor forbids process creation')
    sys.addaudithook(forbid)
    start=time.monotonic();out=Path(output);out.mkdir(parents=True,exist_ok=False);written={}
    def tick():need(time.monotonic()-start<175,'audit reserve')
    def emit(name,value,terminal=False):
        need(time.monotonic()-start<(180 if terminal else 175),'audit wall limit')
        raw=value if isinstance(value,bytes) else encoded(value)
        need(sum(v['size'] for v in written.values())+len(raw)<134217728-(0 if terminal else 1048576),'audit byte reserve')
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);actual=bytearray()
        try:
            with p.open('xb') as handle:
                while len(actual)<len(raw):
                    n=handle.write(raw[len(actual):]);need(n>0,'short write');actual.extend(raw[len(actual):len(actual)+n])
        finally:written[name]=dict(size=len(actual),sha256=sha(actual))
    result=dict(status='fail',world_transitions=0,keyed_evaluations=0,scientific_status='untested',behavioral_outcomes=None)
    try:
        protocol,cache,snapshots,receipt,closure,native_rows=custody(test_path,closure_path,tick)
        for name,b in snapshots.items():emit('sources/'+name,b)
        emit('custody.json',receipt)
        data,work=inventory(Path(source),tick)
        for name,b in snapshots.items():need(data['sources/'+name]==b,'source/test snapshot')
        need(parse(data['custody.json'])==receipt,'independent custody work')
        gate=parse(data['source_gate.json'])
        for role in ('pipeline','guard','fixture'):
            source_bytes=cache[protocol['future_paths'][role]];need(gate['sources'][role]==sha(source_bytes),'reviewed source identity')
            tree=ast.parse(source_bytes);modules=[]
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):modules.extend(alias.name for alias in node.names)
                if isinstance(node,ast.ImportFrom):modules.append(node.module)
                if isinstance(node,ast.Call):need(ast.unparse(node.func).split('.')[-1] not in {'step','bounded_step','generate','check_report','validate_native'},'forbidden execution edge')
            need(sorted(set(modules))==gate['imports'][role],'source import closure')
        need(gate['status']=='pass','source gate status')
        descriptors=[dict(slot=i,proposal=6000+i//4,initial=i%4,file=name,sha256=h) for i,(name,h) in enumerate(sorted(protocol['saved_requests'].items()))]
        pins=parse(data['executor.json']);need(pins['interpreter']==closure['interpreter'] and pins['interpreter_sha256']==closure['interpreter_sha256'],'interpreter closure')
        need(pins['fixture_sha256']==receipt['sources'][protocol['future_paths']['fixture']],'fixture closure')
        result.update(verify_panel(data,descriptors,cache.__getitem__,native_rows,pins),status='pass',output_work=work,completion_sha256=sha(data['completion.json']))
    except Exception as error:result['error']=repr(error)
    try:
        emit('audit.json',result,True);emit('checksums.json',written,True)
        c=dict(status=result['status'],checksums_sha256=written['checksums.json']['sha256'],wall_seconds=time.monotonic()-start,output_bytes=0)
        while True:
            raw=encoded(c);total=sum(v['size'] for v in written.values())+len(raw)
            if total==c['output_bytes']:break
            c['output_bytes']=total
        emit('completion.json',raw,True)
    except Exception as error:result.update(status='fail',terminal_receipt='missing',terminal_error=repr(error))
    print(json.dumps(result));return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]))


def verify_unknown_failure(data):
    completion=parse(data['completion.json']);manifest=parse(data['manifest.json']);inv=parse(data['checksums.json'])
    need(completion['status']=='fail' and manifest['status']=='fail' and completion['reconciliation']=='incomplete','incomplete failure')
    need(completion['output_bytes'] is None and completion['extra_bound_bytes']>=0,'unknown exact bytes')
    need(set(inv)<set(data) and set(inv)<=set(data)-{'checksums.json','completion.json'},'known-path subset')
    for name,entry in inv.items():need(entry==dict(size=len(data[name]),sha256=sha(data[name])),'known-path hash')
    known=sum(entry['size'] for entry in inv.values())+len(data['checksums.json'])+len(data['completion.json'])
    need(completion['known_path_bytes']==known and completion['usage_upper_bound_bytes']==known+completion['extra_bound_bytes'],'justified conservative bound')
    need(sum(map(len,data.values()))<=completion['usage_upper_bound_bytes']<134217728,'actual partial bytes bounded')
    return True
