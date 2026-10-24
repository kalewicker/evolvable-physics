"""Retained invented fixtures, filesystem spies and independent-auditor mutations."""
import ast
import copy
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
import p01s_readiness as r
import audit_p01s as a
from p01s_accounting import Ledger, terminal


class Recovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=Path(os.environ['P01S_TEST_OUT']);cls.out.mkdir(parents=True,exist_ok=False)
        cls.declared=r.packet()
        # Persist authored descriptors before executing controls.
        (cls.out/'packet.json').write_bytes(r.raw(cls.declared))
        cls.records=r.run_suite(cls.out/'fixtures',cls.declared)
        (cls.out/'results.json').write_bytes(r.raw(cls.records))

    def test_all_controls_independent_oracle(self):
        result=a.verify_results(self.records,self.declared,self.out/'fixtures')
        self.assertEqual(result['controls'],24)
        self.assertEqual(result['terminal_rows'],512)

    def test_request_mutation_rejected(self):
        records=copy.deepcopy(self.records)
        records[0]['cases'][0]['result']['request']['initial']['native']['world']['resource']=8
        with self.assertRaises(ValueError):a.verify_results(records,self.declared,self.out/'fixtures')

    def test_counter_mutation_rejected(self):
        records=copy.deepcopy(self.records);records[10]['cases'][0]['counters']['stat_calls']+=1
        with self.assertRaises(ValueError):a.verify_results(records,self.declared,self.out/'fixtures')

    def test_inventory_mutation_rejected(self):
        records=copy.deepcopy(self.records);records[10]['cases'][0]['files']['a']['sha256']='0'*64
        with self.assertRaises(ValueError):a.verify_results(records,self.declared,self.out/'fixtures')

    def test_missing_control_rejected(self):
        with self.assertRaises(ValueError):a.verify_results(self.records[:-1],self.declared,self.out/'fixtures')

    def test_terminal_status_mutation_rejected(self):
        records=copy.deepcopy(self.records);records[18]['cases'][0]['terminal']['rows'][127]['status']='complete'
        with self.assertRaises(ValueError):a.verify_results(records,self.declared,self.out/'fixtures')

    def test_budget_has_no_filesystem_calls(self):
        ledger=Ledger(self.out/'forbidden-filesystem')
        with patch('os.stat',side_effect=RuntimeError('stat forbidden')),patch('os.lstat',side_effect=RuntimeError('lstat forbidden')),patch('os.scandir',side_effect=RuntimeError('scan forbidden')),patch('builtins.open',side_effect=RuntimeError('open forbidden')),patch('io.open',side_effect=RuntimeError('io open forbidden')),patch('os.open',side_effect=RuntimeError('os open forbidden')):
            for _ in range(100):ledger.budget()
        self.assertEqual(ledger.counts['budget_polls'],100)

    def test_terminal_no_scan_and_preserves_io_error(self):
        ledger=Ledger(self.out/'terminal-no-scan')
        with patch('os.scandir',side_effect=RuntimeError('scan forbidden')):
            result=terminal(ledger,'first failure',write_failure=True)
        self.assertEqual(result['first_error'],'first failure')
        self.assertEqual(result['terminal_receipt'],'missing')
        self.assertEqual(len(result['rows']),128)
        self.assertEqual(ledger.counts['output_full_scans'],1)

    def test_partial_os_write_error_accounted(self):
        ledger=Ledger(self.out/'actual-os-error')
        original=os.write;calls=[]
        def fail(fd,data):
            if calls:raise OSError('actual injected syscall error')
            calls.append(True);return original(fd,data[:2])
        with patch('os.write',side_effect=fail):
            with self.assertRaises(OSError):ledger.write('partial',b'abcdef')
        self.assertEqual(ledger.total,2)
        self.assertEqual((ledger.root/'partial').read_bytes(),b'ab')
        self.assertTrue(ledger.reconcile())

    def test_stage_failure_cannot_be_retried(self):
        ledger=Ledger(self.out/'stage-no-retry');ledger.declare_stage('s',['a'],4)
        (ledger.root/'s'/'bad').write_text('x')
        with self.assertRaises(ValueError):ledger.reconcile_stage('s')
        with self.assertRaises(ValueError):ledger.reconcile_stage('s')
        self.assertEqual(ledger.counts['stage_reconciliations'],1)
        self.assertEqual(ledger.reserved,4)

    def test_no_old_runtime_or_process_imports(self):
        paths=json.loads((r.ROOT/'docs/p01s_protocol.json').read_bytes())['future_paths']
        for n in paths.values():
            tree=ast.parse((r.ROOT/n).read_text())
            imports=[]
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
                if isinstance(node,ast.ImportFrom):imports.append(node.module or '')
            self.assertFalse(any(x in ('subprocess','campaign','generator_v4','p01q_cell','p01q_campaign') for x in imports))
            if n==paths['audit']:self.assertFalse(any(x.startswith('p01s_') for x in imports))

    def test_relative_launch_path_fixture(self):
        relative=(self.out/'relative-path-case').relative_to(Path.cwd())
        case=r.accounting_case(23,'absolute',relative)
        self.assertTrue(case['rejected'])
        self.assertFalse((self.out/'relative-path-case'/'absolute').exists())

    def test_process_guard(self):
        for event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn'):
            with self.assertRaises(RuntimeError):r.prohibit(event,())

if __name__=='__main__':unittest.main()
