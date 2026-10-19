"""Failure-path accounting and exact launch boundaries, independent of panel outcomes."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pilot


class PilotControls(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((pilot.ROOT/'docs/p01a_protocol.json').read_text())

    def test_fixed_denominator_survives_infrastructure_failure(self):
        runs = pilot.planned_runs(self.protocol)
        runs[0]['status'] = 'complete'
        runs[1]['status'] = 'launching'
        pilot.mark_infrastructure_failure(runs, RuntimeError('observation failed'))
        self.assertEqual(len(runs), 64)
        self.assertEqual(len({(r['proposal'], r['initial_state']) for r in runs}), 64)
        self.assertEqual(runs[0]['status'], 'complete')
        self.assertEqual(runs[1]['status'], 'infrastructure_error')
        self.assertTrue(all(r['status'] == 'not_started_infrastructure' for r in runs[2:]))

    def test_campaign_reserves_full_next_worker_at_exact_boundary(self):
        p = self.protocol
        wall = p['campaign']['wall_seconds']-p['supervisor']['wall_seconds']
        cpu = p['campaign']['worker_cpu_seconds']-p['supervisor']['wall_seconds']
        trace = p['campaign']['trace_bytes']-p['worker']['max_trace_bytes']
        self.assertTrue(pilot.can_launch(p, wall, cpu, trace))
        self.assertFalse(pilot.can_launch(p, wall+.001, cpu, trace))
        self.assertFalse(pilot.can_launch(p, wall, cpu+.001, trace))
        self.assertFalse(pilot.can_launch(p, wall, cpu, trace+1))

    def test_failed_memory_observation_kills_and_reaps_worker(self):
        children = []
        popen = subprocess.Popen
        def record(*a, **kw):
            child = popen(*a, **kw)
            children.append(child)
            return child
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(pilot.subprocess, 'Popen', side_effect=record), patch.object(
                    pilot.subprocess, 'run', side_effect=PermissionError('RSS denied')):
                with self.assertRaises(PermissionError):
                    pilot.supervise([sys.executable, '-c', 'import time; time.sleep(5)'],
                                    Path(temp)/'run', self.protocol['supervisor'])
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].returncode, -9)
        with self.assertRaises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)


if __name__ == '__main__':
    unittest.main()
