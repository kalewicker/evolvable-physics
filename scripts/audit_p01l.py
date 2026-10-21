#!/usr/bin/env python3
"""Independent five-class state oracle and saved P01l record audit."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

MIN, MAX = -(2**31), 2**31 - 1
BLOCKS = [(MIN, -1), (0, 0), (1, 1), (2, 2), (3, MAX)]


def check(ok, message):
    if not ok:
        raise ValueError(message)


def load(p):
    return json.loads(p.read_bytes())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def category(state):
    return 0 if state < 0 else 4 if state > 2 else state + 1


def project(intervals):
    return {i for i, (lo, hi) in enumerate(BLOCKS) if any(a <= hi and lo <= b for a, b in intervals)}


def relation(writers):
    edges = set()
    for rule in writers:
        guard, op = rule['nodes'][0]['state'], rule['ops'][0]
        check(guard in (None, 0, 1, 2), 'quotient guard alphabet')
        sources = range(5) if guard is None else [guard + 1]
        for src in sources:
            if op['op'] == 'SetState':
                check(op['value'] in (0, 1, 2), 'quotient constant alphabet')
                edges.add((src, op['value'] + 1))
            else:
                check(op['op'] == 'AddState' and op['delta'] in (-1, 1), 'quotient delta alphabet')
                delta = op['delta']
                if src in (0, 4):
                    # Existential within the exterior block; no wrap at i32 bound.
                    edges.add((src, src))
                    if (src, delta) == (0, 1):
                        edges.add((0, 1))
                    if (src, delta) == (4, -1):
                        edges.add((4, 3))
                else:
                    edges.add((src, category(src - 1 + delta)))
    return edges


def reachable(start, writers):
    seen = set(start)
    edges = relation(writers)
    while True:
        after = seen | {b for a, b in edges if a in seen}
        if after == seen:
            return seen
        seen = after


def chain(start, guards, writers, record):
    check(project(record['start']) == start and len(record['phases']) == len(guards), 'phase start/length')
    seen = set(start)
    for guard, phase in zip(guards, record['phases']):
        seen = reachable(seen, writers)
        check(phase['guard'] == guard and project(phase['reachable']) == seen, 'independent phase closure')
        seen &= set(range(5)) if guard is None else {guard + 1}
        check(project(phase['accepted']) == seen, 'independent predicate filter')
    check(record['permitted'] == bool(seen), 'phase verdict')
    return bool(seen)


def topology_premises(rules):
    """Check every retained body needed by the conditional bootstrap argument."""
    structural = {'class': 'Structural', 'kind': 0, 'ends': [0, 1]}
    contact = dict(structural, **{'class': 'Contact'})
    for r in rules:
        tags = [o['op'] for o in r['ops']]
        if tags == ['CreateNode', 'CreateEdge', 'Transfer', 'Burn']:
            check(len(r['nodes']) == 1 and r['edges'] == [] and r['absent'] == [], 'birth topology')
            check(r['ops'][0]['account'] == 0 and r['ops'][1] == dict(op='CreateEdge', account=0, kind=0, ends=[0, 1]) and
                  r['ops'][2] == {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1} and
                  r['ops'][3] == dict(op='Burn', node=0, amount=1), 'birth resource premise')
        elif tags == ['CreateEdge']:
            check(r['edges'] == [contact] and r['absent'] == [structural] and
                  r['ops'] == [dict(op='CreateEdge', account=0, kind=0, ends=[0, 1])], 'Contact-only reconnection premise')
        elif tags == ['Transfer']:
            check(r['edges'] in ([structural], [contact]) and len(r['nodes']) == 2 and
                  r['ops'][0]['from'] == 0 and r['ops'][0]['to'] == 1, 'ordered incoming funding premise')
        elif tags in (['DeleteEdge'], ['DeleteEdge', 'DeleteNode', 'Burn']):
            check(r['edges'] == [structural] and r['ops'][0] == dict(op='DeleteEdge', account=0, kind=0, ends=[0, 1]), 'edge refund source')
            if len(tags) > 1:
                check(r['ops'][1] == dict(op='DeleteNode', node=1, recipient=0) and
                      r['ops'][2] == dict(op='Burn', node=0, amount=1), 'recycling refund source')
        else:
            check(tags in (['SetState'], ['AddState'], ['Burn']) and len(r['nodes']) == 1 and
                  r['ops'][0]['node'] == 0 and r['edges'] == [], 'remaining unary forms')


def audit(bundle, analysis):
    for name, digest in load(analysis / 'checksums.json').items():
        check(sha(analysis / name) == digest, 'analysis custody: ' + name)
    check({p.name for p in analysis.iterdir()} == set(load(analysis / 'checksums.json')) | {'checksums.json'}, 'analysis membership')
    root = Path(__file__).resolve().parents[1]
    manifest = load(analysis / 'manifest.json')
    for name, digest in manifest['sources'].items():
        check(sha(root / name) == digest, 'review source identity')
    check(manifest['input_seal_sha256'] == sha(bundle / 'seal.json') and
          manifest['input_manifest_sha256'] == sha(bundle / 'manifest.json'), 'input links')
    old_inventory = load(bundle / 'checksums.json')
    for name, digest in old_inventory.items():
        check(sha(bundle / name) == digest, 'original custody')
    laws = load(analysis / 'laws.json')
    cells = load(analysis / 'cells.json')
    check([l['proposal'] for l in laws] == list(range(5000, 5032)) and len(cells) == 128, 'all denominators')
    count = 0
    for law in laws:
        slot = (law['proposal'] - 5000) * 4
        rules = load(bundle / 'runs' / str(slot) / 'rust_generation/stdout.bin')['environment']['native']['rules']
        check(law['rules'] == rules, 'retained rules')
        topology_premises(rules)
        births = [r for r in rules if r['ops'][0]['op'] == 'CreateNode']
        funds = [r for r in rules if len(r['ops']) == 1 and r['ops'][0]['op'] == 'Transfer' and r['edges'][0]['class'] == 'Structural']
        recycles = [r for r in rules if any(o['op'] == 'DeleteNode' for o in r['ops'])]
        def writers(kind):
            return [r for r in rules if r['nodes'][0]['kind'] == kind and r['ops'][0]['op'] in ('SetState', 'AddState')]
        groups = {'funding_pairs': [(b, f, None, None) for b, f in itertools.product(births, funds)],
                  'recycling_pairs': [(b, None, None, r) for b, r in itertools.product(births, recycles)],
                  'descendant_pairs': [(b, None, d, None) for b, d in itertools.product(births, births)],
                  'funded_descendant_triples': [(b, f, d, None) for b, f, d in itertools.product(births, funds, births)],
                  'joined_quadruples': list(itertools.product(births, funds, births, recycles))}
        for group, tuples in groups.items():
            check(len(law[group]) == len(tuples), 'all body combinations')
            for row, (b, f, d, r) in zip(law[group], tuples):
                check([row[k] for k in ('birth', 'funding', 'next_birth', 'recycling')] ==
                      [x['id'] if x is not None else None for x in (b, f, d, r)], 'combination identity')
                pk, ck, bs, cs = b['nodes'][0]['kind'], b['ops'][0]['kind'], b['nodes'][0]['state'], b['ops'][0]['state']
                dg, cg, types = [], [], {}
                for other, name in [(f, 'funding'), (d, 'next_birth'), (r, 'recycling')]:
                    if other is None:
                        continue
                    if name == 'next_birth':
                        types[name] = ck == other['nodes'][0]['kind']
                        cg.append(other['nodes'][0]['state'])
                    else:
                        types[name] = (pk, ck) == tuple(n['kind'] for n in other['nodes'])
                        dg.append(other['nodes'][0]['state'])
                        cg.append(other['nodes'][1]['state'])
                donor_ok = chain(set(range(5)) if bs is None else {bs + 1}, dg, writers(pk), row['donor'])
                child_ok = chain({cs + 1}, cg, writers(ck), row['child'])
                kinds = all(types.values())
                immediate = kinds and len({s for s in [bs] + dg if s is not None}) <= 1 and all(s is None or s == cs for s in cg)
                check(row['kind_checks'] == types and row['kind_match'] == kinds and row['immediate_state_aligned'] == immediate, 'kind/immediate oracle')
                permitted = kinds and donor_ok and child_ok
                material = None if f is None else f['ops'][0]['matter'] > 0
                check(row['phased_state_permitted'] == permitted and row['material_bearing'] == material and
                      row['phased_state_and_material'] == bool(permitted and material), 'phased/material oracle')
                if f is not None:
                    m, a = f['ops'][0]['matter'], f['ops'][0]['activation']
                    budget = row['budget']
                    check(budget['transfers_required'] == (2 if m else None) and budget['affordable_from_untouched_original'] == bool(m), 'budget feasibility')
                    check(budget['conditional_original_donor_after_birth'] == [8-3, 8-2], 'birth budget')
                    if m:
                        check(budget['conditional_child_after_funding'] == [1+2*m, 1+2*a] and
                              budget['conditional_donor_after_funding'] == [8-3-2*m, 8-2-2*a], 'funding arithmetic')
                check(row['executable_reachability'] is None, 'no reachability admission')
                count += 1
            for key, value in law['counts'][group].items():
                check(value == (len(tuples) if key == 'total' else sum(bool(r[key]) for r in law[group])), 'descriptive counts')
        for initial in range(4):
            cell = cells[slot + initial]
            check((cell['slot'], cell['proposal'], cell['initial']) == (slot + initial, law['proposal'], initial), 'initial identity')
            native = load(bundle / 'runs' / str(slot + initial) / 'rust_generation/stdout.bin')['environment']['native']
            check(native['rules'] == rules, 'all-initial rule identity')
            check(len(native['world']['nodes']) == 8 and native['world']['next_node'] == 8 and
                  native['world']['activation_total'] == 64 and all(n['matter'] == n['activation'] == 8 for n in native['world']['nodes'].values()), 'original resource premise')
            contact_edges = [e for e in native['world']['edges'].values() if e['class'] == 'Contact']
            check(len(contact_edges) == 8 and {tuple(e['ends']) for e in contact_edges} == {(i, (i + 1) % 8) for i in range(8)}, 'original Contact ring')
            nodes = native['world']['nodes'].values()
            seeds = {str(k): sorted({n['state'] for n in nodes if n['kind'] == k}) for k in (1, 2, 3)}
            check(seeds == cell['original_state_seeds'] and len(cell['original_birth_state_checks']) == len(births), 'original seeds/denominator')
            for b, p in zip(births, cell['original_birth_state_checks']):
                check(p['birth'] == b['id'], 'original birth identity')
                kind = b['nodes'][0]['kind']
                chain({s + 1 for s in seeds[str(kind)]}, [b['nodes'][0]['state']], writers(kind), p['state_path'])
    summary = load(analysis / 'summary.json')
    for group in laws[0]['counts']:
        for key in laws[0]['counts'][group]:
            check(summary['totals'][group][key] == sum(l['counts'][group][key] for l in laws), 'summary totals')
            check(summary['positive_tables'][group][key] == sum(l['counts'][group][key] > 0 for l in laws), 'positive-table denominator')
    check(summary['original_birth_checks'] == sum(len(c['original_birth_state_checks']) for c in cells) and
          summary['original_birth_state_permitted'] == sum(p['state_path']['permitted'] for c in cells for p in c['original_birth_state_checks']), 'original-state totals')
    check(summary['behavioral_outcomes'] is None and summary['behavioral_missing_reason'] == 'not_executed' and
          summary['chemistry_continuation_gate'] is None and summary['keyed_hash_evaluations'] == summary['world_transitions'] == 0, 'scope')
    partition = {k: [] for k in ('no_birth_body', 'no_kind_compatible_funding_descendant_path',
                                 'no_material_funding_on_kind_compatible_path', 'unary_state_exclusion_on_material_path',
                                 'not_excluded_by_this_review')}
    for law in laws:
        paths = [p for p in law['funded_descendant_triples'] if p['kind_match']]
        material = [p for p in paths if p['material_bearing']]
        reason = ('no_birth_body' if not law['birth_bodies'] else
                  'no_kind_compatible_funding_descendant_path' if not paths else
                  'no_material_funding_on_kind_compatible_path' if not material else
                  'unary_state_exclusion_on_material_path' if not any(p['phased_state_permitted'] for p in material) else
                  'not_excluded_by_this_review')
        partition[reason].append(law['proposal'])
    return dict(schema='p01l-independent-state-record-audit-v1', status='pass', laws=32, cells=128,
                combinations_verified=count, state_oracle='independent five-block quotient',
                topology_and_resource_premises_checked=True, bootstrap_partition=partition,
                conditional_source_argument='Under the frozen topology/templates, a newborn first birth requires a material funding/descendant path permitted by this state abstraction; exclusion is scoped to these exact 32 tables, not the sampler or kernel.',
                input_seal_sha256=sha(bundle / 'seal.json'), analysis_checksums_sha256=sha(analysis / 'checksums.json'),
                audit_source_sha256=sha(Path(__file__)), keyed_hash_evaluations=0, world_transitions=0, scientific_status='untested')


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]), Path(sys.argv[2]))
    with Path(sys.argv[3]).open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps(result, sort_keys=True))
