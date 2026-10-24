"""P01u guarded validation; only the pinned validation-only binary may run."""
import ctypes
import hashlib
import json
import math
import os
import re
import selectors
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def typed(value):
    if type(value) is dict:return ('dict',tuple(sorted((k,typed(v)) for k,v in value.items())))
    if type(value) is list:return ('list',tuple(map(typed,value)))
    if type(value) is float:need(math.isfinite(value),'nonfinite')
    return (type(value).__name__,value)


def parse(data):
    def pairs(items):
        need(len(items)==len({k for k,v in items}),'duplicate key')
        return dict(items)
    value=json.loads(data,object_pairs_hook=pairs);typed(value);return value


def policy(value):
    fixed=dict(schema='p01-worker-request-v1',epochs=128,max_events=16384,max_trace_bytes=4194304)
    return type(value) is dict and set(value)==set(fixed)|{'initial'} and all(typed(value[k])==typed(v) for k,v in fixed.items())


def rows():return [dict(slot=i,proposal=6000+i//4,initial=i%4,status='unstarted') for i in range(128)]


class Output:
    def __init__(self,root,clock=time.monotonic):
        self.root=Path(root).absolute();os.mkdir(self.root);self.clock=clock;self.start=clock()
        with os.scandir(self.root) as entries:need(not list(entries),'empty output root')
        self.data={};self.total=0;self.reserved=0;self.rows=rows();self.first_error=None;self.closeout_errors=[]
        self.counts=dict(output_scans=1,write_calls=0,write_bytes=0,ledger_updates=0,budget_polls=0)
    def poll(self):
        self.counts['budget_polls']+=1
        need(self.clock()-self.start<175,'aggregate wall reserve')
        need(self.total+self.reserved<133169152,'aggregate byte reserve')
    def write(self,name,data,append=False,terminal=False):
        name=str(name);p=Path(name)
        need(not p.is_absolute() and '..' not in p.parts,'owned output path')
        if terminal:need(self.clock()-self.start<180,'terminal wall limit')
        else:self.poll()
        need(self.total+self.reserved+len(data)<134217728-(0 if terminal else 1048576),'write reserve')
        need(append or name not in self.data,'no replacement')
        target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
        flags=os.O_WRONLY|os.O_NOFOLLOW|(os.O_APPEND if append else os.O_CREAT|os.O_EXCL)
        fd=os.open(target,flags,0o600);actual=bytearray()
        try:
            while len(actual)<len(data):
                n=os.write(fd,data[len(actual):]);need(n>0,'zero write')
                actual.extend(data[len(actual):len(actual)+n]);self.counts['write_calls']+=1;self.counts['write_bytes']+=n
        finally:
            os.close(fd);self.data.setdefault(name,bytearray()).extend(actual);self.total+=len(actual);self.counts['ledger_updates']+=1
    def finish(self):
        status='fail' if self.first_error else 'pass'
        try:
            self.reserved=0
            self.write('manifest.json',encoded(dict(schema='p01u-manifest-v1',status=status,rows=self.rows,
                first_error=self.first_error,closeout_errors=self.closeout_errors,world_transitions=0,keyed_evaluations=0,
                scientific_status='untested',behavioral_outcomes=None)),terminal=True)
            inv={n:dict(size=len(b),sha256=sha(b)) for n,b in self.data.items()}
            self.write('checksums.json',encoded(inv),terminal=True)
            c=dict(status=status,checksums_sha256=sha(self.data['checksums.json']),output_bytes=0,
                counts_before_completion=dict(self.counts),wall_seconds=self.clock()-self.start,
                reconciliation='pending_independent_audit' if status=='pass' else 'incomplete')
            while True:
                raw=encoded(c);total=self.total+len(raw)
                if total==c['output_bytes']:break
                c['output_bytes']=total
            self.write('completion.json',raw,terminal=True)
        except Exception as error:status='fail';self.closeout_errors.append(repr(error))
        return dict(status=status,first_error=self.first_error,closeout_errors=self.closeout_errors,
            terminal_receipt='written' if 'completion.json' in self.data and not self.closeout_errors else 'missing',output_bytes=self.total)


# SDK sys/proc_info.h: PROC_PIDTASKINFO=4; six uint64 and twelve int32 fields.
class TaskInfo(ctypes.Structure):
    _fields_=[('u'+str(i),ctypes.c_uint64) for i in range(6)]+[('i'+str(i),ctypes.c_int32) for i in range(12)]
_LIBPROC=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
_LIBPROC.proc_pidinfo.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
_LIBPROC.proc_pidinfo.restype=ctypes.c_int


def rss(pid):
    info=TaskInfo();size=_LIBPROC.proc_pidinfo(pid,4,0,ctypes.byref(info),ctypes.sizeof(info))
    return info.u1 if size==ctypes.sizeof(info) else None


def stage_boundary(wall,bytes_used,resident):
    return wall<2 and bytes_used<1048576 and (resident is None or resident<268435456)


def run_stage(out,name,command,data,expected_binary=None,wall_cap=2,byte_cap=1048576):
    """Fixture command lists are allowed only by direct tests; retained call pins one binary."""
    if expected_binary is not None:
        need(len(command)==1 and Path(command[0]).is_absolute(),'one native executable')
        need(sha(Path(command[0]).read_bytes())==expected_binary,'binary substitution')
    out.reserved=byte_cap;out.poll()
    stdout_name=f'{name}/stdout.bin';stderr_name=f'{name}/stderr.bin'
    out.write(stdout_name,b'');out.write(stderr_name,b'')
    start=time.monotonic();proc=None;selector=selectors.DefaultSelector();chunks={'stdout':0,'stderr':0}
    stats=dict(status='failed',returncode=None,wall_seconds=0,output_bytes=0,stdin_bytes=0,polls=0,rss_samples=0,
               rss_sample_interval_seconds=0.005,max_sampled_rss_bytes=None,kills=0,stdout_file=stdout_name,stderr_file=stderr_name,
               binary_sha256=expected_binary,guard_error=None)
    try:
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,bufsize=0)
        for label,handle in [('stdout',proc.stdout),('stderr',proc.stderr),('stdin',proc.stdin)]:
            os.set_blocking(handle.fileno(),False);selector.register(handle,selectors.EVENT_WRITE if label=='stdin' else selectors.EVENT_READ,label)
        last_sample=-1
        while selector.get_map() or proc.poll() is None:
            stats['polls']+=1;out.poll();now=time.monotonic();elapsed=now-start
            if now-last_sample>=0.005 and proc.poll() is None:
                resident=rss(proc.pid);last_sample=now
                if resident is not None:
                    stats['rss_samples']+=1;stats['max_sampled_rss_bytes']=max(stats['max_sampled_rss_bytes'] or 0,resident)
            need(elapsed<wall_cap,'stage wall limit')
            need(stats['max_sampled_rss_bytes'] is None or stats['max_sampled_rss_bytes']<268435456,'stage rss limit')
            for key,mask in selector.select(0.005):
                label=key.data;handle=key.fileobj
                if label=='stdin':
                    # Withhold input until a pre-input resident-size sample exists.
                    if stats['rss_samples']==0:continue
                    if stats['stdin_bytes']==len(data):selector.unregister(handle);handle.close();continue
                    try:n=os.write(handle.fileno(),data[stats['stdin_bytes']:stats['stdin_bytes']+16384])
                    except BrokenPipeError:selector.unregister(handle);handle.close();continue
                    stats['stdin_bytes']+=n
                else:
                    try:chunk=os.read(handle.fileno(),min(16384,byte_cap-stats['output_bytes']))
                    except BlockingIOError:continue
                    if not chunk:selector.unregister(handle);handle.close();continue
                    stats['output_bytes']+=len(chunk);chunks[label]+=1;out.reserved=byte_cap-stats['output_bytes']
                    out.write(stdout_name if label=='stdout' else stderr_name,chunk,append=True)
                    need(stats['output_bytes']<byte_cap,'stage output limit')
        stats['returncode']=proc.wait(timeout=0.1)
        stats['wall_seconds']=time.monotonic()-start
        need(stats['wall_seconds']<wall_cap,'stage wall limit')
        need(stats['returncode']==0,'native process failure')
        need(stats['rss_samples']>0 and stats['stdin_bytes']==len(data),'input/sample coverage')
        stats['status']='complete'
    except Exception as error:
        stats['guard_error']=repr(error)
        if proc is not None:
            try:os.killpg(proc.pid,signal.SIGKILL);stats['kills']+=1
            except ProcessLookupError:pass
            proc.wait();stats['returncode']=proc.returncode
    finally:
        for key in list(selector.get_map().values()):
            try:key.fileobj.close()
            except OSError:pass
        selector.close();out.reserved=0;stats['wall_seconds']=time.monotonic()-start;stats['chunks']=chunks
    out.write(f'{name}/stage.json',encoded(stats),terminal=stats['status']!='complete')
    return stats,bytes(out.data[stdout_name]),bytes(out.data[stderr_name])


def check_report(request,report):
    need(report['schema']=='p01u-validation-result-v1' and report['input_sha256']==sha(request),'native report identity')
    original=parse(request);roundtrip=report['roundtrip_request']
    need(typed(original)==typed(roundtrip),'typed roundtrip')
    request_hash=sha(encoded(roundtrip));world_hash=sha(encoded(roundtrip['initial']['native']['world']))
    need(report['request_before_sha256']==report['request_after_sha256']==request_hash,'request immutable digest')
    need(report['world_before_sha256']==report['world_after_sha256']==world_hash,'world immutable digest')
    need(type(report['accepted']) is bool,'acceptance bool')
    need((report['accepted'] and report['rejection_stage'] is None and report['error'] is None) or
         (not report['accepted'] and report['rejection_stage'] in ('worker_prefix','initial_validate') and type(report['error']) is str),'acceptance/stage consistency')
    return policy(original)


def source_gate(source,expected_hash,semantic_sources):
    need(sha(source.encode())==expected_hash,'native source substitution')
    # Exact reviewed source identity plus forbidden-call rejection, not a generic Rust sandbox.
    stripped=re.sub(r'//[^\n]*|"(?:\\.|[^"\\])*"','',source)
    need(not re.search(r'\b(bounded_step|step|generate|Matcher|runtime|Command|spawn|unsafe|include|apply|commit)\b',stripped),'forbidden native call')
    calls=re.findall(r'([A-Za-z_][A-Za-z0-9_:]*)\s*\(',stripped)
    allowed={'Sha256::digest','Vec::new','let','validate_bytes','main','format','digest','serde_json::from_slice','to_string','Some','None','validate','is_none','io::stdin','io::stdout','lock','take','read_to_end','len','into','canonical','push','write_all','new'}
    need(set(calls)<=allowed|{'Ok','Err'},'unreviewed native calls: '+str(set(calls)-allowed-{'Ok','Err'}))
    spans=[]
    for name,h in semantic_sources.items():
        data=(ROOT/name).read_bytes();need(sha(data)==h,'semantic source substitution')
        if name in ('src/core.rs','src/environment.rs'):
            text=data.decode()
            for match in re.finditer(r'(?:pub )?fn validate(?:_ends)?\(',text):
                begin=text.index('{',match.start());depth=1;end=begin+1
                while depth:
                    depth+=(text[end]=='{')-(text[end]=='}');end+=1
                body=text[match.start():end]
                need(not re.search(r'\b(?:bounded_step|generate|step|Matcher)\b',body),'validator transition closure')
                spans.append(dict(file=name,line=text.count('\n',0,match.start())+1,sha256=sha(body.encode())))
    need(len(spans)==5,'immutable validation closure')
    return dict(status='pass',native_source_sha256=expected_hash,authored_calls=sorted(set(calls)),validator_spans=spans)


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


def main(output,test_path,closure_path):
    out=Output(output)
    try:
        protocol,cache,snapshots,receipt,closure=custody(test_path,closure_path,out.poll)
        gate=source_gate(cache[protocol['future_paths']['native_source']].decode(),
                         receipt['sources'][protocol['future_paths']['native_source']],protocol['semantic_sources'])
        for n,b in snapshots.items():out.write('sources/'+n,b)
        out.write('binary/validator',cache[closure['binary']]);os.chmod(out.root/'binary/validator',0o700)
        pinned=sha(out.data['binary/validator'])
        out.write('custody.json',encoded(receipt));out.write('source_gate.json',encoded(gate))
        for row,(name,h) in zip(out.rows,sorted(protocol['saved_requests'].items())):
            try:
                data=cache[name];need(sha(data)==h,'request changed');request=parse(data);panel_policy=policy(request)
                need(panel_policy,'panel policy')
                stage,stdout,stderr=run_stage(out,f"stages/{row['slot']:03}",[str(out.root/'binary/validator')],data,pinned)
                row.update(input_sha256=h,panel_policy=panel_policy,stage=stage)
                need(stage['status']=='complete' and not stderr,'guard success')
                report=parse(stdout);check_report(data,report)
                row.update(native_accepted=report['accepted'],rejection_stage=report['rejection_stage'],
                           roundtrip_equal=True,world_unchanged=True,report_sha256=sha(stdout))
                need(report['accepted'],'native rejection')
                row['status']='complete'
            except Exception as error:row.update(status='failed',error=repr(error));out.first_error=repr(error);break
    except Exception as error:out.first_error=repr(error)
    result=out.finish();print(json.dumps(result));return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3]))
