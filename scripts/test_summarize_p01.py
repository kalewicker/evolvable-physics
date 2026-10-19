"""Reporting regressions: unfinished slots stay in the denominator and cannot gain AP."""
import copy
import json
import unittest
import campaign
import summarize_p01


class PilotSummaryTests(unittest.TestCase):
    def setUp(self):
        self.protocol=json.loads((campaign.ROOT/'docs/p01_protocol.json').read_text())
        self.rows=campaign.ledger(self.protocol)
        for row in self.rows:row['status']='not_started_campaign_budget'

    def complete(self,slot,label):
        self.rows[slot].update(status='verified_complete',coverage='complete',full_horizon_ap=label,
            observed_epochs=1000,events=2,applicable_candidates=3,stages={'audit':{'wall_seconds':1,'child_cpu_seconds':.5}})

    def test_all_512_states_and_128_laws_remain_partitioned(self):
        self.complete(0,'supported');self.complete(1,'inconclusive')
        self.rows[2].update(status='verified_censored',coverage='censored_prefix',observed_epochs=8,
                            events=1,applicable_candidates=2,stages={'native':{'wall_seconds':1}})
        self.rows[3].update(status='audit_child_failed',stages={'native':{'wall_seconds':1}})
        for slot in range(4,8):self.complete(slot,'not_supported')
        result=summarize_p01.describe({'protocol':self.protocol,'runs':self.rows})
        self.assertEqual(result['endpoint_counts_all_512'],{'supported':1,'not_supported':4,'inconclusive':1,
                                                          'censored':1,'unmeasured_started':1,'not_started':504})
        self.assertEqual(result['law_outcomes_all_128'],{'at_least_one_verified_supported_state':1,'all_four_not_supported':1,
            'inconclusive_without_verified_support':0,'censored_or_unmeasured_without_verified_support':126})
        self.assertEqual(result['independently_verified_prefix_epochs'],6008)

    def test_missing_slot_or_unaudited_positive_is_rejected(self):
        with self.assertRaises(AssertionError):summarize_p01.describe({'protocol':self.protocol,'runs':self.rows[:-1]})
        self.rows[0]['full_horizon_ap']='supported'
        with self.assertRaises(AssertionError):summarize_p01.describe({'protocol':self.protocol,'runs':self.rows})

    def test_unreadable_failed_native_summary_stays_unmeasured(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            bundle=Path(temp);directory=bundle/'runs/0/native';directory.mkdir(parents=True)
            (directory/'worker.json').write_text('partial JSON')
            row={'slot':0,'stages':{'native':{'status':'exited'}}}
            self.assertEqual(summarize_p01.declared_native(bundle,row),{'status':'missing_or_invalid_summary'})
