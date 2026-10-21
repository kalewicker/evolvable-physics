#!/usr/bin/env python3
"""Literal-only implementation preflight. No admitted sampler source is invoked."""
import itertools
import json
import sys
import time
from pathlib import Path
from audit_p01k import verify_payload
from p01k_contract import ROOT, canonical, load, require, sha
from validate_p01j import requests, guarded, check_streams, expected


def literal_digest(req, preimage):
    _, proposal, initial, field, index = json.loads(preimage)
    require(proposal == req['cell']['proposal'], 'mock proposal')
    if field == 'child_kind_by_donor':
        raw = req['map'][index] - 1
    elif field in req['rule_fields'][0]:
        require(initial == 0, 'mock rule initial')
        raw = req['rule_fields'][index][field]
    else:
        require(initial == req['initial_id'], 'mock world initial')
        raw = req['initial_fields'][field] if field == 'scheduler' else req['initial_fields'][field][index]
    return f'{raw:016x}' + '0' * 48


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    deadline = start + 120
    result = dict(schema='p01k-literal-implementation-readiness-v1', status='started',
                  keyed_hash_evaluations=0, world_transitions=0, literal_only=True, stages={})
    try:
        frozen = load(ROOT / 'docs/p01k_registration_freeze.json')['files']
        for name, digest in frozen.items():
            require(sha(ROOT / name) == digest, 'frozen source identity: ' + name)
        sources = ['src/bin/generator-v3.rs', 'scripts/generator_v3.py', 'scripts/p01k_contract.py',
                   'scripts/p01k_static.py', 'scripts/p01k_census.py', 'scripts/audit_p01k.py',
                   'scripts/test_p01k_implementation.py', 'scripts/validate_p01k_implementation.py']
        for name in sources:
            target = out / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        result['source_sha256'] = {name: sha(ROOT / name) for name in sources}
        binary = ROOT / 'target/release/generator-v3'
        result['rust_binary_sha256'] = sha(binary)
        registry = load(ROOT / 'docs/p01j_literal_fields.json')
        inputs = out / 'literal-inputs.jsonl'
        recorded_inputs = out / 'recorded-inputs.jsonl'
        with inputs.open('x') as f, recorded_inputs.open('x') as recorded:
            count = 0
            for req in requests(registry):
                f.write(canonical(req) + '\n')
                if req['mode'] == 'assembly' and req['case_id'].startswith('assembly-'):
                    slot = count % 128
                    req['cell'] = dict(slot=slot, proposal=5000 + slot // 4, initial=req['initial_id'])
                    recorded.write(canonical(req) + '\n')
                    count += 1
        require(count == 972, 'recorded assembly census')
        for panel, mode, input_file in [('literal', '--literal', inputs), ('recorded', '--record-literal', recorded_inputs)]:
            for language, command in [('rust', [str(binary), mode]),
                                      ('python', [sys.executable, str(ROOT / 'scripts/generator_v3.py'), mode])]:
                name = language + '-' + panel
                receipt = guarded(command, input_file, out / (name + '.jsonl'), out / (name + '.stderr'),
                                  30, 67108864, deadline)
                result['stages'][name] = receipt
                require(receipt['status'] == 'complete', 'mock process guard failed: ' + name)
        result['literal_counts'] = check_streams(inputs, out / 'python-literal.jsonl', out / 'rust-literal.jsonl', deadline)
        with recorded_inputs.open() as ins, (out / 'python-recorded.jsonl').open() as py, (out / 'rust-recorded.jsonl').open() as rs:
            records = 0
            for lines in itertools.zip_longest(ins, py, rs):
                require(time.monotonic() < deadline and all(line is not None for line in lines), 'recorded deadline/census')
                req, a, b = (json.loads(line) for line in lines)
                require(canonical(a) == canonical(b), 'recorded differential')
                verify_payload(req['cell'], a, lambda message: literal_digest(req, message))
                env, _ = expected(req)
                require(canonical(a['environment']) == canonical(env), 'recorded environment oracle')
                records += 1
        require(records == 972 and all(sha(ROOT / n) == digest for n, digest in result['source_sha256'].items()), 'recorded census/source stability')
        result.update(status='pass', literal_gate_pass=True, recorded_mock_assemblies=records,
                      mock_draw_records_per_implementation=records * 116,
                      registration_files_verified=len(frozen), sampling_admitted=False,
                      scope='authored literal inputs and deliberately fake prefix metadata only; no actual hash sampler equivalence')
    except Exception as error:
        result.update(status='fail', literal_gate_pass=False, error=repr(error))
    result['wall_seconds_through_checks'] = time.monotonic() - start
    (out / 'assessment.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    inventory = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'checksums.json').write_text(json.dumps(inventory, sort_keys=True, indent=2) + '\n')
    completion = dict(schema='p01k-implementation-preflight-completion-v1', checksums_sha256=sha(out / 'checksums.json'),
                      wall_seconds_including_inventory=time.monotonic() - start, aggregate_wall_ceiling_seconds=120)
    (out / 'completion.json').write_text(json.dumps(completion, sort_keys=True, indent=2) + '\n')
    print(canonical({k: result[k] for k in ('status', 'literal_only', 'keyed_hash_evaluations', 'world_transitions')}))
    if result['status'] != 'pass' or completion['wall_seconds_including_inventory'] > 120:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
