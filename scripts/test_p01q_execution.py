"""Invented closure files only; no trajectories or process launches."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import check_p01q_execution as c

class Closure(unittest.TestCase):
    def put(self,n,v):
        p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v)+'\n')
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.put('docs/p01q_protocol.json',dict(epochs=128));self.put('source.py','invented')
        self.put('dep/file','dependency');self.put('tool','tool')
        self.put('docs/p01q_registration_freeze.json',dict(files={'source.py':c.sha(self.root/'source.py')},inputs={},prior_public_receipts={}))
        self.put('ready.json',dict(sources={'source.py':c.sha(self.root/'source.py')}))
        self.put('docs/p01q_implementation_readiness.json',dict(implementation_complete=True,invented_mock_checks_pass=True,world_execution_admitted=False,readiness_receipt='ready.json',readiness_sha256=c.sha(self.root/'ready.json')))
        self.put('metadata.json',dict(packages=[dict(source='invented',manifest_path=str(self.root/'dep/file'))]))
        bins={}
        for n in ('pilot-worker','pilot-report'):
            self.put('bin/'+n,'invented binary');bins[n]=dict(path='bin/'+n,sha256=c.sha(self.root/'bin'/n))
        self.put('docs/p01g_execution_freeze.json',dict(binaries=bins))
        self.f=dict(files={'source.py':c.sha(self.root/'source.py')},dependencies={str(self.root/'dep/file'):c.sha(self.root/'dep/file')},tools={str(self.root/'tool'):c.sha(self.root/'tool')},membership=[dict(root=str(self.root/'dep'),files=['file'])],binaries=bins,prior_public_receipts={},cargo_metadata='metadata.json')
        self.put('docs/p01q_execution_freeze.json',self.f)
        self.a=dict(schema='p01q-execution-admission-v1',world_execution_admitted=True,keyed_evaluation_admitted=False,e01_authorized=False,fixed_slots=128,fixed_laws=32,epochs=128,admitted_output='artifacts/p01q-001',output_absolute=str(self.root/'artifacts/p01q-001'),no_retries_or_replacements=True,world_transitions_so_far=0,scientific_status='untested',required_environment={'PYTHONDONTWRITEBYTECODE':'1'},implementation_readiness_sha256=c.sha(self.root/'docs/p01q_implementation_readiness.json'),**{k+'_sha256':c.sha(self.root/'docs'/('p01q_'+k+'.json')) for k in ('protocol','registration_freeze','execution_freeze')})
        self.put('docs/p01q_execution_admission.json',self.a)
    def test_complete_invented_closure(self):self.assertEqual(c.review(self.root)['fixed_environments'],128)
    def test_bytes_tamper(self):
        for n in ('source.py','dep/file','tool','bin/pilot-worker','bin/pilot-report'):
            p=self.root/n;old=p.read_bytes();p.write_bytes(old+b' ')
            with self.subTest(n=n),self.assertRaises(ValueError):c.review(self.root)
            p.write_bytes(old)
    def test_added_dependency_rejected(self):
        self.put('dep/extra','unlisted')
        with self.assertRaisesRegex(ValueError,'membership'):c.review(self.root)
    def test_existing_attempt_rejected(self):
        (self.root/'artifacts/p01q-001').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'no resume'):c.review(self.root)
    def test_admission_links_scope_and_output_rejected(self):
        for key,value in [('keyed_evaluation_admitted',True),('e01_authorized',True),('fixed_slots',127),('epochs',256),('execution_freeze_sha256','0'*64),('implementation_readiness_sha256','0'*64),('output_absolute',str(self.root/'retry')),('required_environment',{})]:
            self.put('docs/p01q_execution_admission.json',dict(self.a,**{key:value}))
            with self.subTest(key=key),self.assertRaises(ValueError):c.review(self.root)
    def test_omitted_hash_coverage_rejected(self):
        f=copy.deepcopy(self.f);f['membership'][0]['files'].append('second');self.put('dep/second','unhashed')
        self.put('docs/p01q_execution_freeze.json',f)
        self.put('docs/p01q_execution_admission.json',dict(self.a,execution_freeze_sha256=c.sha(self.root/'docs/p01q_execution_freeze.json')))
        with self.assertRaisesRegex(ValueError,'hash coverage'):c.review(self.root)

if __name__=='__main__':unittest.main()
