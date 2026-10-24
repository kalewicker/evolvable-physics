"""P01v authored controls; production input loader and real inert subprocesses."""
import ast
import copy
import json
import os
import signal
import stat
import subprocess
import sys
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import p01v_pipeline as pipeline
import p01v_guard as guard
import audit_p01v as audit


def request(slot):
    return dict(schema='p01-worker-request-v1',epochs=128,max_events=16384,max_trace_bytes=4194304,
                initial=dict(authored_inert_fixture=True,slot=slot,metadata=[False,0,1.0,'é']))


def packet():
    protocol=json.loads((pipeline.ROOT/'docs/p01v_protocol.json').read_bytes())
    cases=[]
    expansions={
        'first_and_last_identity':['first_identity','last_identity'],
        'relative_and_absolute_output_paths':['relative_path','absolute_path'],
        'wrong_role_or_cell_rejected':['wrong_role','wrong_slot','wrong_proposal','wrong_initial'],
        'missing_or_unknown_fields':['missing_field','unknown_field'],
        'wall_below_equal_above':['stage_wall_below','stage_wall_equal','stage_wall_above'],
        'output_below_equal_above':['stage_output_below','stage_output_equal','stage_output_above'],
        'rss_below_equal_above_injected_sampler':['rss_below','rss_equal','rss_above'],
        'validator_or_reporter_command_rejected':['validator_command','reporter_command'],
        'fixture_or_interpreter_substitution_rejected':['fixture_substitution','interpreter_substitution'],
        'wall_reserve_below_equal_above':['aggregate_wall_below','aggregate_wall_equal','aggregate_wall_above'],
        'byte_reserve_below_equal_above':['aggregate_bytes_below','aggregate_bytes_equal','aggregate_bytes_above'],
        'first_error_and_closeout_error_distinct':['first_error_preserved','closeout_error_separate'],
        'missing_duplicate_extra_reordered_rows':['missing_row','duplicate_row','extra_row','reordered_rows'],
        'missing_duplicate_extra_reordered_stages':['missing_stage','duplicate_stage','extra_stage','reordered_stages'],
        'changed_input_or_prior_report_identity':['changed_input','changed_prior_identity'],
        'changed_stdout_or_chained_digest':['changed_stdout','changed_chain'],
        'changed_stage_status_or_guard_counters':['changed_status','changed_counter'],
        'inventory_membership_hash_or_total_changed':['unlisted_file','missing_file','changed_hash','changed_total'],
    }
    for family,names in protocol['controls'].items():
        for name in names:
            for case in expansions.get(name,[name]):cases.append(dict(family=family,registered_name=name,subcase=case,expected='pass_registered_invariant_or_reject_injected_fault'))
    failures=[dict(label='before_cell0',cell=None,role=None,invocations=0),
        dict(label='bad_hash_cell0',cell=0,role=None,invocations=0)]
    for cell,role in [(0,'native_stub'),(0,'report_stub'),(0,'audit_stub'),(63,'report_stub'),(127,'audit_stub')]:
        failures.append(dict(label=f'{role}_failure_cell{cell}',cell=cell,role=role,invocations=cell*3+guard.ROLES.index(role)+1))
    return dict(schema='p01v-authored-controls-v1',registered=protocol['controls'],cases=cases,failure_scenarios=failures,
                expected_complete_cells=128,expected_complete_stages=384,request_template=request(0))


class Plumbing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['P01V_TEST_OUT']);cls.root.mkdir(parents=True,exist_ok=False)
        cls.packet=packet();(cls.root/'packet.json').write_bytes(guard.encoded(cls.packet))
        cls.descriptors=[];cls.native=[];directory=cls.root/'authored_inputs';directory.mkdir()
        for slot in range(128):
            file=directory/f'{slot:03}.json';data=guard.encoded(request(slot));file.write_bytes(data);h=guard.sha(data)
            cls.descriptors.append(dict(slot=slot,proposal=6000+slot//4,initial=slot%4,file=str(file),sha256=h))
            cls.native.append(dict(slot=slot,proposal=6000+slot//4,initial=slot%4,status='complete',native_accepted=True,input_sha256=h,
                                   authored_native_receipt_fixture=True))
        (cls.root/'input_manifest.json').write_bytes(guard.encoded(dict(descriptors=cls.descriptors,prior_native=cls.native)))
        fixture=(pipeline.ROOT/'scripts/p01v_fixture.py').absolute();interpreter=Path(sys.executable).resolve()
        cls.pins=dict(interpreter=str(interpreter),fixture=str(fixture),interpreter_sha256=guard.sha(interpreter.read_bytes()),fixture_sha256=guard.sha(fixture.read_bytes()))
        cls.out=guard.Output(cls.root/'complete');cls.out.write('sources/scripts/p01v_fixture.py',fixture.read_bytes());cls.out.write('provenance/interpreter.bin',interpreter.read_bytes())
        proc=subprocess.Popen;counts={'processes':0}
        def observe(*args,**kwargs):counts['processes']+=1;return proc(*args,**kwargs)
        with patch('subprocess.Popen',observe):pipeline.run_pipeline(cls.out,cls.descriptors,lambda name:Path(name).read_bytes(),cls.native,cls.pins)
        cls.out.finish();cls.data={name:bytes(value) for name,value in cls.out.data.items()}
        cls.observed_processes=counts['processes'];(cls.root/'process_spy.json').write_bytes(guard.encoded(counts))
        cls.manifest=guard.parse(cls.data['manifest.json']);cls.failure_results=[]

    def test_01_admission(self):
        for index in (0,127):
            d=self.descriptors[index];row=self.out.rows[index];data=Path(d['file']).read_bytes()
            self.assertEqual(pipeline.load_request(data,d['sha256'],row,self.native[index]),data)
            self.assertEqual(guard.typed(guard.parse(guard.encoded(guard.parse(data)))),guard.typed(guard.parse(data)))
        d=self.descriptors[0]
        with self.assertRaises(ValueError):pipeline.load_request(Path(d['file']).read_bytes(),'0'*64,self.out.rows[0],self.native[0])
        prior=dict(self.native[0],native_accepted=False)
        with self.assertRaises(ValueError):pipeline.load_request(Path(d['file']).read_bytes(),d['sha256'],self.out.rows[0],prior)
        source=(pipeline.ROOT/'scripts/p01v_pipeline.py').read_text();self.assertIn('load_request(reader(',source)

    def test_02_stage_bindings(self):
        row=self.out.rows[0];previous=None
        for stage,role in zip(row['stages'],guard.ROLES):
            raw=self.data[stage['guard']['stdout_file']];audit.verify_receipt(raw,role,row,row['input_sha256'],previous)
            value=guard.parse(raw)
            for key,val in [('role','wrong'),('slot',1),('proposal',6001),('initial',1),('previous_stdout_sha256','0'*64),('input_request_sha256','0'*64)]:
                bad=dict(value,**{key:val})
                with self.assertRaises(ValueError):audit.verify_receipt(guard.encoded(bad)+b'\n',role,row,row['input_sha256'],previous)
            other=dict(row,slot=1)
            with self.assertRaises(ValueError):audit.verify_receipt(raw,role,other,row['input_sha256'],previous)
            previous=raw

    def test_03_complete_pipeline(self):
        result=audit.verify_panel(self.data,self.descriptors,lambda name:Path(name).read_bytes(),self.native,self.pins)
        self.assertEqual(result['inert_stages'],384);self.assertEqual(self.observed_processes,384)
        self.assertIsNone(self.manifest['behavioral_outcomes']);self.assertEqual(self.manifest['behavioral_missing_reason'],'not_executed')
        for label,path in [('relative',(self.root/'relative').relative_to(Path.cwd())),('absolute',self.root/'absolute')]:
            out=guard.Output(path);out.write('sources/scripts/p01v_fixture.py',Path(self.pins['fixture']).read_bytes());out.write('provenance/interpreter.bin',Path(self.pins['interpreter']).read_bytes())
            pipeline.run_pipeline(out,self.descriptors,lambda name:Path(name).read_bytes(),self.native,self.pins);self.assertEqual(out.finish()['status'],'pass')
            data={name:bytes(value) for name,value in out.data.items()};self.assertEqual(audit.verify_panel(data,self.descriptors,lambda name:Path(name).read_bytes(),self.native,self.pins)['cells'],128)

    def test_04_failures(self):
        for scenario in self.packet['failure_scenarios']:
            out=guard.Output(self.root/scenario['label']);descriptors=copy.deepcopy(self.descriptors);fault=None
            if scenario['cell'] is None:fault=dict(kind='before')
            elif scenario['role'] is None:descriptors[0]['sha256']='0'*64
            else:fault=dict(kind='stage',slot=scenario['cell'],role=scenario['role'])
            pipeline.run_pipeline(out,descriptors,lambda name:Path(name).read_bytes(),self.native,self.pins,fault=fault,invented=True)
            self.assertEqual(out.finish()['status'],'fail');data={n:bytes(b) for n,b in out.data.items()}
            result=audit.verify_failure(data,scenario['cell'],scenario['role']);self.assertEqual(result['expected_invocations'],scenario['invocations'])
            self.failure_results.append(dict(scenario=scenario,result=result,manifest_sha256=guard.sha(data['manifest.json'])))
        (self.root/'failure_results.json').write_bytes(guard.encoded(self.failure_results))

    def test_05_bad_receipts(self):
        row=self.out.rows[0];raw=self.data[row['stages'][0]['guard']['stdout_file']]
        malformed=[b'{',raw.replace(b'"inert":true',b'"inert":true,"inert":true'),raw.replace(b'"slot":0',b'"slot":NaN')]
        value=guard.parse(raw)
        missing=dict(value);missing.pop('role');extra=dict(value,unknown=1);notinert=dict(value,inert=False);badhash=dict(value,input_request_sha256='0'*64)
        malformed.extend(guard.encoded(v)+b'\n' for v in (missing,extra,notinert,badhash))
        for data in malformed:
            with self.assertRaises(ValueError):audit.verify_receipt(data,'native_stub',row,row['input_sha256'],None)

    def test_06_process_guards(self):
        for delta in (-1,0,1):
            self.assertEqual(guard.within_stage_limits(2+delta/1000,0,1),delta<0)
            self.assertEqual(guard.within_stage_limits(0,1048576+delta,1),delta<0)
            self.assertEqual(guard.within_stage_limits(0,0,268435456+delta),delta<0)
        # Actual injected RSS samples exercise the retained guard implementation.
        for delta in (-1,0,1):
            out=guard.Output(self.root/f'rss-{delta}');role='native_stub';d=self.descriptors[0];raw=Path(d['file']).read_bytes()
            with patch.dict(guard.run_stage.__globals__,rss=lambda pid:268435456+delta):
                stats,stdout,stderr=guard.invoke(out,'s',self.pins,role,out.rows[0],d['sha256'],raw)
            self.assertEqual(stats['status'],'complete' if delta<0 else 'failed')
            out.first_error='injected sampler case' if delta>=0 else None;out.finish()
        # Separate inert guard fixtures can spawn descendants; the production fixture never does.
        code='import sys,subprocess,time;sys.stdin.buffer.read();c=subprocess.Popen([sys.executable,"-c","import time;time.sleep(10)"]);print(c.pid,flush=True);sys.stderr.write("partial stderr\\n");sys.stderr.flush();time.sleep(10)'
        out=guard.Output(self.root/'process_group')
        stats,stdout,stderr=guard.run_stage(out,'s',[sys.executable,'-I','-B','-c',code],b'',wall_cap=0.1)
        self.assertEqual(stats['status'],'failed');self.assertEqual(stats['kills'],1);self.assertTrue(stderr);self.assertTrue(stdout)
        child=int(stdout.splitlines()[0]);time.sleep(0.01)
        # A dead unreaped child can remain a zombie, so use the SDK RSS query as liveness evidence.
        self.assertIn(guard.rss(child),(None,0));out.first_error='inert group cap';out.finish()
        for name,code in [('nonzero','import sys;sys.stdin.buffer.read();sys.exit(7)'),('output','import sys,os,time;sys.stdin.buffer.read();os.write(1,b"x"*4096);time.sleep(1)')]:
            out=guard.Output(self.root/name);kwargs={'byte_cap':1024} if name=='output' else {}
            stats,stdout,stderr=guard.run_stage(out,'s',[sys.executable,'-I','-B','-c',code],b'',**kwargs)
            self.assertEqual(stats['status'],'failed');out.first_error='inert guard case';out.finish()
            if name=='output':self.assertEqual(len(stdout),1024);self.assertEqual(stats['kills'],1)

    def test_07_executor(self):
        d=self.descriptors[0];row=self.out.rows[0];argv=guard.command(self.pins,'native_stub',row,d['sha256'])
        guard.check_command(argv,self.pins,'native_stub',row,d['sha256'])
        with patch('subprocess.Popen',side_effect=RuntimeError('must not launch')):
            for command in [[self.pins['interpreter'],'-c','print(1)'],['target/release/pilot-worker','run','request.json'],['validator'],['reporter']]:
                with self.assertRaises(ValueError):guard.check_command(command,self.pins,'native_stub',row,d['sha256'])
            for key in ('fixture_sha256','interpreter_sha256'):
                pins=dict(self.pins,**{key:'0'*64})
                with self.assertRaises(ValueError):guard.check_command(argv,pins,'native_stub',row,d['sha256'])
        sources={role:(pipeline.ROOT/f'scripts/p01v_{role}.py').read_text() for role in ('pipeline','guard','fixture')}
        gate=guard.source_gate(sources);(self.root/'source_gate.json').write_bytes(guard.encoded(gate))
        for injection in ('\nimport subprocess\n','\nstep()\n','\nimport p01u_validation\n'):
            changed=dict(sources,fixture=sources['fixture']+injection)
            with self.assertRaises(ValueError):guard.source_gate(changed)

    def test_08_budgets_accounting(self):
        for kind in ('wall','bytes'):
            for delta in (-1,0,1):
                out=guard.Output(self.root/f'{kind}-{delta}')
                if kind=='wall':out.clock=lambda:out.start+175+delta
                else:out.total=133169152+delta
                if delta<0:out.poll()
                else:
                    with self.assertRaises(ValueError):out.poll()
        out=guard.Output(self.root/'reserved');out.reserved=1048576;before=out.reserved;out.poll();self.assertEqual(before,1048576)
        out.write('old',b'old');out.write('temporary',b'new');self.assertEqual(out.total,6)
        original=os.write;calls=[]
        def partial(fd,data):
            if calls:raise OSError('injected partial syscall')
            calls.append(True);return original(fd,data[:3])
        with patch('os.write',partial):
            with self.assertRaises(OSError):out.write('partial',b'abcdef')
        self.assertEqual(len(out.data['partial']),3);out.first_error='partial';out.finish()
        counts=dict(write_calls=0,write_bytes=0,scans=0);write=os.write;scan=os.scandir
        def write_spy(fd,data):
            n=write(fd,data)
            if stat.S_ISREG(os.fstat(fd).st_mode):counts['write_calls']+=1;counts['write_bytes']+=n
            return n
        def scan_spy(*args,**kwargs):counts['scans']+=1;return scan(*args,**kwargs)
        with patch('os.write',write_spy),patch('os.scandir',scan_spy):
            out=guard.Output(self.root/'spies');out.write('snapshot',b'source snapshot');out.write('log',b'log')
            with patch('os.scandir',side_effect=RuntimeError('no stage tree scan')):
                d=self.descriptors[0];stats,stdout,stderr=guard.invoke(out,'s',self.pins,'native_stub',out.rows[0],d['sha256'],Path(d['file']).read_bytes())
            self.assertEqual(stats['status'],'complete');out.finish()
        self.assertEqual(counts['write_calls'],out.counts['write_calls']);self.assertEqual(counts['write_bytes'],out.counts['write_bytes']);self.assertEqual(counts['scans'],1)
        (self.root/'spy_results.json').write_bytes(guard.encoded(dict(observed=counts,ledger=out.counts)))
        out=guard.Output(self.root/'budget_trap')
        with ExitStack() as stack:
            for target in ('os.scandir','os.stat','os.lstat','os.open','builtins.open','io.open'):stack.enter_context(patch(target,side_effect=RuntimeError('filesystem forbidden')))
            for _ in range(100):out.poll()
        self.assertEqual(out.counts['budget_polls'],100)

    def test_09_terminal(self):
        out=guard.Output(self.root/'terminal');self.assertEqual(len(out.rows),128);self.assertEqual(sum(len(r['stages']) for r in out.rows),384)
        out.first_error='original failure'
        with patch('os.scandir',side_effect=RuntimeError('no terminal scan')),patch('os.open',side_effect=OSError('terminal I/O')):result=out.finish()
        self.assertEqual(result['first_error'],'original failure');self.assertTrue(result['closeout_errors']);self.assertEqual(result['terminal_receipt'],'missing')
        (self.root/'terminal_failure.json').write_bytes(guard.encoded(result))
        out=guard.Output(self.root/'unknown');out.write('partial',b'abc');out.first_error='incomplete failure'
        # Author a128-byte conservative allowance before the external fixture's3-byte write.
        out.reserved=128;(out.root/'untracked.bin').write_bytes(b'xyz');out.mark_unknown(128);out.finish()
        data,_=audit.inventory(out.root);self.assertTrue(audit.verify_unknown_failure(data))
        completion=guard.parse(data['completion.json']);completion['output_bytes']=completion['known_path_bytes'];changed=dict(data,**{'completion.json':guard.encoded(completion)})
        with self.assertRaises(ValueError):audit.verify_unknown_failure(changed)

    def test_10_audit_mutations(self):
        rows=self.manifest['rows']
        for changed in (rows[:-1],rows+rows[:1],rows[:1]+rows,rows[::-1]):
            with self.assertRaises(ValueError):audit.verify_rows(changed)
        for stages in (rows[0]['stages'][:-1],rows[0]['stages']+rows[0]['stages'][:1],rows[0]['stages'][:1]+rows[0]['stages'],rows[0]['stages'][::-1]):
            changed=copy.deepcopy(rows);changed[0]['stages']=stages
            with self.assertRaises(ValueError):audit.verify_rows(changed)
        for action in ('unlisted','missing','hash','total','counter'):
            data=dict(self.data)
            if action=='unlisted':data['extra']=b'x'
            elif action=='missing':data.pop('manifest.json')
            elif action=='hash':data['stages/000/native_stub/stdout.bin']+=b' '
            else:
                c=guard.parse(data['completion.json'])
                if action=='total':c['output_bytes']=None
                else:c['counts_before_completion']['write_bytes']+=1
                data['completion.json']=guard.encoded(c)
            with self.assertRaises((ValueError,KeyError)):audit.verify_inventory(data)
        # Mutations of already-sealed fields are also rejected independently by the row/chain gates.
        prior=copy.deepcopy(self.native);prior[0]['input_sha256']='0'*64
        with self.assertRaises(ValueError):audit.verify_panel(self.data,self.descriptors,lambda name:Path(name).read_bytes(),prior,self.pins)
        changed=copy.deepcopy(rows);changed[0]['stages'][0]['status']='failed'
        with self.assertRaises(ValueError):audit.verify_rows(changed)

    def test_11_attempt_preservation(self):
        before={name:guard.sha(data) for name,data in self.data.items()}
        with self.assertRaises(FileExistsError):guard.Output(self.root/'complete')
        self.assertEqual(before,{name:guard.sha((self.root/'complete'/name).read_bytes()) for name in self.data})
        for scenario in self.failure_results:
            path=self.root/scenario['scenario']['label']/'manifest.json';self.assertEqual(guard.sha(path.read_bytes()),scenario['manifest_sha256'])
        source=(pipeline.ROOT/'scripts/p01v_pipeline.py').read_text();self.assertNotIn('p01q_campaign',source)

    def test_12_scientific_scope(self):
        self.assertEqual(self.manifest['schema'],'p01v-inert-campaign-manifest-v1');self.assertIsNone(self.manifest['behavioral_outcomes'])
        self.assertEqual(self.manifest['world_transitions'],0)
        for row in self.manifest['rows']:
            self.assertEqual(row['status'],'plumbing_complete')
            for stage in row['stages']:self.assertIs(guard.parse(self.data[stage['guard']['stdout_file']])['inert'],True)
        tree=ast.parse((pipeline.ROOT/'scripts/audit_p01v.py').read_text())
        modules=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        self.assertFalse(any(name and name.startswith('p01') for name in modules))


if __name__=='__main__':unittest.main()
