"""Contract/scope regressions for finite design review, not adapter readiness."""
import ast
import copy
import json
import unittest
from pathlib import Path
import review_generator_v4_design as review
import audit_generator_v4_design as independent


class DesignContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((review.ROOT / 'docs/generator_v4_design.json').read_bytes())

    def test_proposed_contract_has_no_execution_admission(self):
        review.verify_contract(self.spec)
        self.assertEqual(self.spec['proposal_ids'], [])
        self.assertIsNone(self.spec['execution_protocol'])

    def test_six_malformed_contracts_are_rejected(self):
        changes = [
            ('zero_structural_matter', lambda p: p['effective_overrides']['structural_transfer_3_route_1'].update(matter=0)),
            ('state_map_wrong_scope', lambda p: p['state_map'].update(scope='per_slot')),
            ('forced_body_insertion', lambda p: p.update(body_presence='insert_lifecycle')),
            ('actual_sampling_panel', lambda p: p.update(proposal_ids=[1])),
            ('changed_operation_costs', lambda p: p['unchanged_except_namespace'].remove('operation_order_and_costs')),
            ('lost_unused_field_records', lambda p: p.update(logical_field_records_per_environment=116))]
        for name, change in changes:
            with self.subTest(name=name):
                altered = copy.deepcopy(self.spec)
                change(altered)
                with self.assertRaises(ValueError):
                    review.verify_contract(altered)

    def test_review_imports_and_hash_input_are_file_only(self):
        for module in (review, independent):
            tree = ast.parse(Path(module.__file__).read_text())
            imports = {name.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for name in n.names}
            imports |= {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertLessEqual(imports, {'hashlib', 'itertools', 'json', 'sys', 'collections', 'pathlib'})
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'sha256']
            self.assertEqual(len(calls), 1)
            self.assertEqual(ast.unparse(calls[0].args[0]), 'path.read_bytes()')


if __name__ == '__main__':
    unittest.main()
