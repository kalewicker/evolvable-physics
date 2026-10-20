"""Registration tamper checks on descriptors only; no sampler or world imports."""
import ast
import copy
import unittest

import check_p01j_registration as checker


class Registration(unittest.TestCase):
    def setUp(self):
        self.p = checker.load(checker.ROOT / 'docs/p01j_protocol.json')
        self.r = checker.load(checker.ROOT / 'docs/p01j_literal_fields.json')

    def test_complete_descriptor_census_and_slot_ids(self):
        result = checker.validate(self.p, self.r)
        self.assertEqual(result['rule_field_case_descriptors'], 11664)
        self.assertEqual(result['assembly_case_descriptors'], 972)
        rows = list(checker.rule_descriptors(self.r))
        self.assertEqual(rows[0], {'ordinal': 0, 'map_index': 0, 'donor_raw': 0,
            'variant_index': 0, 'state_pair_index': 0, 'rule_id': 0})
        self.assertEqual(rows[-1], {'ordinal': 11663, 'map_index': 26, 'donor_raw': 2,
            'variant_index': 8, 'state_pair_index': 15, 'rule_id': 7})

    def test_no_sampling_execution_or_panel_drift(self):
        for key, value in [('proposal_ids', [5000]), ('law_sampling_admitted', True),
                           ('world_execution_admitted', True), ('e01_authorized', True),
                           ('literal_field_validation_executed', True)]:
            p = copy.deepcopy(self.p)
            p[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                checker.validate(p, self.r)
        self.p['panels']['rule_field_cases'] -= 1
        with self.assertRaisesRegex(ValueError, 'denominators'):
            checker.validate(self.p, self.r)

    def test_map_removal_duplication_and_boolean_coercion_rejected(self):
        for change in ('remove', 'duplicate', 'boolean'):
            r = copy.deepcopy(self.r)
            if change == 'remove':
                r['maps'].pop()
            elif change == 'duplicate':
                r['maps'][1] = r['maps'][0]
            else:
                r['maps'][0][0] = True
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'maps'):
                checker.validate(self.p, r)

    def test_contact_route_and_operation_order_cannot_be_collapsed(self):
        for field, value in [('route', 1), ('ops', ['Burn', 'Transfer'])]:
            r = copy.deepcopy(self.r)
            r['variants'][3][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'variants|shapes'):
                checker.validate(self.p, r)

    def test_wildcard_and_law_initial_routing_remain_fixed(self):
        self.r['raw_state_pairs'].pop()
        with self.assertRaisesRegex(ValueError, 'state pairs'):
            checker.validate(self.p, self.r)
        self.r = checker.load(checker.ROOT / 'docs/p01j_literal_fields.json')
        self.p['assembly_expansion']['state0'] = '(slot + rotation + initial) % 4'
        with self.assertRaisesRegex(ValueError, 'assembly expansion'):
            checker.validate(self.p, self.r)

    def test_incoming_kind_coherence_does_not_admit_child_donor(self):
        row = next(b for b in self.r['barriers'] if b['name'] == 'child_donor_absent')
        self.assertEqual(checker.barrier_verdict(row), [True, True, True, False, True, False])
        row['expected'][3] = True
        with self.assertRaisesRegex(ValueError, 'child_donor_absent'):
            checker.validate(self.p, self.r)

    def test_states_and_material_are_separate_predicates(self):
        cases = {b['name']: b for b in self.r['barriers']}
        no_matter = checker.barrier_verdict(cases['funding_has_no_matter'])
        wrong_donor_state = checker.barrier_verdict(cases['child_donor_state_mismatch'])
        wrong_funding_state = checker.barrier_verdict(cases['funding_state_mismatch'])
        self.assertEqual(no_matter, [True, True, True, True, False, True])
        self.assertEqual(wrong_donor_state, [True, True, True, True, True, False])
        self.assertEqual(wrong_funding_state, [True, True, True, True, False, True])
        cases['funding_has_no_matter']['transfer_matter'] = 1
        with self.assertRaisesRegex(ValueError, 'funding_has_no_matter'):
            checker.validate(self.p, self.r)

    def test_ignored_fields_and_invalid_boundaries_cannot_be_weakened(self):
        self.r['ignored_field_probes'].pop()
        with self.assertRaisesRegex(ValueError, 'ignored-field'):
            checker.validate(self.p, self.r)
        self.r = checker.load(checker.ROOT / 'docs/p01j_literal_fields.json')
        self.r['invalid_inputs'][-2]['value'] = 2**64 - 2
        with self.assertRaisesRegex(ValueError, 'invalid boundaries'):
            checker.validate(self.p, self.r)

    def test_checker_has_only_standard_library_imports(self):
        tree = ast.parse((checker.ROOT / 'scripts/check_p01j_registration.py').read_text())
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                modules.add(node.module)
        self.assertEqual(modules, {'hashlib', 'itertools', 'json', 'sys', 'collections', 'pathlib'})
        self.assertNotIn('subprocess', modules)


if __name__ == '__main__':
    unittest.main()
