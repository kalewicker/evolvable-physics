"""Invented admission metadata only. No productive freeze or admission is created."""
import copy
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import check_p01w_execution as c
ROOT=Path(__file__).resolve().parents[1]

class ExecutionAdmission(unittest.TestCase):
    def test_current_checkout_not_admitted(self):
        self.assertFalse((ROOT/'docs/p01w_execution_admission.json').exists())
        with self.assertRaises(FileNotFoundError):c.review(ROOT)
        self.assertFalse((ROOT/'artifacts/p01w-001').exists())
    def test_unpublished_freeze_rejected(self):
        with patch.object(c.subprocess,'check_output',return_value=b'not a committed file'):
            with self.assertRaises((ValueError,FileNotFoundError)):c.publication_check(ROOT)
    def test_scope_and_fixed_attempt(self):
        a=dict(schema='p01w-execution-admission-v1',world_execution_admitted=True,keyed_evaluation_admitted=False,e01_authorized=False,admitted_output='artifacts/p01w-001',fixed_slots=128,epochs=128,no_retries_or_replacements=True)
        for key,value in [('schema','p01q-execution-admission-v1'),('world_execution_admitted',False),('keyed_evaluation_admitted',True),('e01_authorized',True),('admitted_output','artifacts/p01q-001'),('fixed_slots',127),('epochs',0),('no_retries_or_replacements',False)]:
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate(ROOT,{},dict(a,**{key:value}),{}, {})
    def test_cell_entry_requires_admission(self):
        with self.assertRaises((ValueError,FileNotFoundError)):c.check_cell_admission(ROOT,ROOT/'invented/request.json',ROOT/'invented')




def fixture(root):
    def write(n,value):
        file=root/n;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(json.dumps(value,sort_keys=True)+'\n');return c.sha(file)
    protocol=json.loads((ROOT/'docs/p01w_protocol.json').read_bytes())
    for n in protocol['future_paths'].values():write(n,{'invented_source':n})
    requests={f'invented/{i}.json':write(f'invented/{i}.json',{'slot':i,'not_a_world':True}) for i in range(128)}
    binary=write('bin/inert',{'never_executed':True});prior=write('prior.json',{'invented':True})
    bundle='artifacts/invented';mh=write(bundle+'/manifest.json',{'invented':True})
    ih=write(bundle+'/checksums.json',{'manifest.json':mh});sh=write(bundle+'/seal.json',dict(manifest_sha256=mh,checksums_sha256=ih))
    protocol.update(saved_requests=requests,production_binaries={'bin/inert':binary},prerequisite_receipts={'prior.json':prior},source_bundles={bundle:sh})
    ph=write('docs/p01w_protocol.json',protocol)
    registration=dict(files={'docs/p01w_protocol.json':ph},inputs=requests,prior_public_receipts={'prior.json':prior})
    rh=write('docs/p01w_registration_freeze.json',registration)
    dependency=root/'runtime/dep.py';dh=write('runtime/dep.py',{'invented_dependency':True})
    interpreter=str(Path(sys.executable).resolve());ihash=c.sha(interpreter)
    receipt=dict(status='pass',controls=protocol['controls'],sources={n:c.sha(root/n) for n in protocol['future_paths'].values()},runtime_files={str(dependency):dh,interpreter:ihash})
    th=write('tests.json',receipt)
    ready=dict(implementation_complete=True,invented_controls_pass=True,world_execution_admitted=False,test_receipt='tests.json',test_receipt_sha256=th)
    ready_hash=write('docs/p01w_implementation_readiness.json',ready)
    files={str(f.relative_to(root)):c.sha(f) for f in root.rglob('*') if f.is_file() and not f.is_relative_to(root/'runtime')}
    freeze=dict(files=files,dependencies={str(dependency):dh},tools={interpreter:ihash},interpreter=interpreter,existing_bytecode_included=True,membership=[dict(root=str(root/'runtime'),files=['dep.py'])])
    fh=write('docs/p01w_execution_freeze.json',freeze)
    admission=dict(schema='p01w-execution-admission-v1',world_execution_admitted=True,keyed_evaluation_admitted=False,e01_authorized=False,
        admitted_output='artifacts/p01w-001',fixed_slots=128,epochs=128,no_retries_or_replacements=True,
        protocol_sha256=ph,registration_freeze_sha256=rh,execution_freeze_sha256=fh,readiness_sha256=ready_hash)
    write('docs/p01w_execution_admission.json',admission)
    return freeze,admission,protocol,registration

class ClosureControls(unittest.TestCase):
    def test_full_invented_closure_and_mutations(self):
        base=Path(os.environ['P01W_EXECUTION_TEST_OUT']).resolve();base.mkdir(exist_ok=False)
        outcomes=[]
        for mode in ('positive','changed','missing','extra','unlisted_bytecode','omit_bytecode_policy','omit_registered','omit_runtime','change_binary','change_readiness'):
            root=base/mode;root.mkdir();f,a,p,r=fixture(root)
            if mode=='changed':(root/'runtime/dep.py').write_text('changed')
            if mode=='missing':(root/'scripts/p01w_cell.py').unlink()
            if mode=='extra':(root/'runtime/extra.py').write_text('extra')
            if mode=='unlisted_bytecode':(root/'scripts/injected.pyc').write_bytes(b'not real bytecode')
            if mode=='omit_bytecode_policy':f['existing_bytecode_included']=False
            if mode=='omit_registered':del f['files']['invented/0.json']
            if mode=='omit_runtime':f['dependencies']={}
            if mode=='change_binary':f['files']['bin/inert']='0'*64
            if mode=='change_readiness':a['readiness_sha256']='0'*64
            if mode=='positive':self.assertEqual(c.validate(root,f,a,p,r)['status'],'pass')
            else:
                with self.subTest(mode=mode),self.assertRaises((ValueError,FileNotFoundError)):c.validate(root,f,a,p,r)
            outcomes.append(dict(mode=mode,expected='pass' if mode=='positive' else 'reject',matched=True))
        (base/'results.json').write_text(json.dumps(outcomes,sort_keys=True,indent=2)+'\n')

if __name__=='__main__':unittest.main()
