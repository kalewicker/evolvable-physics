#!/usr/bin/env python3
"""Bounded independent audit stage; invoked only by the sealed campaign guard."""
import hashlib
import json
import sys
from pathlib import Path
import audit
import pilot
import pilot_reporting

if not __debug__: raise RuntimeError('Assertions are required')
request_path, directory, report_path = map(Path, sys.argv[1:4])
request = json.loads(request_path.read_text())
report_raw = report_path.read_bytes(); report = json.loads(report_raw)
if len(sys.argv) == 6:
    assert request['initial'] == pilot.generate(int(sys.argv[4]), int(sys.argv[5])), 'Independent generator mismatch'
endpoint = pilot_reporting.verify(request, directory, report)
summary = json.loads((directory/'worker.json').read_bytes())
print(json.dumps({'schema': 'p01-independent-slot-audit-v1', 'status': 'pass',
                  'request_digest': audit.digest(request), 'report_sha256': hashlib.sha256(report_raw).hexdigest(),
                  'trace_sha256': hashlib.sha256((directory/'trace.jsonl').read_bytes()).hexdigest(),
                  'coverage': report['coverage'], 'full_horizon_ap': endpoint,
                  'worker_status': summary['status'], 'observed_epochs': summary['epochs'],
                  'events': summary['events'], 'applicable_candidates': summary['applicable_candidates']}, sort_keys=True))
