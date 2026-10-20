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

import generator_v3_fields as adapter
import validate_p01j as validator


class Readiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = validator.load(validator.ROOT / 'docs/p01j_literal_fields.json')

    def birth(self):
        return {'case_id': 'rule-unit', 'mode': 'rule', 'map': [2, 3, 1], 'rule_id': 0,
                'fields': {'form': 4, 'route': 0, 'kind0': 0, 'kind1': 2, 'new_kind': 0,
                           'state0': 3, 'state1': 3, 'value': 2, 'sign': 0, 'amount': 1, 'matter': 1}}

    def test_panel_expansion_exact_and_unique(self):
        rows = list(validator.requests(self.registry))
        self.assertEqual(len(rows), 12671)
        self.assertEqual(len({r['case_id'] for r in rows}), len(rows))
        self.assertEqual(Counter(r['case_id'].split('-')[0] for r in rows),
                         {'rule': 11664, 'assembly': 972, 'barrier': 8, 'invalid': 12, 'probe': 15})

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
                if r['mode'] == 'assembly' and r['map'] == [2, 3, 1]][:4]
        laws = []
        for req in rows:
            response = adapter.respond(req)
            validator.check_response(req, response)
            map_reads = [r for r in response['field_reads'] if r[1] == 'child_kind_by_donor']
            self.assertEqual(map_reads, [[0, 'child_kind_by_donor', i, 3, k] for i, k in enumerate([1, 2, 0])])
            laws.append(validator.canonical(response['value']['native']['rules']))
        self.assertEqual(len(rows), 4)
        self.assertEqual(len(set(laws)), 1)

    def test_local_barriers_match_literal_expectations(self):
        for row in self.registry['barriers']:
            req = {'case_id': 'barrier-' + row['name'], 'mode': 'barrier', 'descriptor': row}
            validator.check_response(req, adapter.respond(req))

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


if __name__ == '__main__':
    unittest.main()
