"""Invented inert-envelope/byte-map controls; no retained payloads or old runtimes."""
import ast
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import review_p01r as review
import audit_p01r as audit


def wrapper():
    return dict(schema='p01o-generated-environment-v1',slot=0,proposal=6000,initial=0,map=[1,2,3],state_map=[0,1,2],
        draws=[dict(namespace='invented',proposal=6000,initial=0,field='inert',index=0,modulus=3,raw=1)],
        environment=dict(profile='p00c-local-driven-v1',channels=[],initial_activation=64,injected=0,extracted=0,
            native=dict(profile='inert_descriptor_not_executable',seed=0,rules=[dict(opaque_rule=1)],limits={},world=dict(opaque_resource=8))))


def fixtures():
    base=wrapper();items=[]
    def add(name,a,b):items.append(dict(name=name,kind='interface',left=a,right=b))
    add('complete_wrapper_preserves_all_fields',base,copy.deepcopy(base))
    add('already_unwrapped_fixture_is_wrong_boundary',base['environment'],copy.deepcopy(base['environment']))
    for name,key in [('missing_environment','environment'),('missing_native','native')]:
        a=copy.deepcopy(base)
        if key=='environment':del a[key]
        else:del a['environment'][key]
        add(name,a,copy.deepcopy(a))
    a=copy.deepcopy(base);a['schema']='wrong';add('wrong_schema',a,copy.deepcopy(a))
    a=copy.deepcopy(base);a['initial']=1;add('wrong_cell_ids',a,copy.deepcopy(a))
    a=copy.deepcopy(base);a['initial']=False;add('bool_vs_integer_mismatch',base,a)
    a=copy.deepcopy(base);a['draws'][0]['raw']=2;add('stream_disagreement',base,a)
    a=copy.deepcopy(base);a['additional_metadata']={'opaque':[False,0]};add('extra_metadata_preserved',a,copy.deepcopy(a))
    a=copy.deepcopy(base);a['environment']['native']['world']['opaque_resource']=9;a['environment']['native']['rules'][0]['opaque_rule']=2
    add('nested_resource_or_rule_mutation_rejected',base,a)
    def op(tag,path,**kw):return dict(op=tag,path=path,**kw)
    def acct(name,**case):items.append(dict(name=name,kind='accounting',case=case))
    acct('create_and_append',operations=[op('set','trace',bytes=5),op('append','trace',bytes=3)])
    acct('atomic_replace_counts_old_and_temporary_until_rename',operations=[op('set','manifest',bytes=10),op('set','manifest.pending',bytes=14),op('rename','manifest.pending',to='manifest')])
    acct('failed_partial_write_is_retained',operations=[op('set','failed.trace',bytes=5),op('append','failed.trace',bytes=2)])
    acct('duplicate_path_not_double_counted',operations=[op('set','trace',bytes=5),op('set','trace',bytes=5)])
    acct('snapshot_bytes_included',operations=[op('set','source/a',bytes=12),op('set','dependencies/a',bytes=20)])
    acct('metadata_and_seal_bytes_included',operations=[op('set','trace',bytes=8),op('set','manifest',bytes=10),op('set','checksums',bytes=6),op('set','seal',bytes=4)])
    def reserve(cpu='1',wall='1',size='1'):
        return dict(usage=dict(cpu=cpu,wall=wall,bytes=size),reserve=dict(cpu='5',wall='5',bytes='1048576'),cap=dict(cpu='600',wall='1200',bytes='134217728'))
    acct('cpu_reserve_boundary',reservations=[reserve(cpu='594.999'),reserve(cpu='595')])
    acct('wall_and_byte_reserve_boundaries',reservations=[reserve(wall='1194.999'),reserve(wall='1195'),reserve(size=str(134217728-1048576-1)),reserve(size=str(134217728-1048576))])
    acct('terminal_failure_preserves_all_cells',terminal_statuses=[dict(slot=i,status='failed' if i==0 else 'unstarted') for i in range(128)])
    acct('inventory_mismatch_and_unlisted_file',operations=[op('set','unlisted',bytes=7)],inventory=['expected'])
    return copy.deepcopy(items)


def answer(module,c):return module.pair(c['left'],c['right'],0,6000,0) if c['kind']=='interface' else module.accounting(c['case'])


class Controls(unittest.TestCase):
    def setUp(self):
        self.items=fixtures()
        # Descriptor functions have no need to read any retained files or spawn processes.
        real_sha=hashlib.sha256
        def guard(data=b'',**kw):
            if data.startswith(b'["p01-generator-'):raise AssertionError('keyed evaluation forbidden')
            return real_sha(data,**kw)
        p=patch.object(hashlib,'sha256',side_effect=guard);p.start();self.addCleanup(p.stop)
    def test_twenty_controls_and_independent_oracle(self):
        self.assertEqual(len(self.items),20)
        for c in self.items:
            with self.subTest(control=c['name']):self.assertEqual(answer(review,c),answer(audit,c))
    def test_complete_envelope_extra_metadata_and_no_mutation(self):
        before=copy.deepcopy(self.items)
        for c in (self.items[0],self.items[8]):
            r=answer(review,c);self.assertTrue(r['typed_equal']);self.assertTrue(r['nested_native_available']);self.assertFalse(r['root_native_expected_by_runner'])
            self.assertTrue(r['left']['valid_envelope']);self.assertEqual(r['left']['keys'],sorted(c['left']))
        self.assertEqual(self.items,before)
    def test_wrong_boundary_and_malformed_metadata(self):
        for i in range(1,6):
            with self.subTest(i=i):self.assertFalse(answer(review,self.items[i])['left']['valid_envelope'])
        for i in (6,7,9):self.assertFalse(answer(review,self.items[i])['typed_equal'])
        self.assertFalse(answer(review,self.items[6])['right']['valid_envelope'])
        self.assertFalse(answer(review,self.items[9])['nested_environment_equal'])
        self.assertTrue(answer(review,self.items[7])['nested_environment_equal'])
    def test_typed_equality_rejects_nested_boolean_integer(self):
        for a,b in [({'x':1},{'x':True}),([0],[False]),({'a':[1]},{'a':[1.0]}),({'x':1},{'y':1})]:
            self.assertFalse(review.equal(a,b));self.assertNotEqual(audit.typed(a),audit.typed(b))
    def test_sizes_include_transients_partial_writes_and_metadata(self):
        expected=[[5,8],[10,24,14],[5,7],[5,5],[12,32],[8,18,24,28]]
        for c,want in zip(self.items[10:16],expected):self.assertEqual(answer(review,c)['totals'],want)
        self.assertEqual(answer(review,self.items[11])['paths'],['manifest'])
        self.assertFalse(answer(review,self.items[19])['inventory_matches'])
    def test_strict_decimal_reserves_and_terminal_denominator(self):
        self.assertEqual(answer(review,self.items[16])['reservations_fit'],[True,False])
        self.assertEqual(answer(review,self.items[17])['reservations_fit'],[True,False,True,False])
        for module in (review,audit):
            self.assertEqual(len(answer(module,self.items[18])['terminal_statuses']),128)
            bad=copy.deepcopy(self.items[18]['case']);bad['terminal_statuses'].pop()
            with self.assertRaises(ValueError):module.accounting(bad)
            with self.assertRaises(ValueError):module.accounting({'operations':[{'op':'set','path':'a','bytes':True}]})
    def test_invented_ast_spans_loops_and_unknown_timings(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            sources={
                'scripts/generator_v4.py':'def construct_with_source():\n    return {}\n',
                'scripts/p01q_cell.py':'def saved_initial():\n    return {}\n',
                'scripts/p01q_campaign.py':'def check_execution(tick):\n    for x in []:\n        tick()\ndef run():\n    def usage():\n        return campaign.file_bytes(out)\n    def check_budget():\n        return usage()\n    try:\n        while pending:\n            check_budget()\n    finally:\n        check_execution(tick=check_budget)\ndef execute_pipeline():\n    tick()\n',
                'scripts/test_p01q.py':'def test():\n    def saved():\n        return {}\n',
                'scripts/campaign.py':'def file_bytes(root):\n    return sum(p.size for p in root.files)\n',
                'src/bin/pilot-worker.rs':'let request: Request = inert;\nlet start_event = inert;\n'}
            for n,s in sources.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
            with patch.object(review,'ROOT',root),patch.object(audit,'ROOT',root):
                r=review.source_analysis();audit.verify_sources(r)
                self.assertIsNone(r['timing_attribution']);self.assertTrue(any(c['context'] for c in r['call_sites']))
                r['call_sites'].pop()
                with self.assertRaises(ValueError):audit.verify_sources(r)
                r=review.source_analysis();r['spans'][0]['text']+='tampered'
                with self.assertRaises(ValueError):audit.verify_sources(r)
    def test_bounded_terminal_receipts_and_tampered_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'attempt';a=review.Attempt(out);a.cap=1048600
            with self.assertRaises(ValueError):a.raw('oversized',b'x'*100)
            a.finish(dict(status='fail',error='invented limit'))
            self.assertEqual(json.loads((out/'assessment.json').read_text())['status'],'fail')
            self.assertTrue((out/'completion.json').exists())
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'attempt';a=review.Attempt(out);a.finish(dict(status='pass'))
            audit.verify_review_bundle(out);(out/'unlisted').write_text('x')
            with self.assertRaises(ValueError):audit.verify_review_bundle(out)
    def test_no_runtime_imports_or_process_permissions(self):
        allowed={'ast','hashlib','json','sys','time','collections','decimal','pathlib'}
        for module in (review,audit):
            tree=ast.parse(Path(module.__file__).read_text())
            imports={n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|{a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
            self.assertLessEqual(imports,allowed)
            for event in ('subprocess.Popen','os.system','os.posix_spawn'):
                with self.assertRaises(RuntimeError):module.prohibit_processes(event,())

if __name__=='__main__':unittest.main()
