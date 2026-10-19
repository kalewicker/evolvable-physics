"""Exact budget boundaries and guard cleanup tests; no full-P01 work."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import campaign
import campaign_guard


class CampaignTests(unittest.TestCase):
    def setUp(self): self.protocol=json.loads((campaign.ROOT/'docs/p01_protocol.json').read_text())

    def test_full_fixed_denominator_and_order(self):
        rows=campaign.ledger(self.protocol)
        self.assertEqual(len(rows),512)
        self.assertEqual([(r['proposal'],r['initial_state']) for r in rows],[(p,i) for p in range(3000,3128) for i in range(4)])
        self.assertTrue(all(r['full_horizon_ap'] is None for r in rows))

    def test_each_campaign_boundary_reserves_complete_next_stage(self):
        p=self.protocol
        for stage in ('slot','native','rust','audit'):
            wall,artifacts,trace=campaign.reservations(p,stage)
            u={'wall_seconds':p['campaign']['wall_seconds']-wall,
               'total_process_cpu_seconds':p['campaign']['total_process_cpu_seconds']-wall,
               'artifact_bytes':p['campaign']['total_artifact_bytes']-p['campaign']['metadata_reserve_bytes']-artifacts,
               'trace_bytes':p['campaign']['trace_bytes']-trace}
            self.assertTrue(campaign.can_launch(p,u,stage))
            for key in u:
                bad=copy.deepcopy(u);bad[key]+=1
                self.assertFalse(campaign.can_launch(p,bad,stage),(stage,key))

    def test_observation_failure_reaps_and_records_no_endpoint(self):
        import sys
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp);old_handler=__import__('signal').getsignal(__import__('signal').SIGTERM)
            try:
                desc={'parent_pid':os.getppid(),'directory':str(d),'cwd':str(d),
                      'command':[sys.executable,'-c','import time; time.sleep(5)'],
                      'campaign_deadline':__import__('time').monotonic()+5,
                      'limits':dict(campaign.stage_limits(self.protocol,'native'),wall_seconds=1)}
                with patch.object(campaign_guard.subprocess,'run',side_effect=PermissionError('RSS denied')):
                    r=campaign_guard.guard(desc)
                self.assertEqual(r['status'],'rss_observation_failed')
                self.assertEqual(r['returncode'],-9)
                pid=json.loads((d/'live.json').read_text())['child_pid']
                with self.assertRaises(ChildProcessError):os.waitpid(pid,os.WNOHANG)
            finally:__import__('signal').signal(__import__('signal').SIGTERM,old_handler)
