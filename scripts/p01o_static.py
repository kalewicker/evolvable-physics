#!/usr/bin/env python3
"""Static body algebra and initial inventories. No matching or world execution."""
import itertools
import sys
from collections import Counter
from pathlib import Path
from p01o_contract import canonical, load, require
import hashlib


def table_digest(rules):
    bodies = [{k: v for k, v in r.items() if k != 'id'} for r in rules]
    return hashlib.sha256(canonical(bodies).encode()).hexdigest()


def intersects(*states):
    return len({s for s in states if s is not None}) <= 1


def accepts(predicate, state):
    return predicate is None or predicate == state


def classify(rule):
    tags = [op['op'] for op in rule['ops']]
    names = {('SetState',): 0, ('AddState',): 1, ('Burn',): 2, ('Transfer',): 3,
             ('CreateNode', 'CreateEdge', 'Transfer', 'Burn'): 4, ('CreateEdge',): 5,
             ('DeleteEdge',): 6, ('DeleteEdge', 'DeleteNode', 'Burn'): 7}
    require(tuple(tags) in names, 'unknown body')
    return names[tuple(tags)]


def law_report(mapping, states, rules):
    forms = {r['id']: classify(r) for r in rules}
    births = [r for r in rules if forms[r['id']] == 4]
    funding = [r for r in rules if forms[r['id']] == 3 and r['edges'][0]['class'] == 'Structural']
    recycling = [r for r in rules if forms[r['id']] == 7]
    pairs_f, pairs_r, pairs_d = [], [], []
    for b in births:
        donor, child = b['nodes'][0]['kind'], b['ops'][0]['kind']
        state = b['ops'][0]['state']
        for population, target in [(funding, pairs_f), (recycling, pairs_r)]:
            for r in population:
                row = {'birth': b['id'], 'body': r['id'], 'birth_kinds': [donor, child],
                       'pattern_kinds': [n['kind'] for n in r['nodes']],
                       'kind_match': [donor, child] == [n['kind'] for n in r['nodes']],
                       'donor_state_intersection': intersects(b['nodes'][0]['state'], r['nodes'][0]['state']),
                       'child_birth_state_acceptance': accepts(r['nodes'][1]['state'], state)}
                if population is funding:
                    row.update(matter=r['ops'][0]['matter'], activation=r['ops'][0]['activation'],
                               material_funding=r['ops'][0]['matter'] > 0)
                target.append(row)
        for d in births:
            pairs_d.append({'birth': b['id'], 'next_birth': d['id'], 'child_kind': child,
                            'next_donor_kind': d['nodes'][0]['kind'],
                            'kind_match': child == d['nodes'][0]['kind'],
                            'child_birth_state_acceptance': accepts(d['nodes'][0]['state'], state),
                            'newborn_resources': [1, 1], 'birth_requirements': [3, 2],
                            'affordable_at_creation': False})
    by_id = {r['id']: r for r in rules}
    motifs = []
    for b in births:
        fs = [p for p in pairs_f if p['birth'] == b['id']]
        rs = [p for p in pairs_r if p['birth'] == b['id']]
        ds = [p for p in pairs_d if p['birth'] == b['id']]
        for f, r, d in itertools.product(fs, rs, ds):
            types = f['kind_match'] and r['kind_match'] and d['kind_match']
            joint = intersects(b['nodes'][0]['state'], by_id[f['body']]['nodes'][0]['state'],
                               by_id[r['body']]['nodes'][0]['state'])
            aligned = types and joint and all(x['child_birth_state_acceptance'] for x in (f, r, d))
            motifs.append({'birth': b['id'], 'funding': f['body'], 'recycle': r['body'],
                           'next_birth': d['next_birth'], 'type_only': types,
                           'joint_donor_state_intersection': joint,
                           'immediate_state_aligned': aligned,
                           'matter_bearing': types and f['material_funding'],
                           'immediate_state_aligned_and_material': aligned and f['material_funding']})
    donors = {b['nodes'][0]['kind'] for b in births}
    paths = []
    for start in sorted(donors):
        seen, current = [], start
        while current in donors and current not in seen:
            seen.append(current)
            current = mapping[current - 1]
        paths.append({'start': start, 'visited': seen, 'terminus': current,
                      'closed_type_path': current in seen, 'missing_donor': current not in donors})
    require(all(not m['type_only'] or m['immediate_state_aligned_and_material'] for m in motifs),
            'v4 designed correlation violated')
    return {'state_map': states, 'v4_correlations_verified': True, 'map': mapping, 'law_digest': table_digest(rules),
            'template_slots': [{'id': r['id'], 'form': forms[r['id']],
                                'transfer_route': r['edges'][0]['class'] if forms[r['id']] == 3 else None}
                               for r in rules],
            'template_counts': dict(Counter(str(x) for x in forms.values())),
            'birth_funding_pairs': pairs_f, 'birth_recycle_pairs': pairs_r, 'child_donor_pairs': pairs_d,
            'joined_motifs': motifs, 'type_paths': paths,
            'state_write_bodies': [r['id'] for r in rules if forms[r['id']] in (0, 1)],
            'interpretation': 'local schema predicates only; later state/resource/topology/scheduling reachability untested',
            'behavioral_outcomes': {name: {'value': None, 'reason': 'not_executed'} for name in
                ('births', 'recycling', 'descendants', 'AP', 'maintenance', 'reproduction', 'heredity', 'adaptation')}}


def initial_inventory(environment):
    w = environment['native']['world']
    return {'kind_state_histogram': {f'{k},{s}': n for (k, s), n in sorted(Counter(
                (v['kind'], v['state']) for v in w['nodes'].values()).items())},
            'edge_classes': dict(Counter(e['class'] for e in w['edges'].values())),
            'free_matter': sum(n['matter'] for n in w['nodes'].values()),
            'free_activation': sum(n['activation'] for n in w['nodes'].values()),
            'matter_total': w['matter_total'], 'activation_total': w['activation_total']}


def panel_report(bundle):
    manifest = load(bundle / 'manifest.json')
    require(len(manifest['rows']) == 128 and all(r['status'] == 'complete' for r in manifest['rows']), 'incomplete static panel')
    laws, cells = {}, []
    for row in manifest['rows']:
        sampled = load(bundle / 'runs' / str(row['slot']) / 'rust_generation/stdout.bin')
        report = law_report(sampled['map'], sampled['state_map'], sampled['environment']['native']['rules'])
        proposal = row['proposal']
        require(laws.setdefault(proposal, report) == report, 'map/law census changed across initials')
        cells.append({**{k: row[k] for k in ('slot', 'proposal', 'initial')},
                      'law_digest': report['law_digest'], 'inventory': initial_inventory(sampled['environment'])})
    require(len(laws) == 32, 'law census')
    return {'schema': 'p01o-static-census-v1', 'law_denominator': 32, 'environment_denominator': 128,
            'distinct_tables': len({r['law_digest'] for r in laws.values()}),
            'laws': [{'proposal': p, **r} for p, r in laws.items()], 'cells': cells,
            'chemistry_continuation_gate': None, 'world_transitions': 0, 'scientific_status': 'untested'}


if __name__ == '__main__':
    print(canonical(panel_report(Path(sys.argv[1]))))
