"""Registered P01u invented native controls and independent mutation checks."""
import ast
import copy
import json
import os
import re
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import p01u_validation as p
import audit_p01u as a


def base_request():
    world=dict(nodes={'0':dict(kind=0,state=0,matter=2,activation=3),'1':dict(kind=1,state=1,matter=2,activation=1)},
        edges={'0':dict(class_='Contact',kind=0,ends=[0,1])},next_node=2,next_edge=1,epoch=0,dissipated=0,matter_total=7,
        activation_total=4,next_event=1,writers={})
    world['edges']['0']['class']=world['edges']['0'].pop('class_')
    rule=dict(id=0,nodes=[dict(kind=0,state=None)],edges=[],absent=[],ops=[dict(op='SetState',node=0,value=1)])
    native=dict(profile='p00a-local-closed-v1',seed=0,rules=[rule],limits=dict(max_candidates=4096,max_bindings=65536,max_nodes=128,max_edges=256),world=world)
    return dict(schema='p01-worker-request-v1',epochs=128,max_events=16384,max_trace_bytes=4194304,
        initial=dict(profile='p00c-local-driven-v1',channels=[],initial_activation=4,injected=0,extracted=0,native=native))


def controls():
    protocol=json.loads((p.ROOT/'docs/p01u_protocol.json').read_bytes());cases=[]
    alternatives={
        'zero_supply_or_extract':['zero_supply','zero_extract'],
        'wrong_transport_class_or_ends':['wrong_transport_class','wrong_transport_ends'],
        'relative_and_absolute_paths':['relative_path','absolute_path'],
        'stage_wall_equal_and_one_unit_sides':['wall_below','wall_equal','wall_above'],
        'stage_output_equal_and_one_unit_sides':['output_below','output_equal','output_above'],
        'aggregate_reserve_equal_and_one_unit_sides':['aggregate_wall_below','aggregate_wall_equal','aggregate_wall_above','aggregate_bytes_below','aggregate_bytes_equal','aggregate_bytes_above'],
        'missing_duplicate_extra_reordered_rows':['missing_row','duplicate_row','extra_row','reordered_rows'],
        'accepted_flag_or_error_stage_changed':['acceptance_changed','error_stage_changed'],
        'inventory_or_byte_total_changed':['inventory_changed','total_changed'],
        'old_source_or_binary_substitution_rejected':['source_substitution','binary_substitution'],
        'stepping_or_matching_call_rejected':['step_call','matcher_call'],
    }
    non_native={'guard_and_failure_closeout','immutability_and_roundtrip','independent_audit_mutations','no_transition_source_boundary'}
    for family,names in protocol['controls'].items():
        for name in names:
            for sub in alternatives.get(name,[name]):
                case=dict(family=family,registered_name=name,subcase=sub,kind='native' if family not in non_native else 'engineering')
                if family not in non_native:case.update(native_descriptor(sub))
                cases.append(case)
    return dict(schema='p01u-invented-controls-v1',registered=protocol['controls'],cases=cases)


def native_descriptor(name):
    v=base_request();env=v['initial'];native=env['native'];world=native['world'];rule=native['rules'][0]
    error=None;stage=None;strict=True;panel=True;special=None
    parse_cases={'malformed','duplicate_struct_field','unknown_field','missing_field','bool_integer','negative_unsigned','u64_overflow','nonfinite'}
    if name=='valid_connected_rule':
        rule['nodes'].append(dict(kind=1,state=None));rule['edges']=[dict(kind=0,**{'class':'Contact'},ends=[0,1])]
    elif name=='valid_environment_channel':env['channels']=[channel()]
    elif name in parse_cases:
        stage='parse';panel=False
        if name=='unknown_field':v['unknown']=1
        if name=='missing_field':v.pop('epochs')
        if name=='bool_integer':v['epochs']=True
        if name=='negative_unsigned':v['epochs']=-1
        if name=='u64_overflow':v['epochs']=18446744073709551616
        if name in ('malformed','duplicate_struct_field','nonfinite'):special=name
    elif name=='duplicate_map_key_precheck':special=name;strict=False
    elif name=='wrong_schema':v['schema']='wrong';stage='worker_prefix';error='invalid_request';panel=False
    elif name=='epochs_1001':v['epochs']=1001;stage='worker_prefix';error='invalid_request';panel=False
    elif name=='epochs_127_native_accept_policy_reject':v['epochs']=127;panel=False
    elif name=='max_events_changed_native_accept_policy_reject':v['max_events']=1;panel=False
    elif name=='max_trace_changed_native_accept_policy_reject':v['max_trace_bytes']=1;panel=False
    elif name=='wrong_environment_profile':env['profile']='wrong';error='unknown_environment_profile'
    elif name=='wrong_native_profile':native['profile']='wrong';error='unknown_profile'
    elif name=='node_allocator_not_ahead':world['next_node']=1;error='allocator_not_ahead'
    elif name=='edge_allocator_not_ahead':world['next_edge']=0;error='allocator_not_ahead'
    elif name=='missing_endpoint':world['edges']['0']['ends']=[0,99];error='invalid_endpoints'
    elif name=='repeated_endpoint':world['edges']['0']['ends']=[0,0];error='invalid_endpoints'
    elif name=='arity_out_of_range':world['edges']['0']['ends']=[0];error='invalid_endpoints'
    elif name=='duplicate_edge':world['edges']['1']=copy.deepcopy(world['edges']['0']);world['next_edge']=2;world['matter_total']=8;error='duplicate_edge'
    elif name=='matter_mismatch':world['matter_total']=8;error='matter_not_conserved'
    elif name=='activation_mismatch':world['activation_total']=5;error='activation_not_conserved'
    elif name=='invalid_writer':world['writers']={'x':1};error='invalid_writer'
    elif name=='empty_nodes':rule['nodes']=[];error='grammar_bounds'
    elif name=='too_many_nodes':rule['nodes']*=7;error='grammar_bounds'
    elif name=='empty_ops':rule['ops']=[];error='grammar_bounds'
    elif name=='too_many_ops':rule['ops']*=9;error='grammar_bounds'
    elif name in ('too_many_positive_edges','too_many_absent_edges'):
        rule['edges' if name=='too_many_positive_edges' else 'absent']=[dict(kind=0,**{'class':'Contact'},ends=[0,1])]*9;error='grammar_bounds'
    elif name=='bad_pattern_endpoints':rule['edges']=[dict(kind=0,**{'class':'Contact'},ends=[0,0])];error='invalid_pattern_endpoints'
    elif name=='disconnected_pattern':rule['nodes'].append(dict(kind=1,state=None));error='disconnected_pattern'
    elif name=='operation_slot_out_of_range':rule['ops'][0]['node']=1;error='invalid_slot'
    elif name=='duplicate_rule_id':native['rules'].append(copy.deepcopy(rule));error='duplicate_rule_id'
    elif name=='valid_created_slot_reference':rule['ops']=[dict(op='CreateNode',account=0,kind=2,state=0),dict(op='SetState',node=1,value=2)]
    elif name=='node_limit_exceeded':native['limits']['max_nodes']=1;error='world_size_exceeded'
    elif name=='edge_limit_exceeded':native['limits']['max_edges']=0;error='world_size_exceeded'
    elif name=='balance_mismatch':env['initial_activation']=5;error='environment_balance_mismatch'
    elif name=='too_many_channels':env['channels']=[dict(channel(),id=i) for i in range(33)];error='environment_channel_limit'
    elif name=='duplicate_channel_id':env['channels']=[channel(),channel()];error='invalid_channel_schedule'
    elif name in ('zero_period','invalid_end','zero_supply','zero_extract','missing_channel_node'):
        c=channel();env['channels']=[c]
        if name=='zero_period':c['period']=0;error='invalid_channel_schedule'
        if name=='invalid_end':c['end']=0;error='invalid_channel_schedule'
        if name in ('zero_supply','zero_extract'):c['action']['amount']=0;c['action']['op']='Supply' if name=='zero_supply' else 'Extract';error='zero_environment_amount'
        if name=='missing_channel_node':c['action']['node']=99;error='missing_environment_node'
    elif name in ('zero_transport','missing_transport_edge','wrong_transport_class','wrong_transport_ends'):
        c=channel();c['action']=dict(op='Transport',edge=0,**{'from':0,'to':1},matter=1,activation=0);env['channels']=[c]
        if name=='zero_transport':c['action']['matter']=0;error='zero_environment_amount'
        if name=='missing_transport_edge':c['action']['edge']=99;error='missing_transport_contact'
        if name=='wrong_transport_class':world['edges']['0']['class']='Structural';error='invalid_transport_contact'
        if name=='wrong_transport_ends':c['action']['from']=1;c['action']['to']=0;error='invalid_transport_contact'
    elif name!='valid_minimal':raise ValueError('unexpanded native subcase '+name)
    if error and stage is None:stage='initial_validate'
    raw=p.encoded(v)
    if special=='malformed':raw=b'{'
    if special=='duplicate_struct_field':raw=raw.replace(b'"epochs":128',b'"epochs":128,"epochs":128')
    if special=='nonfinite':raw=raw.replace(b'"epochs":128',b'"epochs":NaN');strict=False
    if special=='duplicate_map_key_precheck':raw=raw.replace(b'"writers":{}',b'"writers":{"x":0,"x":0}')
    if special in ('malformed','duplicate_struct_field'):strict=False
    return dict(raw=raw.decode(),expected_accept=stage is None,expected_stage=stage,expected_error=error,strict_precheck=strict,panel_policy=panel)


def channel():return dict(id=0,start=0,end=None,period=1,action=dict(op='Supply',node=0,amount=1))


class Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['P01U_TEST_OUT']);cls.root.mkdir(parents=True,exist_ok=False)
        cls.binary=Path(os.environ['P01U_BINARY']).absolute();cls.binary_hash=p.sha(cls.binary.read_bytes());cls.packet=controls()
        (cls.root/'packet.json').write_bytes(p.encoded(cls.packet));cls.native_results=[];cls.engineering_results=[]
        protocol=json.loads((p.ROOT/'docs/p01u_protocol.json').read_bytes());source=(p.ROOT/protocol['future_paths']['native_source']).read_text()
        cls.gate=p.source_gate(source,p.sha(source.encode()),protocol['semantic_sources'])
        (cls.root/'source_gate.json').write_bytes(p.encoded(cls.gate))
        cls.out=p.Output(cls.root/'native')
        for i,case in enumerate(cls.packet['cases']):
            if case['kind']!='native':continue
            raw=case['raw'].encode();stage,stdout,stderr=p.run_stage(cls.out,f'cases/{i:03}',[str(cls.binary)],raw,cls.binary_hash)
            observed=dict(subcase=case['subcase'],guard=stage,stdout_sha256=p.sha(stdout),stderr_bytes=len(stderr))
            if stage['status']=='complete':
                report=p.parse(stdout);observed.update(accepted=report['accepted'],rejection_stage=report['rejection_stage'],error=report['error'])
            cls.native_results.append(observed)
        (cls.root/'native_results.json').write_bytes(p.encoded(cls.native_results));cls.out.finish()
        valid_observation=next(obs for obs in cls.native_results if obs['subcase']=='valid_minimal')
        cls.valid_report=p.parse(bytes(cls.out.data[valid_observation['guard']['stdout_file']]))
        cls.valid_data=next(c['raw'].encode() for c in cls.packet['cases'] if c['subcase']=='valid_minimal')

    def check_family(self,family):
        by_name={c['subcase']:c for c in self.packet['cases'] if c['family']==family}
        for obs in self.native_results:
            if obs['subcase'] not in by_name:continue
            c=by_name[obs['subcase']]
            with self.subTest(case=c['subcase']):
                self.assertEqual(obs['guard']['status'],'complete',obs['guard']);self.assertEqual(obs['stderr_bytes'],0)
                self.assertEqual(obs['accepted'],c['expected_accept']);self.assertEqual(obs['rejection_stage'],c['expected_stage'])
                if c['expected_error'] is not None:self.assertEqual(obs['error'],c['expected_error'])
                raw=c['raw'].encode();precheck=True
                try:p.parse(raw)
                except (ValueError,TypeError):precheck=False
                self.assertEqual(precheck,c['strict_precheck'])
                if precheck:self.assertEqual(p.policy(p.parse(raw)),c['panel_policy'])
                if obs['rejection_stage']!='parse' and precheck:
                    report=p.parse(bytes(self.out.data[obs['guard']['stdout_file']]))
                    self.assertEqual(a.verify_report(raw,report),c['panel_policy'])

    def test_01_valid(self):self.check_family('valid_authored_request')
    def test_02_json(self):self.check_family('json_shape_and_numeric_parsing')
    def test_03_prefix_policy(self):self.check_family('worker_prefix_and_panel_policy')
    def test_04_profiles(self):self.check_family('profile_validation')
    def test_05_world_structure(self):self.check_family('world_allocator_and_endpoints')
    def test_06_conservation(self):self.check_family('world_conservation_and_writers')
    def test_07_grammar(self):self.check_family('rule_grammar_and_connectivity')
    def test_08_slots(self):self.check_family('rule_slots_and_ids')
    def test_09_world_limits(self):self.check_family('world_size_limits')
    def test_10_environment_balance(self):self.check_family('environment_balance')
    def test_11_channels(self):self.check_family('environment_channels')

    def test_12_immutability(self):
        self.assertTrue(a.verify_report(self.valid_data,self.valid_report))
        self.assertEqual(self.valid_report['world_before_sha256'],self.valid_report['world_after_sha256'])
        for val in (8,7.0):
            report=copy.deepcopy(self.valid_report);report['roundtrip_request']['initial']['native']['world']['matter_total']=val
            with self.assertRaises(ValueError):a.verify_report(self.valid_data,report)

    def test_13_source_boundary(self):
        protocol=json.loads((p.ROOT/'docs/p01u_protocol.json').read_bytes());source=(p.ROOT/protocol['future_paths']['native_source']).read_text()
        self.assertEqual(len(self.gate['validator_spans']),5)
        for extra in ('\nfn forbidden(){step();}\n','\nfn forbidden(){Matcher();}\n'):
            bad=source+extra
            with self.assertRaises(ValueError):p.source_gate(bad,p.sha(bad.encode()),protocol['semantic_sources'])
        with self.assertRaises(ValueError):p.source_gate(source,'0'*64,protocol['semantic_sources'])
        out=p.Output(self.root/'binary_substitution')
        with self.assertRaises(ValueError):p.run_stage(out,'s',[str(self.binary)],self.valid_data,'0'*64)
        modules=[n.module for n in ast.walk(ast.parse((p.ROOT/'scripts/audit_p01u.py').read_text())) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any(n and n.startswith('p01') for n in modules))

    def test_14_guard_and_closeout(self):
        for delta in (-1,0,1):
            self.assertEqual(p.stage_boundary(2+delta/1000,0,1),delta<0)
            self.assertEqual(p.stage_boundary(0,1048576+delta,1),delta<0)
            out=p.Output(self.root/f'aggregate-{delta}',clock=lambda:0)
            out.clock=lambda:175+delta
            if delta<0:out.poll()
            else:
                with self.assertRaises(ValueError):out.poll()
            out=p.Output(self.root/f'aggregate-bytes-{delta}');out.total=133169152+delta
            if delta<0:out.poll()
            else:
                with self.assertRaises(ValueError):out.poll()
        for label,target in [('relative',(self.root/'relative').relative_to(Path.cwd())),('absolute',self.root/'absolute')]:
            out=p.Output(target);s,stdout,stderr=p.run_stage(out,'s',[str(self.binary)],self.valid_data,self.binary_hash)
            self.assertEqual(s['status'],'complete');self.assertTrue(a.verify_report(self.valid_data,p.parse(stdout)))
        # Actual capped inert children test process-group termination and partial stream retention.
        for label,code,kwargs in [('process_failure','import sys;sys.stdin.buffer.read();sys.exit(7)',{}),('truncated_output','import sys;sys.stdin.buffer.read();print("{")',{}),
            ('output_cap','import sys,os,time;sys.stdin.buffer.read();os.write(1,b"x"*4096);time.sleep(1)',{'byte_cap':1024}),('wall_cap','import time;time.sleep(1)',{'wall_cap':0.03})]:
            out=p.Output(self.root/label);s,stdout,stderr=p.run_stage(out,'s',[sys.executable,'-c',code],b'',**kwargs)
            if label=='truncated_output':
                self.assertEqual(s['status'],'complete')
                with self.assertRaises(ValueError):p.parse(stdout)
            else:self.assertEqual(s['status'],'failed')
            if label in ('output_cap','wall_cap'):self.assertEqual(s['kills'],1)
            out.first_error='fixture first error';out.rows[0]['status']='failed';r=out.finish()
            self.assertEqual(len(out.rows),128);self.assertEqual(out.rows[1]['status'],'unstarted');self.assertEqual(r['first_error'],'fixture first error')
        out=p.Output(self.root/'partial');write=os.write;calls=[]
        def fail(fd,data):
            if calls:raise OSError('injected partial syscall')
            calls.append(True);return write(fd,data[:3])
        with patch('os.write',side_effect=fail):
            with self.assertRaises(OSError):out.write('partial.bin',b'abcdef')
        self.assertEqual(out.total,3);out.first_error='partial first';self.assertEqual(out.finish()['first_error'],'partial first')
        out=p.Output(self.root/'terminal_io');out.first_error='original'
        with patch('os.open',side_effect=OSError('terminal write error')):result=out.finish()
        self.assertEqual(result['first_error'],'original');self.assertEqual(result['terminal_receipt'],'missing')
        (self.root/'terminal_failure.json').write_bytes(p.encoded(result))
        out=p.Output(self.root/'poll_spies')
        with ExitStack() as stack:
            for name in ('os.scandir','os.stat','os.lstat','os.open','builtins.open','io.open'):stack.enter_context(patch(name,side_effect=RuntimeError('filesystem forbidden')))
            for _ in range(100):out.poll()
        self.assertEqual(out.counts['budget_polls'],100)
        # Compare actual kernel writes and scan calls independently of ledger increments.
        counts=dict(write_calls=0,write_bytes=0,scans=0);original_write=os.write;original_scan=os.scandir
        def spy_write(fd,data):
            n=original_write(fd,data);counts['write_calls']+=1;counts['write_bytes']+=n;return n
        def spy_scan(*args,**kwargs):counts['scans']+=1;return original_scan(*args,**kwargs)
        with patch('os.write',spy_write),patch('os.scandir',spy_scan):
            out=p.Output(self.root/'write_spies');out.write('a',b'abc');out.finish()
        self.assertEqual(counts['write_calls'],out.counts['write_calls']);self.assertEqual(counts['write_bytes'],out.counts['write_bytes']);self.assertEqual(counts['scans'],1)
        (self.root/'spy_results.json').write_bytes(p.encoded(dict(observed=counts,ledger=out.counts)))

    def test_15_audit_mutations(self):
        fake=[dict(slot=i,proposal=6000+i//4,initial=i%4,status='complete',native_accepted=True,panel_policy=True,roundtrip_equal=True,world_unchanged=True,rejection_stage=None) for i in range(128)]
        a.validate_rows(fake)
        for changed in (fake[:-1],fake+fake[:1],fake[:1]+fake,fake[::-1]):
            with self.assertRaises(ValueError):a.validate_rows(changed)
        for field,value in [('input_sha256','0'*64),('accepted',False),('rejection_stage','parse')]:
            report=copy.deepcopy(self.valid_report);report[field]=value
            with self.assertRaises(ValueError):a.verify_report(self.valid_data,report,True)
        report=copy.deepcopy(self.valid_report);report['roundtrip_request']['epochs']=127
        with self.assertRaises(ValueError):a.verify_report(self.valid_data,report,True)
        # Construct a retained-like invented128 panel to exercise full inventory/counter gates.
        out=p.Output(self.root/'audit_fixture');protocol=copy.deepcopy(json.loads((p.ROOT/'docs/p01u_protocol.json').read_bytes()));cache={}
        for row,(name,h) in zip(out.rows,sorted(protocol['saved_requests'].items())):
            cache[name]=self.valid_data;protocol['saved_requests'][name]=p.sha(self.valid_data)
            stdout=p.encoded(self.valid_report);prefix=f"stages/{row['slot']:03}"
            out.write(prefix+'/stdout.bin',b'');out.write(prefix+'/stderr.bin',b'');out.write(prefix+'/stdout.bin',stdout,append=True)
            stage=dict(status='complete',returncode=0,guard_error=None,kills=0,wall_seconds=0.01,output_bytes=len(stdout),binary_sha256=self.binary_hash,
                rss_samples=1,max_sampled_rss_bytes=1,rss_sample_interval_seconds=0.005,stdin_bytes=len(self.valid_data),chunks=dict(stdout=1,stderr=0),
                stdout_file=prefix+'/stdout.bin',stderr_file=prefix+'/stderr.bin')
            out.write(prefix+'/stage.json',p.encoded(stage));row.update(status='complete',stage=stage,native_accepted=True,panel_policy=True,roundtrip_equal=True,
                world_unchanged=True,rejection_stage=None,input_sha256=p.sha(self.valid_data),report_sha256=p.sha(stdout))
        out.write('binary/validator',self.binary.read_bytes());out.finish();data={n:bytes(b) for n,b in out.data.items()}
        self.assertEqual(a.verify_panel(data,cache,protocol,self.binary_hash)['cells'],128)
        for action in ('inventory','total','counter'):
            altered=dict(data)
            if action=='inventory':altered['stages/000/stdout.bin']+=b' '
            else:
                c=p.parse(altered['completion.json'])
                if action=='total':c['output_bytes']=None
                else:
                    c['counts_before_completion']['write_bytes']+=1
                altered['completion.json']=p.encoded(c)
                if action=='counter':
                    while c['output_bytes']!=sum(map(len,altered.values())):
                        c['output_bytes']=sum(map(len,altered.values()));altered['completion.json']=p.encoded(c)
            with self.assertRaises(ValueError):a.verify_inventory(altered)


if __name__=='__main__':unittest.main()
