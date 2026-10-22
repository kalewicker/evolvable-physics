"""All SHA calls on v4 keyed preimages are forbidden throughout these tests."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import audit_p01o as auditor
import generator_v4 as generator
import p01o_census as runner
import p01o_static as census
from p01o_contract import ROOT, canonical, load, plans

REGISTRY = load(ROOT / 'docs/p01n_literal_fields.json')


def mock_request(cell):
    rows = [dict(form=i, route=1, kind0=0, kind1=2, new_kind=2, state0=3, state1=3,
                 value=0, sign=0, amount=0, matter=1) for i in range(8)]
    return dict(mode='assembly', map=[1, 2, 3], state_map=[2, 0, 1], rule_fields=rows, initial_id=cell['initial'],
                initial_fields=REGISTRY['initial_fields'][cell['initial']], cell=cell)


def mock_digest(preimage):
    # A literal lookup/formatting oracle, never a hash function.
    _, proposal, initial, field, index = json.loads(preimage)
    req = mock_request(dict(slot=0, proposal=proposal, initial=initial))
    if field == 'child_kind_by_donor':
        raw = req['map'][index] - 1
    elif field == 'role_state_by_kind':
        raw = req['state_map'][index]
    elif field in generator.literal.DOMAINS:
        raw = req['rule_fields'][index][field]
    elif field == 'scheduler':
        raw = req['initial_fields'][field]
    else:
        raw = req['initial_fields'][field][index]
    return f'{raw:016x}' + '0' * 48


class Implementation(unittest.TestCase):
    def setUp(self):
        original = hashlib.sha256
        def no_keyed_sha(data=b'', **kwargs):
            if data.startswith(b'["p01-generator-v4",'):
                raise AssertionError('Keyed SHA evaluation forbidden before execution freeze')
            return original(data, **kwargs)
        self.guard = patch('hashlib.sha256', side_effect=no_keyed_sha)
        self.guard.start()
        self.addCleanup(self.guard.stop)
        self.protocol = load(ROOT / 'docs/p01o_protocol.json')
        self.cell = plans(self.protocol)[0]

    def test_primitive_vectors_are_strings_and_arithmetic_only(self):
        vectors = load(ROOT / 'docs/p01o_primitive_vectors.json')
        for row in vectors['serialization']:
            self.assertEqual(generator.message(*row['arguments'][1:]).decode(), row['utf8'])
        for row in vectors['prefix_reduction']:
            self.assertEqual(generator.reduce_prefix(row['prefix_hex'], row['modulus']), row['raw'])

    def test_absent_admission_rejects_before_keyed_source(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises((OSError, ValueError)):
                generator.sample(Path(td), 0)

    def test_injected_draws_and_independent_output_reconstruction(self):
        payload = generator.mock_record(mock_request(self.cell))
        raw, mapping, states, _ = auditor.verify_payload(self.cell, payload, mock_digest)
        self.assertEqual(len(payload['draws']), 119)
        self.assertEqual(mapping, [1, 2, 3])
        report = census.law_report(mapping, states, payload['environment']['native']['rules'])
        auditor.verify_law_report(report, raw, mapping, states, payload['environment']['native']['rules'])
        self.assertTrue(report['joined_motifs'][0]['immediate_state_aligned_and_material'])
        self.assertFalse(report['child_donor_pairs'][0]['affordable_at_creation'])

    def test_wrong_preimage_modulo_or_operation_rejected(self):
        original = generator.mock_record(mock_request(self.cell))
        for change in ('preimage', 'raw', 'operation', 'draw_order', 'state_map', 'boolean_map'):
            payload = copy.deepcopy(original)
            if change == 'preimage':
                payload['draws'][0]['preimage'] += ' '
            elif change == 'raw':
                payload['draws'][0]['raw'] = 2
            elif change == 'draw_order':
                payload['draws'][3], payload['draws'][4] = payload['draws'][4], payload['draws'][3]
            elif change == 'boolean_map':
                payload['map'][0] = True
            elif change == 'state_map':
                payload['state_map'][0] = 1
            else:
                payload['environment']['native']['rules'][4]['ops'][3]['amount'] = 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                auditor.verify_payload(self.cell, payload, mock_digest)

    def test_joint_donor_state_is_stronger_than_pairwise_intersections(self):
        self.assertTrue(census.intersects(None, 0))
        self.assertTrue(census.intersects(None, 1))
        self.assertFalse(census.intersects(None, 0, 1))
        req = mock_request(self.cell)
        req['rule_fields'][3]['state0'] = 0
        req['rule_fields'][7]['state0'] = 1
        payload = generator.mock_record(req)
        lookup = {r['preimage'].encode(): r['digest'] for r in payload['draws']}
        raw, mapping, states, _ = auditor.verify_payload(self.cell, payload, lookup.__getitem__)
        report = census.law_report(mapping, states, payload['environment']['native']['rules'])
        self.assertTrue(report['joined_motifs'][0]['joint_donor_state_intersection'])
        auditor.verify_law_report(report, raw, mapping, states, payload['environment']['native']['rules'])

    def test_zero_raw_matter_is_overridden_but_missing_funding_is_not(self):
        req = mock_request(self.cell)
        req['rule_fields'][3]['matter'] = 0
        payload = generator.mock_record(req)
        report = census.law_report(payload['map'], payload['state_map'], payload['environment']['native']['rules'])
        self.assertTrue(report['joined_motifs'][0]['type_only'])
        self.assertTrue(report['joined_motifs'][0]['matter_bearing'])
        req['rule_fields'][3]['route'] = 0
        payload = generator.mock_record(req)
        report = census.law_report(payload['map'], payload['state_map'], payload['environment']['native']['rules'])
        self.assertEqual(report['birth_funding_pairs'], [])
        self.assertEqual(report['joined_motifs'], [])
        self.assertTrue(all(v['value'] is None for v in report['behavioral_outcomes'].values()))

    def test_child_as_donor_and_type_closure_are_not_guaranteed(self):
        req = mock_request(self.cell)
        req['map'] = [2, 3, 1]
        payload = generator.mock_record(req)
        report = census.law_report(payload['map'], payload['state_map'], payload['environment']['native']['rules'])
        self.assertFalse(report['child_donor_pairs'][0]['kind_match'])
        self.assertTrue(report['type_paths'][0]['missing_donor'])

    def test_reservations_and_stream_caps(self):
        usage = dict(wall_seconds=0, total_process_cpu_seconds=0, artifact_bytes=0)
        self.assertTrue(runner.launch_fits(self.protocol, usage, 'independent_audit'))
        for field, value in [('wall_seconds', 271), ('total_process_cpu_seconds', 61), ('artifact_bytes', 1073741824)]:
            with self.subTest(field=field):
                self.assertFalse(runner.launch_fits(self.protocol, dict(usage, **{field: value}), 'independent_audit'))
        limits = runner.stream_limits(self.protocol, 'rust_generation')
        self.assertEqual(limits['stdout_bytes'] + limits['stderr_bytes'], 1048576)
        self.assertEqual(limits['rss_bytes'], 134217728)

    def test_all_128_mock_cells_pipeline_and_independent_census(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            manifest = dict(rows=runner.manifest_rows(self.protocol), analysis={}, execution_status='running')
            def save():
                (bundle / 'manifest.json').write_text(canonical(manifest))
            def stage(name, row):
                directory = bundle / ('analysis' if row is None else 'runs/' + str(row['slot'])) / name
                directory.mkdir(parents=True)
                if row is not None:
                    output = generator.mock_record(mock_request({k: row[k] for k in ('slot', 'proposal', 'initial')}))
                    row['stages'][name] = {'status': 'exited', 'mock': True}
                else:
                    output = census.panel_report(bundle) if name == 'static_report' else auditor.audit_panel(bundle, self.protocol, mock_digest)
                    manifest['analysis'][name] = {'status': 'exited', 'mock': True}
                (directory / 'stdout.bin').write_text(canonical(output))
                return directory
            save()
            runner.execute_pipeline(bundle, self.protocol, manifest, stage, save)
            manifest['execution_status'] = 'complete'
            summary = runner.summarize(self.protocol, manifest, dict(wall_seconds=0, total_process_cpu_seconds=0, artifact_bytes=0))
            self.assertTrue(summary['engineering_gate_pass'])
            self.assertEqual(summary['complete_environments'], 128)
            self.assertEqual(summary['distinct_observed_tables'], 1)
            self.assertIsNone(summary['chemistry_continuation_gate'])
            report_path = bundle / 'analysis/static_report/stdout.bin'
            original = load(report_path)
            for key, value in [('law_denominator', 31), ('environment_denominator', 127),
                               ('scientific_status', 'supported'), ('world_transitions', False)]:
                corrupted = dict(original, **{key: value})
                report_path.write_text(canonical(corrupted))
                with self.subTest(field=key), self.assertRaisesRegex(ValueError, 'census scope'):
                    auditor.audit_panel(bundle, self.protocol, mock_digest)
            report_path.write_text(canonical(original))
            manifest['rows'].pop()
            save()
            with self.assertRaisesRegex(ValueError, 'complete manifest'):
                auditor.audit_panel(bundle, self.protocol, mock_digest)

    def test_stage_failure_does_not_launch_later_cells(self):
        with tempfile.TemporaryDirectory() as td:
            manifest = dict(rows=runner.manifest_rows(self.protocol), analysis={}, execution_status='running')
            calls = []
            def stage(name, row):
                calls.append((name, row['slot']))
                raise runner.ReservationStop('mock budget')
            with self.assertRaises(runner.ReservationStop):
                runner.execute_pipeline(Path(td), self.protocol, manifest, stage, lambda: None)
            self.assertEqual(calls, [('rust_generation', 0)])
            self.assertEqual(len(manifest['rows']), 128)
            self.assertTrue(all(r['status'] == 'pending' for r in manifest['rows'][1:]))


if __name__ == '__main__':
    unittest.main()
