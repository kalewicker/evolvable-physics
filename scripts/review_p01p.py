#!/usr/bin/env python3
"""Registered saved-record analysis only; no world, sampler or binding engine."""
import hashlib
import itertools
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOW, HIGH = -(2**31), 2**31-1
ACTIVE = None


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def tick():
    if ACTIVE is not None:
        ACTIVE.check()


def load(path):
    tick()
    return json.loads(Path(path).read_bytes())


def sha(path):
    tick()
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Attempt:
    def __init__(self, out):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=False)
        self.start = time.monotonic()
        self.bytes = 0
        self.cap = 134217728
        self.write('started.json', dict(status='started', keyed_evaluations=0, world_transitions=0))

    def check(self):
        require(time.monotonic()-self.start < 120, 'cooperative wall limit')

    def raw(self, name, data, terminal=False):
        if not terminal:
            self.check()
        require(self.bytes+len(data) <= self.cap-(0 if terminal else 1048576), 'emitted byte limit')
        p = self.out/name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(data)
        self.bytes += len(data)

    def write(self, name, data, terminal=False):
        self.raw(name, (json.dumps(data, sort_keys=True, indent=2)+'\n').encode(), terminal)

    def finish(self, result):
        global ACTIVE
        ACTIVE = None
        if time.monotonic()-self.start >= 120:
            result.update(status='fail', error='cooperative wall limit at finalization')
        self.write('assessment.json', result, True)
        inventory = {str(p.relative_to(self.out)): sha(p) for p in sorted(self.out.rglob('*')) if p.is_file()}
        self.write('checksums.json', inventory, True)
        completion = dict(wall_seconds_including_inventory=time.monotonic()-self.start,
            output_bytes_including_completion=0, wall_ceiling_seconds=120, output_ceiling_bytes=self.cap,
            checksums_sha256=sha(self.out/'checksums.json'), status=result['status'])
        while True:
            data = (json.dumps(completion, sort_keys=True, indent=2)+'\n').encode()
            total = self.bytes+len(data)
            if completion['output_bytes_including_completion'] == total:
                break
            completion['output_bytes_including_completion'] = total
        self.raw('completion.json', data, True)
        return result


def prohibit_processes(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in ('os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('P01p read-only tools forbid process creation')


def custody(attempt, test_receipt):
    freeze = load(ROOT/'docs/p01p_analysis_freeze.json')
    for section in ('files', 'inputs', 'prior_public_receipts'):
        for name, digest in freeze[section].items():
            require(sha(ROOT/name) == digest, section+': '+name)
    sources = {**freeze['files'], **{name: sha(ROOT/name) for name in
        ['docs/p01p_analysis_freeze.json', 'scripts/review_p01p.py', 'scripts/audit_p01p.py', 'scripts/test_p01p.py']}}
    tests = load(test_receipt)
    require(tests['status'] == 'pass' and tests['returncodes'] == [0, 0] and tests['state_comparisons'] == 924,
            'invented tests prerequisite')
    for name in ('scripts/review_p01p.py', 'scripts/audit_p01p.py', 'scripts/test_p01p.py'):
        require(tests['sources'][name] == sources[name], 'tested source identity: '+name)
    identities = dict(sources=sources, inputs=freeze['inputs'], test_receipt_sha256=sha(test_receipt))
    attempt.write('identities.json', identities)
    attempt.raw('invented_tests.json', Path(test_receipt).read_bytes())
    for section in ('sources', 'inputs'):
        for name in identities[section]:
            attempt.raw(section+'/'+name, (ROOT/name).read_bytes())
    bundle = ROOT/'artifacts/p01o-001'
    inventory = load(bundle/'checksums.json')
    require({str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file()} ==
            set(inventory)|{'checksums.json', 'seal.json'}, 'original inventory membership')
    for name, digest in inventory.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'inventory path')
        require(sha(bundle/name) == digest, 'original sealed file: '+name)
    seal = load(bundle/'seal.json')
    require(sha(bundle/'seal.json') == freeze['source_seal_sha256'] and
            seal['checksums_sha256'] == sha(bundle/'checksums.json') and
            seal['manifest_sha256'] == sha(bundle/'manifest.json') and seal['engineering_gate_pass'] is True,
            'original seal')
    for name in ('artifacts/p01o-001-receipt-audit.json', 'artifacts/p01o-001-cost-audit.json'):
        require(load(ROOT/name)['status'] == 'pass', 'original independent receipt')
    attempt.write('input_audit.json', dict(status='pass', original_inventory_entries=len(inventory),
        sources_verified=len(sources), analysis_inputs_verified=len(freeze['inputs']),
        prior_receipts_verified=len(freeze['prior_public_receipts']), seal_sha256=sha(bundle/'seal.json')))
    return identities

TAGS = [('SetState',), ('AddState',), ('Burn',), ('Transfer',),
        ('CreateNode', 'CreateEdge', 'Transfer', 'Burn'), ('CreateEdge',),
        ('DeleteEdge',), ('DeleteEdge', 'DeleteNode', 'Burn')]


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
        tick()
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



def validate_rules(rules, mapping=None, states=None):
    require([r['id'] for r in rules] == list(range(8)) and len(rules) == 8, 'ordered slots')
    structural = dict(**{'class': 'Structural'}, kind=0, ends=[0, 1])
    contact = dict(structural, **{'class': 'Contact'})
    for r in rules:
        require(set(r) == {'id', 'nodes', 'edges', 'absent', 'ops'}, 'rule shape')
        f = form(r)
        require(len(r['nodes']) == (2 if f in (3, 5, 6, 7) else 1), 'role count')
        for n in r['nodes']:
            require(set(n) == {'kind', 'state'} and type(n['kind']) is int and n['kind'] in (1, 2, 3) and
                    (n['state'] is None or type(n['state']) is int and n['state'] in (0, 1, 2)), 'predicate alphabet')
        require(r['absent'] == ([structural] if f == 5 else []), 'absent topology')
        if f in (0, 1, 2, 4):
            require(r['edges'] == [], 'unary/birth topology')
        elif f in (6, 7):
            require(r['edges'] == [structural], 'deletion topology')
        elif f == 5:
            require(r['edges'] == [contact], 'Contact creation premise')
        else:
            require(r['edges'] in ([contact], [structural]), 'transfer topology')
        op = r['ops'][0]
        if f == 0:
            require(type(op.get('value')) is int and op['value'] in (0, 1, 2) and
                    op == dict(op='SetState', node=0, value=op['value']), 'SetState alphabet')
        elif f == 1:
            require(type(op.get('delta')) is int and op['delta'] in (-1, 1) and
                    op == dict(op='AddState', node=0, delta=op['delta']), 'AddState alphabet')
        elif f == 2:
            require(type(op.get('amount')) is int and op['amount'] in (1, 2) and
                    op == dict(op='Burn', node=0, amount=op['amount']), 'Burn alphabet')
        elif f == 3:
            require(type(op.get('matter')) is int and type(op.get('activation')) is int and
                    op['matter'] in (0, 1) and op['activation'] in (1, 2) and
                    op == {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': op['matter'], 'activation': op['activation']}, 'Transfer alphabet')
        elif f == 4:
            require(type(op.get('kind')) is int and op['kind'] in (1, 2, 3) and
                    type(op.get('state')) is int and op['state'] in (0, 1, 2), 'newborn alphabet')
            require(r['ops'] == [dict(op='CreateNode', account=0, kind=op['kind'], state=op['state']),
                dict(op='CreateEdge', account=0, kind=0, ends=[0, 1]),
                {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1},
                dict(op='Burn', node=0, amount=1)], 'birth costs/order')
        elif f in (5, 6):
            require(r['ops'] == [dict(op='CreateEdge' if f == 5 else 'DeleteEdge', account=0, kind=0, ends=[0, 1])], 'edge operands')
        else:
            require(r['ops'] == [dict(op='DeleteEdge', account=0, kind=0, ends=[0, 1]),
                dict(op='DeleteNode', node=1, recipient=0), dict(op='Burn', node=0, amount=1)], 'refund operands/order')
        if mapping is not None and (f in (4, 7) or f == 3 and r['edges'] == [structural]):
            p = r['nodes'][0]['kind']; c = mapping[p-1]
            require(r['nodes'][0]['state'] == states[p-1], 'v4 donor state')
            if f == 4:
                require(op['kind'] == c and op['state'] == states[c-1], 'v4 newborn role')
            else:
                require(r['nodes'][1] == dict(kind=c, state=states[c-1]), 'v4 pair role')
                if f == 3:
                    require(op['matter'] == 1, 'v4 material funding')


def ledger(matter, activation, cleanup=None):
    require(matter in (0, 1) and activation in (1, 2) and cleanup in (None, 6, 7), 'ledger alphabet')
    funded = [1+2*matter, 1+2*activation]
    parent = [5-2*matter, 6-2*activation]
    feasible = funded[0] >= 3 and funded[1] >= 2 and all(n >= 0 for n in parent)
    result = dict(newborn=[1, 1], birth_requirement=[3, 2], matter_per_transfer=matter,
        activation_per_funding=activation, transfers=2, parent_after_birth=[5, 6],
        parent_after_funding=parent, child_after_funding=funded, funded_birth_affordable=feasible)
    if cleanup is not None:
        result.update(cleanup_form=cleanup, child_after_descendant_birth=[0, 2*activation-1] if feasible else None,
            grandchild_at_birth=[1, 1] if feasible else None,
            child_after_cleanup=[1 if cleanup == 6 else 3, 2*activation-1] if feasible else None,
            parent_after_recycling=[6 if cleanup == 6 else 8, 4] if feasible else None,
            grandchild_after_cleanup=([1, 1] if cleanup == 6 else None) if feasible else None,
            total_dissipated_activation=(3 if cleanup == 6 else 4) if feasible else None)
    return result


def topology_conditions(cleanup, creation_edge_present=True, child_extra_incidence=False, grandchild_leaf=True):
    return dict(scenario='conditional isolated P-C-G branch', creation_edge_present=creation_edge_present,
        child_extra_incidence=child_extra_incidence, grandchild_leaf=grandchild_leaf,
        grandchild_leaf_required=cleanup == 7, grandchild_survives=cleanup == 6,
        permitted=creation_edge_present and not child_extra_incidence and (cleanup != 7 or grandchild_leaf),
        measured_world_topology=False)


def evaluate(rules, b, f=None, d=None, r=None, k=None, **assumptions):
    tick()
    pk, ck = b['nodes'][0]['kind'], b['ops'][0]['kind']
    gk = None if d is None else d['ops'][0]['kind']
    dg, cg, gg, kinds = [], [], [], {}
    if f is not None:
        kinds['funding'] = [pk, ck] == [n['kind'] for n in f['nodes']]
        dg.append(f['nodes'][0]['state']); cg.append(f['nodes'][1]['state'])
    if d is not None:
        kinds['next_birth'] = ck == d['nodes'][0]['kind']; cg.append(d['nodes'][0]['state'])
    if k is not None:
        require(d is not None, 'cleanup requires descendant descriptor')
        kinds['cleanup'] = [ck, gk] == [n['kind'] for n in k['nodes']]
        cg.append(k['nodes'][0]['state']); gg.append(k['nodes'][1]['state'])
    if r is not None:
        kinds['recycling'] = [pk, ck] == [n['kind'] for n in r['nodes']]
        dg.append(r['nodes'][0]['state']); cg.append(r['nodes'][1]['state'])
    bs = b['nodes'][0]['state']; cs = b['ops'][0]['state']
    donor = phase_chain([[LOW, HIGH]] if bs is None else [[bs, bs]], dg, writers_for(rules, pk))
    child = phase_chain([[cs, cs]], cg, writers_for(rules, ck))
    grandchild = None if d is None else phase_chain([[d['ops'][0]['state'], d['ops'][0]['state']]], gg, writers_for(rules, gk))
    paths = {'parent': donor, 'child': child, **({} if grandchild is None else {'grandchild': grandchild})}
    kind_ok = all(kinds.values()); state_ok = all(v['permitted'] for v in paths.values())
    immediate = kind_ok and len({s for s in [bs]+dg if s is not None}) <= 1 and all(s in (None, cs) for s in cg)
    if d is not None:
        immediate = immediate and all(s in (None, d['ops'][0]['state']) for s in gg)
    material = None if f is None else f['ops'][0]['matter'] == 1
    budget = None if f is None else ledger(f['ops'][0]['matter'], f['ops'][0]['activation'], None if k is None else form(k))
    topology = None if k is None else topology_conditions(form(k), **assumptions)
    reasons = ['kind_mismatch:'+name for name, value in kinds.items() if not value]
    reasons += ['state_phase_exclusion:'+name for name, value in paths.items() if not value['permitted']]
    if material is False:
        reasons.append('no_material_funding')
    if budget is not None and not budget['funded_birth_affordable']:
        reasons.append('conditional_funding_budget')
    if topology is not None and not topology['permitted']:
        reasons.append('conditional_topology_assumption')
    classification = 'local_condition_excluded' if reasons else 'permitted_by_abstraction'
    if not reasons and r is not None and d is not None and k is None:
        classification = 'unresolved'
    return dict(birth=b['id'], funding=None if f is None else f['id'], next_birth=None if d is None else d['id'],
        recycling=None if r is None else r['id'], cleanup=None if k is None else k['id'],
        cleanup_form=None if k is None else form(k), kind_checks=kinds, kind_match=kind_ok,
        paths=paths, immediate_state_aligned=bool(immediate), phased_state_permitted=kind_ok and state_ok,
        material_bearing=material, phased_state_and_material=bool(kind_ok and state_ok and material),
        budget=budget, topology=topology, classification=classification, reasons=reasons,
        executable_reachability=None, unresolved=['scheduler', 'caps', 'outside_family_interference', 'resource_history', 'detectors'])


def combinations(rules):
    births = [r for r in rules if form(r) == 4]
    funds = [r for r in rules if form(r) == 3 and r['edges'][0]['class'] == 'Structural']
    recycles = [r for r in rules if form(r) == 7]
    cleanups = [r for r in rules if form(r) in (6, 7)]
    return dict(birth_funding_pairs=[(b, f, None, None, None) for b, f in itertools.product(births, funds)],
        birth_recycle_pairs=[(b, None, None, r, None) for b, r in itertools.product(births, recycles)],
        child_next_birth_pairs=[(b, None, d, None, None) for b, d in itertools.product(births, births)],
        funded_descendant_triples=[(b, f, d, None, None) for b, f, d in itertools.product(births, funds, births)],
        joined_quadruples=[(b, f, d, r, None) for b, f, d, r in itertools.product(births, funds, births, recycles)],
        cleanup_annotated_quintuples=[(b, f, d, r, k) for b, f, d, r, k in itertools.product(births, funds, births, recycles, cleanups)])


def counts(rows):
    return dict(total=len(rows), kind_match=sum(r['kind_match'] for r in rows),
        immediate_state_aligned=sum(r['immediate_state_aligned'] for r in rows),
        phased_state_permitted=sum(r['phased_state_permitted'] for r in rows),
        phased_state_and_material=sum(r['phased_state_and_material'] for r in rows),
        cleanup6_permitted=sum(r['cleanup_form'] == 6 and r['classification'] == 'permitted_by_abstraction' for r in rows),
        cleanup7_permitted=sum(r['cleanup_form'] == 7 and r['classification'] == 'permitted_by_abstraction' for r in rows),
        classifications={name: sum(r['classification'] == name for r in rows) for name in
            ('local_condition_excluded', 'permitted_by_abstraction', 'unresolved')})


def law_review(proposal, digest, mapping, states, rules):
    validate_rules(rules, mapping, states)
    groups = {name: [evaluate(rules, *args) for args in tuples] for name, tuples in combinations(rules).items()}
    populations = dict(birth=sum(form(r) == 4 for r in rules),
        funding=sum(form(r) == 3 and r['edges'][0]['class'] == 'Structural' for r in rules),
        recycling=sum(form(r) == 7 for r in rules), cleanup=sum(form(r) in (6, 7) for r in rules))
    return dict(proposal=proposal, law_digest=digest, map=mapping, state_map=states, rules=rules,
        populations=populations, missing_body_roles=[k for k, v in populations.items() if v == 0],
        counts={name: counts(rows) for name, rows in groups.items()}, **groups)


def summarize(laws, cells):
    totals, positive = {}, {}
    for group in laws[0]['counts']:
        totals[group] = {key: sum(l['counts'][group][key] for l in laws) for key in laws[0]['counts'][group] if key != 'classifications'}
        positive[group] = {key: sum(l['counts'][group][key] > 0 for l in laws) for key in totals[group]}
        totals[group]['classifications'] = {name: sum(l['counts'][group]['classifications'][name] for l in laws)
            for name in ('local_condition_excluded', 'permitted_by_abstraction', 'unresolved')}
    return dict(schema='p01p-resource-state-topology-review-v1', law_cells=len(laws), initial_records=len(cells),
        totals=totals, positive_tables=positive,
        original_birth_checks=sum(len(c['original_birth_state_checks']) for c in cells),
        original_birth_state_permitted=sum(b['state_path']['permitted'] for c in cells for b in c['original_birth_state_checks']),
        founder_cleanup_checks=sum(len(c['founder_cleanup_checks']) for c in cells),
        founder_cleanup_classifications={name: sum(r['classification'] == name for c in cells for r in c['founder_cleanup_checks'])
            for name in ('local_condition_excluded', 'permitted_by_abstraction', 'unresolved')},
        behavioral_outcomes=None, behavioral_missing_reason='not_executed', executable_reachability=None,
        chemistry_continuation_gate=None, keyed_evaluations=0, world_transitions=0, scientific_status='untested')


def founder_check(q, index, permitted_seed):
    return dict(quintuple_index=index, birth=q['birth'], original_seed_permitted=permitted_seed,
        classification=q['classification'] if permitted_seed else 'local_condition_excluded',
        reason='inherits_conditional_local_checks' if permitted_seed else 'original_seed_exclusion_for_this_founder_only',
        scope='specified_original_founder_only')


def analyze(bundle, attempt, identities):
    manifest = load(bundle/'manifest.json')
    census = load(bundle/'analysis/static_report/stdout.bin')
    require(len(manifest['rows']) == 128 and manifest['execution_status'] == 'complete', 'complete original panel')
    laws, cells = {}, []
    for slot, row in enumerate(manifest['rows']):
        tick()
        require(canonical({k: row[k] for k in ('slot', 'proposal', 'initial', 'status')}) ==
                canonical(dict(slot=slot, proposal=6000+slot//4, initial=slot%4, status='complete')), 'fixed cell identity')
        sample = load(bundle/'runs'/str(slot)/'rust_generation/stdout.bin')
        require(canonical(sample) == canonical(load(bundle/'runs'/str(slot)/'python_generation/stdout.bin')), 'saved generator agreement')
        require(canonical({k: sample[k] for k in ('slot', 'proposal', 'initial')}) ==
                canonical(dict(slot=slot, proposal=6000+slot//4, initial=slot%4)), 'saved payload identity')
        mapping, states = sample['map'], sample['state_map']
        require(len(mapping) == len(states) == 3 and all(type(n) is int and 1 <= n <= 3 for n in mapping) and
                all(type(s) is int and 0 <= s <= 2 for s in states), 'maps')
        native = sample['environment']['native']; rules = native['rules']
        digest = hashlib.sha256(canonical([{k: v for k, v in r.items() if k != 'id'} for r in rules]).encode()).hexdigest()
        require(digest == row['law_digest'] == census['laws'][slot//4]['law_digest'], 'ordered law identity')
        if row['proposal'] not in laws:
            laws[row['proposal']] = law_review(row['proposal'], digest, mapping, states, rules)
        law = laws[row['proposal']]
        require(canonical([law['rules'], law['map'], law['state_map']]) == canonical([rules, mapping, states]), 'cross-initial reuse')
        world = native['world']; nodes = list(world['nodes'].values())
        require(len(nodes) == 8 and set(world['nodes']) == {str(i) for i in range(8)} and world['next_node'] == 8 and
                world['epoch'] == world['next_event'] == world['dissipated'] == 0 and world['activation_total'] == 64,
                'original inventory counters')
        require(all(type(n['kind']) is int and n['kind'] in (1, 2, 3) and type(n['state']) is int and n['state'] in (0, 1, 2)
                    and n['matter'] == n['activation'] == 8 for n in nodes), 'original resources/seeds')
        require(sample['environment']['profile'] == 'p00c-local-driven-v1' and sample['environment']['channels'] == [] and
                native['profile'] == 'p00a-local-closed-v1' and native['limits'] ==
                dict(max_candidates=4096, max_bindings=65536, max_nodes=128, max_edges=256), 'original profiles/caps')
        require(len([e for e in world['edges'].values() if e['class'] == 'Contact']) == 8 and
                {tuple(e['ends']) for e in world['edges'].values() if e['class'] == 'Contact'} == {(i, (i+1)%8) for i in range(8)}, 'Contact ring')
        histogram = {f'{k},{s}': sum(n['kind'] == k and n['state'] == s for n in nodes) for k in (1, 2, 3) for s in (0, 1, 2)}
        seeds = {str(k): sorted({n['state'] for n in nodes if n['kind'] == k}) for k in (1, 2, 3)}
        births = [r for r in rules if form(r) == 4]
        birth_checks = []
        for b in births:
            kind = b['nodes'][0]['kind']
            path = phase_chain([[s, s] for s in seeds[str(kind)]], [b['nodes'][0]['state']], writers_for(rules, kind))
            birth_checks.append(dict(birth=b['id'], kind=kind, original_kind_count=sum(n['kind'] == kind for n in nodes), state_path=path))
        access = {b['birth']: b['state_path']['permitted'] for b in birth_checks}
        founder = []
        for i, q in enumerate(law['cleanup_annotated_quintuples']):
            permitted_seed = access[q['birth']]
            founder.append(founder_check(q, i, permitted_seed))
        cells.append(dict(slot=slot, proposal=row['proposal'], initial=slot%4, original_kind_state_histogram=histogram,
            original_state_seeds=seeds, original_birth_state_checks=birth_checks, founder_cleanup_checks=founder))
    rows = list(laws.values())
    require([r['proposal'] for r in rows] == list(range(6000, 6032)) and len(cells) == 128, 'all-table denominator')
    summary = summarize(rows, cells)
    attempt.write('laws.json', rows)
    attempt.write('public_laws.json', [{k: v for k, v in r.items() if k != 'rules'} for r in rows])
    attempt.write('cells.json', cells)
    attempt.write('summary.json', summary)
    attempt.write('manifest.json', dict(schema='p01p-read-only-review-manifest-v1', status='complete',
        input_manifest_sha256=sha(bundle/'manifest.json'), input_seal_sha256=sha(bundle/'seal.json'),
        laws=32, cells=128, sources=identities['sources'], scope='registered conditional state/resource/topology abstraction only'))
    return dict(status='pass', laws=32, cells=128, body_combinations=sum(c['total'] for l in rows for c in l['counts'].values()),
        keyed_evaluations=0, world_transitions=0, scientific_status='untested')


def run(bundle, out, test_receipt):
    global ACTIVE
    attempt = Attempt(out); ACTIVE = attempt
    try:
        require(Path(bundle).resolve() == (ROOT/'artifacts/p01o-001').resolve(), 'fixed retained bundle')
        identities = custody(attempt, test_receipt)
        result = analyze(Path(bundle), attempt, identities)
    except Exception as error:
        result = dict(status='fail', error=repr(error), keyed_evaluations=0, world_transitions=0, scientific_status='untested')
    return attempt.finish(result)


if __name__ == '__main__':
    sys.addaudithook(prohibit_processes)
    result = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(canonical(result))
    if result['status'] != 'pass':
        raise SystemExit(1)
