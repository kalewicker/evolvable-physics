"""P01w invented descriptors, inert OS processes and independent receipt controls."""
import ast
import copy
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import p01w_guard as guard
import p01w_campaign as runner
import audit_p01w_receipts as receipts
import check_p01w_execution as execution
if __debug__:
    import p01w_cell as cell
    import audit_p01w_events as independent
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ['P01W_TEST_OUT']);OUT.mkdir(exist_ok=False)
P=json.loads((ROOT/'docs/p01w_protocol.json').read_bytes())
_COUNTER=0
def fresh(label):
    global _COUNTER
    _COUNTER+=1
    return OUT/(str(_COUNTER)+'-'+label)
def writer(label,p=None):return guard.Output(fresh(label),copy.deepcopy(p or P))
def rule(form,route='Structural'):
    node={'kind':1,'state':None}
    edge={'class':route,'kind':0,'ends':[0,1]}
    ops={0:[{'op':'SetState','node':0,'value':0}],
         4:[{'op':'CreateNode','account':0,'kind':2,'state':0},
            {'op':'CreateEdge','account':0,'kind':0,'ends':[0,1]},
            {'op':'Transfer','from':0,'to':1,'matter':1,'activation':1},{'op':'Burn','node':0,'amount':1}],
         3:[{'op':'Transfer','from':0,'to':1,'matter':1,'activation':1}],
         7:[{'op':'DeleteEdge','account':0,'kind':0,'ends':[0,1]},
            {'op':'DeleteNode','node':1,'recipient':0},{'op':'Burn','node':0,'amount':1}],
         6:[{'op':'DeleteEdge','account':0,'kind':0,'ends':[0,1]}]}
    return {'id':0,'nodes':[node]*(1 if form in (0,4) else 2),'edges':[] if form in (0,4) else [edge],
            'absent':[],'ops':ops[form]}


def node(m,a,kind=1):return {'kind':kind,'state':0,'matter':m,'activation':a}
def initial():return {'nodes':{'42':node(8,8)},'edges':{},'next_node':100}
def birth(before,donor):
    # Directly authored record, not a kernel operation or interpreter.
    after=copy.deepcopy(before);child=before['next_node'];after['next_node']+=1
    after['nodes'][str(donor)]['matter']-=3;after['nodes'][str(donor)]['activation']-=2
    after['nodes'][str(child)]=node(1,1,2)
    after['edges'][str(200+child)]={'class':'Structural','kind':0,'ends':[donor,child]}
    return after


def branch(form=7, extra=False):
    """Literal expected records, with arithmetic, not calls into any interpreter."""
    events=[];worlds=[initial()];worlds[0]['nodes']['42']['kind']=2
    def add(form,ids,after):
        events.append(dict(rule=rule(form),binding=ids,event=10+len(events),sample=len(worlds),before=worlds[-1],after=after))
        worlds.append(after)
    add(4,[42],birth(worlds[-1],42))
    for _ in range(2):
        a=copy.deepcopy(worlds[-1])
        for k in ('matter','activation'):a['nodes']['42'][k]-=1;a['nodes']['100'][k]+=1
        add(3,[42,100],a)
    if extra:
        a=copy.deepcopy(worlds[-1]);a['nodes']['42']['state']=1;rr=rule(0);rr['ops'][0]['value']=1
        add(0,[42],a);events[-1]['rule']=rr
    add(4,[100],birth(worlds[-1],100))
    a=copy.deepcopy(worlds[-1]);del a['edges']['301']
    if form==7:del a['nodes']['101'];a['nodes']['100']['matter']+=3
    else:a['nodes']['100']['matter']+=1
    add(form,[100,101],a)
    a=copy.deepcopy(worlds[-1]);old=a['nodes'].pop('100');del a['edges']['300']
    a['nodes']['42']['matter']+=old['matter']+2;a['nodes']['42']['activation']+=old['activation']-1
    add(7,[42,100],a)
    samples=[[dict(members=[int(n) for n in w['nodes']])] for w in worlds]
    detection={k:dict(samples=copy.deepcopy(samples)) for k in ('connected','interaction')}
    return events,worlds,detection


def receipt(obs,complete=True):
    counts={k:len(obs[k]) for k in ('births','recycling','visibility','additional_structural_funding',
        'descendant_construction','orphaning','visible_birth_recycle_ids','cleanup_events')}
    counts['ordered_branch']=obs['ordered_branch_count']
    return dict(independent_events_pass=True,prefix_observations=obs,prefix_counts=counts,
                full_horizon_counts=counts if complete else None,full_horizon_verified=complete,
                full_horizon_ap='not_supported' if complete else None)


@unittest.skipUnless(__debug__, "assert-enabled event oracle only; optimized rejection tested separately")
class ObservationControls(unittest.TestCase):
    def test_reused_body_same_kind_distinct_nodes_and_cleanup7(self):
        e,w,d=branch();obs=cell.observations(e,w,d)
        self.assertEqual(obs['ordered_branch_count'],1)
        b=obs['ordered_branch'][0]
        self.assertEqual(b['roles'],[42,100,101]);self.assertEqual(b['parent_net'],[0,-4])
        self.assertEqual(b['total_burns'],4)
        self.assertEqual(len(obs['additional_structural_funding']),2)
        self.assertEqual(obs['descendant_construction'][0]['donor_birth_event'],10)
        receipts.validate_observations(receipt(obs))
    def test_cleanup6_preserves_orphan_and_spends_activation(self):
        e,w,d=branch(6);obs=cell.observations(e,w,d)
        self.assertIn('101',w[-1]['nodes']);self.assertEqual(obs['ordered_branch'][0]['parent_net'],[-2,-4])
        self.assertEqual(obs['ordered_branch'][0]['total_burns'],3)
        self.assertEqual(obs['recycled_ids'],[100]);self.assertEqual(obs['orphaning'][0]['node'],101)
    def test_availability_and_initial_nodes_are_not_births(self):
        e,w,d=branch();self.assertEqual(cell.observations([],w[:1],{k:{'samples':[[]]} for k in d})['births'],[])
        self.assertNotIn(42,cell.observations(e,w,d)['attached_funded_birth_ids'])
    def test_birth_internal_transfer_not_additional_funding(self):
        e,w,d=branch();out=cell.observations(e[:1],w[:2],{k:{'samples':v['samples'][:2]} for k,v in d.items()})
        self.assertEqual(out['additional_structural_funding'],[])
    def test_birth_must_be_funded_attached_and_paid(self):
        for kind in ('unfunded','unattached','unpaid'):
            e,w,d=branch();x=e[0]
            if kind=='unfunded':x['after']['nodes']['100']['matter']=0
            elif kind=='unattached':x['after']['edges']={}
            else:x['after']['nodes']['42']['matter']+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):cell.observations(e,w,d)
    def test_visibility_needs_both_proposals_same_live_sample(self):
        e,w,d=branch();d['interaction']['samples']=[[] for _ in w]
        self.assertEqual(cell.observations(e,w,d)['visible_birth_ids'],[])
        e,w,d=branch()
        for k in d:d[k]['samples']=[[] for _ in w]
        d['connected']['samples'][1]=[dict(members=[100])];d['interaction']['samples'][2]=[dict(members=[100])]
        self.assertEqual(cell.observations(e,w,d)['visibility'],[])
    def test_funding_donor_and_same_node_cannot_be_pooled(self):
        e,w,d=branch();obs=cell.observations(e,w,d)
        altered=copy.deepcopy(obs);altered['additional_structural_funding'][0]['recipient']=101
        with self.assertRaises(ValueError):receipts.validate_observations(receipt(altered))
        altered=copy.deepcopy(obs);altered['descendant_construction'][0]['donor']=42
        with self.assertRaises(ValueError):receipts.validate_observations(receipt(altered))
    def test_wrong_edge_nonleaf_and_refund_rejected(self):
        for kind in ('direction','missing','nonleaf','refund'):
            e,w,d=branch();x=e[-2]
            if kind=='direction':x['before']['edges']['301']['ends'].reverse()
            elif kind=='missing':del x['before']['edges']['301']
            elif kind=='nonleaf':x['after']['edges']['777']={'class':'Structural','kind':0,'ends':[101,42]}
            else:x['after']['nodes']['100']['activation']+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):cell.observations(e,w,d)
    def test_order_and_unrelated_intervening_events(self):
        e,w,d=branch(extra=True);o=cell.observations(e,w,d)
        self.assertEqual(o['ordered_branch'][0]['intervening_events'],[13])
        e[1]['event']=e[0]['event']
        with self.assertRaises(AssertionError):cell.observations(e,w,d)
    def test_censored_and_disagreement_keep_null_or_inconclusive(self):
        o=cell.observations(*branch());r=receipt(o,False);receipts.validate_observations(r)
        r['full_horizon_counts']=r['prefix_counts']
        with self.assertRaises(ValueError):receipts.validate_observations(r)
        r=receipt(o);r['full_horizon_ap']='inconclusive';receipts.validate_observations(r)
        self.assertEqual(r['full_horizon_ap'],'inconclusive')
    def test_independent_oracle_and_receipt_mutations(self):
        e,w,d=branch();o=cell.observations(e,w,d)
        with patch.object(cell,'branch_records',return_value=[]):
            with self.assertRaisesRegex(AssertionError,'independent'):cell.observations(e,w,d)
        for field in ('events','roles','creation_edges'):
            a=copy.deepcopy(o);a['ordered_branch'][0][field][0]+=1
            with self.subTest(field=field),self.assertRaises((ValueError,KeyError)):receipts.validate_observations(receipt(a))
        a=copy.deepcopy(o);a['cleanup_events'][0]['returned_matter']+=1
        with self.assertRaises(ValueError):receipts.validate_observations(receipt(a))



def invented_inputs():
    cache={};descriptors=[];native=[]
    for slot in range(128):
        row=dict(slot=slot,proposal=6000+slot//4,initial=slot%4)
        # Intentionally non-native descriptor. It cannot be executed as a world.
        environment=dict(native=dict(rules=[dict(id=i,authored_rule=i,law=slot//4) for i in range(8)],world=dict(authored=True,slot=slot)))
        envelope=dict(schema='p01o-generated-environment-v1',**row,environment=environment)
        request=dict(schema='p01-worker-request-v1',initial=environment,epochs=128,max_events=16384,max_trace_bytes=4194304)
        raw=guard.encoded(request);name=f'requests/{slot}.json';streams=[f'streams/{slot}/{lang}' for lang in ('rust','python')]
        cache[name]=raw
        for n in streams:cache[n]=guard.encoded(envelope)
        descriptors.append(dict(**row,file=name,sha256=guard.sha(raw),streams=streams,stream_hashes=[guard.sha(cache[n]) for n in streams]))
        native.append(dict(**row,status='complete',native_accepted=True,input_sha256=guard.sha(raw)))
    return cache,descriptors,native

def mock_pins():
    return dict(worker='/invented/worker',reporter='/invented/reporter',python='/invented/python',cell='/invented/cell',hashes={n:'0'*64 for n in ['/invented/worker','/invented/reporter','/invented/python','/invented/cell']})

def mock_stage(failure=None,calls=None,censored_slot=None):
    def invoke(out,role,argv,name,identities):
        slot=int(name.split('/')[1]);base=out.root/f'runs/{slot:03}';raw=(base/'request.json').read_bytes();identity=json.loads((base/'identity.json').read_bytes())
        if calls is not None:calls.append((slot,role))
        censored=slot==censored_slot;epochs=127 if censored else 128
        if role=='native':
            stdout=b''.join(guard.encoded(dict(authored_frame=i))+b'\n' for i in range(epochs))
            stderr=guard.encoded(dict(schema='p01-worker-result-v1',status='trace_budget_exceeded' if censored else 'complete',epochs=epochs,events=0,native_events=0,applicable_candidates=0,trace_bytes=len(stdout),step_ns=0,serialize_ns=0,write_ns=0,final_state=guard.parse(raw)['initial']))+b'\n'
        elif role=='rust_report':
            worker=guard.parse((base/'worker.json').read_bytes())
            stdout=guard.encoded(dict(schema='p01-detector-report-v1',request_digest=guard.sha(guard.encoded(guard.parse(raw))),worker_result_digest=guard.sha(guard.encoded(worker)),trace_bytes=worker['trace_bytes'],observed_epochs=epochs,requested_epochs=128,coverage='censored_prefix' if censored else 'complete',worker_status=worker['status'],maintenance_status='not_assessed',scientific_status='untested',full_horizon_ap=None if censored else 'inconclusive',prefix_detection={k:dict(samples=[[]]*129) for k in ('connected','interaction')}))+b'\n';stderr=b''
        else:
            obs={k:[] for k in ['births','recycling','visibility','additional_structural_funding','descendant_construction','orphaning','visible_birth_recycle_ids','cleanup_events','ordered_branch','attached_funded_birth_ids','visible_birth_ids','recycled_ids']};obs['ordered_branch_count']=0
            proof=receipt(obs,not censored);proof.update(schema='p01w-cell-audit-v1',**identity,status='censored' if censored else 'complete',worker_status='trace_budget_exceeded' if censored else 'complete',observed_epochs=epochs,observed_events=0,
                attached_funded_birth_ids=[],visible_birth_ids=[],recycled_ids=[],full_horizon_ap=None if censored else 'inconclusive',scientific_status='untested',
                inputs_sha256={k:guard.sha(path.read_bytes()) for k,path in [('request',base/'request.json'),('trace',base/'trace.jsonl'),('summary',base/'worker.json'),('report',base/'report.json')]})
            stdout=guard.encoded(proof)+b'\n';stderr=b''
        fail=failure==(slot,role)
        stats=dict(role=role,status='failed' if fail else 'complete',launched=True,argv=argv,identities=identities,returncode=1 if fail else 0,
            stdout_bytes=len(stdout),stderr_bytes=len(stderr),stdout_observed_bytes=len(stdout),stderr_observed_bytes=len(stderr),
            stdout_file=name+'/stdout.bin',stderr_file=name+'/stderr.bin',wall_seconds=0,child_cpu_seconds=0,
            peak_sampled_rss_bytes=1,peak_rss_bytes=1,pre_input_sample=True,rss_samples=1,polls=1,kills=0,error='invented failure' if fail else None)
        out.counts['launches']+=1;out.counts['reaped']+=1
        out.write(stats['stdout_file'],stdout);out.write(stats['stderr_file'],stderr);out.write(name+'/guard.json',guard.encoded(stats))
        return stats,stdout,stderr
    return invoke

def run_invented(label,failure=None,mutation=None,censored_slot=None):
    out=writer(label);cache,desc,native=invented_inputs();calls=[]
    if mutation:mutation(cache,desc,native)
    out.write('protocol.json',guard.encoded(P))
    runner.pipeline(out,desc,cache.__getitem__,native,mock_pins(),invoke=mock_stage(failure,calls,censored_slot))
    result=out.finish(runner.summary(out.rows,P,out.first_error is None),dict(invented=True))
    return out,result,calls

class AdmissionAndGuards(unittest.TestCase):
    def test_strict_parser_and_optimized_rejection(self):
        for raw in (b'{"x":0,"x":1}',b'{"x":NaN}',b'{"x":1e999}',b'{'):
            with self.assertRaises((ValueError,json.JSONDecodeError)):guard.parse(raw)
        completed=subprocess.run([sys.executable,'-B','-O','-c',"import sys;sys.path.insert(0,'scripts');import p01w_cell"],cwd=ROOT,capture_output=True)
        self.assertNotEqual(completed.returncode,0);self.assertIn(b'requires assertions',completed.stderr)
        (OUT/'optimized-rejection.stderr').write_bytes(completed.stderr)
    @unittest.skipUnless(__debug__,'assert-enabled loader; optimized adapter is rejected')
    def test_real_loader_and_typed_paired_envelopes(self):
        cache,descs,prior=invented_inputs()
        for slot in range(128):
            d=descs[slot];r,h=cell.admit_request(cache[d['file']],d['sha256'],[cache[n] for n in d['streams']],d['stream_hashes'],d,prior[slot])
            self.assertIn('native',r['initial']);self.assertNotIn('environment',r['initial']);self.assertEqual(len(h),64)
        d=descs[0];raw=cache[d['file']];streams=[cache[n] for n in d['streams']]
        for mode in ('hash','typed','wrapper','epochs','slot','prior','one_stream'):
            rr=guard.parse(raw);ss=list(streams);row=copy.deepcopy(d);pp=copy.deepcopy(prior[0]);h=d['sha256']
            if mode=='hash':h='f'*64
            if mode=='typed':v=guard.parse(ss[1]);v['environment']['native']['world']['slot']=False;ss[1]=guard.encoded(v)
            if mode=='wrapper':rr['initial']=guard.parse(ss[0])
            if mode=='epochs':rr['epochs']=0
            if mode=='slot':row['slot']=False
            if mode=='prior':pp['native_accepted']=False
            if mode=='one_stream':ss.pop()
            altered=raw if mode in ('hash','typed','slot','prior','one_stream') else guard.encoded(rr)
            if mode in ('wrapper','epochs'):h=guard.sha(altered)
            with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError)):
                cell.admit_request(altered,h,ss,[guard.sha(s) for s in ss],row,pp)
    def test_all_stage_and_aggregate_boundaries(self):
        for role in guard.ROLES:
            s=P['per_process'][role];c=P['production_contracts'][role]
            for key in ('wall','stdout','stderr','rss'):
                for delta,want in [(-1,True),(0,True),(1,False)]:
                    values=dict(wall=0,stdout=0,stderr=0,rss=0)
                    values[key]={'wall':s['wall_seconds'],'stdout':c['stdout_cap_bytes'],'stderr':c['stderr_cap_bytes'],'rss':s['sampled_rss_bytes']}[key]+delta
                    self.assertEqual(guard.stage_fits(P,role,**dict(wall=values['wall'],stdout=values['stdout'],stderr=values['stderr'],resident=values['rss'])),want)
            for k,limit in [('wall_seconds',1200-s['wall_seconds']-5),('total_process_cpu_seconds',600-2*s['wall_seconds']-5),('artifact_bytes',2147483648-s['output_bytes']-67108864)]:
                for delta,want in [(-1,True),(0,True),(1,False)]:
                    u=dict(wall_seconds=0,total_process_cpu_seconds=0,artifact_bytes=0);u[k]=limit+delta
                    self.assertEqual(guard.fits(P,u,role),want)
    def test_live_cpu_bound_and_partial_write_ledger(self):
        clock=[0.0];cpu=[0.0];out=guard.Output(fresh('cpu'),P,clock=lambda:clock[0],cpu_clock=lambda:cpu[0]);out.cores=4
        out.live_started=0;clock[0]=2;cpu[0]=1
        self.assertEqual(out.usage()['total_process_cpu_seconds'],9)
        out.live_started=None;cpu[0]=3;self.assertEqual(out.usage()['total_process_cpu_seconds'],3)
        real=os.write;calls=[];base=out.total
        def partial(fd,data):
            n=real(fd,data[:3]);calls.append(n);return n
        with patch.object(os,'write',side_effect=partial),patch.object(Path,'rglob',side_effect=AssertionError('scan')):
            out.write('a',b'abcdefgh');out.write('a',b'ij',append=True);out.poll()
        self.assertEqual(out.total-base,10);self.assertEqual(sum(calls),10);self.assertEqual((out.root/'a').read_bytes(),b'abcdefghij')
        def broken(fd,data):
            if data.startswith(b'xyz'):return real(fd,data[:2])
            raise OSError('invented partial failure')
        base=out.total
        with patch.object(os,'write',side_effect=broken),self.assertRaises(OSError):out.write('partial',b'xyz123')
        self.assertEqual(out.total-base,2);self.assertEqual((out.root/'partial').read_bytes(),b'xy')
        with self.assertRaises(ValueError):out.write('a',b'overwrite')
    def test_inert_real_spawn_caps_partial_streams_and_reaping(self):
        records=[]
        for kind in ('pass','nonzero','wall','stdout','stderr','rss','rss_missing'):
            p=copy.deepcopy(P)
            if kind=='wall':p['per_process']['native']['wall_seconds']=.1
            if kind in ('stdout','stderr'):p['production_contracts']['native'][kind+'_cap_bytes']=8
            out=writer('process-'+kind,p);code="import sys,time;sys.stdout.write('ok');sys.stdout.flush();sys.stderr.write('err');sys.stderr.flush();"
            if kind=='nonzero':code+='sys.exit(4)'
            if kind=='wall':code+='time.sleep(2)'
            if kind=='stdout':code+="sys.stdout.write('x'*32)"
            if kind=='stderr':code+="sys.stderr.write('x'*32)"
            sampler=(lambda _:p['per_process']['native']['sampled_rss_bytes']+1) if kind=='rss' else (lambda _:None) if kind=='rss_missing' else guard.rss
            binary=str(Path(sys.executable).resolve());pins={binary:guard.sha(Path(binary).read_bytes())}
            stats,stdout,stderr=guard.run_stage(out,'native',[binary,'-I','-B','-c',code],'fixture',pins,sampler=sampler)
            records.append(dict(kind=kind,stats=stats))
            self.assertEqual(stats['status']=='complete',kind=='pass',stats)
            self.assertIsNotNone(stats['returncode']);self.assertEqual(out.counts['launches'],out.counts['reaped']);self.assertIsNone(out.live_started)
            if kind=='pass':self.assertTrue(stats['pre_input_sample']);self.assertEqual(stdout,b'ok');self.assertEqual(stderr,b'err')
            if kind=='wall':self.assertEqual(stdout,b'ok');self.assertGreater(stats['kills'],0)
        (OUT/'process_results.json').write_bytes(guard.encoded(records))
    def test_executor_pin_and_terminal_failure(self):
        out=writer('substitution');binary=str(Path(sys.executable).resolve())
        with self.assertRaises(ValueError):guard.run_stage(out,'native',[binary,'-c','pass'],'fixture',{binary:'0'*64})
        self.assertEqual(out.counts['launches'],0)
        out.first_error='first failure';real=out.write
        def bad(name,data,**kw):
            if name=='checksums.json':raise OSError('terminal failure')
            return real(name,data,**kw)
        with patch.object(out,'write',side_effect=bad):result=out.finish(runner.summary(out.rows,P,False),{})
        self.assertEqual(result['first_error'],'first failure');self.assertTrue(result['closeout_errors']);self.assertEqual(result['terminal_receipt'],'missing_or_invalid')
        with self.assertRaises(FileExistsError):guard.Output(out.root,P)
        out=writer('unknown');out.first_error='unknown accounting';out.mark_unknown(12)
        # Unknown byte accounting is never accepted as exact or as a successful run.
        result=out.finish(runner.summary(out.rows,P,False),{})
        self.assertEqual(result['status'],'fail')
    def test_source_execution_boundary(self):
        for name in ('audit_p01w_events.py','audit_p01w_receipts.py'):
            tree=ast.parse((ROOT/'scripts'/name).read_text())
            imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|{x.name for n in ast.walk(tree) if isinstance(n,ast.Import) for x in n.names}
            self.assertFalse(any(n and n.startswith(('p01','audit','pilot')) for n in imports));self.assertNotIn('subprocess',imports)
        src=(ROOT/'scripts/p01w_campaign.py').read_text();self.assertNotIn('p01q_cell',src);self.assertNotIn('saved_initial(',src)
        self.assertFalse((ROOT/'artifacts/p01w-001').exists())
        for name in ('audit','audit_single_pass','pilot_reporting'):
            self.assertNotIn(name,sys.modules,'tests must not import replay runtime')

@unittest.skipUnless(__debug__,'production pipeline requires assertions')
class PipelineControls(unittest.TestCase):
    def test_full_128_production_contract_pipeline_and_independent_audit(self):
        out,result,calls=run_invented('full')
        self.assertEqual(result['status'],'pass');self.assertEqual(len(calls),384)
        self.assertTrue(all(r['status']=='complete' for r in out.rows));proof=receipts.verify(out.root,require_closure=False)
        self.assertTrue(proof['engineering_gate_pass']);self.assertFalse(proof['mechanism_gate_pass']);self.assertEqual(proof['verified_cell_receipts'],128)
        (OUT/'full_pipeline.json').write_bytes(guard.encoded(dict(result=result,audit=proof,calls=len(calls),bundle=str(out.root))))
    def test_registered_failure_matrix_and_no_retries(self):
        results=[]
        for slot,role in [(0,'native'),(0,'rust_report'),(0,'python_audit'),(63,'rust_report'),(127,'python_audit')]:
            out,result,calls=run_invented(f'failure-{slot}-{role}',(slot,role))
            self.assertEqual(result['status'],'fail');self.assertEqual(len(calls),slot*3+guard.ROLES.index(role)+1)
            self.assertEqual(out.rows[slot]['status'],'failed');self.assertTrue(all(r['status']=='unstarted' for r in out.rows[slot+1:]))
            proof=receipts.verify(out.root,require_closure=False);self.assertFalse(proof['engineering_gate_pass'])
            results.append(dict(slot=slot,role=role,calls=len(calls),audit=proof))
        def corrupt(cache,desc,native):desc[0]['sha256']='0'*64
        out,result,calls=run_invented('bad-input',mutation=corrupt)
        self.assertFalse(calls);self.assertEqual(out.rows[0]['status'],'failed');self.assertEqual(sum(r['status']=='unstarted' for r in out.rows),127)
        (OUT/'failure_matrix.json').write_bytes(guard.encoded(results))
    def test_gate_duplicates_same_node_and_no_pooling(self):
        out,result,calls=run_invented('gates');rows=copy.deepcopy(out.rows)
        for i in (0,4):rows[i]['observation'].update(attached_funded_birth_ids=[8],visible_birth_ids=[8],recycled_ids=[8])
        self.assertTrue(runner.summary(rows,P,True)['continuation_gate_pass']);self.assertEqual(receipts.gates(rows)[1:],(2,2))
        for r in rows:r['law_digest']='a'*64
        self.assertFalse(runner.summary(rows,P,True)['mechanism_gate_pass'])
        rows=copy.deepcopy(out.rows);rows[0]['observation'].update(attached_funded_birth_ids=[8],visible_birth_ids=[8]);rows[1]['observation'].update(attached_funded_birth_ids=[8],recycled_ids=[8])
        self.assertEqual(runner.summary(rows,P,True)['distinct_tables_with_same_trajectory_visible_birth_recycle_loop'],0)
        empty=guard.rows();self.assertIsNone(runner.summary(empty,P,False)['mechanism_gate_pass'])
        def changed_ordered_id(cache,descs,native):
            d=descs[1];envelope=guard.parse(cache[d['streams'][0]])
            envelope['environment']['native']['rules'][0]['id']=999
            for name in d['streams']:cache[name]=guard.encoded(envelope)
            d['stream_hashes']=[guard.sha(cache[name]) for name in d['streams']]
            request=guard.parse(cache[d['file']]);request['initial']=envelope['environment'];cache[d['file']]=guard.encoded(request)
            d['sha256']=guard.sha(cache[d['file']]);native[1]['input_sha256']=d['sha256']
        altered,result,calls=run_invented('ordered-table-mismatch',mutation=changed_ordered_id)
        self.assertEqual(len(calls),3);self.assertEqual(altered.rows[1]['status'],'failed')
        self.assertIn('ordered table',altered.first_error)

    def test_independent_inventory_mutations(self):
        out,result,calls=run_invented('audit-base');receipts.verify(out.root,require_closure=False)
        for mode in ('extra','bytes','missing','seal_count','false_gate','row_order','stage_order','guard','identity','full_horizon','counter','cost_distribution','missing_cost_role','per_run_cost'):
            dest=fresh('mutation-'+mode);shutil.copytree(out.root,dest)
            if mode=='extra':(dest/'extra').write_bytes(b'unlisted')
            elif mode=='bytes':(dest/'runs/000/trace.jsonl').write_bytes(b'tampered')
            elif mode=='missing':(dest/'runs/000/report.json').unlink()
            elif mode=='seal_count':
                s=json.loads((dest/'seal.json').read_bytes());s['known_path_bytes']+=1;(dest/'seal.json').write_bytes(guard.encoded(s))
            else:
                # Re-seal invented mutations to exercise semantics beyond hash rejection.
                m=json.loads((dest/'manifest.json').read_bytes())
                if mode=='false_gate':m['assessment']['mechanism_gate_pass']=True
                if mode=='row_order':m['rows'][0],m['rows'][1]=m['rows'][1],m['rows'][0]
                if mode=='stage_order':m['rows'][0]['stages'].reverse()
                if mode=='guard':m['rows'][0]['stages'][0]['guard']['wall_seconds']=11
                if mode=='identity':m['rows'][0]['law_digest']='f'*64
                if mode=='full_horizon':m['rows'][0]['observation']['observed_epochs']=127
                if mode=='cost_distribution':m['assessment']['stage_costs']['native']['wall_seconds']['maximum']=1
                if mode=='missing_cost_role':del m['assessment']['stage_costs']['python_audit']
                if mode=='per_run_cost':m['assessment']['per_run_stage_wall_seconds']['maximum']=1
                (dest/'manifest.json').write_bytes(guard.encoded(m));inv=json.loads((dest/'checksums.json').read_bytes())
                inv['manifest.json']=dict(size=(dest/'manifest.json').stat().st_size,sha256=guard.sha((dest/'manifest.json').read_bytes()));(dest/'checksums.json').write_bytes(guard.encoded(inv))
                s=json.loads((dest/'seal.json').read_bytes());s['manifest_sha256']=inv['manifest.json']['sha256'];s['checksums_sha256']=guard.sha((dest/'checksums.json').read_bytes())
                s['counts_before_seal']['write_bytes']=sum(x['size'] for x in inv.values())+(dest/'checksums.json').stat().st_size
                if mode=='counter':s['counts_before_seal']['launches']+=1
                base=sum(x['size'] for x in inv.values())+(dest/'checksums.json').stat().st_size
                while True:
                    raw=guard.encoded(s);total=base+len(raw)
                    if s['known_path_bytes']==total:break
                    s.update(known_path_bytes=total,output_bytes=total,usage_upper_bound_bytes=total)
                (dest/'seal.json').write_bytes(raw)
            with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError,FileNotFoundError)):receipts.verify(dest,require_closure=False)



class AdditionalControls(unittest.TestCase):
    def test_suspended_spawn_prevents_early_input_and_group_kill(self):
        marker=fresh('pre-input-marker');exe=str(Path(sys.executable).resolve())
        code="from pathlib import Path;Path("+repr(str(marker.resolve()))+").write_text('started')"
        pid,fds=guard.spawn_suspended([exe,'-I','-B','-c',code])
        try:
            self.assertFalse(marker.exists());self.assertGreater(guard.rss(pid),0)
            os.kill(pid,signal.SIGCONT);got,status,used=os.wait4(pid,0)
            self.assertEqual(os.waitstatus_to_exitcode(status),0);self.assertEqual(marker.read_text(),'started')
        finally:
            for fd in fds:os.close(fd)
        p=copy.deepcopy(P);p['per_process']['native']['wall_seconds']=.15
        out=writer('group',p)
        code="import os,sys,time;child=os.fork();print(child,flush=True);time.sleep(2)"
        stats,stdout,stderr=guard.run_stage(out,'native',[exe,'-I','-B','-c',code],'group',{exe:guard.sha(Path(exe).read_bytes())})
        self.assertEqual(stats['status'],'failed');self.assertEqual(stats['kills'],1)
        self.assertGreater(out.cpu_extra_upper,0);self.assertIn(b'0',stdout)
    def test_unknown_bytes_and_no_terminal_scan(self):
        out=writer('unknown-seal');out.first_error='partial unknown';out.mark_unknown(17)
        with patch.object(Path,'rglob',side_effect=AssertionError('terminal scan')):
            result=out.finish(runner.summary(out.rows,P,False),{})
        self.assertEqual(result['terminal_receipt'],'written');seal=json.loads((out.root/'seal.json').read_bytes())
        self.assertIsNone(seal['output_bytes']);self.assertEqual(seal['usage_upper_bound_bytes'],seal['known_path_bytes']+17)
    def test_capability_failure_precedes_attempt_creation(self):
        output=ROOT/'artifacts/p01w-001'
        with patch.object(execution,'review',return_value={}),patch.object(execution,'publication_check'),patch.object(runner,'probe',side_effect=ValueError('invented capability failure')),patch.object(runner,'Output') as create:
            with self.assertRaises(ValueError):runner.main(str(output))
            create.assert_not_called()
        self.assertFalse(output.exists())
    @unittest.skipUnless(__debug__,'assert-enabled cell adapter')
    def test_production_receipt_rejections_and_replay_wiring(self):
        out,result,calls=run_invented('contract-wiring');base=out.root/'runs/000';row=out.rows[0]
        raw=(base/'request.json').read_bytes();worker=guard.parse((base/'worker.json').read_bytes());report=guard.parse((base/'report.json').read_bytes())
        prior=dict(worker=worker,worker_raw=(base/'worker.json').read_bytes(),trace_raw=(base/'trace.jsonl').read_bytes(),report=report,report_raw=(base/'report.json').read_bytes())
        for role,file in [('native','worker.json'),('rust_report','report.json'),('python_audit','python_audit/stdout.bin')]:
            original=guard.parse((base/file).read_bytes())
            for mode in ('schema','digest','inert','partial','duplicate'):
                bad=copy.deepcopy(original)
                if mode=='schema':bad['schema']='p01v-inert-stage-receipt-v1'
                if mode=='digest':
                    if role=='native':bad['trace_bytes']+=1
                    elif role=='rust_report':bad['worker_result_digest']='0'*64
                    else:bad['inputs_sha256']['trace']='0'*64
                if mode=='inert':bad['inert']=True
                payload=guard.encoded(bad)+b'\n'
                if mode=='partial':payload=payload[:-1]
                if mode=='duplicate':payload=b'{"schema":"x","schema":"y"}\n'
                stdout,stderr=(prior['trace_raw'],payload) if role=='native' else (payload,b'')
                with self.subTest(role=role,mode=mode),self.assertRaises((ValueError,KeyError)):
                    runner.check_stage(role,stdout,stderr,raw,prior,row)
        # Spy only on inert replacements: no original replay module is imported.
        from types import SimpleNamespace
        calls=[]
        def replay(label):
            def run(request,directory,actual_report):
                self.assertEqual(request,guard.parse(raw));self.assertEqual(directory,base);self.assertEqual(actual_report,report)
                calls.append(label);return 'inconclusive'
            return run
        obs=guard.parse((base/'python_audit/stdout.bin').read_bytes())['prefix_observations']
        with patch.dict(sys.modules,{'audit':SimpleNamespace(),'pilot_reporting':SimpleNamespace(verify=replay('original')),'audit_single_pass':SimpleNamespace(verify=replay('single_pass'))}),patch.object(execution,'check_cell_admission'),patch.object(cell,'extract',return_value=obs):
            proof=cell.verify(base/'request.json',base)
        self.assertEqual(calls,['original','single_pass']);self.assertEqual(proof['inputs_sha256']['request'],guard.sha(raw))
        self.assertNotIn('pilot_reporting',sys.modules)


@unittest.skipUnless(__debug__,'assert-enabled production adapter')
class CensoredControls(unittest.TestCase):
    def test_verified_prefix_stops_without_fabricated_full_horizon(self):
        out,result,calls=run_invented('censored',censored_slot=0)
        self.assertEqual(len(calls),3);self.assertEqual(out.rows[0]['status'],'censored')
        self.assertTrue(all(r['status']=='unstarted' for r in out.rows[1:]))
        self.assertIsNone(out.rows[0]['observation']['full_horizon_ap']);self.assertIsNone(out.rows[0]['observation']['full_horizon_counts'])
        proof=receipts.verify(out.root,require_closure=False)
        self.assertFalse(proof['engineering_gate_pass']);self.assertIsNone(proof['mechanism_gate_pass'])


@unittest.skipUnless(__debug__,'assert-enabled production adapter')
class CompleteClosureAudit(unittest.TestCase):
    def test_all128_with_snapshot_admission_and_executor_bindings(self):
        cache,descs,native=invented_inputs();protocol=copy.deepcopy(P)
        sources={'scripts/p01w_cell.py':b'# inert placeholder, never imported',
                 'target/release/pilot-worker':b'inert worker descriptor',
                 'target/release/pilot-report':b'inert report descriptor','prior.json':b'{}'}
        protocol['request_bundle']='invented'
        protocol['saved_requests']={f'invented/requests/{i:03}.json':d['sha256'] for i,d in enumerate(descs)}
        for i,d in enumerate(descs):
            sources[f'invented/requests/{i:03}.json']=cache[d['file']]
            for name in d['streams']:sources[name]=cache[name]
        oldmanifest=b'{"invented":true}';oldinv=guard.encoded({'manifest.json':guard.sha(oldmanifest)})
        oldseal=guard.encoded(dict(manifest_sha256=guard.sha(oldmanifest),checksums_sha256=guard.sha(oldinv)))
        sources.update({'invented-old/manifest.json':oldmanifest,'invented-old/checksums.json':oldinv,'invented-old/seal.json':oldseal})
        protocol['source_bundles']={'invented-old':guard.sha(oldseal)}
        protocol['prerequisite_receipts']={'prior.json':guard.sha(sources['prior.json'])}
        protocol['production_binaries']={n:guard.sha(raw) for n,raw in sources.items() if n.startswith('target/')}
        sources['docs/p01w_protocol.json']=guard.encoded(protocol)
        reg=dict(files={n:guard.sha(raw) for n,raw in sources.items()},inputs={},prior_public_receipts={})
        sources['docs/p01w_registration_freeze.json']=guard.encoded(reg)
        deps={'/invented/python':b'inert interpreter descriptor','/invented/runtime.py':b'# inert runtime'}
        freeze=dict(files={n:guard.sha(raw) for n,raw in sources.items()},tools={'/invented/python':guard.sha(deps['/invented/python'])},interpreter='/invented/python',dependencies={'/invented/runtime.py':guard.sha(deps['/invented/runtime.py'])})
        sources['docs/p01w_execution_freeze.json']=guard.encoded(freeze)
        admission=dict(schema='p01w-execution-admission-v1',world_execution_admitted=True,
            **{key+'_sha256':guard.sha(sources[f'docs/p01w_{key}.json']) for key in ('protocol','registration_freeze','execution_freeze')})
        sources['docs/p01w_execution_admission.json']=guard.encoded(admission)
        out=writer('complete-closure',protocol)
        for name,raw in sources.items():out.write('source/'+name,raw)
        depinv={}
        for name,raw in deps.items():
            file='dependencies/'+guard.sha(name.encode());out.write(file,raw);depinv[name]=dict(file=file,sha256=guard.sha(raw))
        out.write('dependency_inventory.json',guard.encoded(depinv))
        pins={key:str(out.root/'source'/file) for key,file in [('worker','target/release/pilot-worker'),('reporter','target/release/pilot-report'),('cell','scripts/p01w_cell.py')]}
        pins['python']='/invented/python';pins['hashes']={pins[key]:guard.sha(sources[file]) for key,file in [('worker','target/release/pilot-worker'),('reporter','target/release/pilot-report'),('cell','scripts/p01w_cell.py')]};pins['hashes'][pins['python']]=guard.sha(deps[pins['python']])
        runner.pipeline(out,descs,cache.__getitem__,native,pins,invoke=mock_stage())
        provenance={key+'_sha256':guard.sha(sources[f'docs/p01w_{key}.json']) for key in ('protocol','execution_freeze','execution_admission')}
        result=out.finish(runner.summary(out.rows,protocol,out.first_error is None),dict(provenance,invented=True))
        self.assertEqual(result['status'],'pass');proof=receipts.verify(out.root)
        self.assertEqual(proof['verified_cell_receipts'],128);self.assertEqual(proof['guarded_stages'],384)
        (OUT/'complete_closure_audit.json').write_bytes(guard.encoded(dict(result=result,audit=proof,bundle=str(out.root))))

if __name__=='__main__':unittest.main()