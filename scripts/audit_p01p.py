#!/usr/bin/env python3
"""Independent state quotient, conditional ledgers and saved-record audit."""
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

MIN, MAX = LOW, HIGH
BLOCKS = [(MIN, -1), (0, 0), (1, 1), (2, 2), (3, MAX)]
check = require


def category(state):
    return 0 if state < 0 else 4 if state > 2 else state + 1


def project(intervals):
    return {i for i, (lo, hi) in enumerate(BLOCKS) if any(a <= hi and lo <= b for a, b in intervals)}


def relation(writers):
    edges = set()
    for rule in writers:
        guard, op = rule['nodes'][0]['state'], rule['ops'][0]
        check(guard is None or type(guard) is int and guard in (0, 1, 2), 'quotient guard alphabet')
        sources = range(5) if guard is None else [guard + 1]
        for src in sources:
            if op['op'] == 'SetState':
                check(type(op['value']) is int and op['value'] in (0, 1, 2), 'quotient constant alphabet')
                edges.add((src, op['value'] + 1))
            else:
                check(op['op'] == 'AddState' and type(op['delta']) is int and op['delta'] in (-1, 1), 'quotient delta alphabet')
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
        tick()
        after = seen | {b for a, b in edges if a in seen}
        if after == seen:
            return seen
        seen = after


def chain(start, guards, writers, record):
    check(type(record['permitted']) is bool, 'phase verdict type')
    for phase in record['phases']:
        for intervals in (phase['reachable'], phase['accepted']):
            check(all(len(v) == 2 and all(type(x) is int for x in v) and MIN <= v[0] <= v[1] <= MAX for v in intervals), 'phase interval bounds')
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




def ledger_check(saved, matter, activation, cleanup=None):
    # Independently account debits/credits of the fixed conditional branch.
    p_m, p_a = 8-1-1-1, 8-1-1
    transfer_m, transfer_a = 2*matter, 2*activation
    child_m, child_a = 1+transfer_m, 1+transfer_a
    possible = child_m >= 3 and child_a >= 2 and p_m >= transfer_m and p_a >= transfer_a
    want = dict(newborn=[1, 1], birth_requirement=[3, 2], matter_per_transfer=matter,
        activation_per_funding=activation, transfers=2, parent_after_birth=[p_m, p_a],
        parent_after_funding=[p_m-transfer_m, p_a-transfer_a], child_after_funding=[child_m, child_a], funded_birth_affordable=possible)
    if cleanup is not None:
        remaining_m, remaining_a = child_m-3, child_a-2
        edge_refund, node_refund = 1, 2 if cleanup == 7 else 0
        child_post_m = remaining_m+edge_refund+node_refund
        child_post_a = remaining_a+(1-1 if cleanup == 7 else 0)
        want.update(cleanup_form=cleanup,
            child_after_descendant_birth=[remaining_m, remaining_a] if possible else None,
            grandchild_at_birth=[1, 1] if possible else None,
            child_after_cleanup=[child_post_m, child_post_a] if possible else None,
            parent_after_recycling=[p_m-transfer_m+1+1+child_post_m, p_a-transfer_a+child_post_a-1] if possible else None,
            grandchild_after_cleanup=([1, 1] if cleanup == 6 else None) if possible else None,
            total_dissipated_activation=(2+1+(1 if cleanup == 7 else 0)) if possible else None)
    check(canonical(saved) == canonical(want), 'independent conditional ledger')


def validate_native(rules, mapping, states):
    check(len(rules) == 8 and [r['id'] for r in rules] == list(range(8)), 'ordered native slots')
    topology_premises(rules)
    for r in rules:
        check(set(r) == {'id', 'nodes', 'edges', 'absent', 'ops'}, 'native shape')
        for n in r['nodes']:
            check(set(n) == {'kind', 'state'} and type(n['kind']) is int and n['kind'] in (1, 2, 3) and
                  (n['state'] is None or type(n['state']) is int and n['state'] in (0, 1, 2)), 'native predicates')
        tags = tuple(o['op'] for o in r['ops']); op = r['ops'][0]
        check(len(r['nodes']) == (2 if tags in (('Transfer',), ('CreateEdge',), ('DeleteEdge',), ('DeleteEdge', 'DeleteNode', 'Burn')) else 1), 'native role count')
        if tags[0] == 'CreateNode':
            check(type(op['kind']) is int and type(op['state']) is int and op['kind'] in (1, 2, 3) and op['state'] in (0, 1, 2), 'newborn alphabet')
        constructive = tags in (('CreateNode', 'CreateEdge', 'Transfer', 'Burn'), ('DeleteEdge', 'DeleteNode', 'Burn')) or tags == ('Transfer',) and r['edges'][0]['class'] == 'Structural'
        if constructive:
            parent = r['nodes'][0]['kind']; child = mapping[parent-1]
            check(r['nodes'][0]['state'] == states[parent-1], 'exact constructive donor state')
            if tags[0] == 'CreateNode':
                check(op['kind'] == child and op['state'] == states[child-1], 'exact newborn role')
            else:
                check(len(r['nodes']) == 2 and r['nodes'][1] == dict(kind=child, state=states[child-1]), 'exact pair role')
                if tags == ('Transfer',):check(op['matter'] == 1, 'positive Structural matter')
        if tags == ('SetState',):
            check(type(op.get('value')) is int and op['value'] in (0, 1, 2) and op == dict(op='SetState', node=0, value=op['value']), 'SetState operands')
        elif tags == ('AddState',):
            check(type(op.get('delta')) is int and op['delta'] in (-1, 1) and op == dict(op='AddState', node=0, delta=op['delta']), 'AddState operands')
        elif tags == ('Burn',):
            check(type(op.get('amount')) is int and op['amount'] in (1, 2) and op == dict(op='Burn', node=0, amount=op['amount']), 'Burn operands')
        elif tags == ('Transfer',):
            check(type(op.get('matter')) is int and type(op.get('activation')) is int and op['matter'] in (0, 1) and op['activation'] in (1, 2) and
                  op == {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': op['matter'], 'activation': op['activation']}, 'Transfer operands')
        if tags != ('CreateEdge',):check(r['absent'] == [], 'absence premise')


def audit_row(rules, row, b, f, d, r, k):
    check(all(type(row[name]) is bool for name in ('kind_match', 'phased_state_permitted', 'immediate_state_aligned', 'phased_state_and_material')), 'verdict boolean types')
    pk, ck = b['nodes'][0]['kind'], b['ops'][0]['kind']
    parent_guards, child_guards, grand_guards, types = [], [], [], {}
    if f is not None:
        types['funding'] = (pk, ck) == tuple(n['kind'] for n in f['nodes'])
        parent_guards.append(f['nodes'][0]['state']);child_guards.append(f['nodes'][1]['state'])
    if d is not None:
        types['next_birth'] = d['nodes'][0]['kind'] == ck;child_guards.append(d['nodes'][0]['state'])
    if k is not None:
        types['cleanup'] = (ck, d['ops'][0]['kind']) == tuple(n['kind'] for n in k['nodes'])
        child_guards.append(k['nodes'][0]['state']);grand_guards.append(k['nodes'][1]['state'])
    if r is not None:
        types['recycling'] = (pk, ck) == tuple(n['kind'] for n in r['nodes'])
        parent_guards.append(r['nodes'][0]['state']);child_guards.append(r['nodes'][1]['state'])
    def writers(kind):
        return [body for body in rules if body['nodes'][0]['kind'] == kind and body['ops'][0]['op'] in ('SetState', 'AddState')]
    bs, cs = b['nodes'][0]['state'], b['ops'][0]['state']
    parent_ok = chain(set(range(5)) if bs is None else {bs+1}, parent_guards, writers(pk), row['paths']['parent'])
    child_ok = chain({cs+1}, child_guards, writers(ck), row['paths']['child'])
    states_ok = dict(parent=parent_ok, child=child_ok)
    if d is not None:
        g = d['ops'][0]
        states_ok['grandchild'] = chain({g['state']+1}, grand_guards, writers(g['kind']), row['paths']['grandchild'])
    check(set(row['paths']) == set(states_ok), 'role path census')
    kinds = all(types.values()); phased = kinds and all(states_ok.values())
    immediate = kinds and len({s for s in [bs]+parent_guards if s is not None}) <= 1 and all(s is None or s == cs for s in child_guards)
    if d is not None:immediate = immediate and all(s is None or s == d['ops'][0]['state'] for s in grand_guards)
    material = None if f is None else f['ops'][0]['matter'] != 0
    check(row['kind_checks'] == types and row['kind_match'] == kinds and row['phased_state_permitted'] == phased and
          row['immediate_state_aligned'] == bool(immediate) and row['material_bearing'] == material and
          row['phased_state_and_material'] == bool(phased and material), 'independent role verdicts')
    cleanup_form = None if k is None else (7 if len(k['ops']) == 3 else 6)
    check([row[x] for x in ('birth', 'funding', 'next_birth', 'recycling', 'cleanup')] ==
          [v['id'] if v is not None else None for v in (b, f, d, r, k)] and row['cleanup_form'] == cleanup_form, 'ordered body identity')
    if f is None:check(row['budget'] is None, 'absent funding budget')
    else:ledger_check(row['budget'], f['ops'][0]['matter'], f['ops'][0]['activation'], cleanup_form)
    if k is None:check(row['topology'] is None, 'absent cleanup topology')
    else:
        expected = dict(scenario='conditional isolated P-C-G branch', creation_edge_present=True,
            child_extra_incidence=False, grandchild_leaf=True, grandchild_leaf_required=cleanup_form == 7,
            grandchild_survives=cleanup_form == 6, permitted=True, measured_world_topology=False)
        check(canonical(row['topology']) == canonical(expected), 'conditional topology premises')
    reasons = ['kind_mismatch:'+name for name, value in types.items() if not value]
    reasons += ['state_phase_exclusion:'+name for name, value in states_ok.items() if not value]
    if material is False:reasons.append('no_material_funding')
    if f is not None and not row['budget']['funded_birth_affordable']:reasons.append('conditional_funding_budget')
    status = 'local_condition_excluded' if reasons else ('unresolved' if r is not None and d is not None and k is None else 'permitted_by_abstraction')
    check(row['classification'] == status and row['reasons'] == reasons and row['executable_reachability'] is None and
          row['unresolved'] == ['scheduler', 'caps', 'outside_family_interference', 'resource_history', 'detectors'], 'classification scope')


def audit_records(bundle, analysis, attempt):
    inventory = load(analysis/'checksums.json')
    check({str(p.relative_to(analysis)) for p in analysis.rglob('*') if p.is_file()} ==
          set(inventory)|{'checksums.json', 'completion.json'}, 'analysis inventory membership')
    for name, digest in inventory.items():check(sha(analysis/name) == digest, 'analysis inventory identity: '+name)
    completion = load(analysis/'completion.json')
    check(completion['checksums_sha256'] == sha(analysis/'checksums.json') and completion['status'] == 'pass' and
          completion['wall_seconds_including_inventory'] < 120 and
          completion['output_bytes_including_completion'] == sum(p.stat().st_size for p in analysis.rglob('*') if p.is_file()) <= 134217728,
          'analysis completion limits')
    check(load(analysis/'assessment.json')['status'] == 'pass', 'analysis gate')
    identities = load(analysis/'identities.json')
    for section in ('sources', 'inputs'):
        for name, digest in identities[section].items():
            check(sha(ROOT/name) == digest and sha(analysis/section/name) == digest, 'source/input snapshot identity')
    original = load(bundle/'manifest.json')
    manifest = load(analysis/'manifest.json')
    check(manifest['input_seal_sha256'] == sha(bundle/'seal.json') and manifest['input_manifest_sha256'] == sha(bundle/'manifest.json') and
          manifest['sources'] == identities['sources'] and manifest['status'] == 'complete', 'analysis input links')
    laws, cells = load(analysis/'laws.json'), load(analysis/'cells.json')
    check([l['proposal'] for l in laws] == list(range(6000, 6032)) and len(cells) == 128 and len(original['rows']) == 128, 'all denominators')
    check(canonical(load(analysis/'public_laws.json')) == canonical([{k: v for k, v in l.items() if k != 'rules'} for l in laws]), 'complete public projection')
    verified = 0
    for law in laws:
        tick()
        slot = (law['proposal']-6000)*4
        saved = load(bundle/'runs'/str(slot)/'rust_generation/stdout.bin')
        rules = saved['environment']['native']['rules']
        check(canonical([law['rules'], law['map'], law['state_map']]) == canonical([rules, saved['map'], saved['state_map']]), 'saved rule/map identity')
        validate_native(rules, saved['map'], saved['state_map'])
        digest = hashlib.sha256(canonical([{k: v for k, v in r.items() if k != 'id'} for r in rules]).encode()).hexdigest()
        check(law['law_digest'] == digest == original['rows'][slot]['law_digest'], 'table digest')
        births = [r for r in rules if r['ops'][0]['op'] == 'CreateNode']
        funds = [r for r in rules if len(r['ops']) == 1 and r['ops'][0]['op'] == 'Transfer' and r['edges'][0]['class'] == 'Structural']
        recycles = [r for r in rules if any(o['op'] == 'DeleteNode' for o in r['ops'])]
        cleanups = [r for r in rules if r['ops'][0]['op'] == 'DeleteEdge']
        populations = dict(birth=len(births), funding=len(funds), recycling=len(recycles), cleanup=len(cleanups))
        check(law['populations'] == populations and law['missing_body_roles'] == [k for k, v in populations.items() if not v], 'absent populations')
        groups = dict(birth_funding_pairs=[(b, f, None, None, None) for b, f in itertools.product(births, funds)],
            birth_recycle_pairs=[(b, None, None, r, None) for b, r in itertools.product(births, recycles)],
            child_next_birth_pairs=[(b, None, d, None, None) for b, d in itertools.product(births, births)],
            funded_descendant_triples=[(b, f, d, None, None) for b, f, d in itertools.product(births, funds, births)],
            joined_quadruples=[(b, f, d, r, None) for b, f, d, r in itertools.product(births, funds, births, recycles)],
            cleanup_annotated_quintuples=list(itertools.product(births, funds, births, recycles, cleanups)))
        check(set(law['counts']) == set(groups), 'group denominator')
        for name, combinations in groups.items():
            check(len(law[name]) == len(combinations), 'complete ordered combinations')
            for record, args in zip(law[name], combinations):
                audit_row(rules, record, *args);verified += 1
            records = law[name]
            want = dict(total=len(records), **{key: sum(record[key] for record in records) for key in
                ('kind_match', 'immediate_state_aligned', 'phased_state_permitted', 'phased_state_and_material')},
                cleanup6_permitted=sum(r['cleanup_form'] == 6 and r['classification'] == 'permitted_by_abstraction' for r in records),
                cleanup7_permitted=sum(r['cleanup_form'] == 7 and r['classification'] == 'permitted_by_abstraction' for r in records),
                classifications={label: sum(r['classification'] == label for r in records) for label in
                    ('local_condition_excluded', 'permitted_by_abstraction', 'unresolved')})
            check(canonical(law['counts'][name]) == canonical(want), 'all combination counts')
        for initial in range(4):
            tick()
            cell = cells[slot+initial];raw = original['rows'][slot+initial]
            check(canonical({k: cell[k] for k in ('slot', 'proposal', 'initial')}) == canonical(dict(slot=slot+initial, proposal=law['proposal'], initial=initial)) and
                  all(raw[k] == cell[k] for k in ('slot', 'proposal', 'initial')) and raw['status'] == 'complete', 'cell identity')
            payload = load(bundle/'runs'/str(slot+initial)/'rust_generation/stdout.bin')
            check(canonical(payload) == canonical(load(bundle/'runs'/str(slot+initial)/'python_generation/stdout.bin')), 'all-cell differential custody')
            check(canonical([payload['map'], payload['state_map'], payload['environment']['native']['rules']]) ==
                  canonical([law['map'], law['state_map'], rules]), 'all-initial rule identity')
            native = payload['environment']['native'];world = native['world'];nodes = list(world['nodes'].values())
            check(len(nodes) == 8 and set(world['nodes']) == {str(i) for i in range(8)} and world['next_node'] == 8 and
                  world['epoch'] == world['next_event'] == world['dissipated'] == 0 and world['activation_total'] == 64 and
                  all(n['matter'] == n['activation'] == 8 for n in nodes), 'original inventory premises')
            check(payload['environment']['profile'] == 'p00c-local-driven-v1' and payload['environment']['channels'] == [] and
                  native['profile'] == 'p00a-local-closed-v1' and native['limits'] ==
                  dict(max_candidates=4096, max_bindings=65536, max_nodes=128, max_edges=256), 'profiles/caps')
            check(len([e for e in world['edges'].values() if e['class'] == 'Contact']) == 8 and
                  {tuple(e['ends']) for e in world['edges'].values() if e['class'] == 'Contact'} == {(i, (i+1)%8) for i in range(8)}, 'Contact ring')
            histogram = {f'{k},{s}': sum(n['kind'] == k and n['state'] == s for n in nodes) for k in (1, 2, 3) for s in (0, 1, 2)}
            seeds = {str(k): sorted({n['state'] for n in nodes if n['kind'] == k}) for k in (1, 2, 3)}
            check(cell['original_kind_state_histogram'] == histogram and cell['original_state_seeds'] == seeds and
                  len(cell['original_birth_state_checks']) == len(births), 'all initial seeds')
            access = {}
            for b, record in zip(births, cell['original_birth_state_checks']):
                kind = b['nodes'][0]['kind']
                check(record['birth'] == b['id'] and record['kind'] == kind and record['original_kind_count'] == sum(n['kind'] == kind for n in nodes), 'initial birth descriptor')
                writers = [r for r in rules if r['nodes'][0]['kind'] == kind and r['ops'][0]['op'] in ('SetState', 'AddState')]
                access[b['id']] = chain({s+1 for s in seeds[str(kind)]}, [b['nodes'][0]['state']], writers, record['state_path'])
            check(len(cell['founder_cleanup_checks']) == len(law['cleanup_annotated_quintuples']), 'all conditional founder checks')
            for i, (q, record) in enumerate(zip(law['cleanup_annotated_quintuples'], cell['founder_cleanup_checks'])):
                a = access[q['birth']]
                expected = dict(quintuple_index=i, birth=q['birth'], original_seed_permitted=a,
                    classification=q['classification'] if a else 'local_condition_excluded',
                    reason='inherits_conditional_local_checks' if a else 'original_seed_exclusion_for_this_founder_only', scope='specified_original_founder_only')
                check(canonical(record) == canonical(expected), 'founder scope/identity')
    summary = load(analysis/'summary.json')
    for group in laws[0]['counts']:
        for key in laws[0]['counts'][group]:
            if key == 'classifications':
                want = {label: sum(l['counts'][group][key][label] for l in laws) for label in laws[0]['counts'][group][key]}
                check(summary['totals'][group][key] == want, 'summary classifications')
            else:
                check(summary['totals'][group][key] == sum(l['counts'][group][key] for l in laws) and
                      summary['positive_tables'][group][key] == sum(l['counts'][group][key] > 0 for l in laws), 'summary totals/table counts')
    check(summary['law_cells'] == 32 and summary['initial_records'] == 128 and
          summary['original_birth_checks'] == sum(len(c['original_birth_state_checks']) for c in cells) and
          summary['original_birth_state_permitted'] == sum(b['state_path']['permitted'] for c in cells for b in c['original_birth_state_checks']) and
          summary['founder_cleanup_checks'] == sum(len(c['founder_cleanup_checks']) for c in cells), 'summary initial denominators')
    for label, value in summary['founder_cleanup_classifications'].items():
        check(value == sum(r['classification'] == label for c in cells for r in c['founder_cleanup_checks']), 'summary founder counts')
    check(summary['behavioral_outcomes'] is None and summary['behavioral_missing_reason'] == 'not_executed' and
          summary['executable_reachability'] is None and summary['chemistry_continuation_gate'] is None and
          summary['keyed_evaluations'] == summary['world_transitions'] == 0 and summary['scientific_status'] == 'untested', 'scientific scope')
    return dict(schema='p01p-independent-state-ledger-topology-audit-v1', status='pass', laws=32, cells=128,
        combinations_verified=verified, analysis_inventory_entries=len(inventory),
        state_oracle='independent five-region quotient', conditional_ledger_and_topology_checks=True,
        input_seal_sha256=sha(bundle/'seal.json'), analysis_checksums_sha256=sha(analysis/'checksums.json'),
        executable_reachability=None, keyed_evaluations=0, world_transitions=0, scientific_status='untested')


def run(analysis, out, test_receipt):
    global ACTIVE
    attempt = Attempt(out); ACTIVE = attempt
    try:
        custody(attempt, test_receipt)
        result = audit_records(ROOT/'artifacts/p01o-001', Path(analysis), attempt)
        attempt.write('audit.json', result)
    except Exception as error:
        result = dict(status='fail', error=repr(error), keyed_evaluations=0, world_transitions=0, scientific_status='untested')
    return attempt.finish(result)


if __name__ == '__main__':
    sys.addaudithook(prohibit_processes)
    result = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(canonical(result))
    if result['status'] != 'pass':raise SystemExit(1)
