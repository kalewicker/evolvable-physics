"""Fixed P01v input admission and three inert stage chains; no native execution."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from p01v_guard import Output, ROLES, invoke, source_gate, parse, encoded, sha, typed, policy, lock_executor
ROOT=Path(__file__).resolve().parents[1]


def need(ok,why):
    if not ok:raise ValueError(why)


def load_request(data,expected,row,prior_native):
    need(len(data)<524288 and sha(data)==expected,'saved request bytes')
    request=parse(data);need(policy(request),'request policy')
    need(typed(parse(encoded(request)))==typed(request),'typed request roundtrip')
    need(type(prior_native) is dict and prior_native['status']=='complete' and prior_native['native_accepted'] is True,'prior native acceptance')
    need(typed([prior_native[k] for k in ('slot','proposal','initial')])==typed([row[k] for k in ('slot','proposal','initial')]),'prior native cell identity')
    need(prior_native['input_sha256']==expected,'prior native request binding')
    return data


def expected_receipt(role,row,request_hash,previous_hash):
    return dict(schema='p01v-inert-stage-receipt-v1',inert=True,role=role,slot=row['slot'],proposal=row['proposal'],
                initial=row['initial'],input_request_sha256=request_hash,previous_stdout_sha256=previous_hash)


def stage_input(request,previous):
    if previous is None:return request
    return encoded(dict(schema='p01v-stage-input-v1',request_utf8=request.decode(),previous_stdout_utf8=previous.decode()))


def run_pipeline(out,descriptors,reader,native_rows,pins,fault=None,invented=False):
    need(fault is None or invented,'failure injection is invented-only')
    try:
        need(len(descriptors)==128 and len(native_rows)==128,'all128 input descriptors')
        need([d['slot'] for d in descriptors]==list(range(128)),'all128 descriptor order')
        if fault and fault['kind']=='before':raise ValueError('invented failure before cell0')
        for row,descriptor,prior_native in zip(out.rows,descriptors,native_rows):
            current=None
            try:
                out.poll();row['status']='admitting_input'
                need(typed([descriptor[k] for k in ('slot','proposal','initial')])==typed([row[k] for k in ('slot','proposal','initial')]),'saved cell identity')
                request=load_request(reader(descriptor['file']),descriptor['sha256'],row,prior_native)
                row.update(input_sha256=sha(request),request_bytes=len(request),prior_native_accepted=True)
                previous=None
                for current,role in zip(row['stages'],ROLES):
                    current['status']='running';payload=stage_input(request,previous)
                    if fault and row['slot']==fault['slot'] and role==fault['role']:
                        need(fault['kind']=='stage','invented stage fault')
                        # Malformed only in invented fixtures; the real saved requests are never altered.
                        payload=b'{' if role!='native_stub' else b'{}'
                    name=f"stages/{row['slot']:03}/{role}"
                    guard,stdout,stderr=invoke(out,name,pins,role,row,row['input_sha256'],payload)
                    current.update(guard=guard,stdin_sha256=sha(payload),stdout_sha256=sha(stdout),stderr_bytes=len(stderr))
                    need(guard['status']=='complete' and not stderr,'inert process guard')
                    receipt=parse(stdout);previous_hash=None if previous is None else sha(previous)
                    need(typed(receipt)==typed(expected_receipt(role,row,row['input_sha256'],previous_hash)),'inert receipt identity/chain')
                    need(stdout==encoded(receipt)+b'\n','inert receipt serialization')
                    current['status']='fixture_complete';previous=stdout
                row['status']='plumbing_complete'
            except Exception as error:
                if current is not None:current['status']='failed';current['error']=repr(error)
                row.update(status='failed',error=repr(error));out.first_error=repr(error);break
    except Exception as error:out.first_error=repr(error)


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


def main(output,test_path,closure_path):
    lock_executor()
    out=Output(output)
    try:
        protocol,cache,snapshots,receipt,closure,native_rows=custody(test_path,closure_path,out.poll)
        gate=source_gate({role:cache[protocol['future_paths'][role]].decode() for role in ('pipeline','guard','fixture')})
        for name,data in snapshots.items():out.write('sources/'+name,data)
        out.write('provenance/interpreter.bin',cache[closure['interpreter']])
        pins=dict(interpreter=closure['interpreter'],fixture=str(out.root/'sources'/protocol['future_paths']['fixture']),
                  interpreter_sha256=closure['interpreter_sha256'],fixture_sha256=receipt['sources'][protocol['future_paths']['fixture']])
        out.write('custody.json',encoded(receipt));out.write('source_gate.json',encoded(gate));out.write('executor.json',encoded(pins))
        descriptors=[dict(slot=i,proposal=6000+i//4,initial=i%4,file=name,sha256=h) for i,(name,h) in enumerate(sorted(protocol['saved_requests'].items()))]
        run_pipeline(out,descriptors,cache.__getitem__,native_rows,pins)
    except Exception as error:out.first_error=repr(error)
    result=out.finish();print(json.dumps(result));return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3]))
