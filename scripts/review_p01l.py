#!/usr/bin/env python3
"""Saved-table state algebra; no sampler, rule binding or world interpreter."""
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOW, HIGH = -(2**31), 2**31 - 1
TAGS = [('SetState',), ('AddState',), ('Burn',), ('Transfer',),
        ('CreateNode', 'CreateEdge', 'Transfer', 'Burn'), ('CreateEdge',),
        ('DeleteEdge',), ('DeleteEdge', 'DeleteNode', 'Burn')]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write('\n')


def normalize(intervals):
    result = []
    for lo, hi in sorted(intervals):
        require(LOW <= lo <= hi <= HIGH, 'i32 interval')
        if result and lo <= result[-1][1] + 1:
            result[-1][1] = max(hi, result[-1][1])
        else:
            result.append([lo, hi])
    return result


def contains(intervals, state):
    return any(lo <= state <= hi for lo, hi in intervals)


def predicate(intervals, guard):
    return intervals if guard is None else ([[guard, guard]] if contains(intervals, guard) else [])


def closure(intervals, writers):
    """Exact unary-state relation closure, compact even for wildcard drift."""
    current = normalize(intervals)
    while True:
        extended = list(current)
        for w in writers:
            guard, op = w['nodes'][0]['state'], w['ops'][0]
            seeds = predicate(current, guard)
            if not seeds:
                continue
            if op['op'] == 'SetState':
                extended.append([op['value'], op['value']])
            elif guard is None:
                # Repetition of the same wildcard writer fills this whole ray.
                extended.append([min(x[0] for x in seeds), HIGH] if op['delta'] == 1
                                else [LOW, max(x[1] for x in seeds)])
            else:
                target = guard + op['delta']
                if LOW <= target <= HIGH:
                    extended.append([target, target])
        after = normalize(extended)
        if after == current:
            return current
        current = after


def phase_chain(start, guards, writers):
    phases = []
    current = start
    for guard in guards:
        reachable = closure(current, writers)
        current = predicate(reachable, guard)
        phases.append(dict(guard=guard, reachable=reachable, accepted=current))
    return dict(start=start, phases=phases, permitted=bool(current))


def form(rule):
    tags = tuple(o['op'] for o in rule['ops'])
    require(tags in TAGS, 'template operation alphabet')
    return TAGS.index(tags)


def writers_for(rules, kind):
    return [r for r in rules if form(r) in (0, 1) and r['nodes'][0]['kind'] == kind]


def validate_rules(rules):
    require([r['id'] for r in rules] == list(range(8)), 'ordered slots')
    for r in rules:
        f = form(r)
        require(all(n['kind'] in (1, 2, 3) and n['state'] in (None, 0, 1, 2) for n in r['nodes']), 'predicate alphabet')
        if f in (0, 1):
            require(len(r['nodes']) == 1 and not r['edges'] and not r['absent'], 'unary template')
            op = r['ops'][0]
            require(op['node'] == 0 and (op.get('value') in (0, 1, 2) if f == 0 else op.get('delta') in (-1, 1)), 'writer alphabet')
        elif f == 3:
            require(r['ops'][0]['matter'] in (0, 1) and r['ops'][0]['activation'] in (1, 2), 'transfer alphabet')
        elif f == 4:
            require(r['ops'][0]['state'] in (0, 1, 2), 'newborn state')


def evaluate_motif(rules, b, funding=None, descendant=None, recycling=None):
    parent, child = b['nodes'][0], b['ops'][0]
    kind_checks = {}
    donor_guards, child_guards = [], []
    if funding is not None:
        kind_checks['funding'] = [parent['kind'], child['kind']] == [n['kind'] for n in funding['nodes']]
        donor_guards.append(funding['nodes'][0]['state'])
        child_guards.append(funding['nodes'][1]['state'])
    if descendant is not None:
        kind_checks['next_birth'] = child['kind'] == descendant['nodes'][0]['kind']
        child_guards.append(descendant['nodes'][0]['state'])
    if recycling is not None:
        kind_checks['recycling'] = [parent['kind'], child['kind']] == [n['kind'] for n in recycling['nodes']]
        donor_guards.append(recycling['nodes'][0]['state'])
        child_guards.append(recycling['nodes'][1]['state'])
    start = [[LOW, HIGH]] if parent['state'] is None else [[parent['state'], parent['state']]]
    donor_path = phase_chain(start, donor_guards, writers_for(rules, parent['kind']))
    child_path = phase_chain([[child['state'], child['state']]], child_guards, writers_for(rules, child['kind']))
    kinds = all(kind_checks.values())
    phased = kinds and donor_path['permitted'] and child_path['permitted']
    immediate = kinds and all(predicate(start, g) for g in donor_guards)
    # A single common donor state is required for the original immediate test.
    exact_donor = {g for g in [parent['state']] + donor_guards if g is not None}
    immediate = bool(immediate and len(exact_donor) <= 1 and all(g in (None, child['state']) for g in child_guards))
    material = None if funding is None else funding['ops'][0]['matter'] == 1
    amount = None if funding is None else funding['ops'][0]['activation']
    budget = None if funding is None else dict(
        newborn=[1, 1], construction_requirement=[3, 2],
        matter_per_transfer=funding['ops'][0]['matter'], activation_per_transfer=amount,
        transfers_required=2 if material else None,
        conditional_original_donor_after_birth=[5, 6],
        conditional_donor_after_funding=[3, 6 - 2 * amount] if material else None,
        conditional_child_after_funding=[3, 1 + 2 * amount] if material else None,
        affordable_from_untouched_original=bool(material and 6 >= 2 * amount))
    return dict(birth=b['id'], funding=None if funding is None else funding['id'],
                next_birth=None if descendant is None else descendant['id'],
                recycling=None if recycling is None else recycling['id'],
                kind_checks=kind_checks, kind_match=kinds, immediate_state_aligned=immediate,
                donor=donor_path, child=child_path, phased_state_permitted=phased,
                material_bearing=material, phased_state_and_material=bool(phased and material),
                budget=budget, executable_reachability=None, unresolved=['topology', 'resource_history', 'scheduler', 'caps', 'detectors'])


def law_review(proposal, digest, rules):
    validate_rules(rules)
    births = [r for r in rules if form(r) == 4]
    funds = [r for r in rules if form(r) == 3 and r['edges'][0]['class'] == 'Structural']
    recycles = [r for r in rules if form(r) == 7]
    groups = {
        'funding_pairs': [evaluate_motif(rules, b, funding=f) for b, f in itertools.product(births, funds)],
        'recycling_pairs': [evaluate_motif(rules, b, recycling=r) for b, r in itertools.product(births, recycles)],
        'descendant_pairs': [evaluate_motif(rules, b, descendant=d) for b, d in itertools.product(births, births)],
        'funded_descendant_triples': [evaluate_motif(rules, b, funding=f, descendant=d) for b, f, d in itertools.product(births, funds, births)],
        'joined_quadruples': [evaluate_motif(rules, b, funding=f, descendant=d, recycling=r) for b, f, d, r in itertools.product(births, funds, births, recycles)]}
    counts = {name: dict(total=len(rows), **{k: sum(bool(r[k]) for r in rows) for k in
              ('kind_match', 'immediate_state_aligned', 'phased_state_permitted', 'phased_state_and_material')}) for name, rows in groups.items()}
    return dict(proposal=proposal, law_digest=digest, rules=rules, birth_bodies=len(births),
                state_writer_ids=[r['id'] for r in rules if form(r) in (0, 1)],
                counts=counts, **groups)


def verify_inputs(bundle):
    freeze = load(ROOT / 'docs/p01l_analysis_freeze.json')
    for name, digest in freeze['files'].items():
        require(sha(ROOT / name) == digest, 'plan/semantics identity: ' + name)
    for name, digest in freeze['inputs'].items():
        require(sha(ROOT / name) == digest, 'input identity: ' + name)
    inventory = load(bundle / 'checksums.json')
    actual = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file()}
    require(actual == set(inventory) | {'checksums.json', 'seal.json'}, 'original inventory membership')
    for name, digest in inventory.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'inventory path')
        require(sha(bundle / name) == digest, 'sealed file: ' + name)
    seal = load(bundle / 'seal.json')
    require(seal['checksums_sha256'] == sha(bundle / 'checksums.json') and seal['manifest_sha256'] == sha(bundle / 'manifest.json'), 'seal links')
    require(seal['engineering_gate_pass'] and not seal['overshoot'], 'original gate')
    return dict(status='pass', inventory_files=len(inventory), seal_sha256=sha(bundle / 'seal.json'),
                plan_sha256=sha(ROOT / 'docs/p01l_analysis_plan.md'), keyed_hash_evaluations=0, world_transitions=0)


def run(bundle, out):
    require(bundle.resolve() == (ROOT / 'artifacts/p01k-001').resolve(), 'fixed retained bundle')
    custody = verify_inputs(bundle)
    manifest = load(bundle / 'manifest.json')
    census = load(bundle / 'analysis/static_report/stdout.bin')
    require(len(manifest['rows']) == 128, 'environment denominator')
    laws, cells = {}, []
    for slot, row in enumerate(manifest['rows']):
        require((row['slot'], row['proposal'], row['initial'], row['status']) ==
                (slot, 5000 + slot // 4, slot % 4, 'complete'), 'complete cell identity')
        sampled = load(bundle / 'runs' / str(slot) / 'rust_generation/stdout.bin')
        other = load(bundle / 'runs' / str(slot) / 'python_generation/stdout.bin')
        require(sampled == other, 'saved adapter agreement')
        rules = sampled['environment']['native']['rules']
        digest = hashlib.sha256(json.dumps([{k: v for k, v in r.items() if k != 'id'} for r in rules],
                                sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        require(digest == row['law_digest'] == census['laws'][slot // 4]['law_digest'], 'ordered table identity')
        if row['proposal'] not in laws:
            laws[row['proposal']] = law_review(row['proposal'], digest, rules)
        require(laws[row['proposal']]['rules'] == rules, 'cross-initial table reuse')
        original = sampled['environment']['native']['world']['nodes']
        require(len(original) == 8 and all(n['matter'] == 8 and n['activation'] == 8 for n in original.values()), 'original budget')
        seeds = {str(k): sorted({n['state'] for n in original.values() if n['kind'] == k}) for k in (1, 2, 3)}
        checks = []
        for b in rules:
            if form(b) != 4:
                continue
            parent = b['nodes'][0]
            path = phase_chain([[s, s] for s in seeds[str(parent['kind'])]], [parent['state']], writers_for(rules, parent['kind']))
            checks.append(dict(birth=b['id'], state_path=path))
        cells.append(dict(slot=slot, proposal=row['proposal'], initial=row['initial'], original_state_seeds=seeds,
                          original_birth_state_checks=checks))
    rows = list(laws.values())
    require(len(rows) == 32 and len({r['law_digest'] for r in rows}) == 32, 'all distinct tables')
    totals = {g: {k: sum(r['counts'][g][k] for r in rows) for k in rows[0]['counts'][g]} for g in rows[0]['counts']}
    positive = {g: {k: sum(r['counts'][g][k] > 0 for r in rows) for k in rows[0]['counts'][g]} for g in rows[0]['counts']}
    summary = dict(schema='p01l-static-state-resource-review-v1', law_cells=32, initial_environments=128,
                   totals=totals, positive_tables=positive, birth_bodies=sum(r['birth_bodies'] for r in rows),
                   original_birth_checks=sum(len(c['original_birth_state_checks']) for c in cells),
                   original_birth_state_permitted=sum(p['state_path']['permitted'] for c in cells for p in c['original_birth_state_checks']),
                   chemistry_continuation_gate=None, behavioral_outcomes=None, behavioral_missing_reason='not_executed',
                   executable_reachability=None, keyed_hash_evaluations=0, world_transitions=0, scientific_status='untested')
    out.mkdir(parents=True, exist_ok=False)
    sources = {name: sha(ROOT / name) for name in ['docs/p01l_analysis_plan.md', 'docs/p01l_analysis_freeze.json', 'scripts/review_p01l.py']}
    write(out / 'input_audit.json', custody)
    write(out / 'laws.json', rows)
    write(out / 'cells.json', cells)
    write(out / 'summary.json', summary)
    write(out / 'manifest.json', dict(schema='p01l-review-manifest-v1', status='complete', sources=sources,
          input_manifest_sha256=sha(bundle / 'manifest.json'), input_seal_sha256=sha(bundle / 'seal.json'),
          laws=32, cells=128, scope='post-hoc unary-state algebra and conditional resource budgets only'))
    write(out / 'checksums.json', {str(p.relative_to(out)): sha(p) for p in sorted(out.iterdir())})
    return summary


def prohibit_processes(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in ('os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('P01l saved-record review forbids process execution')


if __name__ == '__main__':
    sys.addaudithook(prohibit_processes)
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
