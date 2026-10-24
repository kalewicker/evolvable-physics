"""Restricted P01v executor and inert terminal manifest over frozen P01u guards."""
import ast
import os
import sys
import time
from pathlib import Path
from p01u_validation import Output as BaseOutput, run_stage, parse, encoded, sha, typed, policy, rss
ROOT=Path(__file__).resolve().parents[1]
ROLES=('native_stub','report_stub','audit_stub')
_ACTIVE_EXECUTOR=None
_STRICT_EXECUTOR=False

def _observe_process(event,args):
    if event=='subprocess.Popen':
        if _ACTIVE_EXECUTOR is None:
            if _STRICT_EXECUTOR:raise RuntimeError('process outside pinned executor')
        else:
            expected,out=_ACTIVE_EXECUTOR
            if list(args[1])!=expected:raise RuntimeError('process argv substitution')
            out.executor_counts['invocations']+=1
    elif _STRICT_EXECUTOR and event in ('os.system','os.fork','os.posix_spawn'):
        raise RuntimeError('unapproved process API')

sys.addaudithook(_observe_process)

def lock_executor():
    global _STRICT_EXECUTOR
    _STRICT_EXECUTOR=True


def need(ok,why):
    if not ok:raise ValueError(why)


def initialize_rows():
    return [dict(slot=i,proposal=6000+i//4,initial=i%4,status='unstarted',
        stages=[dict(role=role,status='unstarted') for role in ROLES]) for i in range(128)]


class Output(BaseOutput):
    def __init__(self,root,clock=time.monotonic):
        super().__init__(root,clock);self.rows=initialize_rows();self.exact=True;self.extra_bound=0
        self.executor_counts=dict(invocations=0,interpreter_recheck_bytes=0,fixture_recheck_bytes=0)
    def poll(self):
        need(self.exact,'incomplete accounting')
        super().poll()
    def mark_unknown(self,upper_extra_bytes):
        need(type(upper_extra_bytes) is int and upper_extra_bytes>=0,'unknown bound')
        self.exact=False;self.extra_bound=upper_extra_bytes
    def finish(self):
        status='fail' if self.first_error else 'pass'
        if not self.exact and status=='pass':status='fail';self.first_error='incomplete accounting'
        try:
            self.reserved=0
            manifest=dict(schema='p01v-inert-campaign-manifest-v1',status=status,rows=self.rows,
                first_error=self.first_error,closeout_errors=self.closeout_errors,executor_counts=self.executor_counts,
                world_transitions=0,keyed_evaluations=0,scientific_status='untested',behavioral_outcomes=None,
                behavioral_missing_reason='not_executed')
            self.write('manifest.json',encoded(manifest),terminal=True)
            inv={name:dict(size=len(data),sha256=sha(data)) for name,data in self.data.items()}
            self.write('checksums.json',encoded(inv),terminal=True)
            completion=dict(status=status,checksums_sha256=sha(self.data['checksums.json']),output_bytes=0 if self.exact else None,
                known_path_bytes=0,usage_upper_bound_bytes=0,extra_bound_bytes=self.extra_bound,
                counts_before_completion=dict(self.counts),wall_seconds=self.clock()-self.start,
                reconciliation='pending_independent_audit' if status=='pass' else 'incomplete')
            while True:
                data=encoded(completion);known=self.total+len(data);upper=known+self.extra_bound
                if completion['known_path_bytes']==known and completion['usage_upper_bound_bytes']==upper:break
                completion['known_path_bytes']=known;completion['usage_upper_bound_bytes']=upper
                if self.exact:completion['output_bytes']=known
            need(upper<134217728,'terminal conservative byte bound')
            self.write('completion.json',data,terminal=True)
        except Exception as error:status='fail';self.closeout_errors.append(repr(error))
        return dict(status=status,first_error=self.first_error,closeout_errors=self.closeout_errors,
            terminal_receipt='written' if 'completion.json' in self.data and not self.closeout_errors else 'missing',
            output_bytes=self.total if self.exact else None,known_path_bytes=self.total,usage_upper_bound_bytes=self.total+self.extra_bound)


def command(pins,role,row,request_hash):
    need(role in ROLES,'allowed role')
    need(all(type(row[k]) is int for k in ('slot','proposal','initial')),'integer identity')
    need(0<=row['slot']<128 and row['proposal']==6000+row['slot']//4 and row['initial']==row['slot']%4,'cell identity')
    return [pins['interpreter'],'-I','-B',pins['fixture'],role,str(row['slot']),str(row['proposal']),str(row['initial']),request_hash]


def check_command(argv,pins,role,row,request_hash):
    need(argv==command(pins,role,row,request_hash),'executor argv allowlist')
    need(Path(pins['interpreter']).is_absolute() and Path(pins['fixture']).is_absolute(),'absolute executors')
    interpreter=Path(pins['interpreter']).read_bytes();fixture=Path(pins['fixture']).read_bytes()
    need(sha(interpreter)==pins['interpreter_sha256'] and sha(fixture)==pins['fixture_sha256'],'executor substitution')
    return len(interpreter),len(fixture)


def invoke(out,name,pins,role,row,request_hash,data):
    argv=command(pins,role,row,request_hash);interpreter_bytes,fixture_bytes=check_command(argv,pins,role,row,request_hash)
    out.executor_counts['interpreter_recheck_bytes']+=interpreter_bytes;out.executor_counts['fixture_recheck_bytes']+=fixture_bytes
    global _ACTIVE_EXECUTOR
    need(_ACTIVE_EXECUTOR is None,'nested executor')
    _ACTIVE_EXECUTOR=(argv,out)
    try:stats,stdout,stderr=run_stage(out,name,argv,data)
    finally:_ACTIVE_EXECUTOR=None
    stats.update(argv=argv,interpreter_sha256=pins['interpreter_sha256'],fixture_sha256=pins['fixture_sha256'],
                 stdin_sha256=sha(data),invocation_ordinal=out.executor_counts['invocations'])
    # The frozen guard wrote its own stage.json. Preserve it and add a distinct binding receipt.
    out.write(name+'/binding.json',encoded(stats),terminal=stats['status']!='complete')
    return stats,stdout,stderr


def source_gate(sources):
    """Exact source pins are supplied by custody; inspect imports and authored call edges."""
    calls={};imports={}
    allowed_imports={
        'fixture':{'hashlib','json','math','sys'},
        'guard':{'ast','os','sys','time','pathlib','p01u_validation'},
        'pipeline':{'hashlib','json','os','sys','time','pathlib','p01v_guard'},
    }
    forbidden={'main_native','check_report','source_gate_native','generate','bounded_step','step','match_candidates','validate_native'}
    for role,source in sources.items():
        tree=ast.parse(source);names=[];edges=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.extend(x.name for x in node.names)
            if isinstance(node,ast.ImportFrom):names.append(node.module)
            if isinstance(node,ast.Call):
                name=ast.unparse(node.func);edges.append(name)
                need(name.split('.')[-1] not in forbidden and not name.startswith(('subprocess.','os.system','os.spawn','os.exec','__import__','eval','exec')),'forbidden source call')
        need(set(names)<=allowed_imports[role],'unexpected imports '+role)
        if role=='fixture':need(not any(name.startswith(('os.','p01')) for name in edges),'fixture runtime calls')
        if role=='guard':
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module=='p01u_validation':
                    need({x.name for x in node.names}<={'Output','run_stage','parse','encoded','sha','typed','policy','rss'},'frozen helper call surface')
        calls[role]=sorted(set(edges));imports[role]=sorted(set(names))
    return dict(status='pass',sources={role:sha(src.encode()) for role,src in sources.items()},authored_calls=calls,imports=imports)


def within_stage_limits(wall,combined_bytes,resident):
    return wall<2 and combined_bytes<1048576 and resident<268435456
