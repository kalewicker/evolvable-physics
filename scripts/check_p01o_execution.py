#!/usr/bin/env python3
"""Read-only execution closure/admission checks; no sampler imports or calls."""
import json
import sys
from pathlib import Path
from p01o_contract import ROOT, canonical, load, plans, require, sha, verify_closure


def review(root=ROOT):
    protocol, freeze, admission = verify_closure(root)
    output = (root / 'artifacts/p01o-001').resolve()
    require(admission['admitted_output'] == 'artifacts/p01o-001' and
            admission['output_absolute'] == str(output), 'fixed output directory')
    require(not output.exists(), 'attempt directory already exists; no resume')
    readiness_path = root / 'docs/p01o_implementation_readiness.json'
    readiness = load(readiness_path)
    require(readiness['literal_mock_gate_pass'] is True and readiness['sampling_admitted'] is False and
            readiness['actual_keyed_source_executed'] is False, 'literal implementation prerequisite')
    require(admission['literal_implementation_readiness_sha256'] == sha(readiness_path), 'readiness identity')
    require(admission['keyed_sampler_evaluations_so_far'] == 0 and admission['world_transitions_so_far'] == 0 and
            admission['no_retries_or_replacements'] is True and admission['scientific_status'] == 'untested', 'scope')
    for name, digest in readiness['implementation_files'].items():
        require(sha(root / name) == digest and freeze['files'].get(name) == digest, 'changed implementation: ' + name)
    require(set(freeze['binaries']) == {'generator-v4'} and
            freeze['binaries']['generator-v4']['sha256'] == readiness['rust_binary_sha256'], 'tested binary')
    for name, digest in load(root / 'docs/p01o_registration_freeze.json')['files'].items():
        require(freeze['files'].get(name) == digest, 'registration not preserved: ' + name)
    for name, digest in freeze['prior_public_receipts'].items():
        require(sha(root / name) == digest, 'historical receipt: ' + name)
    metadata = load(root / freeze['cargo_metadata'])
    package_manifests = [p['manifest_path'] for p in metadata['packages'] if p['source'] is not None]
    require(package_manifests and all(n in freeze['dependencies'] for n in package_manifests), 'dependency manifest coverage')
    cells = plans(protocol)
    require(len(cells) == 128 and cells[0] == dict(slot=0, proposal=6000, initial=0) and
            cells[-1] == dict(slot=127, proposal=6031, initial=3), 'complete fixed panel')
    require(admission['fixed_laws'] == 32 and admission['fixed_cells'] == 128 and protocol['epochs'] == 0, 'denominators')
    return dict(schema='p01o-pre-execution-readiness-v1', status='pass', source_files=len(freeze['files']),
                dependency_files=len(freeze['dependencies']), tool_files=len(freeze['tools']),
                cargo_dependency_packages=len(package_manifests), prior_public_receipts_verified=len(freeze['prior_public_receipts']),
                binary_sha256=freeze['binaries']['generator-v4']['sha256'],
                protocol_sha256=sha(root / 'docs/p01o_protocol.json'),
                execution_freeze_sha256=sha(root / 'docs/p01o_execution_freeze.json'),
                execution_admission_sha256=sha(root / 'docs/p01o_execution_admission.json'),
                fixed_laws=32, fixed_environments=128, keyed_evaluations_so_far=0, world_transitions=0,
                scope='identity/closure/admission review only; commit/push gate must precede sampled execution',
                scientific_status='untested')


if __name__ == '__main__':
    result = review()
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    (out / 'readiness.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(canonical(result))
