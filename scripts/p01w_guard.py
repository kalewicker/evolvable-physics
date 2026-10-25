"""P01w production guards: emitted-byte ledger, conservative CPU, suspended spawn.

Darwin SDK sys/spawn.h flags: SETPGROUP=2, START_SUSPENDED=128,
CLOEXEC_DEFAULT=16384. No worker or world implementation is imported here.
"""
import ctypes
import hashlib
import json
import math
import os
import resource
import selectors
import signal
import sys
import time
from pathlib import Path

ROLES=('native','rust_report','python_audit')
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def typed(x):
    if type(x) is dict:return ('dict',tuple(sorted((k,typed(v)) for k,v in x.items())))
    if type(x) is list:return ('list',tuple(map(typed,x)))
    if type(x) is float:need(math.isfinite(x),'nonfinite')
    return (type(x).__name__,x)
def parse(raw):
    def pairs(items):
        need(len(items)==len({k for k,v in items}),'duplicate key');return dict(items)
    result=json.loads(raw,object_pairs_hook=pairs);typed(result);return result
def cpu():
    return time.process_time()+sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2])
def rows():return [dict(slot=i,proposal=6000+i//4,initial=i%4,status='unstarted',stages=[dict(role=r,status='unstarted') for r in ROLES]) for i in range(128)]
def fits(p,usage,role):
    stage=p['per_process'][role];cap=p['campaign'];w=stage['wall_seconds']
    return (usage['wall_seconds']+w+5<=cap['wall_seconds'] and
        usage['total_process_cpu_seconds']+2*w+5<=cap['total_process_cpu_seconds'] and
        usage['artifact_bytes']+stage['output_bytes']+cap['metadata_reserve_bytes']<=cap['artifact_bytes'])
def stage_fits(p,role,wall,stdout,stderr,resident):
    s=p['per_process'][role];c=p['production_contracts'][role]
    return (wall<=s['wall_seconds'] and stdout<=c['stdout_cap_bytes'] and stderr<=c['stderr_cap_bytes'] and
            stdout+stderr<=s['output_bytes'] and resident<=s['sampled_rss_bytes'])

class Output:
    def __init__(self,root,protocol,clock=time.monotonic,cpu_clock=cpu):
        self.root=Path(root).resolve();self.p=protocol;self.clock=clock;self.cpu_clock=cpu_clock
        self.start=clock();self.cpu_start=cpu_clock();self.root.mkdir(exist_ok=False)
        with os.scandir(self.root) as entries:need(not list(entries),'empty output')
        self.rows=rows();self.files={};self.total=0;self.reserved=0;self.live_started=None
        self.cores=os.cpu_count();need(type(self.cores) is int and self.cores>0,'CPU capacity bound')
        self.first_error=None;self.closeout_errors=[];self.exact=True;self.extra_bound=0;self.cpu_extra_upper=0
        self.counts=dict(output_scans=1,poll_scans=0,closeout_scans=0,budget_polls=0,write_calls=0,write_bytes=0,launches=0,kills=0,reaped=0)
        self.write('initial_manifest.json',encoded(dict(schema='p01w-initial-manifest-v1',rows=self.rows)))
    def usage(self):
        # All machine cores over the entire live interval is conservative even for
        # multithreaded children. Replace this upper bound with reaped CPU exactly once.
        live=0 if self.live_started is None else max(0,self.clock()-self.live_started)*self.cores
        actual=self.cpu_clock()-self.cpu_start
        return dict(wall_seconds=self.clock()-self.start,total_process_cpu_seconds=actual+live+self.cpu_extra_upper,
                    controller_and_reaped_cpu_seconds=actual,live_cpu_upper_seconds=live,failed_stage_cpu_upper_seconds=self.cpu_extra_upper,
                    artifact_bytes=self.total+self.extra_bound)
    def poll(self,terminal=False):
        self.counts['budget_polls']+=1;u=self.usage();cap=self.p['campaign']
        need(self.exact or terminal,'unknown accounting')
        for key,reserve in [('wall_seconds',0 if terminal else 5),('total_process_cpu_seconds',0 if terminal else 5),('artifact_bytes',0 if terminal else cap['metadata_reserve_bytes'])]:
            need(u[key]+reserve+(self.reserved if key=='artifact_bytes' else 0)<=cap[key],'aggregate '+key)
    def mark_unknown(self,upper):
        need(type(upper) is int and upper>=0,'unknown bound');self.exact=False;self.extra_bound=upper
    def write(self,name,data,append=False,terminal=False):
        self.poll(terminal);name=str(name);part=Path(name)
        need(not part.is_absolute() and '..' not in part.parts and name not in ('','.'),'owned path')
        need(type(data) is bytes,'byte writer');need(append or name not in self.files,'no replacement')
        cap=self.p['campaign'];reserve=0 if terminal else cap['metadata_reserve_bytes']
        need(self.total+self.extra_bound+self.reserved+len(data)+reserve<=cap['artifact_bytes'],'write reservation')
        target=self.root/part;target.parent.mkdir(parents=True,exist_ok=True)
        flags=os.O_WRONLY|os.O_NOFOLLOW|(os.O_APPEND if append else os.O_CREAT|os.O_EXCL)
        fd=os.open(target,flags,0o600);entry=self.files.setdefault(name,dict(size=0,hash=hashlib.sha256()));offset=0
        try:
            while offset<len(data):
                n=os.write(fd,data[offset:]);need(0<n<=len(data)-offset,'partial syscall count')
                entry['hash'].update(data[offset:offset+n]);entry['size']+=n;self.total+=n;offset+=n
                self.counts['write_calls']+=1;self.counts['write_bytes']+=n
        finally:os.close(fd)
    def finish(self,assessment,provenance):
        self.reserved=0
        try:
            need(self.live_started is None,'unreaped stage')
            self.poll(terminal=True);status='fail' if self.first_error or not self.exact else 'pass'
            manifest=dict(schema='p01w-saved-panel-dynamics-manifest-v1',status=status,rows=self.rows,assessment=assessment,
                first_error=self.first_error,closeout_errors=self.closeout_errors,provenance=provenance,
                scientific_status='untested',e01_authorized=False)
            self.write('manifest.json',encoded(manifest),terminal=True)
            inventory={n:dict(size=e['size'],sha256=e['hash'].hexdigest()) for n,e in self.files.items()}
            self.write('checksums.json',encoded(inventory),terminal=True)
            u=self.usage();cap=self.p['campaign']
            # Seal cannot measure its own final syscall retroactively. State an
            # explicit five-second upper allowance, checked again after that syscall.
            need(u['wall_seconds']+5<=cap['wall_seconds'] and u['total_process_cpu_seconds']+5<=cap['total_process_cpu_seconds'],'seal reserve')
            seal=dict(schema='p01w-campaign-seal-v1',status=status,checksums_sha256=sha(encoded(inventory)),
                manifest_sha256=self.files['manifest.json']['hash'].hexdigest(),usage_before_seal=u,
                terminal_wall_upper_seconds=u['wall_seconds']+5,terminal_cpu_upper_seconds=u['total_process_cpu_seconds']+5,
                output_bytes=0 if self.exact else None,known_path_bytes=0,usage_upper_bound_bytes=0,
                extra_bound_bytes=self.extra_bound,counts_before_seal=dict(self.counts),exact_bytes=self.exact)
            while True:
                data=encoded(seal);known=self.total+len(data);upper=known+self.extra_bound
                if seal['known_path_bytes']==known and seal['usage_upper_bound_bytes']==upper:break
                seal.update(known_path_bytes=known,usage_upper_bound_bytes=upper)
                if self.exact:seal['output_bytes']=known
            self.write('seal.json',data,terminal=True);last=self.usage()
            need(last['wall_seconds']<=seal['terminal_wall_upper_seconds'] and last['total_process_cpu_seconds']<=seal['terminal_cpu_upper_seconds'],'terminal allowance exceeded')
            self.poll(terminal=True)
        except Exception as error:self.closeout_errors.append(repr(error))
        return dict(status='fail' if self.first_error or self.closeout_errors or not self.exact else 'pass',first_error=self.first_error,
                    closeout_errors=self.closeout_errors,terminal_receipt='written' if 'seal.json' in self.files and not self.closeout_errors else 'missing_or_invalid',usage_after_closeout=self.usage())

class TaskInfo(ctypes.Structure):
    _fields_=[('u'+str(i),ctypes.c_uint64) for i in range(6)]+[('i'+str(i),ctypes.c_int32) for i in range(12)]
def rss(pid):
    lib=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True);info=TaskInfo()
    fn=lib.proc_pidinfo;fn.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int];fn.restype=ctypes.c_int
    n=fn(pid,4,0,ctypes.byref(info),ctypes.sizeof(info))
    return int(info.u1) if n==ctypes.sizeof(info) else None

def spawn_suspended(argv):
    """Exact production argv, stopped before user code or request-file reads."""
    need(sys.platform=='darwin','Darwin suspended spawn required')
    lib=ctypes.CDLL(None);actions=ctypes.c_void_p();attr=ctypes.c_void_p();pid=ctypes.c_int()
    def call(name,*args):
        code=getattr(lib,name)(*args)
        if code:raise OSError(code,name)
    call('posix_spawn_file_actions_init',ctypes.byref(actions));call('posix_spawnattr_init',ctypes.byref(attr))
    pipes=[];null=None
    try:
        call('posix_spawnattr_setflags',ctypes.byref(attr),ctypes.c_short(2|128|16384))
        call('posix_spawnattr_setpgroup',ctypes.byref(attr),ctypes.c_int(0))
        null=os.open('/dev/null',os.O_RDONLY);call('posix_spawn_file_actions_adddup2',ctypes.byref(actions),ctypes.c_int(null),ctypes.c_int(0))
        for number in (1,2):
            read,write=os.pipe();pipes.append((read,write))
            call('posix_spawn_file_actions_adddup2',ctypes.byref(actions),ctypes.c_int(write),ctypes.c_int(number))
        args=(ctypes.c_char_p*(len(argv)+1))(*[os.fsencode(a) for a in argv],None)
        env={k:v for k,v in os.environ.items() if not k.startswith(('PYTHON','DYLD_'))};env['PYTHONDONTWRITEBYTECODE']='1'
        environ=(ctypes.c_char_p*(len(env)+1))(*[os.fsencode(k+'='+v) for k,v in env.items()],None)
        call('posix_spawn',ctypes.byref(pid),ctypes.c_char_p(os.fsencode(argv[0])),ctypes.byref(actions),ctypes.byref(attr),args,environ)
        return pid.value,[pair[0] for pair in pipes]
    except BaseException:
        for read,_ in pipes:os.close(read)
        raise
    finally:
        for _,write in pipes:os.close(write)
        if null is not None:os.close(null)
        lib.posix_spawn_file_actions_destroy(ctypes.byref(actions));lib.posix_spawnattr_destroy(ctypes.byref(attr))

def run_stage(out,role,argv,name,identities,sampler=rss):
    need(role in ROLES,'stage role');need(Path(argv[0]).is_absolute(),'absolute executor')
    for filename,digest in identities.items():need(sha(Path(filename).read_bytes())==digest,'executor substitution')
    need(argv[0] in identities,'executor pinned')
    need(fits(out.p,out.usage(),role),'launch reservation')
    s=out.p['per_process'][role];c=out.p['production_contracts'][role]
    out.reserved=s['output_bytes'];out.poll();start=out.clock();pid=None;reaped=None;selector=selectors.DefaultSelector()
    result=dict(role=role,status='failed',launched=False,argv=argv,identities=identities,returncode=None,stdout_bytes=0,stderr_bytes=0,
        stdout_observed_bytes=0,stderr_observed_bytes=0,peak_sampled_rss_bytes=0,peak_rss_bytes=None,rss_samples=0,polls=0,
        pre_input_sample=False,child_cpu_seconds=None,wall_seconds=0,kills=0,error=None)
    names={stream:f'{name}/{stream}.bin' for stream in ('stdout','stderr')}
    for n in names.values():out.write(n,b'')
    def reap(block=False):
        nonlocal reaped
        if pid is not None and reaped is None:
            got,status,usage=os.wait4(pid,0 if block else os.WNOHANG)
            if got:
                reaped=usage;result['returncode']=os.waitstatus_to_exitcode(status);out.counts['reaped']+=1
    try:
        out.live_started=start;pid,fds=spawn_suspended(argv);out.counts['launches']+=1;result['launched']=True
        for stream,fd in zip(('stdout','stderr'),fds):os.set_blocking(fd,False);selector.register(fd,selectors.EVENT_READ,stream)
        sample=sampler(pid);need(sample is not None and sample>0,'pre-input RSS sample')
        result.update(pre_input_sample=True,rss_samples=1,peak_sampled_rss_bytes=sample)
        need(stage_fits(out.p,role,out.clock()-start,0,0,sample),'stage pre-input limits')
        out.poll();os.kill(pid,signal.SIGCONT)
        while reaped is None or selector.get_map():
            result['polls']+=1;reap();out.poll()
            if reaped is None:
                resident=sampler(pid)
                if resident is None:
                    reap();need(reaped is not None,'RSS observation failed')
                else:result['rss_samples']+=1;result['peak_sampled_rss_bytes']=max(result['peak_sampled_rss_bytes'],resident)
            need(stage_fits(out.p,role,out.clock()-start,result['stdout_bytes'],result['stderr_bytes'],result['peak_sampled_rss_bytes']),'stage wall/RSS limit')
            for key,_ in selector.select(out.p['campaign']['poll_seconds']):
                stream=key.data
                try:chunk=os.read(key.fd,16384)
                except BlockingIOError:continue
                if not chunk:selector.unregister(key.fd);os.close(key.fd);continue
                result[stream+'_observed_bytes']+=len(chunk)
                remaining=c[stream+'_cap_bytes']-result[stream+'_bytes'];retained=chunk[:remaining]
                out.reserved-=len(retained);out.write(names[stream],retained,append=True)
                result[stream+'_bytes']+=len(retained)
                need(len(retained)==len(chunk),'stage '+stream+' cap')
        need(result['returncode']==0,'stage nonzero exit')
        # Unexpected descendants may keep the group alive after the direct child.
        try:os.killpg(pid,0)
        except ProcessLookupError:pass
        else:
            raise ValueError('unexpected surviving process group')
        result['peak_rss_bytes']=int(reaped.ru_maxrss)
        need(result['peak_rss_bytes']<=s['sampled_rss_bytes'],'reaped peak RSS')
        out.live_started=None
        result['status']='complete'
    except BaseException as error:
        result['error']=repr(error)
        if pid is not None:
            try:os.killpg(pid,signal.SIGKILL);result['kills']+=1;out.counts['kills']+=1
            except ProcessLookupError:pass
            reap(True)
        else:out.live_started=None
    finally:
        if result['status']!='complete' and pid is not None:
            # A failed stage may have descendants whose exact CPU is unavailable.
            # Charge all hardware cores over its entire lifetime as an upper bound.
            out.cpu_extra_upper+=(out.clock()-start)*out.cores
        out.live_started=None
        for key in list(selector.get_map().values()):os.close(key.fd)
        selector.close();out.reserved=0
        if reaped is not None:
            result['child_cpu_seconds']=reaped.ru_utime+reaped.ru_stime;result['peak_rss_bytes']=int(reaped.ru_maxrss)
        result['wall_seconds']=out.clock()-start
        result['stdout_file']=names['stdout'];result['stderr_file']=names['stderr']
    out.write(name+'/guard.json',encoded(result),terminal=result['status']!='complete')
    return result,(out.root/names['stdout']).read_bytes(),(out.root/names['stderr']).read_bytes()

def probe():
    need(sys.platform=='darwin' and rss(os.getpid())>0,'RSS capability')
    need(type(os.cpu_count()) is int and os.cpu_count()>0 and cpu()>=0,'CPU capability')
    pid=None;done=False;start=time.monotonic()
    try:
        pid,fds=spawn_suspended([str(Path(sys.executable).resolve()),'-I','-B','-c','pass'])
        for fd in fds:os.close(fd)
        need(rss(pid) is not None and rss(pid)>0,'suspended child RSS capability')
        need(os.getpgid(pid)==pid,'process group capability');os.kill(pid,signal.SIGCONT)
        while not done:
            got,status,used=os.wait4(pid,os.WNOHANG)
            if got:
                done=True;need(os.waitstatus_to_exitcode(status)==0 and used.ru_utime+used.ru_stime>=0,'reaped CPU capability')
            else:
                need(time.monotonic()-start<2,'capability timeout');time.sleep(.005)
    finally:
        if pid is not None and not done:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:pass
            os.wait4(pid,0)
    return dict(platform=sys.platform,cpu_bound_cores=os.cpu_count(),self_rss_bytes=rss(os.getpid()),cpu_accounting='self_plus_reaped_plus_all_cores_live_upper_bound')
