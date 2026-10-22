#!/usr/bin/env python3
"""Static P01o registration review: addresses/strings/arithmetic, no keyed hashes."""
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
    law += [(0, 'role_state_by_kind', i, 3) for i in range(3)]
    law += [(0, field, i, n) for i in range(8) for field, n in p['draw_contract']['rule_domains'].items()]
    initial = [(cell['initial'], field, i, 3) for i in range(8) for field in ('node_kind', 'node_state')]
    initial += [(cell['initial'], 'structural', i, 2) for i in range(8)]
    initial += [(cell['initial'], 'scheduler', 0, 2**64-1)]
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
    require(p['schema'] == 'p01o-v4-static-census-registration-v1', 'protocol schema')
    require(p['generator'] == 'p01-generator-v4', 'namespace')
    require(all(type(x) is int for x in p['proposal_ids']+p['initial_state_ids']), 'integer IDs')
    require(p['proposal_ids'] == list(range(6000, 6032)) and p['initial_state_ids'] == list(range(4)), 'fixed IDs')
    require((p['law_denominator'], p['environment_denominator'], p['epochs']) == (32, 128, 0), 'denominators/zero epochs')
    for key, expected in [('registration_only_now', True), ('sampler_implemented_now', False), ('sampling_admitted_now', False),
                           ('world_execution_admitted', False), ('e01_authorized', False),
                           ('implementation_admitted_after_registration_commit', True), ('scientific_status', 'untested')]:
        require(type(p[key]) is type(expected) and p[key] == expected, 'admission: ' + key)
    require(p['chemistry_continuation_gate'] is None, 'no chemistry threshold')
    d = p['draw_contract']
    for mapping in (d['map'], d['state_map']):
        require(all(type(mapping[k]) is int for k in ('initial', 'modulus', 'offset')) and
                all(type(i) is int for i in mapping['indices']), 'integer map coordinates')
    require(d['map'] == {'field': 'child_kind_by_donor', 'initial': 0, 'indices': [0, 1, 2], 'modulus': 3, 'offset': 1}, 'map fields')
    require(d['state_map'] == {'field': 'role_state_by_kind', 'initial': 0, 'indices': [0, 1, 2], 'modulus': 3, 'offset': 0}, 'state map fields')
    require(list(d['rule_domains']) == list(RULE_DOMAINS), 'rule field order')
    require(d['rule_domains'] == RULE_DOMAINS and d['rule_initial'] == 0 and d['rule_indices'] == list(range(8)), 'rule scope/domains')
    require(d['initial_domains'] == {'node_kind': 3, 'node_state': 3, 'structural': 2, 'scheduler': 2**64 - 1}, 'initial fields')
    cells = planned_cells(p)
    keys = [address for cell in cells for address in addresses(p, cell)]
    unique_messages = {key[:-1] for key in keys}
    require(len(cells) == 128 and len(keys) == 15232 and len(unique_messages) == 6208, 'field address census')
    require((d['logical_field_records_per_cell'], d['logical_field_records_per_implementation'],
             d['unique_message_addresses']) == (119, 15232, 6208), 'declared field counts')
    require(vectors['schema'] == 'p01o-unhashed-primitive-vectors-v1', 'vector schema')
    require(len(vectors['serialization']) == 6 and len(vectors['prefix_reduction']) == 6, 'primitive vector census')
    expected_arguments = [
        ['p01-generator-v4', 6000, 0, 'child_kind_by_donor', 0],
        ['p01-generator-v4', 6000, 0, 'role_state_by_kind', 2],
        ['p01-generator-v4', 6000, 0, 'route', 7],
        ['p01-generator-v4', 6000, 3, 'node_state', 7],
        ['p01-generator-v4', 6031, 3, 'scheduler', 0],
        ['p01-generator-v4', 2**64-1, 3, 'scheduler', 0]]
    require([row['arguments'] for row in vectors['serialization']] == expected_arguments, 'vector addresses')
    require(d['read_order'] == ['type map indices 0..2 at initial=0', 'state map indices 0..2 at initial=0',
        'rule slots 0..7, then rule_domains insertion order, at initial=0',
        'nodes 0..7, interleaved node_kind then node_state, at requested initial',
        'structural indices 0..7 at requested initial', 'scheduler index 0 at requested initial'], 'draw read order')
    require(p['effective_rule_contract']['source'] == 'docs/generator_v4_design.json' and
            p['effective_rule_contract']['literal_prerequisite'] == 'docs/p01n_readiness_admission.json', 'v4 prerequisite')
    require(p['static_predicate_contract']['joint_donor_states'] ==
            'intersect birth, funding and recycle donor predicates in one common state set; pairwise compatibility with a wildcard birth is insufficient', 'joint donor intersection')
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
    require(p['future_paths'] == {'rust_sampler': 'src/bin/generator-v4.rs', 'python_sampler': 'scripts/generator_v4.py',
        'runner': 'scripts/p01o_census.py', 'static_report': 'scripts/p01o_static.py', 'auditor': 'scripts/audit_p01o.py'}, 'new paths')
    return {'schema': 'p01o-static-registration-review-v1', 'status': 'pass', 'law_cells': 32,
            'initial_environment_cells': 128, 'requested_epochs': 0,
            'logical_field_addresses_per_implementation': len(keys), 'unique_message_addresses': len(unique_messages),
            'unhashed_serialization_vectors': 6, 'literal_prefix_vectors': 6,
            'sampler_implementations_or_keyed_calls': 0, 'world_transitions': 0,
            'sampling_admitted': False, 'chemistry_continuation_gate': None, 'scientific_status': 'untested'}


def main():
    result = validate(load(ROOT / 'docs/p01o_protocol.json'), load(ROOT / 'docs/p01o_primitive_vectors.json'))
    freeze = load(ROOT / 'docs/p01o_registration_freeze.json')
    for name, expected in freeze['files'].items():
        require(sha(ROOT / name) == expected, 'frozen identity: ' + name)
    for name, expected in freeze['prior_public_receipts'].items():
        require(sha(ROOT / name) == expected, 'frozen receipt: ' + name)
    for path in load(ROOT / 'docs/p01o_protocol.json')['future_paths'].values():
        require(not (ROOT / path).exists(), 'sampler implementation before registration: ' + path)
    admission = load(ROOT / 'docs/p01n_readiness_admission.json')
    require(admission['engineering_gate_pass'] is True and admission['law_sampling_admitted'] is False, 'literal prerequisite')
    for name, expected in admission['implementation_files'].items():
        require(sha(ROOT / name) == expected, 'literal adapter identity: ' + name)
    inventory = load(ROOT / 'docs/evidence/publication_inventory.json')['files']
    for row in inventory:
        require(sha(ROOT / row['file']) == row['sha256'], 'historical receipt: ' + row['file'])
    result.update(registration_freeze_sha256=sha(ROOT / 'docs/p01o_registration_freeze.json'),
                  registration_files=freeze['files'], prior_public_receipts_verified=len(inventory))
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'static_review.json').open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'registration_files'}, sort_keys=True))


if __name__ == '__main__':
    main()
