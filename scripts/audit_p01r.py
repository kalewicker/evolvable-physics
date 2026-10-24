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


def typed(value):
    if isinstance(value,dict):return ('object',tuple((k,typed(v)) for k,v in sorted(value.items())))
    if isinstance(value,list):return ('array',tuple(map(typed,value)))
    return (type(value).__name__,value)


def describe(x,want):
    obj=type(x) is dict
    if not obj:return {'valid_envelope':False,'reasons':['not_object'],'keys':[],'root_native':False,'nested_native':False}
    bad=[]
    if x.get('schema')!='p01o-generated-environment-v1':bad.append('schema')
    for field,value in zip(('slot','proposal','initial'),want):
        if typed(x.get(field))!=typed(value):bad.append(field)
    nested=x.get('environment')
    if type(nested) is not dict:bad.append('environment')
    has_native=type(nested) is dict and type(nested.get('native')) is dict
    if not has_native:bad.append('environment.native')
    return dict(valid_envelope=len(bad)==0,reasons=bad,keys=sorted(x),root_native=type(x.get('native')) is dict,nested_native=has_native)


def pair(a,b,slot,proposal,initial):
    l,r=describe(a,(slot,proposal,initial)),describe(b,(slot,proposal,initial))
    both_env=type(a) is dict and type(b) is dict and type(a.get('environment')) is dict and type(b.get('environment')) is dict
    return dict(left=l,right=r,typed_equal=typed(a)==typed(b),nested_environment_equal=(typed(a['environment'])==typed(b['environment']) if both_env else None),
        root_native_expected_by_runner=all(x['root_native'] for x in (l,r)),nested_native_available=all(x['nested_native'] for x in (l,r)),
        classification='confirmed_from_saved_records',worker_semantic_validity=None)


def accounting(case):
    if 'terminal_statuses' in case:
        rows=case['terminal_statuses']
        require(len(rows)==128 and [r['slot'] for r in rows]==list(range(128)) and rows[0]['status']=='failed' and all(r['status']=='unstarted' for r in rows[1:]),'terminal denominator')
    entries=[];totals=[]
    for record in case.get('operations',[]):
        path=record['path'];current=dict(entries);op=record['op']
        if op=='set':current[path]=record['bytes']
        elif op=='append':current[path]=current.get(path,0)+record['bytes']
        elif op=='rename':current[record['to']]=current.pop(path)
        elif op=='delete':current.pop(path)
        else:raise ValueError('unknown descriptor operation')
        require(all(type(v) is int and v>=0 for v in current.values()),'integer byte descriptor')
        entries=sorted(current.items());totals.append(sum(v for _,v in entries))
    fits=[]
    for r in case.get('reservations',[]):
        remaining=[Decimal(r['cap'][k])-Decimal(r['usage'][k])-Decimal(r['reserve'][k]) for k in ('bytes','wall','cpu')]
        fits.append(min(remaining)>0)
    paths=[k for k,_ in entries]
    return dict(totals=totals,final_bytes=sum(v for _,v in entries),paths=paths,reservations_fit=fits,
        inventory_matches=paths==sorted(case['inventory']) if 'inventory' in case else None,terminal_statuses=case.get('terminal_statuses'))


def verify_sources(record):
    expected=[];calls=[]
    for path,names in SOURCE_FUNCTIONS.items():
        text=(ROOT/path).read_text();tree=ast.parse(text);lines=text.splitlines();parents={child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
                expected.append(dict(path=path,start=node.lineno,end=node.end_lineno,name=node.name,source_sha256=sha(ROOT/path),text='\n'.join(lines[node.lineno-1:node.end_lineno])+'\n',classification='source_derived'))
            if path=='scripts/p01q_campaign.py' and isinstance(node,ast.Call) and ast.unparse(node.func) in CALL_NAMES:
                ancestors=[];cur=node
                while cur in parents:cur=parents[cur];ancestors.insert(0,cur)
                calls.append(dict(path=path,line=node.lineno,end=node.end_lineno,call=ast.unparse(node.func),
                    functions=[n.name for n in ancestors if isinstance(n,ast.FunctionDef)],
                    context=[dict(kind=type(n).__name__,line=n.lineno) for n in ancestors if isinstance(n,(ast.For,ast.While,ast.If,ast.Try,ast.ExceptHandler,ast.ListComp,ast.DictComp,ast.SetComp,ast.GeneratorExp))],
                    text=ast.get_source_segment(text,node),classification='source_derived',dynamic_calls=None,dynamic_calls_reason='uninstrumented'))
    path='src/bin/pilot-worker.rs';lines=(ROOT/path).read_text().splitlines()
    starts=[i for i,l in enumerate(lines,1) if 'let request: Request' in l];ends=[i for i,l in enumerate(lines,1) if 'let start_event' in l]
    require(len(starts)==len(ends)==1,'worker span uniqueness')
    expected.append(dict(path=path,start=starts[0],end=ends[0],name='worker_request_consumer',source_sha256=sha(ROOT/path),text='\n'.join(lines[starts[0]-1:ends[0]])+'\n',classification='source_derived'))
    want=dict(spans=sorted(expected,key=lambda x:(x['path'],x['start'])),call_sites=sorted(calls,key=lambda x:x['line']),timing_attribution=None,timing_attribution_reason='uninstrumented',classification='source_derived')
    require(typed(want)==typed(record),'complete source spans and static call sites')
    return len(expected),len(calls)


def verify_review_bundle(b):
    inv=load(b/'checksums.json');completion=load(b/'completion.json')
    require({str(p.relative_to(b)) for p in b.rglob('*') if p.is_file()}==set(inv)|{'checksums.json','completion.json'},'review membership')
    for name,h in inv.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,'review path')
        require(sha(b/name)==h,'review inventory')
    require(completion['checksums_sha256']==sha(b/'checksums.json') and completion['status']=='pass','review completion')
    require(completion['output_bytes_including_completion']==sum(p.stat().st_size for p in b.rglob('*') if p.is_file()),'review byte count')
    require(completion['output_bytes_including_completion']<=134217728 and completion['wall_seconds_including_inventory']<120,'review bounds')
    return len(inv)


def work(a,test_receipt,review):
    p,packet=custody(a,test_receipt);count=verify_review_bundle(review)
    require(typed(load(a.out/'identities.json'))==typed(load(review/'identities.json')),'same identities')
    require(typed(packet)==typed(load(review/'controls.json')),'same invented packet')
    controls=[]
    for c in packet:
        answer=pair(c['left'],c['right'],0,6000,0) if c['kind']=='interface' else accounting(c['case'])
        require(typed(answer)==typed(c['expected']),'independent control: '+c['name'])
        controls.append(dict(name=c['name'],result=answer))
    require(typed(controls)==typed(load(review/'control_results.json')),'review control answers')
    rows=load(review/'cells.json');require(len(rows)==128,'all cells')
    rebuilt=[]
    for slot,row in enumerate(rows):
        proposal=6000+slot//4;initial=slot%4;data=[];ids=[];errors=[]
        for lang in ('rust_generation','python_generation'):
            name=f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin';ids.append(dict(path=name,sha256=sha(ROOT/name)))
            try:data.append(load(ROOT/name))
            except (ValueError,OSError) as e:data.append(None);errors.append(dict(language=lang,error=repr(e)))
        want=dict(slot=slot,proposal=proposal,initial=initial,inputs=ids,parse_errors=errors,**pair(*data,slot,proposal,initial))
        require(typed(want)==typed(row),'independent cell: '+str(slot));rebuilt.append(want)
    span_count,call_count=verify_sources(load(review/'source_analysis.json'))
    terminal=terminal_records();require(typed(terminal)==typed(load(review/'terminal.json')),'terminal records')
    require(terminal['stage_records']==0 and terminal['status_counts']==dict(failed=1,unstarted=127),'zero stages, retained denominator')
    require(terminal['first_error']=="KeyError('native')" and terminal['terminal_recheck_error']=="AssertionError('aggregate CPU reserve')",'both failures')
    f=load(ROOT/'docs/p01q_execution_freeze.json');sizes={}
    for name in p['source_bundles']:
        b=ROOT/name;inv=load(b/'checksums.json');sizes[name]=dict(entries=len(inv),listed_bytes=sum((b/k).stat().st_size for k in sorted(inv)),seal_and_inventory_bytes=(b/'seal.json').stat().st_size+(b/'checksums.json').stat().st_size)
    rec=dict(classification='confirmed_from_saved_records',inventories=sizes,declared_source_entries=len(f['files']),declared_dependency_entries=len(f['dependencies']),copied_source_bytes=sum((ROOT/'artifacts/p01q-001/source'/n).stat().st_size for n in sorted(f['files'])),actual_scan_invocations=None,per_operation_costs=None,missing_reason='uninstrumented')
    require(typed(rec)==typed(load(review/'accounting.json')),'inventory sizes and unknown timing')
    require(sizes['artifacts/p01q-001']['listed_bytes']+sizes['artifacts/p01q-001']['seal_and_inventory_bytes']==terminal['resource_usage']['artifact_bytes'],'sealed byte reconciliation')
    expected=dict(status='pass',cells=128,saved_streams=256,typed_equal_cells=sum(r['typed_equal'] for r in rebuilt),nested_native_cells=sum(r['nested_native_available'] for r in rebuilt),root_native_cells=sum(r['root_native_expected_by_runner'] for r in rebuilt),valid_envelope_pairs=sum(r['left']['valid_envelope'] and r['right']['valid_envelope'] for r in rebuilt),parse_error_cells=sum(bool(r['parse_errors']) for r in rebuilt),controls=len(controls),world_transitions=0,keyed_evaluations=0,behavioral_outcomes=None,behavioral_missing_reason='not_executed',scientific_status='untested')
    require(typed(expected)==typed(load(review/'summary.json')) and typed(expected)==typed(load(review/'assessment.json')),'summary')
    result=dict(status='pass',cells_verified=128,saved_streams_verified=256,controls_verified=len(controls),source_spans_verified=span_count,static_call_sites_verified=call_count,review_inventory_entries=count,review_completion_sha256=sha(review/'completion.json'),world_transitions=0,keyed_evaluations=0,timing_attribution=None,scientific_status='untested')
    a.write('audit.json',result);return result

if __name__=='__main__':main()
