#!/usr/bin/env python3
"""Read-only verification of a sealed P01a bundle; writes a new compact receipt."""
import hashlib
import json
import sys
from pathlib import Path
import audit
import pilot


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle):
    manifest = json.loads((bundle/'manifest.json').read_text())
    assert manifest['schema'] == 'p01a-manifest-v2'
    assert manifest['execution_status'] == 'complete'
    assert manifest['scientific_status'] == 'untested'
    assert manifest['p01_ready'] is False and manifest['full_p01_started'] is False
    checksums = json.loads((bundle/'checksums.json').read_text())
    actual = {str(p.relative_to(bundle)): sha(p) for p in bundle.rglob('*')
              if p.is_file() and p != bundle/'checksums.json'}
    assert actual == checksums, 'Bundle inventory or hash mismatch'
    for name, digest in manifest['source_files'].items():
        assert sha(bundle/'source'/name) == digest
    # Bind this verifier's imported independent generator/interpreter to the sealed source.
    for name in ('scripts/pilot.py', 'scripts/audit.py', 'scripts/audit_environment.py'):
        assert sha(pilot.ROOT/name) == manifest['source_files'][name]
    protocol = manifest['protocol']
    assert protocol == json.loads((bundle/'source/docs/p01a_protocol.json').read_text())
    for name in ('p00f_freeze.json', 'p00g_freeze.json', 'p01a_freeze.json'):
        frozen = json.loads((bundle/'source/docs'/name).read_text())
        for path, digest in frozen['files'].items():
            assert sha(bundle/'source'/path) == digest
    runs = manifest['runs']
    expected = pilot.planned_runs(protocol)
    assert [(r['proposal'], r['initial_state']) for r in runs] == [
        (r['proposal'], r['initial_state']) for r in expected]
    assert len(runs) == protocol['denominator'] == 64
    epochs = events = candidates = traces = native_events = 0
    cpu = 0
    laws = []
    for run in runs:
        assert run['status'] == 'complete' and run['returncode'] == 0
        assert run['independent_replay'] == 'pass'
        p, i = run['proposal'], run['initial_state']
        initial = pilot.generate(p, i)
        request = json.loads((bundle/f'runs/{p}-{i}-request.json').read_text())
        assert request == {'schema': 'p01-worker-request-v1', 'initial': initial,
                           'epochs': protocol['epochs'], **protocol['worker']}
        summary, frames = pilot.read_worker(bundle/f'runs/{p}-{i}', initial)
        for key in ('status', 'epochs', 'events', 'native_events', 'applicable_candidates',
                    'trace_bytes', 'step_ns', 'serialize_ns', 'write_ns'):
            assert summary[key] == run[key], key
        assert len(frames) == protocol['epochs']
        assert summary['events'] <= protocol['worker']['max_events']
        assert summary['trace_bytes'] <= protocol['worker']['max_trace_bytes']
        epochs += summary['epochs']; events += summary['events']
        native_events += summary['native_events']; candidates += summary['applicable_candidates']
        traces += summary['trace_bytes']; cpu += run['worker_cpu_seconds']
        if i == 0:
            laws.append(audit.digest([{k: v for k, v in r.items() if k != 'id'}
                                      for r in initial['native']['rules']]))
    assert traces == manifest['trace_bytes'] and cpu == manifest['worker_cpu_seconds']
    assert manifest['duplicate_rule_sets'] == len(laws)-len(set(laws))
    assert manifest['completed_runs'] == 64 and manifest['gate_pass'] is True
    guards = manifest['guard_checks']
    for key in ('event', 'trace', 'event_boundary', 'trace_boundary'):
        assert guards[key] == ('event_budget_exceeded' if key.startswith('event') else 'trace_budget_exceeded')
    assert guards['complete'] == 'complete'
    for key in ('wall', 'rss'):
        assert guards[key]['status'] == key+'_budget_exceeded' and guards[key]['returncode'] == -9
    assert guards['infrastructure']['status'] == 'infrastructure_error'
    for key in ('priority', 'state', 'initial', 'summary'):
        assert guards['tamper_'+key] == 'rejected'
    return {'schema': 'p01a-independent-audit-v1', 'status': 'pass', 'gate_pass': True,
            'manifest_sha256': sha(bundle/'manifest.json'), 'checksums_sha256': sha(bundle/'checksums.json'),
            'sealed_files': len(actual), 'registered_runs': 64, 'replayed_epochs': epochs,
            'events': events, 'native_events': native_events, 'applicable_candidates': candidates,
            'trace_bytes': traces, 'duplicate_rule_sets': manifest['duplicate_rule_sets'],
            'worker_cpu_seconds': cpu, 'guard_checks': guards, 'cost_scenarios': manifest['cost_scenarios'],
            'p01_ready': False, 'full_p01_started': False, 'scientific_status': 'untested'}


if __name__ == '__main__':
    receipt = verify(Path(sys.argv[1]).resolve())
    with Path(sys.argv[2]).open('x') as out:
        json.dump(receipt, out, indent=2); out.write('\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'registered_runs', 'replayed_epochs', 'events', 'trace_bytes')}, indent=2))
