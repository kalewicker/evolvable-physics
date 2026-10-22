"""Invented custody files only; no sampler, keyed message or process execution."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_p01o_execution as checker
from p01o_contract import verify_closure


class ExecutionClosure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.protocol = dict(schema='p01o-v4-static-census-registration-v1', generator='p01-generator-v4',
            proposal_ids=list(range(6000, 6032)), initial_state_ids=list(range(4)), environment_denominator=128,
            epochs=0, world_execution_admitted=False)
        self.put('docs/p01o_protocol.json', self.protocol)
        self.put('scripts/mock.py', {'invented': True})
        source_hash = checker.sha(self.root/'scripts/mock.py')
        self.put('docs/p01o_registration_freeze.json', dict(files={'scripts/mock.py': source_hash}))
        self.put('target/mock', {'invented_binary': True})
        binary_hash = checker.sha(self.root/'target/mock')
        self.readiness = dict(literal_mock_gate_pass=True, sampling_admitted=False, actual_keyed_source_executed=False,
            implementation_files={'scripts/mock.py': source_hash}, rust_binary_sha256=binary_hash)
        self.put('docs/p01o_implementation_readiness.json', self.readiness)
        dep = self.root/'dependency.json'
        tool = self.root/'tool.json'
        self.put('dependency.json', {'invented_dependency': True})
        self.put('tool.json', {'invented_tool': True})
        self.put('metadata.json', {'packages': [dict(source='invented', manifest_path=str(dep))]})
        self.freeze = dict(files={'scripts/mock.py': source_hash}, dependencies={str(dep): checker.sha(dep)},
            tools={str(tool): checker.sha(tool)}, binaries={'generator-v4': dict(path='target/mock', sha256=binary_hash)},
            prior_public_receipts={}, cargo_metadata='metadata.json')
        self.put('docs/p01o_execution_freeze.json', self.freeze)
        self.admission = dict(schema='p01o-static-execution-admission-v1', sampling_admitted=True,
            world_execution_admitted=False, e01_authorized=False, fixed_cells=128, fixed_laws=32,
            admitted_output='artifacts/p01o-001', output_absolute=str(self.root/'artifacts/p01o-001'),
            keyed_sampler_evaluations_so_far=0, world_transitions_so_far=0, no_retries_or_replacements=True,
            scientific_status='untested', literal_implementation_readiness_sha256=checker.sha(self.root/'docs/p01o_implementation_readiness.json'),
            protocol_sha256=checker.sha(self.root/'docs/p01o_protocol.json'),
            registration_freeze_sha256=checker.sha(self.root/'docs/p01o_registration_freeze.json'),
            execution_freeze_sha256=checker.sha(self.root/'docs/p01o_execution_freeze.json'))
        self.put('docs/p01o_execution_admission.json', self.admission)

    def put(self, name, value):
        p = self.root/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, sort_keys=True)+'\n')

    def test_complete_invented_closure_passes_without_sampling(self):
        self.assertEqual(checker.review(self.root)['fixed_environments'], 128)
        self.assertFalse((self.root/'artifacts/p01o-001').exists())

    def test_source_dependency_tool_and_binary_tamper_rejected(self):
        for name in ('scripts/mock.py', 'dependency.json', 'tool.json', 'target/mock'):
            p = self.root/name
            original = p.read_bytes()
            p.write_bytes(original+b' ')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'identity'):
                verify_closure(self.root)
            p.write_bytes(original)

    def test_wrong_output_and_existing_attempt_rejected(self):
        self.admission['output_absolute'] += '-replacement'
        self.put('docs/p01o_execution_admission.json', self.admission)
        with self.assertRaisesRegex(ValueError, 'fixed output'):
            checker.review(self.root)
        self.admission['output_absolute'] = str(self.root/'artifacts/p01o-001')
        self.put('docs/p01o_execution_admission.json', self.admission)
        (self.root/'artifacts/p01o-001').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'no resume'):
            checker.review(self.root)

    def test_linked_freeze_and_admission_flags_rejected(self):
        for key, value in [('sampling_admitted', False), ('e01_authorized', True),
                           ('world_execution_admitted', True), ('fixed_cells', 127),
                           ('execution_freeze_sha256', '0'*64), ('protocol_sha256', '0'*64)]:
            a = dict(self.admission, **{key: value})
            self.put('docs/p01o_execution_admission.json', a)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'not admitted'):
                verify_closure(self.root)

    def test_readiness_and_dependency_manifest_coverage_rejected(self):
        self.admission['literal_implementation_readiness_sha256'] = '0'*64
        self.put('docs/p01o_execution_admission.json', self.admission)
        with self.assertRaisesRegex(ValueError, 'readiness identity'):
            checker.review(self.root)
        self.admission['literal_implementation_readiness_sha256'] = checker.sha(self.root/'docs/p01o_implementation_readiness.json')
        self.put('docs/p01o_execution_admission.json', self.admission)
        self.put('metadata.json', {'packages': [dict(source='invented', manifest_path='missing')]})
        with self.assertRaisesRegex(ValueError, 'manifest coverage'):
            checker.review(self.root)

    def test_hashes_identify_files_only(self):
        original = hashlib.sha256
        def file_hash_only(data=b''):
            if data.startswith(b'["p01-generator-v4",'):
                raise AssertionError('no keyed message evaluation')
            return original(data)
        with patch('hashlib.sha256', side_effect=file_hash_only):
            self.assertEqual(checker.review(self.root)['keyed_evaluations_so_far'], 0)


if __name__ == '__main__':
    unittest.main()
