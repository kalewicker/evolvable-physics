"""Static contract and synthetic receipts only; keyed hash evaluation forbidden."""
import copy
import unittest
from unittest.mock import patch

import check_p01k_registration as checker


class Registration(unittest.TestCase):
    def setUp(self):
        self.p = checker.load(checker.ROOT / 'docs/p01k_protocol.json')
        self.v = checker.load(checker.ROOT / 'docs/p01k_primitive_vectors.json')
        self.cells = [dict(row, status='complete', verified=True, law_digest='a' * 64,
                           type_aligned_routes=0) for row in checker.planned_cells(self.p)]

    def test_registration_validates_without_any_sha_call(self):
        with patch.object(checker.hashlib, 'sha256', side_effect=AssertionError('No keyed hashes')):
            result = checker.validate(self.p, self.v)
        self.assertEqual(result['law_cells'], 32)
        self.assertEqual(result['initial_environment_cells'], 128)
        self.assertEqual(result['requested_epochs'], 0)

    def test_fixed_unfiltered_panel_and_execution_flags(self):
        for key, value in [('proposal_ids', list(range(5001, 5033))), ('epochs', 1),
                           ('environment_denominator', 124), ('sampling_admitted_now', True),
                           ('world_execution_admitted', True), ('chemistry_continuation_gate', {'minimum': 1})]:
            p = copy.deepcopy(self.p)
            p[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                checker.validate(p, self.v)

    def test_source_initial_and_modulus_changes_rejected(self):
        self.p['draw_contract']['rule_initial'] = 1
        with self.assertRaisesRegex(ValueError, 'rule scope'):
            checker.validate(self.p, self.v)
        self.p['draw_contract']['rule_initial'] = 0
        self.p['draw_contract']['initial_domains']['scheduler'] = 2**64
        with self.assertRaisesRegex(ValueError, 'initial fields'):
            checker.validate(self.p, self.v)

    def test_repeated_addresses_are_not_independent_laws(self):
        all_keys = [key for cell in checker.planned_cells(self.p) for key in checker.addresses(self.p, cell)]
        self.assertEqual(len(all_keys), 14848)
        self.assertEqual(len({key[:-1] for key in all_keys}), 6112)
        first = checker.addresses(self.p, self.cells[0])
        second = checker.addresses(self.p, self.cells[1])
        self.assertEqual(first[:91], second[:91])
        self.assertNotEqual(first[91:], second[91:])

    def test_literal_vectors_catch_serialization_and_endian_errors(self):
        self.v['serialization'][0]['utf8'] = self.v['serialization'][0]['utf8'].replace(',', ', ', 1)
        with self.assertRaisesRegex(ValueError, 'serialization'):
            checker.validate(self.p, self.v)
        self.v = checker.load(checker.ROOT / 'docs/p01k_primitive_vectors.json')
        self.v['prefix_reduction'][2]['raw'] = 1  # little-endian interpretation
        with self.assertRaisesRegex(ValueError, 'arithmetic'):
            checker.validate(self.p, self.v)

    def test_zero_routes_does_not_change_engineering_gate_or_admit_dynamics(self):
        result = checker.assess_bookkeeping(self.p, self.cells)
        self.assertTrue(result['engineering_gate_pass'])
        self.assertEqual(result['distinct_verified_tables'], 1)  # all mock tables duplicated
        self.assertIsNone(result['chemistry_continuation_gate'])
        self.assertFalse(result['world_execution_admitted'])

    def test_positive_routes_cannot_hide_unstarted_cell(self):
        for row in self.cells:
            row['type_aligned_routes'] = 100
        self.cells[-1].update(status='unstarted', verified=False, law_digest=None)
        result = checker.assess_bookkeeping(self.p, self.cells)
        self.assertEqual(result['complete_verified_environments'], 127)
        self.assertFalse(result['engineering_gate_pass'])
        self.assertFalse(result['world_execution_admitted'])

    def test_missing_reordered_and_inconsistent_law_cells_rejected(self):
        with self.assertRaisesRegex(ValueError, 'denominator'):
            checker.assess_bookkeeping(self.p, self.cells[:-1])
        reordered = copy.deepcopy(self.cells)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        with self.assertRaisesRegex(ValueError, 'identity/order'):
            checker.assess_bookkeeping(self.p, reordered)
        self.cells[1]['law_digest'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'across initials'):
            checker.assess_bookkeeping(self.p, self.cells)

    def test_budget_drift_is_not_a_static_pass(self):
        self.p['campaign']['total_process_cpu_seconds'] = 240
        with self.assertRaisesRegex(ValueError, 'campaign budgets'):
            checker.validate(self.p, self.v)


if __name__ == '__main__':
    unittest.main()
