"""Gate regressions using synthetic receipts only; do not execute the registered panel."""
import copy
import unittest
import validate_p01e as runner


class OfflineGateTests(unittest.TestCase):
    def setUp(self):
        self.protocol = {'performance_inputs': {'slots': [1, 2]}, 'corruptions': ['world'],
                         'per_process': {'wall_seconds': 90},
                         'campaign': {'wall_seconds': 900, 'total_process_cpu_seconds': 600, 'artifact_bytes': 1024**3},
                         'gate': {'sum_new_leaf_cpu_at_most_fraction_of_sum_reference': .8,
                                  'observed_peak_rss_bytes_at_most': 1024**3}}
        self.pairs = [{'slot': slot, 'results': {name: {'guard': {'status': 'exited', 'child_cpu_seconds': cpu},
                        'receipt': {'status': 'pass', 'full_horizon_ap': None}} for name, cpu in [('reference', 10), ('candidate', 8)]}}
                      for slot in (1, 2)]
        self.corruptions = {'world': {'status': 'pass', 'rejections': {'reference': {}, 'candidate': {}}}}
        self.usage = {'wall_seconds': 100, 'total_process_cpu_seconds': 100, 'artifact_bytes': 100,
                      'peak_observed_rss_bytes': 100}

    def result(self, pairs=None):
        return runner.assess(self.protocol, self.pairs if pairs is None else pairs, True, self.corruptions, self.usage)

    def test_exact_twenty_percent_boundary_and_resource_reservation(self):
        self.assertTrue(self.result()['gate_pass'])
        self.pairs[0]['results']['candidate']['guard']['child_cpu_seconds'] += .0001
        self.assertFalse(self.result()['cost_gate_pass'])
        self.usage['total_process_cpu_seconds'] = 415
        self.assertTrue(runner.launch_fits(self.protocol, self.usage))
        self.usage['total_process_cpu_seconds'] += .001
        self.assertFalse(runner.launch_fits(self.protocol, self.usage))

    def test_missing_or_duplicate_input_cannot_pass_even_when_fast(self):
        self.assertFalse(self.result(self.pairs[:1])['gate_pass'])
        altered = copy.deepcopy(self.pairs)
        altered[1]['slot'] = 1
        self.assertFalse(self.result(altered)['gate_pass'])

    def test_guard_failure_endpoint_change_or_missing_rejection_cannot_pass(self):
        altered = copy.deepcopy(self.pairs)
        altered[0]['results']['candidate']['guard']['status'] = 'rss_observation_failed'
        self.assertFalse(self.result(altered)['gate_pass'])
        altered = copy.deepcopy(self.pairs)
        altered[0]['results']['candidate']['receipt']['full_horizon_ap'] = 'supported'
        self.assertFalse(self.result(altered)['gate_pass'])
        del self.corruptions['world']['rejections']['candidate']
        self.assertFalse(self.result()['gate_pass'])


if __name__ == '__main__':
    unittest.main()
