#!/usr/bin/env python3
"""Read-only custody and registered-input audit; never executes an adapter."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def literal_row(registry, donor, variant_index, state0, state1):
    v = registry['variants'][variant_index]
    return dict(form=v['form'], route=v['route'], kind0=donor, kind1=(donor + state1) % 3,
                new_kind=(donor + state0 + 1) % 3, state0=state0, state1=state1,
                value=(state0 + 2 * state1) % 3, sign=(state0 + state1) % 2,
                amount=state1 % 2, matter=state0 % 2)


def registered_input(req, ordinal, registry):
    """Mixed-radix coordinates, independent of producer iteration and helpers."""
    variants = {v['name']: i for i, v in enumerate(registry['variants'])}
    if ordinal < 6561:
        m, s, donor, v = ordinal // 243, (ordinal // 9) % 27, (ordinal // 3) % 3, ordinal % 3
        mapping, states = registry['type_maps'][m], registry['state_maps'][s]
        variant = registry['variants'][variants[registry['constructive_variants'][v]]]
        row = dict(form=variant['form'], route=variant['route'], kind0=donor, kind1=mapping[donor] % 3,
                   new_kind=mapping[donor] % 3, state0=3, state1=3, value=(states[mapping[donor]-1]+1) % 3,
                   sign=ordinal % 2, amount=ordinal % 2, matter=0)
        expected = dict(case_id=f'rule-{ordinal:05d}', mode='rule', map=mapping, state_map=states,
                        rule_id=ordinal % 8, fields=row)
    elif ordinal < 14337:
        n = ordinal-6561
        m, donor, v, pair = n // 288, (n // 96) % 3, (n // 16) % 6, n % 16
        expected = dict(case_id=f'rule-{ordinal:05d}', mode='rule', map=registry['type_maps'][m],
                        state_map=[2, 0, 1], rule_id=ordinal % 8,
                        fields=literal_row(registry, donor, variants[registry['unchanged_variants'][v]], pair // 4, pair % 4))
    elif ordinal < 17253:
        n = ordinal-14337
        m, s, initial = n // 108, (n // 4) % 27, n % 4
        rotation = (3*m+s) % 9
        expected = dict(case_id=f'assembly-{n:04d}', mode='assembly', map=registry['type_maps'][m],
                        state_map=registry['state_maps'][s], initial_id=initial,
                        initial_fields=registry['initial_fields'][initial],
                        rule_fields=[literal_row(registry, (slot+m) % 3, (slot+rotation) % 9,
                                                 (slot+rotation) % 4, (slot+rotation+1) % 4) for slot in range(8)])
    else:
        base = dict(form=3, route=1, kind0=0, kind1=2, new_kind=0, state0=3, state1=3,
                    value=2, sign=0, amount=0, matter=0)
        expected = dict(map=[2, 3, 1], state_map=[2, 0, 1])
        if ordinal < 17648:
            n = ordinal-17253
            for group, item in enumerate(registry['ignored_field_probes']):
                if n < len(item['values']):
                    break
                n -= len(item['values'])
            variant = registry['variants'][variants[item['variant']]]
            base.update(form=variant['form'], route=variant['route'])
            expected.update(case_id=f'probe-{group:02d}-{n:02d}', mode='rule', rule_id=0, fields=base)
            if item['field'] in ('map', 'state_map'):
                expected[item['field']] = item['values'][n]
            else:
                base[item['field']] = item['values'][n]
        else:
            require(ordinal < 17727, 'extra registered input')
            item = registry['invalid_inputs'][ordinal-17648]
            expected.update(case_id='invalid-'+item['name'], mode=item['mode'])
            if item['mode'] == 'rule':
                expected.update(rule_id=0, fields=base)
            else:
                expected.update(initial_id=0, initial_fields=dict(registry['initial_fields'][0]),
                                rule_fields=[dict(base) for _ in range(8)])
            path = item['target'].split('.')
            owner = expected if len(path) == 1 else (expected['rule_fields'][7] if path[0] == 'rule_fields[7]' else expected[path[0]])
            key = path[-1]
            if item['name'].endswith('_missing') or item['name'] in ('missing_raw_kind0', 'missing_initial_fields'):
                owner.pop(key)
            elif item['name'] == 'rule_fields_short':
                expected['rule_fields'].pop()
            else:
                owner[key] = item['value']
    require(json.dumps(req, sort_keys=True) == json.dumps(expected, sort_keys=True),
            'registered input mismatch at ordinal '+str(ordinal))


def audit(bundle):
    inventory = load(bundle / 'checksums.json')
    actual = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file()}
    require(actual == set(inventory) | {'checksums.json', 'seal.json', 'completion.json'}, 'complete bundle inventory')
    for name, digest in inventory.items():
        require(sha(bundle / name) == digest, 'bundle digest mismatch: ' + name)
    seal = load(bundle / 'seal.json')
    require(seal['checksums_sha256'] == sha(bundle / 'checksums.json'), 'inventory seal')
    completion = load(bundle / 'completion.json')
    require(completion['seal_sha256'] == sha(bundle / 'seal.json'), 'completion seal')
    require(completion['aggregate_wall_pass'] is True and
            completion['wall_seconds_including_sealing'] <= 300, 'aggregate ceiling')
    assessment = load(bundle / 'assessment.json')
    require(assessment['engineering_gate_pass'] is True and assessment['status'] == 'pass', 'readiness gate')
    require(assessment['case_counts'] == {'rule': 14337, 'assembly': 2916, 'invalid': 79, 'probe': 395}, 'counts')
    require(assessment['world_transitions'] == assessment['hash_sampler_calls'] == 0 and
            assessment['law_sampling_admitted'] is False, 'scope')
    sources = assessment['source_identities']
    for name, digest in sources['files'].items():
        require(sha(bundle / 'sources' / name) == digest, 'snapshot identity: ' + name)
        require(sha(ROOT / name) == digest, 'current source identity: ' + name)
    freeze = load(ROOT / 'docs/p01n_registration_freeze.json')
    for name, digest in {**freeze['files'], **freeze['prior_public_receipts']}.items():
        require(sha(ROOT / name) == digest, 'frozen source identity: ' + name)
    require(sha(bundle / 'rust_binary') == sources['rust_binary_sha256'], 'retained binary identity')
    require(sha(ROOT / 'target/release/generator-v4-fields') == sources['rust_binary_sha256'], 'binary identity')
    require(sha(bundle / 'inputs.jsonl') == sources['literal_inputs_sha256'], 'literal input identity')
    registry = load(bundle / 'sources/docs/p01n_literal_fields.json')
    count = 0
    with (bundle / 'inputs.jsonl').open() as ins, (bundle / 'python.jsonl').open() as py, (bundle / 'rust.jsonl').open() as rs:
        for ordinal, lines in enumerate(itertools.zip_longest(ins, py, rs)):
            require(all(line is not None for line in lines), 'missing/extra input or output')
            request, a, b = (json.loads(line) for line in lines)
            registered_input(request, ordinal, registry)
            require(a['case_id'] == b['case_id'] == request['case_id'], 'record identity')
            require(json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), 'differential output')
            require(a['ok'] is (not request['case_id'].startswith('invalid-')), 'record acceptance')
            count += 1
    require(count == 17727, 'complete fixed panel')
    for name in ('python', 'rust'):
        guard = load(bundle / (name + '_guard.json'))
        actual_bytes = (bundle / (name + '.jsonl')).stat().st_size + (bundle / (name + '.stderr')).stat().st_size
        require(guard == assessment['stages'][name], 'guard identity')
        require(guard['status'] == 'complete' and guard['returncode'] == 0 and
                actual_bytes == guard['output_bytes'] <= 268435456 and guard['wall_seconds'] <= 60, 'stage ceilings')
    return {'schema': 'p01n-readiness-receipt-audit-v1', 'status': 'pass',
            'scope': 'read-only custody, independently indexed registered inputs, differential records and ceilings; operation oracle remains the separate validator',
            'panel_records_verified': count, 'registration_files_verified': len(freeze['files']),
            'bundle_inventory_entries': len(inventory), 'readiness_seal_sha256': sha(bundle / 'seal.json'),
            'completion_sha256': sha(bundle / 'completion.json'), 'scientific_status': 'untested',
            'sampling_admitted': False, 'adapter_executions': 0}


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]))
    with Path(sys.argv[2]).open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps(result, sort_keys=True))
