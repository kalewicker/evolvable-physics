"""Tampered registration rejection; no trajectory or transition interpreter is used."""
import copy
import unittest
import check_p01f_registration as checker


class RegistrationChecks(unittest.TestCase):
    def setUp(self):
        self.protocol = checker.load(checker.ROOT / 'docs/p01f_protocol.json')
        self.registry = checker.load(checker.ROOT / 'docs/p01f_witnesses.json')

    def test_census_seed_and_execution_permission_tampering_rejected(self):
        for field, value in [('denominator', 44), ('scheduler_seeds', [0, 1, 2, 4]), ('new_world_runs_admitted_now', True)]:
            protocol = copy.deepcopy(self.protocol)
            protocol[field] = value
            with self.assertRaises(AssertionError): checker.validate(protocol, self.registry)

    def test_incorrect_final_inventory_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry['families'][0]['expected']['root']['matter'] += 1
        with self.assertRaisesRegex(AssertionError, 'Expected matter inventory'):
            checker.validate(self.protocol, registry)

    def test_bad_created_slot_and_dropped_family_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry['families'][0]['initial']['native']['rules'][0]['ops'][1]['ends'] = [0, 2]
        with self.assertRaisesRegex(AssertionError, 'Birth slot/funding order'):
            checker.validate(self.protocol, registry)
        registry = copy.deepcopy(self.registry)
        registry['families'].pop()
        with self.assertRaisesRegex(AssertionError, 'Family census/order'):
            checker.validate(self.protocol, registry)


if __name__ == '__main__':
    unittest.main()
