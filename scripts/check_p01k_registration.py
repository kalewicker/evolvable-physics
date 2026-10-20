#!/usr/bin/env python3
"""Static P01k registration review: addresses/strings/arithmetic, no keyed hashes."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DOMAINS = {'form': 8, 'kind0': 3, 'kind1': 3, 'new_kind': 3, 'state0': 4,
                'state1': 4, 'value': 3, 'sign': 2, 'amount': 2, 'matter': 2, 'route': 2}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def planned_cells(p):
    return [{'slot': n, 'proposal': proposal, 'initial': initial}
            for n, (proposal, initial) in enumerate(itertools.product(p['proposal_ids'], p['initial_state_ids']))]


def addresses(p, cell):
    """Only symbolic coordinates and ranges. Never computes a field value."""
    law = [(0, 'child_kind_by_donor', i, 3) for i in range(3)]
    law += [(0, field, i, n) for i in range(8) for field, n in p['draw_contract']['rule_domains'].items()]
    initial = [(cell['initial'], field, i, n) for field, n in p['draw_contract']['initial_domains'].items()
               for i in (range(1) if field == 'scheduler' else range(8))]
    return [(p['generator'], cell['proposal'], i, field, index, n) for i, field, index, n in law + initial]


def assess_bookkeeping(p, cells):
    """Synthetic status aggregation only; route counts cannot admit dynamics."""
    planned = planned_cells(p)
    require(len(cells) == len(planned), 'retain complete denominator')
    laws, tables = {}, set()
    complete = 0
    for plan, cell in zip(planned, cells):
        require(all(type(cell[k]) is int and cell[k] == v for k, v in plan.items()), 'fixed cell identity/order')
        require(cell['status'] in ('complete', 'failed', 'censored', 'unstarted'), 'cell status')
        require(type(cell['verified']) is bool, 'verification flag')
        digest = cell.get('law_digest')
        if digest is not None:
            require(isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'law digest')
            require(laws.setdefault(cell['proposal'], digest) == digest, 'law identity across initials')
        if cell['status'] == 'complete' and cell['verified']:
            require(digest is not None, 'verified law identity')
            complete += 1
            tables.add(digest)
    return {'complete_verified_environments': complete, 'distinct_verified_tables': len(tables),
            'engineering_gate_pass': complete == 128, 'chemistry_continuation_gate': None,
            'world_execution_admitted': False}


def validate(p, vectors):
    require(p['schema'] == 'p01k-v3-static-census-registration-v1', 'protocol schema')
    require(p['generator'] == 'p01-generator-v3', 'namespace')
    require(p['proposal_ids'] == list(range(5000, 5032)) and p['initial_state_ids'] == list(range(4)), 'fixed IDs')
    require((p['law_denominator'], p['environment_denominator'], p['epochs']) == (32, 128, 0), 'denominators/zero epochs')
    for key, expected in [('sampler_implemented_now', False), ('sampling_admitted_now', False),
                           ('world_execution_admitted', False), ('e01_authorized', False),
                           ('implementation_admitted_after_registration_commit', True), ('scientific_status', 'untested')]:
        require(type(p[key]) is type(expected) and p[key] == expected, 'admission: ' + key)
    require(p['chemistry_continuation_gate'] is None, 'no chemistry threshold')
    d = p['draw_contract']
    require(d['map'] == {'field': 'child_kind_by_donor', 'initial': 0, 'indices': [0, 1, 2], 'modulus': 3, 'offset': 1}, 'map fields')
    require(d['rule_domains'] == RULE_DOMAINS and d['rule_initial'] == 0 and d['rule_indices'] == list(range(8)), 'rule scope/domains')
    require(d['initial_domains'] == {'node_kind': 3, 'node_state': 3, 'structural': 2, 'scheduler': 2**64 - 1}, 'initial fields')
    cells = planned_cells(p)
    keys = [address for cell in cells for address in addresses(p, cell)]
    unique_messages = {key[:-1] for key in keys}
    require(len(cells) == 128 and len(keys) == 14848 and len(unique_messages) == 6112, 'field address census')
    require((d['logical_field_records_per_cell'], d['logical_field_records_per_implementation'],
             d['unique_message_addresses']) == (116, 14848, 6112), 'declared field counts')
    require(vectors['schema'] == 'p01k-unhashed-primitive-vectors-v1', 'vector schema')
    require(len(vectors['serialization']) == 4 and len(vectors['prefix_reduction']) == 6, 'primitive vector census')
    for row in vectors['serialization']:
        text = json.dumps(row['arguments'], separators=(',', ':'), ensure_ascii=False)
        require(text.encode('utf-8') == row['utf8'].encode('utf-8'), 'exact serialization vector')
    for row in vectors['prefix_reduction']:
        require(len(row['prefix_hex']) == 16 and int(row['prefix_hex'], 16) % row['modulus'] == row['raw'], 'prefix arithmetic vector')
    require(p['per_process'] == {
        'rust_generation': {'wall_seconds': 5, 'sampled_rss_bytes': 134217728, 'output_bytes': 1048576},
        'python_generation': {'wall_seconds': 5, 'sampled_rss_bytes': 134217728, 'output_bytes': 1048576},
        'static_report': {'wall_seconds': 30, 'sampled_rss_bytes': 536870912, 'output_bytes': 8388608},
        'independent_audit': {'wall_seconds': 30, 'sampled_rss_bytes': 536870912, 'output_bytes': 8388608}}, 'stage budgets')
    c = p['campaign']
    require({k: c[k] for k in ('wall_seconds', 'total_process_cpu_seconds', 'artifact_bytes', 'metadata_reserve_bytes', 'poll_seconds')}
            == dict(wall_seconds=300, total_process_cpu_seconds=120, artifact_bytes=1073741824,
                    metadata_reserve_bytes=16777216, poll_seconds=0.01), 'campaign budgets')
    require(all(2 * stage['wall_seconds'] < c['total_process_cpu_seconds'] for stage in p['per_process'].values()), 'CPU launch feasibility')
    require(len(p['engineering_gate']) == 4 and len(p['requirements_before_sampling']) == 5, 'gate/execution boundaries')
    require(set(p['observables']) == {'law_identity', 'initial_environment', 'template_census', 'birth_funding_pairs',
        'birth_recycle_pairs', 'child_donor_pairs', 'joined_motifs', 'type_paths', 'initial_histograms',
        'state_limits', 'behavioral_outcomes'}, 'separate route/behavioral observables')
    require(p['future_paths'] == {'rust_sampler': 'src/bin/generator-v3.rs', 'python_sampler': 'scripts/generator_v3.py',
        'runner': 'scripts/p01k_census.py', 'static_report': 'scripts/p01k_static.py', 'auditor': 'scripts/audit_p01k.py'}, 'new paths')
    return {'schema': 'p01k-static-registration-review-v1', 'status': 'pass', 'law_cells': 32,
            'initial_environment_cells': 128, 'requested_epochs': 0,
            'logical_field_addresses_per_implementation': len(keys), 'unique_message_addresses': len(unique_messages),
            'unhashed_serialization_vectors': 4, 'literal_prefix_vectors': 6,
            'sampler_implementations_or_keyed_calls': 0, 'world_transitions': 0,
            'sampling_admitted': False, 'chemistry_continuation_gate': None, 'scientific_status': 'untested'}


def main():
    result = validate(load(ROOT / 'docs/p01k_protocol.json'), load(ROOT / 'docs/p01k_primitive_vectors.json'))
    freeze = load(ROOT / 'docs/p01k_registration_freeze.json')
    for name, expected in freeze['files'].items():
        require(sha(ROOT / name) == expected, 'frozen identity: ' + name)
    admission = load(ROOT / 'docs/p01j_readiness_admission.json')
    require(admission['engineering_gate_pass'] is True and admission['law_sampling_admitted'] is False, 'literal prerequisite')
    for name, expected in admission['implementation_files'].items():
        require(sha(ROOT / name) == expected, 'literal adapter identity: ' + name)
    inventory = load(ROOT / 'docs/evidence/publication_inventory.json')['files']
    for row in inventory:
        require(sha(ROOT / row['file']) == row['sha256'], 'historical receipt: ' + row['file'])
    result.update(registration_freeze_sha256=sha(ROOT / 'docs/p01k_registration_freeze.json'),
                  registration_files=freeze['files'], prior_public_receipts_verified=len(inventory))
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'static_review.json').open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'registration_files'}, sort_keys=True))


if __name__ == '__main__':
    main()
