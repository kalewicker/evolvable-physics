"""Static descriptor tamper tests; no adapter, rule or world construction."""
import ast
import copy
import unittest
import check_p01n_registration as check


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.p = check.load(check.ROOT / 'docs/p01n_protocol.json')
        self.r = check.load(check.ROOT / 'docs/p01n_literal_fields.json')

    def test_fixed_descriptor_counts_and_continuing_slot_ids(self):
        result = check.validate(self.p, self.r)
        self.assertEqual(result['panels']['adapter_requests'], 17727)
        self.assertEqual(result['expected_successful_field_records_per_adapter'], 597448)
        rows = list(check.rule_descriptors())
        self.assertEqual(rows[6560]['panel'], 'constructive')
        self.assertEqual(rows[6561]['panel'], 'unchanged')
        self.assertEqual(rows[-1]['ordinal'], 14336)
        self.assertEqual(rows[-1]['rule_id'], 0)

    def test_no_sampling_world_or_early_validation_admission(self):
        for key, value in [('proposal_ids', [1]), ('sampling_admitted', True), ('world_execution_admitted', True),
                           ('literal_validation_executed', True), ('e01_authorized', True)]:
            p = copy.deepcopy(self.p)
            p[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                check.validate(p, self.r)

    def test_map_removal_duplication_and_boolean_labels_rejected(self):
        for field in ('type_maps', 'state_maps'):
            for mode in ('remove', 'duplicate', 'boolean'):
                r = copy.deepcopy(self.r)
                if mode == 'remove':
                    r[field].pop()
                elif mode == 'duplicate':
                    r[field][1] = r[field][0]
                else:
                    r[field][0][0] = True
                with self.subTest(field=field, mode=mode), self.assertRaises(ValueError):
                    check.validate(self.p, r)

    def test_poisoned_raw_fields_and_unchanged_contact_semantics_fixed(self):
        self.p['constructive_expansion']['matter'] = 1
        with self.assertRaisesRegex(ValueError, 'poison'):
            check.validate(self.p, self.r)
        self.p = check.load(check.ROOT / 'docs/p01n_protocol.json')
        self.r['variants'][3]['edge_class'] = 'Structural'
        with self.assertRaisesRegex(ValueError, 'variants'):
            check.validate(self.p, self.r)

    def test_cross_initial_rules_may_not_depend_on_initial_id(self):
        self.p['assembly_expansion']['rotation'] = '(state_map_index + initial_id) % 9'
        with self.assertRaisesRegex(ValueError, 'assembly'):
            check.validate(self.p, self.r)

    def test_ignored_probes_and_all_raw_reads_are_required(self):
        self.r['ignored_field_probes'].pop()
        with self.assertRaisesRegex(ValueError, 'ignored-field'):
            check.validate(self.p, self.r)
        self.r = check.load(check.ROOT / 'docs/p01n_literal_fields.json')
        self.p['interface']['assembly_field_records'] = 116
        with self.assertRaisesRegex(ValueError, 'recording'):
            check.validate(self.p, self.r)

    def test_invalid_ignored_field_bounds_and_boolean_cases_fixed(self):
        for mode in ('missing', 'weaken', 'bool_to_int'):
            r = copy.deepcopy(self.r)
            if mode == 'missing':
                r['invalid_inputs'].pop()
            elif mode == 'weaken':
                r['invalid_inputs'][1]['value'] = 7
            else:
                r['invalid_inputs'][2]['value'] = 1
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'invalid'):
                check.validate(self.p, r)

    def test_local_negatives_remain_separate_and_counterfactual(self):
        cases = {c['name']: c for c in self.r['local_conditions']}
        self.assertFalse(check.condition_verdict(cases['state_only_control'])[6])
        self.assertFalse(check.condition_verdict(cases['material_only_control'])[4])
        self.assertTrue(check.condition_verdict(cases['material_only_control'])[6])
        for name, index in [('unfunded_newborn', 7), ('nonleaf_after_descendant', 8), ('creation_edge_missing', 9), ('three_kind_full_role_cycle', 10)]:
            r = copy.deepcopy(self.r)
            next(c for c in r['local_conditions'] if c['name'] == name)['expected'][index] = True
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'verdict'):
                check.validate(self.p, r)

    def test_denominators_paths_and_case_order_fixed(self):
        for target in ('panels', 'future_paths', 'case_ids'):
            p = copy.deepcopy(self.p)
            p[target] = {}
            with self.subTest(target=target), self.assertRaises(ValueError):
                check.validate(p, self.r)

    def test_checker_imports_and_sha_inputs_are_file_only(self):
        tree = ast.parse((check.ROOT / 'scripts/check_p01n_registration.py').read_text())
        imports = {alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names}
        imports |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {'hashlib', 'itertools', 'json', 'sys', 'collections', 'pathlib'})
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'sha256']
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.unparse(calls[0].args[0]), 'path.read_bytes()')


if __name__ == '__main__':
    unittest.main()
