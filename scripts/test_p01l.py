"""Invented state algebra regressions. No sampler, world or native execution."""
import ast
import itertools
import unittest
from pathlib import Path
import audit_p01l as independent
import review_p01l as review


def writer(guard=None, op='SetState', value=0, kind=1):
    return dict(id=0, nodes=[dict(kind=kind, state=guard)], edges=[], absent=[],
                ops=[dict(op=op, node=0, **({'value': value} if op == 'SetState' else {'delta': value}))])


class StateTests(unittest.TestCase):
    def test_exhaustive_two_writer_algebra(self):
        schemas = [writer(g, op, v) for g in (None, 0, 1, 2)
                   for op, values in [('SetState', range(3)), ('AddState', (-1, 1))] for v in values]
        cases = [()] + [(w,) for w in schemas] + list(itertools.combinations_with_replacement(schemas, 2))
        self.assertEqual(len(schemas), 20)
        self.assertEqual(len(cases), 231)
        for writers in cases:
            for start in ([[0, 0]], [[1, 1]], [[2, 2]], [[review.LOW, review.HIGH]]):
                exact = review.closure(start, writers)
                abstract = independent.reachable(independent.project(start), writers)
                self.assertEqual(independent.project(exact), abstract)
                self.assertEqual(review.closure(exact, writers), exact)

    def test_directional_drift_and_bounds(self):
        self.assertEqual(review.closure([[2, 2]], [writer(None, 'AddState', 1)]), [[2, review.HIGH]])
        self.assertEqual(review.closure([[0, 0]], [writer(None, 'AddState', -1)]), [[review.LOW, 0]])
        self.assertEqual(review.closure([[review.HIGH, review.HIGH]], [writer(None, 'AddState', 1)]), [[review.HIGH, review.HIGH]])
        self.assertEqual(review.closure([[review.LOW, review.LOW]], [writer(None, 'AddState', -1)]), [[review.LOW, review.LOW]])

    def test_noops_missing_writers_and_guard_chains(self):
        self.assertEqual(review.closure([[0, 0]], []), [[0, 0]])
        self.assertEqual(review.closure([[0, 0]], [writer(0, value=0), writer(2, value=1)]), [[0, 0]])
        self.assertEqual(review.closure([[0, 0]], [writer(0, value=1), writer(1, value=2)]), [[0, 2]])
        self.assertFalse(review.phase_chain([[0, 0]], [1], [])['permitted'])

    def test_phase_filtering_is_directional(self):
        writers = [writer(None, 'AddState', 1)]
        self.assertTrue(review.phase_chain([[0, 0]], [1, 2], writers)['permitted'])
        self.assertFalse(review.phase_chain([[0, 0]], [2, 1], writers)['permitted'])
        # Both target predicates are individually reachable from birth, but
        # that does not prove they are reachable in the specified order.
        self.assertTrue(all(review.phase_chain([[0, 0]], [s], writers)['permitted'] for s in (1, 2)))

    def test_resource_and_missing_body_negatives(self):
        b = dict(id=0, nodes=[dict(kind=1, state=0)], edges=[], absent=[], ops=[
            dict(op='CreateNode', account=0, kind=1, state=0), dict(op='CreateEdge'), dict(op='Transfer'), dict(op='Burn')])
        f = dict(id=1, nodes=[dict(kind=1, state=0)] * 2, edges=[dict(**{'class': 'Structural'})], absent=[],
                 ops=[dict(op='Transfer', matter=0, activation=2)])
        r = review.evaluate_motif([b, f], b, funding=f, descendant=b)
        self.assertTrue(r['phased_state_permitted'])
        self.assertFalse(r['phased_state_and_material'])
        self.assertFalse(r['budget']['affordable_from_untouched_original'])
        f['ops'][0]['matter'] = 1
        r = review.evaluate_motif([b, f], b, funding=f, descendant=b)
        self.assertEqual(r['budget']['conditional_child_after_funding'], [3, 5])
        self.assertEqual(r['budget']['conditional_donor_after_funding'], [3, 2])
        rules = [dict(writer(), id=i) for i in range(8)]
        result = review.law_review(0, 'invented', rules)
        self.assertTrue(all(c['total'] == 0 for c in result['counts'].values()))

    def test_reject_unsupported_quotient_alphabet(self):
        with self.assertRaises(ValueError):
            independent.reachable({1}, [writer(3)])
        with self.assertRaises(ValueError):
            independent.reachable({1}, [writer(None, 'AddState', 2)])
        rules = [dict(writer(), id=i) for i in range(8)]
        rules[0]['nodes'][0]['state'] = 3
        with self.assertRaises(ValueError):
            review.validate_rules(rules)

    def test_entry_points_cannot_import_sampling_or_world_modules(self):
        for module in (review, independent):
            tree = ast.parse(Path(module.__file__).read_text())
            names = {n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
            names |= {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertLessEqual(names, {'hashlib', 'itertools', 'json', 'sys', 'collections', 'pathlib'})
        with self.assertRaises(RuntimeError):
            review.prohibit_processes('subprocess.Popen', ())

    def test_topology_argument_rejects_refund_and_contact_changes(self):
        edge = {'class': 'Structural', 'kind': 0, 'ends': [0, 1]}
        r = dict(id=0, nodes=[dict(kind=1, state=None)] * 2, absent=[], edges=[edge],
                 ops=[dict(op='DeleteEdge', account=0, kind=0, ends=[0, 1])])
        independent.topology_premises([r])
        r['ops'][0]['account'] = 1
        with self.assertRaises(ValueError):
            independent.topology_premises([r])
        r['ops'][0]['account'] = 0
        r['ops'][0]['op'] = 'CreateEdge'
        r['absent'] = [edge]
        with self.assertRaises(ValueError):
            independent.topology_premises([r])


if __name__ == '__main__':
    unittest.main()
