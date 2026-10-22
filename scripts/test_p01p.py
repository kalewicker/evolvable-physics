"""Invented descriptors and arithmetic only; no retained inputs or world execution."""
import ast
import copy
import hashlib
import itertools
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import audit_p01p as independent
import review_p01p as review


def writer(guard=None, op='SetState', value=0, kind=1):
    return dict(id=0, nodes=[dict(kind=kind, state=guard)], edges=[], absent=[],
        ops=[dict(op=op, node=0, **({'value': value} if op == 'SetState' else {'delta': value}))])


def fixture():
    rules = [dict(id=i, nodes=[dict(kind=3, state=None)], edges=[], absent=[],
        ops=[dict(op='Burn', node=0, amount=1)]) for i in range(8)]
    structural = {'class': 'Structural', 'kind': 0, 'ends': [0, 1]}
    rules[0] = dict(id=0, nodes=[dict(kind=1, state=0)], edges=[], absent=[], ops=[
        dict(op='CreateNode', account=0, kind=1, state=0), dict(op='CreateEdge', account=0, kind=0, ends=[0, 1]),
        {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1}, dict(op='Burn', node=0, amount=1)])
    rules[1] = dict(id=1, nodes=[dict(kind=1, state=0), dict(kind=1, state=0)], edges=[structural], absent=[],
        ops=[{'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1}])
    rules[2] = dict(id=2, nodes=[dict(kind=1, state=0), dict(kind=1, state=0)], edges=[structural], absent=[], ops=[
        dict(op='DeleteEdge', account=0, kind=0, ends=[0, 1]), dict(op='DeleteNode', node=1, recipient=0), dict(op='Burn', node=0, amount=1)])
    rules[3] = dict(id=3, nodes=[dict(kind=1, state=0), dict(kind=1, state=0)], edges=[structural], absent=[],
        ops=[dict(op='DeleteEdge', account=0, kind=0, ends=[0, 1])])
    return rules


class StateAndBranchTests(unittest.TestCase):
    def setUp(self):
        original = hashlib.sha256
        def no_keyed(data=b'', **kwargs):
            if data.startswith(b'["p01-generator-v4",'):
                raise AssertionError('keyed hashing forbidden')
            return original(data, **kwargs)
        self.patch = patch('hashlib.sha256', side_effect=no_keyed)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.rules = fixture()

    def evaluate(self, cleanup=3, **assumptions):
        r = self.rules
        return review.evaluate(r, r[0], r[1], r[0], r[2], r[cleanup], **assumptions)

    def test_924_independent_state_closure_comparisons(self):
        schemas = [writer(g, op, v) for g in (None, 0, 1, 2)
            for op, values in [('SetState', range(3)), ('AddState', (-1, 1))] for v in values]
        cases = [()] + [(w,) for w in schemas] + list(itertools.combinations_with_replacement(schemas, 2))
        self.assertEqual((len(schemas), len(cases)), (20, 231))
        comparisons = 0
        for writers in cases:
            for start in ([[0, 0]], [[1, 1]], [[2, 2]], [[review.LOW, review.HIGH]]):
                actual = review.closure(start, writers)
                self.assertEqual(independent.project(actual), independent.reachable(independent.project(start), writers))
                self.assertEqual(review.closure(actual, writers), actual)
                comparisons += 1
        self.assertEqual(comparisons, 924)

    def test_drift_bounds_and_phase_order(self):
        up = [writer(None, 'AddState', 1)]
        self.assertEqual(review.closure([[2, 2]], up), [[2, review.HIGH]])
        self.assertEqual(review.closure([[review.HIGH, review.HIGH]], up), [[review.HIGH, review.HIGH]])
        self.assertEqual(review.closure([[review.LOW, review.LOW]], [writer(None, 'AddState', -1)]), [[review.LOW, review.LOW]])
        self.assertTrue(review.phase_chain([[0, 0]], [1, 2], up)['permitted'])
        self.assertFalse(review.phase_chain([[0, 0]], [2, 1], up)['permitted'])
        self.assertEqual(review.closure([[0, 0]], [writer(0, value=1), writer(1, value=2)]), [[0, 2]])

    def test_all_four_ledgers_have_independent_refund_and_conservation_checks(self):
        protocol = review.load(review.ROOT/'docs/p01p_protocol.json')
        for expected in protocol['conditional_budget_cases']:
            amount, cleanup = expected['activation_per_funding'], expected['cleanup_form']
            record = review.ledger(1, amount, cleanup)
            self.assertEqual({k: record[k] for k in expected if k != 'name'}, {k: v for k, v in expected.items() if k != 'name'})
            independent.ledger_check(record, 1, amount, cleanup)
            corrupted = copy.deepcopy(record);corrupted['parent_after_recycling'][0] += 1
            with self.assertRaisesRegex(ValueError, 'ledger'):independent.ledger_check(corrupted, 1, amount, cleanup)
            remaining = 0 if record['grandchild_after_cleanup'] is None else record['grandchild_after_cleanup'][1]
            self.assertEqual(record['parent_after_recycling'][1]+remaining+record['total_dissipated_activation'], 8)

    def test_edge_cleanup_keeps_orphan_and_recycle_cleanup_refunds_it(self):
        edge, recycle = self.evaluate(3), self.evaluate(2)
        self.assertEqual(edge['budget']['grandchild_after_cleanup'], [1, 1])
        self.assertIsNone(recycle['budget']['grandchild_after_cleanup'])
        self.assertEqual(edge['budget']['parent_after_recycling'], [6, 4])
        self.assertEqual(recycle['budget']['parent_after_recycling'], [8, 4])
        self.assertTrue(edge['topology']['grandchild_survives'])
        self.assertFalse(recycle['topology']['grandchild_survives'])
        for k, record in [(self.rules[3], edge), (self.rules[2], recycle)]:
            independent.audit_row(self.rules, record, self.rules[0], self.rules[1], self.rules[0], self.rules[2], k)

    def test_leaf_and_creation_edge_negatives_are_conditional(self):
        self.assertEqual(self.evaluate(2, grandchild_leaf=False)['classification'], 'local_condition_excluded')
        self.assertEqual(self.evaluate(3, grandchild_leaf=False)['classification'], 'permitted_by_abstraction')
        self.assertEqual(self.evaluate(3, creation_edge_present=False)['classification'], 'local_condition_excluded')
        self.assertEqual(self.evaluate(3, child_extra_incidence=True)['classification'], 'local_condition_excluded')
        self.assertFalse(self.evaluate()['topology']['measured_world_topology'])

    def test_wrong_cleanup_kind_and_state_fail_separately(self):
        self.rules[3]['nodes'][1]['kind'] = 2
        row = self.evaluate()
        self.assertIn('kind_mismatch:cleanup', row['reasons'])
        self.rules = fixture();self.rules[3]['nodes'][0]['state'] = 1
        row = self.evaluate()
        self.assertIn('state_phase_exclusion:child', row['reasons'])

    def test_zero_matter_counterfactual_and_missing_bodies(self):
        self.rules[1]['ops'][0]['matter'] = 0
        row = self.evaluate()
        self.assertTrue(row['phased_state_permitted'])
        self.assertFalse(row['phased_state_and_material'])
        self.assertFalse(row['budget']['funded_birth_affordable'])
        self.assertIsNone(row['budget']['parent_after_recycling'])
        rules = [dict(id=i, nodes=[dict(kind=3, state=None)], edges=[], absent=[], ops=[dict(op='Burn', node=0, amount=1)]) for i in range(8)]
        law = review.law_review(0, 'invented', [1, 2, 3], [0, 1, 2], rules)
        self.assertEqual(law['missing_body_roles'], ['birth', 'funding', 'recycling', 'cleanup'])
        self.assertTrue(all(v['total'] == 0 for v in law['counts'].values()))

    def test_reused_bodies_and_equal_kinds_keep_distinct_roles(self):
        row = self.evaluate(2)
        self.assertEqual([row[k] for k in ('birth', 'next_birth', 'recycling', 'cleanup')], [0, 0, 2, 2])
        self.assertEqual(row['classification'], 'permitted_by_abstraction')
        self.assertEqual(set(row['paths']), {'parent', 'child', 'grandchild'})
        self.assertIsNone(row['executable_reachability'])

    def test_initial_absence_excludes_only_the_specified_founder(self):
        row = self.evaluate()
        absent = review.founder_check(row, 0, False)
        self.assertEqual(absent['scope'], 'specified_original_founder_only')
        self.assertEqual(absent['reason'], 'original_seed_exclusion_for_this_founder_only')
        self.assertEqual(row['classification'], 'permitted_by_abstraction')

    def test_alphabet_and_refund_tampering_rejected(self):
        review.validate_rules(self.rules, [1, 2, 3], [0, 1, 2])
        independent.validate_native(self.rules, [1, 2, 3], [0, 1, 2])
        for w in [writer(3), writer(None, 'AddState', 2), writer(False)]:
            with self.assertRaises(ValueError):independent.reachable({1}, [w])
        self.rules[2]['ops'][0]['account'] = 1
        with self.assertRaises(ValueError):independent.topology_premises(self.rules)
        with self.assertRaises(ValueError):review.validate_rules(self.rules, [1, 2, 3], [0, 1, 2])

    def test_independent_row_verdict_and_trace_corruption_rejected(self):
        row = self.evaluate()
        for mode in ('classification', 'trace', 'identity', 'boolean'):
            bad = copy.deepcopy(row)
            if mode == 'classification':bad['classification'] = 'reproduction_supported'
            elif mode == 'trace':bad['paths']['child']['phases'][0]['accepted'] = []
            elif mode == 'identity':bad['cleanup'] = 5
            else:bad['kind_match'] = 1
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                independent.audit_row(self.rules, bad, self.rules[0], self.rules[1], self.rules[0], self.rules[2], self.rules[3])

    def test_tools_cannot_import_generators_or_launch_processes(self):
        allowed = {'hashlib', 'itertools', 'json', 'sys', 'time', 'collections', 'pathlib'}
        for module in (review, independent):
            tree = ast.parse(Path(module.__file__).read_text())
            imports = {a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            imports |= {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertLessEqual(imports, allowed)
            with self.assertRaises(RuntimeError):module.prohibit_processes('subprocess.Popen', ())

    def test_limits_emit_bounded_failed_receipts(self):
        for module in (review, independent):
            with tempfile.TemporaryDirectory() as td:
                a = module.Attempt(Path(td)/'failure')
                a.start = time.monotonic()-121
                with self.assertRaises(ValueError):a.check()
                result = a.finish(dict(status='fail', error='invented deadline failure'))
                self.assertEqual(result['status'], 'fail')
                completion = module.load(a.out/'completion.json')
                self.assertEqual(completion['output_bytes_including_completion'], sum(p.stat().st_size for p in a.out.rglob('*') if p.is_file()))
            with tempfile.TemporaryDirectory() as td:
                a = module.Attempt(Path(td)/'bytes');a.cap = 1048576+100
                with self.assertRaises(ValueError):a.raw('oversized', b'x'*1000)
                a.finish(dict(status='fail', error='invented byte failure'))


if __name__ == '__main__':
    unittest.main()
