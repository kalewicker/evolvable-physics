"""Regression for the preserved post-run receipt-auditor arithmetic failure."""
import copy
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import unittest
import audit_p01e_v2 as receipt_audit


class ReceiptArithmeticTests(unittest.TestCase):
    def setUp(self):
        # Recorded decimal strings; sum() and repeated += differ in their float rounding.
        self.cpu = {'candidate': Decimal('57.7205979999999980'),
                    'reference': Decimal('115.8454869999999935')}
        self.assessment = {'leaf_cpu_seconds': {'candidate': 57.720598, 'reference': 115.84548699999999},
                           'candidate_to_reference_cpu_ratio': .4982550420803186}

    def test_recorded_float_summation_difference_is_only_a_display_check(self):
        result = receipt_audit.check_reported_arithmetic(self.assessment, self.cpu)
        self.assertLess(Decimal(result['sum_absolute_differences_seconds']['candidate']), Decimal('1e-12'))
        # Admission uses exact sums of recorded decimals, without this tolerance.
        self.assertLess(self.cpu['candidate'], self.cpu['reference'] * Decimal('.8'))

    def test_changed_cpu_or_ratio_still_rejected(self):
        changed = copy.deepcopy(self.assessment)
        changed['leaf_cpu_seconds']['candidate'] += .000001
        with self.assertRaisesRegex(AssertionError, 'Reported CPU sum changed'):
            receipt_audit.check_reported_arithmetic(changed, self.cpu)

    def test_optimized_python_cannot_disable_receipt_checks(self):
        result = subprocess.run([sys.executable, '-O', str(Path(receipt_audit.__file__))],
                                capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Receipt audit requires assertions', result.stderr)
        changed = copy.deepcopy(self.assessment)
        changed['candidate_to_reference_cpu_ratio'] += .000001
        with self.assertRaisesRegex(AssertionError, 'Reported CPU ratio changed'):
            receipt_audit.check_reported_arithmetic(changed, self.cpu)


if __name__ == '__main__':
    unittest.main()
