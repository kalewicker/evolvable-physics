"""Independent oracle/routing and child-process bound regressions; no dynamics."""
import copy
import itertools
import json
import sys
import tempfile
import time
import unittest
from collections import Counter
from pathlib import Path

import generator_v4_fields as adapter
import validate_p01n as validator


class Readiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = validator.load(validator.ROOT / 'docs/p01n_literal_fields.json')

    def birth(self):
        return {'case_id': 'rule-unit', 'mode': 'rule', 'map': [2, 3, 1], 'state_map': [2, 0, 1], 'rule_id': 0,
                'fields': {'form': 4, 'route': 0, 'kind0': 0, 'kind1': 2, 'new_kind': 0,
                           'state0': 3, 'state1': 3, 'value': 2, 'sign': 0, 'amount': 1, 'matter': 1}}

    def test_panel_expansion_exact_and_unique(self):
        rows = list(validator.requests(self.registry))
        from audit_p01n_readiness import registered_input
        for ordinal, req in enumerate(rows):
            registered_input(req, ordinal, self.registry)
        self.assertEqual(len(rows), 17727)
        self.assertEqual(len({r['case_id'] for r in rows}), len(rows))
        self.assertEqual(Counter(r['case_id'].split('-')[0] for r in rows),
                         {'rule': 14337, 'assembly': 2916, 'invalid': 79, 'probe': 395})

    def test_shared_birth_cost_bug_cannot_pass_oracle(self):
        req = self.birth()
        result = adapter.respond(req)
        validator.check_response(req, result)
        for op_index, field, wrong in [(0, 'kind', 1), (2, 'matter', 0), (3, 'amount', 2)]:
            changed = copy.deepcopy(result)
            changed['value']['ops'][op_index][field] = wrong
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'invariant mismatch'):
                validator.check_response(req, changed)

    def test_misrouted_field_read_and_extra_output_are_rejected(self):
        req = self.birth()
        changed = adapter.respond(req)
        changed['field_reads'][0][0] = 3
        with self.assertRaisesRegex(ValueError, 'invariant mismatch'):
            validator.check_response(req, changed)
        changed = adapter.respond(req)
        changed['value']['unregistered_field'] = True
        with self.assertRaisesRegex(ValueError, 'invariant mismatch'):
            validator.check_response(req, changed)

    def test_every_literal_invalid_input_is_rejected(self):
        rows = [r for r in validator.requests(self.registry) if r['case_id'].startswith('invalid-')]
        for req in rows:
            with self.subTest(case=req['case_id']):
                validator.check_response(req, adapter.respond(req))
        req = self.birth()
        req['fields']['amount'] = True  # unused by birth but still invalid
        self.assertFalse(adapter.respond(req)['ok'])

    def test_map_reuse_across_all_initial_ids(self):
        rows = [r for r in validator.requests(self.registry)
                if r['case_id'].startswith('assembly-') and r['map'] == [2, 3, 1]][:4]
        laws = []
        for req in rows:
            response = adapter.respond(req)
            validator.check_response(req, response)
            map_reads = [r for r in response['field_reads'] if r[1] == 'child_kind_by_donor']
            self.assertEqual(map_reads, [[0, 'child_kind_by_donor', i, 3, k] for i, k in enumerate([1, 2, 0])])
            laws.append(validator.canonical(response['value']['native']['rules']))
        self.assertEqual(len(rows), 4)
        self.assertEqual(len(set(laws)), 1)

    def test_local_conditions_are_validator_only(self):
        for row in self.registry['local_conditions']:
            self.assertEqual(validator.condition_verdict(row), row['expected'])
            self.assertFalse(adapter.respond(dict(case_id='unit', mode='barrier', descriptor=row))['ok'])

    def test_missing_case_is_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cases = list(itertools.islice(validator.requests(self.registry), 2))
            (root / 'inputs').write_text(''.join(json.dumps(r) + '\n' for r in cases))
            response = json.dumps(adapter.respond(cases[0])) + '\n'
            (root / 'python').write_text(response)
            (root / 'rust').write_text(response)
            with self.assertRaisesRegex(ValueError, 'missing/extra output'):
                validator.check_streams(root / 'inputs', root / 'python', root / 'rust', time.monotonic() + 10)

    def test_output_guard_retains_bounded_prefix_and_reaps_child(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'input').touch()
            result = validator.guarded([sys.executable, '-c', "import sys; sys.stdout.write('x'*4096)"],
                root / 'input', root / 'out', root / 'err', 2, 64, time.monotonic() + 3)
            self.assertEqual(result['status'], 'output_limit')
            self.assertEqual((root / 'out').stat().st_size + (root / 'err').stat().st_size, 64)
            self.assertIsInstance(result['returncode'], int)

    def test_wall_guard_terminates_silent_child(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'input').touch()
            result = validator.guarded([sys.executable, '-c', 'import time; time.sleep(5)'],
                root / 'input', root / 'out', root / 'err', 0.1, 64, time.monotonic() + 1)
            self.assertEqual(result['status'], 'wall_limit')
            self.assertLess(result['wall_seconds'], 2)
            self.assertLess(result['returncode'], 0)

    def test_constructive_poison_fields_and_contact_preservation(self):
        for form, route in [(3, 1), (4, 0), (7, 0), (3, 0)]:
            req = self.birth()
            req['fields'].update(form=form, route=route, matter=0)
            response = adapter.respond(req)
            validator.check_response(req, response)
            self.assertEqual(len(response['field_reads']), 17)
            if (form, route) != (3, 0):
                self.assertEqual(response['value']['nodes'][0]['state'], 2)
                changed = copy.deepcopy(response)
                changed['value']['nodes'][0]['state'] = None
                with self.assertRaises(ValueError):
                    validator.check_response(req, changed)
            if form == 3:
                self.assertEqual(response['value']['ops'][0]['matter'], route)
                self.assertEqual(response['value']['nodes'][1]['kind'], 2 if route else 3)

    def test_registered_input_audit_rejects_poison_and_order_changes(self):
        from audit_p01n_readiness import registered_input
        row = next(validator.requests(self.registry))
        changed = copy.deepcopy(row)
        changed['fields']['matter'] = 1
        with self.assertRaisesRegex(ValueError, 'registered input mismatch'):
            registered_input(changed, 0, self.registry)
        with self.assertRaisesRegex(ValueError, 'registered input mismatch'):
            registered_input(row, 1, self.registry)

    def test_no_launch_after_aggregate_deadline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = validator.guarded(['/nonexistent'], root/'input', root/'out', root/'err',
                                       1, 64, time.monotonic()-1)
            self.assertEqual(result['status'], 'not_started_aggregate_deadline')
            self.assertEqual(list(root.iterdir()), [])

    def test_launch_failure_and_nonzero_exit_have_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'input').touch()
            for name, command, status in [('missing', ['/nonexistent'], 'launch_failure'),
                ('exit', [sys.executable, '-c', 'raise SystemExit(2)'], 'nonzero_exit')]:
                result = validator.guarded(command, root/'input', root/(name+'out'), root/(name+'err'),
                                           2, 64, time.monotonic()+3)
                self.assertEqual(result['status'], status)


if __name__ == '__main__':
    unittest.main()
