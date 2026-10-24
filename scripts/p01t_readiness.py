"""P01t transport only: hash-pinned saved streams to inert JSON requests."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from p01s_boundary import request_from_streams, strict_load, typed
from p01s_accounting import Ledger
ROOT = Path(__file__).resolve().parents[1]


def need(ok, why):
    if not ok:raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def rows():
    return [dict(slot=i, proposal=6000+i//4, initial=i%4, status='unstarted') for i in range(128)]


def paths(slot):
    return [f'artifacts/p01o-001/runs/{slot}/{lang}/stdout.bin' for lang in ('rust_generation','python_generation')]


def convert(streams, hashes, cell):
    need(all(len(b)<1048576 for b in streams), 'input stream cap')
    result=request_from_streams(streams, hashes, cell)
    data=encoded(result['request'])
    need(len(data)<524288, 'request cap')
    need(typed(strict_load(data))==typed(result['request']), 'request parse-back')
    return data, dict(input_sha256=hashes, typed_pair_equal=True,
        envelope_canonical_sha256=sha(encoded(result['envelope'])),
        environment_canonical_sha256=sha(encoded(result['envelope']['environment'])),
        request_sha256=sha(data), request_bytes=len(data))


class Output:
    def __init__(self, root, clock=time.monotonic):
        self.clock=clock;self.start=clock();self.ledger=Ledger(root)
        self.first_error=None;self.closeout_errors=[];self.rows=rows()
    def poll(self):self.ledger.budget(wall=self.clock()-self.start)
    def write(self,name,data,terminal=False,fail_after=None):
        if terminal:need(self.clock()-self.start<120,'terminal wall limit')
        else:self.poll()
        self.ledger.write(name,data,terminal=terminal,fail_after=fail_after)
    def finish(self):
        status='fail' if self.first_error else 'pass'
        try:
            self.write('manifest.json',encoded(dict(schema='p01t-manifest-v1',status=status,rows=self.rows,
                first_error=self.first_error,closeout_errors=self.closeout_errors,world_transitions=0,
                keyed_evaluations=0,scientific_status='untested',behavioral_outcomes=None)),terminal=True)
            self.write('checksums.json',encoded(self.ledger.files),terminal=True)
            complete=dict(status=status,first_error=self.first_error,closeout_errors=self.closeout_errors,
                checksums_sha256=self.ledger.files['checksums.json']['sha256'],
                counts_before_completion=dict(self.ledger.counts),count_scope='all_output_except_completion',
                wall_seconds=self.clock()-self.start,output_bytes=0,
                reconciliation='pending_independent_audit' if status=='pass' else 'incomplete')
            while True:
                data=encoded(complete);total=self.ledger.total+len(data)
                if complete['output_bytes']==total:break
                complete['output_bytes']=total
            self.write('completion.json',data,terminal=True)
        except Exception as error:
            self.closeout_errors.append(repr(error))
            status='fail'
        return dict(status=status,first_error=self.first_error,closeout_errors=self.closeout_errors,
                    terminal_receipt='written' if 'completion.json' in self.ledger.files and not self.closeout_errors else 'missing',
                    output_bytes=self.ledger.total,rows=self.rows)


def run_panel(out, cache, hashes, fail_after=None):
    for row in out.rows:
        slot=row['slot'];names=paths(slot)
        try:
            out.poll()
            data,details=convert([cache[n] for n in names],[hashes[n] for n in names],(slot,row['proposal'],row['initial']))
            name=f'requests/{slot:03}.json'
            out.write(name,data,fail_after=fail_after if slot==0 else None)
            row.update(details,status='complete',request_file=name)
        except Exception as error:
            row.update(status='failed',error=repr(error));out.first_error=repr(error);break


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


def prohibit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn')) or event in ('os.system','os.fork','os.posix_spawn'):
        raise RuntimeError('P01t forbids process creation')


def main(output,test_path):
    sys.addaudithook(prohibit)
    out=Output(output)
    try:
        cache,hashes,snapshots,receipt=custody(test_path,out.poll)
        for name,data in snapshots.items():out.write('sources/'+name,data)
        out.write('custody.json',encoded(receipt))
        run_panel(out,cache,hashes)
    except Exception as error:out.first_error=repr(error)
    result=out.finish();print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2]))
