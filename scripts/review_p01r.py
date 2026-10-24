#!/usr/bin/env python3
"""P01r read-only saved-record diagnosis; never imports old project runtimes."""
import ast
import hashlib
import json
import sys
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=None
def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def tick():
    if ACTIVE is not None:
        ACTIVE.check()


def load(path):
    tick()
    return json.loads(Path(path).read_bytes())


def sha(path):
    tick()
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Attempt:
    def __init__(self, out):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=False)
        self.start = time.monotonic()
        self.bytes = 0
        self.cap = 134217728
        self.write('started.json', dict(status='started', keyed_evaluations=0, world_transitions=0))

    def check(self):
        require(time.monotonic()-self.start < 120, 'cooperative wall limit')

    def raw(self, name, data, terminal=False):
        if not terminal:
            self.check()
        require(self.bytes+len(data) <= self.cap-(0 if terminal else 1048576), 'emitted byte limit')
        p = self.out/name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(data)
        self.bytes += len(data)

    def write(self, name, data, terminal=False):
        self.raw(name, (json.dumps(data, sort_keys=True, indent=2)+'\n').encode(), terminal)

    def finish(self, result):
        global ACTIVE
        ACTIVE = None
        if time.monotonic()-self.start >= 120:
            result.update(status='fail', error='cooperative wall limit at finalization')
        self.write('assessment.json', result, True)
        inventory = {str(p.relative_to(self.out)): sha(p) for p in sorted(self.out.rglob('*')) if p.is_file()}
        self.write('checksums.json', inventory, True)
        completion = dict(wall_seconds_including_inventory=time.monotonic()-self.start,
            output_bytes_including_completion=0, wall_ceiling_seconds=120, output_ceiling_bytes=self.cap,
            checksums_sha256=sha(self.out/'checksums.json'), status=result['status'])
        while True:
            data = (json.dumps(completion, sort_keys=True, indent=2)+'\n').encode()
            total = self.bytes+len(data)
            if completion['output_bytes_including_completion'] == total:
                break
            completion['output_bytes_including_completion'] = total
        self.raw('completion.json', data, True)
        return result


def prohibit_processes(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in ('os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('P01r read-only tools forbid process creation')


def custody(attempt, receipt_path):
    f=load(ROOT/'docs/p01r_analysis_freeze.json');p=load(ROOT/'docs/p01r_protocol.json')
    for section in ('files','inputs','prior_public_receipts'):
        for name,h in f[section].items():require(sha(ROOT/name)==h,section+': '+name)
    tests=load(receipt_path)
    sources={name:sha(ROOT/name) for name in p['future_paths'].values()}
    require(tests['status']=='pass' and tests['returncodes']==[0,0] and tests['controls']==p['invented_interface_controls']+p['invented_accounting_controls'],'invented test gate')
    require(tests['sources']==sources,'tested sources')
    require(sha(ROOT/tests['packet'])==tests['packet_sha256'],'invented packet')
    identities=dict(frozen_sources=f['files'],inputs=f['inputs'],implementation=sources,
        freeze_sha256=sha(ROOT/'docs/p01r_analysis_freeze.json'),test_receipt_sha256=sha(receipt_path))
    attempt.write('identities.json',identities);attempt.raw('tests.json',Path(receipt_path).read_bytes())
    attempt.raw('controls.json',(ROOT/tests['packet']).read_bytes())
    for name in list(sources)+['docs/p01r_protocol.json','docs/p01r_analysis_freeze.json','docs/p01r_analysis_plan.md']:
        attempt.raw('sources/'+name,(ROOT/name).read_bytes())
    counts={}
    for name,h in p['source_bundles'].items():
        b=ROOT/name;inv=load(b/'checksums.json');seal=load(b/'seal.json')
        require(sha(b/'seal.json')==h,'seal identity')
        require({str(x.relative_to(b)) for x in b.rglob('*') if x.is_file()}==set(inv)|{'checksums.json','seal.json'},'inventory membership')
        for n,d in inv.items():require(sha(b/n)==d,'sealed file: '+n)
        require(sha(b/'manifest.json')==seal['manifest_sha256'] and sha(b/'checksums.json')==seal['checksums_sha256'],'seal links')
        counts[name]=len(inv)
    attempt.write('custody.json',dict(status='pass',frozen_files=len(f['files']),inputs=len(f['inputs']),
        prior_public_receipts=len(f['prior_public_receipts']),original_inventories=counts))
    return p,load(ROOT/tests['packet'])


def inventory_sizes(bundle):
    inv=load(bundle/'checksums.json')
    return dict(entries=len(inv),listed_bytes=sum((bundle/n).stat().st_size for n in inv),
        seal_and_inventory_bytes=sum((bundle/n).stat().st_size for n in ('checksums.json','seal.json')))


def terminal_records():
    m=load(ROOT/'artifacts/p01q-001/manifest.json');s=load(ROOT/'artifacts/p01q-001/seal.json')
    return dict(classification='confirmed_from_saved_records',execution_status=m['execution_status'],
        first_error=m['error'],terminal_recheck_error=m['provenance_error'],
        status_counts=dict(Counter(x['status'] for x in m['rows'])),stage_records=sum(len(x['stages']) for x in m['rows']),
        resource_usage=s['resource_usage'],engineering_gate_pass=s['engineering_gate_pass'],
        frozen_receipt_audit=load(ROOT/'artifacts/p01q-receipt-audit-001/stdout.json')['status'],
        later_custody_check=load(ROOT/'artifacts/p01q-closeout-001/receipt.json')['status'],
        later_check_replaces_original_failure=False,behavioral_outcomes=None,behavioral_missing_reason='not_executed')


SOURCE_FUNCTIONS={'scripts/generator_v4.py':['construct_with_source'],
    'scripts/p01q_cell.py':['saved_initial'],'scripts/p01q_campaign.py':['execute_pipeline','usage','check_budget','check_execution'],
    'scripts/test_p01q.py':['saved'],'scripts/campaign.py':['file_bytes']}
CALL_NAMES={'tick','check_budget','usage','campaign.file_bytes','check_execution'}


def main():
    global ACTIVE
    sys.addaudithook(prohibit_processes)
    out=Path(sys.argv[1]);a=Attempt(out);ACTIVE=a
    try:
        result=work(a,Path(sys.argv[2]),*(Path(x) for x in sys.argv[3:]))
    except BaseException as e:
        result=dict(status='fail',error=repr(e),world_transitions=0,keyed_evaluations=0)
    result=a.finish(result)
    print(json.dumps(result,sort_keys=True))
    if result['status']!='pass':raise SystemExit(1)


def equal(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b


def envelope(value,slot,proposal,initial):
    if not isinstance(value,dict):return dict(valid_envelope=False,reasons=['not_object'],keys=[],root_native=False,nested_native=False)
    reasons=[]
    if value.get('schema')!='p01o-generated-environment-v1':reasons.append('schema')
    for k,want in [('slot',slot),('proposal',proposal),('initial',initial)]:
        if type(value.get(k)) is not int or value[k]!=want:reasons.append(k)
    env=value.get('environment');native=env.get('native') if isinstance(env,dict) else None
    if not isinstance(env,dict):reasons.append('environment')
    if not isinstance(native,dict):reasons.append('environment.native')
    return dict(valid_envelope=not reasons,reasons=reasons,keys=sorted(value),root_native=isinstance(value.get('native'),dict),nested_native=isinstance(native,dict))


def pair(a,b,slot,proposal,initial):
    left=envelope(a,slot,proposal,initial);right=envelope(b,slot,proposal,initial)
    nested=equal(a['environment'],b['environment']) if isinstance(a,dict) and isinstance(b,dict) and isinstance(a.get('environment'),dict) and isinstance(b.get('environment'),dict) else None
    return dict(left=left,right=right,typed_equal=equal(a,b),nested_environment_equal=nested,
        root_native_expected_by_runner=left['root_native'] and right['root_native'],
        nested_native_available=left['nested_native'] and right['nested_native'],
        classification='confirmed_from_saved_records',worker_semantic_validity=None)


def accounting(case):
    if 'terminal_statuses' in case:
        rows=case['terminal_statuses']
        require(len(rows)==128 and [r['slot'] for r in rows]==list(range(128)) and rows[0]['status']=='failed' and all(r['status']=='unstarted' for r in rows[1:]),'terminal denominator')
    sizes={};totals=[]
    for op in case.get('operations',[]):
        tag=op['op'];path=op['path']
        if tag=='set':sizes[path]=op['bytes']
        elif tag=='append':sizes[path]=sizes.get(path,0)+op['bytes']
        elif tag=='rename':sizes[op['to']]=sizes.pop(path)
        elif tag=='delete':del sizes[path]
        else:raise ValueError('unknown descriptor operation')
        require(all(type(v) is int and v>=0 for v in sizes.values()),'integer sizes')
        totals.append(sum(sizes.values()))
    checks=[]
    for c in case.get('reservations',[]):
        checks.append(all(Decimal(c['usage'][k])+Decimal(c['reserve'][k])<Decimal(c['cap'][k]) for k in ('cpu','wall','bytes')))
    return dict(totals=totals,final_bytes=sum(sizes.values()),paths=sorted(sizes),reservations_fit=checks,
        inventory_matches=(sorted(sizes)==sorted(case['inventory'])) if 'inventory' in case else None,
        terminal_statuses=case.get('terminal_statuses'))


def source_analysis():
    spans=[];calls=[]
    for path,names in SOURCE_FUNCTIONS.items():
        tick();text=(ROOT/path).read_text();tree=ast.parse(text);lines=text.splitlines()
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
                snippet='\n'.join(lines[node.lineno-1:node.end_lineno])+'\n'
                spans.append(dict(path=path,start=node.lineno,end=node.end_lineno,name=node.name,source_sha256=sha(ROOT/path),text=snippet,classification='source_derived'))
        if path!='scripts/p01q_campaign.py':continue
        def walk(node,functions,context):
            fs=functions+[node.name] if isinstance(node,ast.FunctionDef) else functions
            cs=context+[dict(kind=type(node).__name__,line=node.lineno)] if isinstance(node,(ast.For,ast.While,ast.If,ast.Try,ast.ExceptHandler,ast.ListComp,ast.DictComp,ast.SetComp,ast.GeneratorExp)) else context
            if isinstance(node,ast.Call):
                name=ast.unparse(node.func)
                if name in CALL_NAMES:calls.append(dict(path=path,line=node.lineno,end=node.end_lineno,call=name,functions=fs,context=cs,text=ast.get_source_segment(text,node),classification='source_derived',dynamic_calls=None,dynamic_calls_reason='uninstrumented'))
            for child in ast.iter_child_nodes(node):walk(child,fs,cs)
        walk(tree,[],[])
    # Rust consumer span is text, never compiled or invoked.
    path='src/bin/pilot-worker.rs';text=(ROOT/path).read_text();lines=text.splitlines()
    start=next(i for i,x in enumerate(lines,1) if 'let request: Request' in x)
    end=next(i for i,x in enumerate(lines,1) if 'let start_event' in x)
    spans.append(dict(path=path,start=start,end=end,name='worker_request_consumer',source_sha256=sha(ROOT/path),text='\n'.join(lines[start-1:end])+'\n',classification='source_derived'))
    return dict(spans=sorted(spans,key=lambda x:(x['path'],x['start'])),call_sites=sorted(calls,key=lambda x:x['line']),
        timing_attribution=None,timing_attribution_reason='uninstrumented',classification='source_derived')


def work(a,test_receipt):
    p,packet=custody(a,test_receipt)
    control_results=[]
    for c in packet:
        result=pair(c['left'],c['right'],0,6000,0) if c['kind']=='interface' else accounting(c['case'])
        require(equal(result,c['expected']),'invented control: '+c['name']);control_results.append(dict(name=c['name'],result=result))
    a.write('control_results.json',control_results)
    rows=[]
    for slot,(proposal,initial) in enumerate((pr,i) for pr in p['proposal_ids'] for i in p['initial_ids']):
        tick();streams=[];inputs=[];errors=[]
        for lang in ('rust_generation','python_generation'):
            path=ROOT/f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin'
            inputs.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
            try:streams.append(load(path))
            except (ValueError,OSError) as e:streams.append(None);errors.append(dict(language=lang,error=repr(e)))
        rows.append(dict(slot=slot,proposal=proposal,initial=initial,inputs=inputs,parse_errors=errors,
                         **pair(*streams,slot,proposal,initial)))
    a.write('cells.json',rows);a.write('source_analysis.json',source_analysis())
    f=load(ROOT/'docs/p01q_execution_freeze.json')
    sizes={n:inventory_sizes(ROOT/n) for n in p['source_bundles']}
    accounting_record=dict(classification='confirmed_from_saved_records',inventories=sizes,
        declared_source_entries=len(f['files']),declared_dependency_entries=len(f['dependencies']),
        copied_source_bytes=sum((ROOT/'artifacts/p01q-001/source'/n).stat().st_size for n in f['files']),
        actual_scan_invocations=None,per_operation_costs=None,missing_reason='uninstrumented')
    a.write('accounting.json',accounting_record);a.write('terminal.json',terminal_records())
    summary=dict(status='pass',cells=len(rows),saved_streams=2*len(rows),typed_equal_cells=sum(x['typed_equal'] for x in rows),
        nested_native_cells=sum(x['nested_native_available'] for x in rows),root_native_cells=sum(x['root_native_expected_by_runner'] for x in rows),
        valid_envelope_pairs=sum(x['left']['valid_envelope'] and x['right']['valid_envelope'] for x in rows),
        parse_error_cells=sum(bool(x['parse_errors']) for x in rows),controls=len(control_results),
        world_transitions=0,keyed_evaluations=0,behavioral_outcomes=None,behavioral_missing_reason='not_executed',scientific_status='untested')
    a.write('summary.json',summary);return summary

if __name__=='__main__':main()
