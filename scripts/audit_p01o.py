#!/usr/bin/env python3
"""Independent raw-field/output/schema audit; keyed checks require active admission."""
import hashlib
import itertools
import sys
from collections import Counter
from pathlib import Path
from p01o_contract import authorize, canonical, load, plans, require, sha
from validate_p01n import expected as literal_oracle

RULE_RANGES = {'form': 8, 'kind0': 3, 'kind1': 3, 'new_kind': 3, 'state0': 4,
               'state1': 4, 'value': 3, 'sign': 2, 'amount': 2, 'matter': 2, 'route': 2}


def verify_payload(cell, payload, digest_function):
    """The caller MUST inject a digest function; tests use literal fake digests."""
    require(set(payload) == {'schema', 'slot', 'proposal', 'initial', 'map', 'state_map', 'environment', 'draws'}, 'payload shape')
    require(payload['schema'] == 'p01o-generated-environment-v1' and
            all(type(payload[k]) is int and payload[k] == v for k, v in cell.items()), 'generated cell identity')
    wanted = {(0, 'child_kind_by_donor', i): 3 for i in range(3)}
    wanted.update({(0, 'role_state_by_kind', i): 3 for i in range(3)})
    wanted.update({(0, field, i): n for i in range(8) for field, n in RULE_RANGES.items()})
    wanted.update({(cell['initial'], field, i): 3 for i in range(8) for field in ('node_kind', 'node_state')})
    wanted.update({(cell['initial'], 'structural', i): 2 for i in range(8)})
    wanted[cell['initial'], 'scheduler', 0] = 2**64 - 1
    require(len(payload['draws']) == len(wanted) == 119, 'draw census')
    values = {}
    for expected_key, record in zip(wanted, payload['draws']):
        require(set(record) == {'namespace', 'proposal', 'initial', 'field', 'index', 'modulus', 'raw', 'preimage', 'digest', 'prefix'}, 'draw shape')
        require(all(type(record[k]) is int for k in ('proposal', 'initial', 'index', 'modulus')), 'draw integer coordinates')
        key = record['initial'], record['field'], record['index']
        require(key == expected_key and key not in values and record['modulus'] == wanted[key], 'draw key/modulus')
        require(record['namespace'] == 'p01-generator-v4' and record['proposal'] == cell['proposal'], 'draw law scope')
        i, field, index = key
        # Deliberately independent of either sampler's serializer/source.
        message = ('["p01-generator-v4",' + str(cell['proposal']) + ',' + str(i) + ',"' + field + '",' + str(index) + ']').encode('utf-8')
        require(record['preimage'].encode('utf-8') == message, 'draw preimage')
        digest = digest_function(message)
        prefix = int(digest[0:16], 16)
        require(record['digest'] == digest and type(record['prefix']) is int and record['prefix'] == prefix,
                'digest/prefix')
        require(type(record['raw']) is int and record['raw'] == prefix % wanted[key], 'modulo result')
        values[key] = record['raw']
    mapping = [1 + values[0, 'child_kind_by_donor', i] for i in range(3)]
    states = [values[0, 'role_state_by_kind', i] for i in range(3)]
    fields = [{field: values[0, field, i] for field in RULE_RANGES} for i in range(8)]
    initial = {'id': cell['initial'], 'scheduler': values[cell['initial'], 'scheduler', 0]}
    initial.update({name: [values[cell['initial'], name, i] for i in range(8)] for name in ('node_kind', 'node_state', 'structural')})
    request = dict(mode='assembly', map=mapping, state_map=states, initial_id=cell['initial'], initial_fields=initial, rule_fields=fields)
    env, _ = literal_oracle(request)
    require(canonical(payload['map']) == canonical(mapping) and canonical(payload['state_map']) == canonical(states) and canonical(payload['environment']) == canonical(env), 'independent environment/operation oracle')
    return fields, mapping, states, initial


def verify_law_report(report, raw, mapping, states, rules):
    """Independent raw-field census and predicate checks, not a second call to report code."""
    # Independently normalize only the registered effective constructive fields.
    raw = [dict(row) for row in raw]
    for row in raw:
        donor = row['kind0']
        child = mapping[donor]-1
        if row['form'] in (4, 7) or (row['form'], row['route']) == (3, 1):
            row['state0'] = states[donor]
        if row['form'] == 4:
            row['value'] = states[child]
        if row['form'] == 7 or (row['form'], row['route']) == (3, 1):
            row['state1'] = states[child]
        if (row['form'], row['route']) == (3, 1):
            row['matter'] = 1
    require(report['state_map'] == states and report['v4_correlations_verified'] is True, 'report role states')
    state = lambda n: None if n == 3 else n
    births = [i for i, f in enumerate(raw) if f['form'] == 4]
    funds = [i for i, f in enumerate(raw) if f['form'] == 3 and f['route'] == 1]
    recycles = [i for i, f in enumerate(raw) if f['form'] == 7]
    require(report['map'] == mapping, 'report map')
    digest = hashlib.sha256(canonical([{k: v for k, v in r.items() if k != 'id'} for r in rules]).encode()).hexdigest()
    require(report['law_digest'] == digest, 'report law digest')
    require(report['template_counts'] == dict(Counter(str(f['form']) for f in raw)), 'template census')
    slots = [{'id': i, 'form': f['form'], 'transfer_route': ('Structural' if f['route'] else 'Contact') if f['form'] == 3 else None}
             for i, f in enumerate(raw)]
    require(report['template_slots'] == slots, 'slot census')
    expected_pairs = {}
    for name, ids in [('birth_funding_pairs', funds), ('birth_recycle_pairs', recycles)]:
        pairs = []
        for b, r in itertools.product(births, ids):
            bf, rf = raw[b], raw[r]
            p, q = bf['kind0'] + 1, rf['kind0'] + 1
            birth_pair, rule_pair = [p, mapping[p - 1]], [q, mapping[q - 1]]
            fixed = {state(f['state0']) for f in (bf, rf)} - {None}
            row = dict(birth=b, body=r, birth_kinds=birth_pair, pattern_kinds=rule_pair,
                       kind_match=birth_pair == rule_pair, donor_state_intersection=len(fixed) <= 1,
                       child_birth_state_acceptance=rf['state1'] == 3 or rf['state1'] == bf['value'])
            if name == 'birth_funding_pairs':
                row.update(matter=rf['matter'], activation=rf['amount'] + 1, material_funding=rf['matter'] != 0)
            pairs.append(row)
        require(report[name] == pairs, 'report pairs: ' + name)
        expected_pairs[name] = pairs
    descendants = []
    for b, d in itertools.product(births, births):
        child = mapping[raw[b]['kind0']]
        descendants.append(dict(birth=b, next_birth=d, child_kind=child, next_donor_kind=raw[d]['kind0'] + 1,
            kind_match=child == raw[d]['kind0'] + 1, child_birth_state_acceptance=raw[d]['state0'] in (3, raw[b]['value']),
            newborn_resources=[1, 1], birth_requirements=[3, 2], affordable_at_creation=False))
    require(report['child_donor_pairs'] == descendants, 'descendant paths')
    motifs = []
    for b, f, r, d in itertools.product(births, funds, recycles, births):
        child = mapping[raw[b]['kind0']]
        kinds = raw[b]['kind0'] == raw[f]['kind0'] == raw[r]['kind0'] and child == raw[d]['kind0'] + 1
        joint = len({raw[i]['state0'] for i in (b, f, r)} - {3}) <= 1
        immediate = kinds and joint and all(raw[i]['state1'] in (3, raw[b]['value']) for i in (f, r)) and raw[d]['state0'] in (3, raw[b]['value'])
        motifs.append(dict(birth=b, funding=f, recycle=r, next_birth=d, type_only=kinds,
            joint_donor_state_intersection=joint, immediate_state_aligned=immediate,
            matter_bearing=kinds and raw[f]['matter'] > 0,
            immediate_state_aligned_and_material=immediate and raw[f]['matter'] > 0))
    require(report['joined_motifs'] == motifs, 'same-birth motifs/joint states')
    donors = {raw[b]['kind0'] + 1 for b in births}
    closed = set(donors)
    while True:
        reduced = {k for k in closed if mapping[k - 1] in closed}
        if reduced == closed:
            break
        closed = reduced
    require([p['start'] for p in report['type_paths']] == sorted(donors), 'type path census')
    for path in report['type_paths']:
        visits, current = [], path['start']
        for _ in range(4):
            if current not in donors or current in visits:
                break
            visits.append(current)
            current = mapping[current - 1]
        require(path == dict(start=path['start'], visited=visits, terminus=current,
                closed_type_path=path['start'] in closed, missing_donor=current not in donors), 'type path')
    require(report['state_write_bodies'] == [i for i, f in enumerate(raw) if f['form'] in (0, 1)], 'state writers')
    require(set(report['behavioral_outcomes']) == {'births', 'recycling', 'descendants', 'AP', 'maintenance', 'reproduction', 'heredity', 'adaptation'} and
            all(v == {'value': None, 'reason': 'not_executed'} for v in report['behavioral_outcomes'].values()), 'behavioral nulls')


def audit_panel(bundle, protocol, digest_function):
    """Injected digest interface is mandatory, allowing unhashed literal tests."""
    manifest = load(bundle / 'manifest.json')
    census = load(bundle / 'analysis/static_report/stdout.bin')
    require(census['schema'] == 'p01o-static-census-v1' and len(census['laws']) == 32 and len(census['cells']) == 128 and
            census['chemistry_continuation_gate'] is None and type(census['world_transitions']) is int and
            census['world_transitions'] == 0 and census['law_denominator'] == 32 and
            census['environment_denominator'] == 128 and census['scientific_status'] == 'untested', 'census scope')
    require(len(manifest['rows']) == 128 and all(r['status'] == 'complete' for r in manifest['rows']), 'complete manifest')
    messages = set()
    seen, tables = {}, set()
    for plan, row, cell_report in zip(plans(protocol), manifest['rows'], census['cells']):
        require(all(type(row[k]) is int and row[k] == v for k, v in plan.items()), 'manifest cell identity')
        directory = bundle / 'runs' / str(plan['slot'])
        a = load(directory / 'rust_generation/stdout.bin')
        b = load(directory / 'python_generation/stdout.bin')
        require(canonical(a) == canonical(b), 'sampler differential')
        raw, mapping, states, initial = verify_payload(plan, a, digest_function)
        messages.update(r['preimage'] for r in a['draws'])
        law = census['laws'][plan['slot'] // 4]
        require(law['proposal'] == plan['proposal'], 'law order')
        verify_law_report(law, raw, mapping, states, a['environment']['native']['rules'])
        require(seen.setdefault(plan['proposal'], (mapping, states, law['law_digest'])) == (mapping, states, law['law_digest']), 'law reuse')
        tables.add(law['law_digest'])
        inv = {'kind_state_histogram': {f'{k+1},{s}': n for (k, s), n in sorted(Counter(zip(initial['node_kind'], initial['node_state'])).items())},
               'edge_classes': {'Contact': 8, **({'Structural': sum(initial['structural'])} if any(initial['structural']) else {})},
               'free_matter': 64, 'free_activation': 64, 'matter_total': 80 + sum(initial['structural']), 'activation_total': 64}
        require(cell_report == {**plan, 'law_digest': law['law_digest'], 'inventory': inv}, 'cell inventory census')
        require(row['law_digest'] == law['law_digest'], 'manifest law identity')
    require(len(messages) == 6208 and census['distinct_tables'] == len(tables), 'unique message/table count')
    return dict(schema='p01o-independent-audit-v1', status='pass', cells=128, laws=32,
                logical_draw_records_verified_per_implementation=15232, unique_message_addresses=6208,
                independent_output_and_static_checks=True, world_transitions=0, scientific_status='untested')


def audit_running(bundle):
    protocol = authorize(bundle, 'independent_audit')
    return audit_panel(bundle, protocol, lambda message: hashlib.sha256(message).hexdigest())


def audit_receipts(bundle):
    """Post-seal mode hashes files only. Does not re-evaluate any keyed message."""
    for name, digest in load(bundle / 'checksums.json').items():
        require(sha(bundle / name) == digest, 'inventory identity: ' + name)
    seal = load(bundle / 'seal.json')
    require(seal['checksums_sha256'] == sha(bundle / 'checksums.json') and seal['manifest_sha256'] == sha(bundle / 'manifest.json'), 'seal')
    require(seal['overshoot'] == [] and seal['engineering_gate_pass'] is True, 'sealed engineering gate')
    manifest = load(bundle / 'manifest.json')
    require(len(manifest['rows']) == 128 and all(r['status'] == 'complete' for r in manifest['rows']), 'sealed cells')
    require(load(bundle / 'analysis/independent_audit/stdout.bin')['status'] == 'pass', 'independent audit receipt')
    return dict(schema='p01o-postseal-receipt-audit-v1', status='pass', inventory_files=len(load(bundle / 'checksums.json')),
                seal_sha256=sha(bundle / 'seal.json'), keyed_hash_evaluations=0, world_transitions=0)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--receipts':
        result = audit_receipts(Path(sys.argv[2]))
        with Path(sys.argv[3]).open('x') as f:
            f.write(canonical(result) + '\n')
    else:
        result = audit_running(Path(sys.argv[1]))
    print(canonical(result))
