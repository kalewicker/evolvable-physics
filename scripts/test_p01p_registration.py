"""Registration mutation controls only; no retained table or state diagnosis."""
import copy
import hashlib
import unittest
from unittest.mock import patch
import check_p01p_registration as checker


class Registration(unittest.TestCase):
    def setUp(self):
        self.p = checker.load(checker.ROOT/'docs/p01p_protocol.json')

    def test_contract_validates_without_hashing(self):
        with patch.object(hashlib, 'sha256', side_effect=AssertionError('no field or file hashes in descriptor validation')):
            result = checker.validate(self.p)
        self.assertEqual(result['retained_rule_bodies_parsed'], 0)
        self.assertEqual(result['fixed_initial_records'], 128)

    def test_changed_panel_and_behavioral_admission_rejected(self):
        for key, value in [('proposal_ids', list(range(6001, 6033))), ('initial_ids', [False, 1, 2, 3]),
            ('epochs', 1), ('law_denominator', 1), ('sampling_admitted', True),
            ('world_execution_admitted', True), ('diagnosis_executed_now', True)]:
            p = copy.deepcopy(self.p);p[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):checker.validate(p)

    def test_cleanup_routes_and_phase_filtering_cannot_be_dropped(self):
        for key, value in [('cleanup_forms', [7]), ('child', ['newborn', 'next_birth', 'funding', 'parent_recycling'])]:
            p = copy.deepcopy(self.p);p['phases'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'ordered phases'):checker.validate(p)

    def test_orphan_and_refund_control_corruptions_rejected(self):
        for key, value in [('parent_after_recycling', [8, 4]), ('grandchild_after_cleanup', None),
                           ('total_dissipated_activation', 4)]:
            p = copy.deepcopy(self.p);p['conditional_budget_cases'][0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'ledger'):checker.validate(p)

    def test_missing_controls_and_wrong_budget_rejected(self):
        p = copy.deepcopy(self.p);p['verification_controls'].pop()
        with self.assertRaisesRegex(ValueError, 'complete groups'):checker.validate(p)
        self.p['development_limits']['output_bytes_per_tool'] *= 2
        with self.assertRaisesRegex(ValueError, 'development limits'):checker.validate(self.p)

    def test_positive_classification_cannot_be_scientific_support(self):
        self.p['reporting']['classification'][1] = 'reproduction_supported'
        with self.assertRaisesRegex(ValueError, 'reporting scope'):checker.validate(self.p)

    def test_all_cells_and_repeated_initials_are_retained(self):
        cells = checker.cells(self.p)
        self.assertEqual(len(cells), 128)
        self.assertEqual(cells[0], dict(slot=0, proposal=6000, initial=0))
        self.assertEqual(cells[-1], dict(slot=127, proposal=6031, initial=3))
        self.assertEqual(len({row['proposal'] for row in cells}), 32)

    def test_state_oracle_and_behavioral_nulls_cannot_drift(self):
        self.p['verification_policy']['state_closure_comparisons'] = 923
        with self.assertRaisesRegex(ValueError, 'state oracle census'):checker.validate(self.p)
        self.p = checker.load(checker.ROOT/'docs/p01p_protocol.json')
        self.p['reporting']['behavioral_outcomes'] = {'births': 0}
        with self.assertRaisesRegex(ValueError, 'reporting scope'):checker.validate(self.p)


if __name__ == '__main__':
    unittest.main()
