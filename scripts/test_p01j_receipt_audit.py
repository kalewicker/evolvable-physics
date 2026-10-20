"""Receipt-audit tampering regressions, without adapter execution."""
import json
import tempfile
import unittest
from pathlib import Path

import audit_p01j_readiness as auditor


class ReceiptAudit(unittest.TestCase):
    def test_valid_domain_field_change_still_breaks_registered_input_identity(self):
        registry = auditor.load(auditor.ROOT / 'docs/p01j_literal_fields.json')
        req = {'case_id': 'rule-00000', 'mode': 'rule', 'map': [1, 1, 1], 'rule_id': 0,
               'fields': {'form': 0, 'route': 0, 'kind0': 0, 'kind1': 0, 'new_kind': 1,
                          'state0': 0, 'state1': 0, 'value': 0, 'sign': 0, 'amount': 0, 'matter': 0}}
        auditor.registered_input(req, 0, registry)
        req['fields']['value'] = 1
        with self.assertRaisesRegex(ValueError, 'registered input mismatch'):
            auditor.registered_input(req, 0, registry)

    def test_tampered_bundle_is_rejected_before_output_interpretation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'payload').write_text('altered')
            (root / 'checksums.json').write_text(json.dumps({'payload': '0' * 64}))
            with self.assertRaisesRegex(ValueError, 'bundle digest mismatch'):
                auditor.audit(root)


if __name__ == '__main__':
    unittest.main()
