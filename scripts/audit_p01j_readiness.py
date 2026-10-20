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
    """Check ordinal coordinates directly, independently of the panel producer."""
    if ordinal < 11664:
        map_index = ordinal // 432
        donor = (ordinal // 144) % 3
        variant = (ordinal // 16) % 9
        state0, state1 = divmod(ordinal % 16, 4)
        expected = {'case_id': f'rule-{ordinal:05}', 'mode': 'rule', 'map': registry['maps'][map_index],
                    'rule_id': ordinal % 8, 'fields': literal_row(registry, donor, variant, state0, state1)}
    elif ordinal < 12636:
        n = ordinal - 11664
        map_index, rotation, initial_id = n // 36, (n // 4) % 9, n % 4
        expected = {'case_id': f'assembly-{n:04}', 'mode': 'assembly', 'map': registry['maps'][map_index],
                    'initial_id': initial_id, 'initial_fields': registry['initial_fields'][initial_id],
                    'rule_fields': [literal_row(registry, slot % 3, (slot + rotation) % 9,
                                               (slot + rotation) % 4, (slot + rotation + 1) % 4)
                                    for slot in range(8)]}
    elif ordinal < 12644:
        row = registry['barriers'][ordinal - 12636]
        expected = {'case_id': 'barrier-' + row['name'], 'mode': 'barrier', 'descriptor': row}
    else:
        # Invalid/probe record construction is checked by exact named mutations
        # against the common literal base, not by calling the producer.
        base = dict(form=3, route=1, kind0=0, kind1=2, new_kind=0,
                    state0=3, state1=3, value=2, sign=0, amount=0, matter=1)
        if ordinal < 12656:
            item = registry['invalid_inputs'][ordinal - 12644]
            initial = dict(registry['initial_fields'][0])
            expected = dict(case_id='invalid-' + item['name'], mode='assembly', map=[2, 3, 1],
                            initial_id=0, initial_fields=initial, rule_fields=[dict(base) for _ in range(8)])
            target = item['target']
            if target in ('map', 'initial_id'):
                expected[target] = item['value']
            elif target == 'scheduler':
                initial['scheduler'] = item['value']
            elif target == 'required_kind0':
                del expected['rule_fields'][0]['kind0']
            else:
                expected['rule_fields'][0][target] = item['value']
        else:
            probes = [(g, p, value) for g, p in enumerate(registry['ignored_field_probes']) for value in p['values']]
            require(ordinal - 12656 < len(probes), 'extra input')
            group, item, value = probes[ordinal - 12656]
            variant = next(v for v in registry['variants'] if v['name'] == item['variant'])
            base.update(form=variant['form'], route=variant['route'])
            base[item['field']] = value
            expected = dict(case_id=f'probe-{group}-{value}', mode='rule', map=[2, 3, 1], rule_id=0, fields=base)
    require(json.dumps(req, sort_keys=True) == json.dumps(expected, sort_keys=True),
            'registered input mismatch at ordinal ' + str(ordinal))


def audit(bundle):
    inventory = load(bundle / 'checksums.json')
    for name, digest in inventory.items():
        require(sha(bundle / name) == digest, 'bundle digest mismatch: ' + name)
    seal = load(bundle / 'seal.json')
    require(seal['checksums_sha256'] == sha(bundle / 'checksums.json'), 'inventory seal')
    completion = load(bundle / 'completion.json')
    require(completion['seal_sha256'] == sha(bundle / 'seal.json'), 'completion seal')
    require(completion['aggregate_wall_pass'] is True and
            completion['wall_seconds_including_sealing'] <= 120, 'aggregate ceiling')
    assessment = load(bundle / 'assessment.json')
    require(assessment['engineering_gate_pass'] is True and assessment['status'] == 'pass', 'readiness gate')
    require(assessment['case_counts'] == {'rule': 11664, 'assembly': 972, 'barrier': 8, 'invalid': 12, 'probe': 15}, 'counts')
    require(assessment['world_transitions'] == assessment['hash_sampler_calls'] == 0 and
            assessment['law_sampling_admitted'] is False, 'scope')
    sources = assessment['source_identities']
    for name, digest in sources['files'].items():
        require(sha(bundle / 'sources' / name) == digest, 'snapshot identity: ' + name)
        require(sha(ROOT / name) == digest, 'current source identity: ' + name)
    freeze = load(ROOT / 'docs/p01j_registration_freeze.json')
    for name, digest in freeze['files'].items():
        require(sha(ROOT / name) == digest, 'frozen source identity: ' + name)
    require(sha(ROOT / 'target/release/generator-v3-fields') == sources['rust_binary_sha256'], 'binary identity')
    require(sha(bundle / 'inputs.jsonl') == sources['literal_inputs_sha256'], 'literal input identity')
    registry = load(bundle / 'sources/docs/p01j_literal_fields.json')
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
    require(count == 12671, 'complete fixed panel')
    for name in ('python', 'rust'):
        guard = load(bundle / (name + '_guard.json'))
        actual_bytes = (bundle / (name + '.jsonl')).stat().st_size + (bundle / (name + '.stderr')).stat().st_size
        require(guard == assessment['stages'][name], 'guard identity')
        require(guard['status'] == 'complete' and guard['returncode'] == 0 and
                actual_bytes == guard['output_bytes'] <= 67108864 and guard['wall_seconds'] <= 30, 'stage ceilings')
    return {'schema': 'p01j-readiness-receipt-audit-v1', 'status': 'pass',
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
