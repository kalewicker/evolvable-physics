#!/usr/bin/env python3
"""Pre-execution identity/admission review only; no sampler or keyed-hash imports."""
import json
import sys
from pathlib import Path
from p01k_contract import ROOT, canonical, load, plans, require, sha, verify_closure


def review():
    protocol, freeze, admission = verify_closure()
    require(admission['output_absolute'] == str((ROOT / 'artifacts/p01k-001').resolve()), 'fixed output directory')
    require(not Path(admission['output_absolute']).exists(), 'attempt directory already exists; no resume')
    readiness = load(ROOT / 'docs/p01k_implementation_readiness.json')
    require(readiness['literal_mock_gate_pass'] is True and readiness['sampling_admitted'] is False,
            'literal implementation prerequisite')
    for name, digest in readiness['implementation_files'].items():
        require(sha(ROOT / name) == digest, 'changed implementation: ' + name)
    require(freeze['binaries']['generator-v3']['sha256'] == readiness['rust_binary_sha256'], 'tested binary')
    for name, digest in load(ROOT / 'docs/p01k_registration_freeze.json')['files'].items():
        require(freeze['files'].get(name) == digest, 'registration not preserved: ' + name)
    cells = plans(protocol)
    require(len(cells) == 128 and cells[0] == dict(slot=0, proposal=5000, initial=0) and
            cells[-1] == dict(slot=127, proposal=5031, initial=3), 'complete fixed panel')
    return dict(schema='p01k-pre-execution-readiness-v1', status='pass', source_files=len(freeze['files']),
                dependency_files=len(freeze['dependencies']), tool_files=len(freeze['tools']),
                binary_sha256=freeze['binaries']['generator-v3']['sha256'],
                protocol_sha256=sha(ROOT / 'docs/p01k_protocol.json'),
                execution_freeze_sha256=sha(ROOT / 'docs/p01k_execution_freeze.json'),
                execution_admission_sha256=sha(ROOT / 'docs/p01k_execution_admission.json'),
                fixed_laws=32, fixed_environments=128, keyed_evaluations_so_far=0, world_transitions=0,
                scope='identity/closure/admission review only; commit/push gate must precede sampled execution',
                scientific_status='untested')


if __name__ == '__main__':
    result = review()
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'readiness.json').open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(canonical(result))
