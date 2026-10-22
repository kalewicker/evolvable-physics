#!/usr/bin/env python3
"""Bounded literal-field readiness panel. Never imports a generator or kernel."""
import copy
import hashlib
import itertools
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {'form': 8, 'kind0': 3, 'kind1': 3, 'new_kind': 3, 'state0': 4,
           'state1': 4, 'value': 3, 'sign': 2, 'amount': 2, 'matter': 2, 'route': 2}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def write(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2) + '\n')


def fields(donor, variant, state0, state1):
    return {'form': variant['form'], 'route': variant['route'], 'kind0': donor,
            'kind1': (donor + state1) % 3, 'new_kind': (donor + state0 + 1) % 3,
            'state0': state0, 'state1': state1, 'value': (state0 + 2 * state1) % 3,
            'sign': (state0 + state1) % 2, 'amount': state1 % 2, 'matter': state0 % 2}


def requests(registry):
    variants = {v['name']: v for v in registry['variants']}
    ordinal = 0
    for mapping, states, donor, name in itertools.product(registry['type_maps'], registry['state_maps'],
            registry['raw_donor_kinds'], registry['constructive_variants']):
        variant = variants[name]
        row = dict(form=variant['form'], route=variant['route'], kind0=donor,
                   kind1=mapping[donor] % 3, new_kind=mapping[donor] % 3, state0=3, state1=3,
                   value=(states[mapping[donor]-1]+1) % 3, sign=ordinal % 2, amount=ordinal % 2, matter=0)
        yield dict(case_id=f'rule-{ordinal:05d}', mode='rule', map=mapping, state_map=states,
                   rule_id=ordinal % 8, fields=row)
        ordinal += 1
    for mapping, donor, name, pair in itertools.product(registry['type_maps'], registry['raw_donor_kinds'],
            registry['unchanged_variants'], registry['raw_state_pairs']):
        yield dict(case_id=f'rule-{ordinal:05d}', mode='rule', map=mapping, state_map=[2, 0, 1],
                   rule_id=ordinal % 8, fields=fields(donor, variants[name], *pair))
        ordinal += 1
    for ordinal, (m, s, initial) in enumerate(itertools.product(range(27), range(27), registry['initial_fields'])):
        rotation = (3*m+s) % 9
        rows = [fields((slot+m) % 3, registry['variants'][(slot+rotation) % 9],
                       (slot+rotation) % 4, (slot+rotation+1) % 4) for slot in range(8)]
        yield dict(case_id=f'assembly-{ordinal:04d}', mode='assembly', map=registry['type_maps'][m],
                   state_map=registry['state_maps'][s], initial_id=initial['id'], initial_fields=initial, rule_fields=rows)
    base = dict(form=3, route=1, kind0=0, kind1=2, new_kind=0, state0=3, state1=3,
                value=2, sign=0, amount=0, matter=0)
    for group, probe in enumerate(registry['ignored_field_probes']):
        for index, value in enumerate(probe['values']):
            row = dict(base, form=variants[probe['variant']]['form'], route=variants[probe['variant']]['route'])
            req = dict(case_id=f'probe-{group:02d}-{index:02d}', mode='rule', map=[2, 3, 1],
                       state_map=[2, 0, 1], rule_id=0, fields=row)
            (req if probe['field'] in ('map', 'state_map') else row)[probe['field']] = value
            yield req
    for item in registry['invalid_inputs']:
        req = dict(case_id='invalid-'+item['name'], mode=item['mode'], map=[2, 3, 1], state_map=[2, 0, 1])
        if item['mode'] == 'rule':
            req.update(rule_id=0, fields=dict(base))
        else:
            req.update(initial_id=0, initial_fields=copy.deepcopy(registry['initial_fields'][0]),
                       rule_fields=[dict(base) for _ in range(8)])
        target = item['target']
        container = req
        if target.startswith('rule_fields[7].'):
            container, target = req['rule_fields'][7], target.split('.')[1]
        elif target.startswith('initial_fields.'):
            container, target = req['initial_fields'], target.split('.')[1]
        if item['name'].endswith('_missing') or item['name'] in ('missing_raw_kind0', 'missing_initial_fields'):
            del container[target]
        elif item['name'] == 'rule_fields_short':
            req['rule_fields'] = req['rule_fields'][:7]
        else:
            container[target] = item['value']
        yield req


def condition_verdict(row):
    parent, child = row['parent'], row['map'][row['parent']-1]
    birth = parent in row['birth_donors']
    funding = birth and parent in row['funding_donors']
    descendant = birth and child in row['birth_donors']
    states_match = [row['creator_state'], row['child_state']] == [row['state_map'][parent-1], row['state_map'][child-1]]
    return [birth, funding, birth and parent in row['recycle_donors'], descendant,
            funding and states_match, descendant and row['child_state'] == row['state_map'][child-1],
            funding and row['transfer_matter'] == 1,
            all(a >= b for a, b in zip(row['child_resources'], [3, 2])),
            row['leaf_after_edge_removal'], row['creation_edge_present'], row['required_bodies'] <= row['slot_cap']]


def oracle_rule(raw, mapping, states, identity):
    """Independent declarative operation table, with complete output comparison."""
    form, route = raw['form'], raw['route']
    donor = raw['kind0'] + 1
    mapped = mapping[raw['kind0']]
    tables = [
        [{'op': 'SetState', 'node': 0, 'value': raw['value']}],
        [{'op': 'AddState', 'node': 0, 'delta': 2 * raw['sign'] - 1}],
        [{'op': 'Burn', 'node': 0, 'amount': raw['amount'] + 1}],
        [{'op': 'Transfer', 'from': 0, 'to': 1, 'matter': [raw['matter'], 1][route], 'activation': raw['amount'] + 1}],
        [{'op': 'CreateNode', 'account': 0, 'kind': mapped, 'state': states[mapped-1]},
         {'op': 'CreateEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]},
         {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1},
         {'op': 'Burn', 'node': 0, 'amount': 1}],
        [{'op': 'CreateEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]}],
        [{'op': 'DeleteEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]}],
        [{'op': 'DeleteEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]},
         {'op': 'DeleteNode', 'node': 1, 'recipient': 0}, {'op': 'Burn', 'node': 0, 'amount': 1}]]
    kinds = [donor]
    if form in (3, 5, 6, 7):
        kinds.append(mapped if (form, route) == (3, 1) or form == 7 else raw['kind1'] + 1)
    nodes = [{'kind': k, 'state': [0, 1, 2, None][raw['state'+str(i)]]} for i, k in enumerate(kinds)]
    if form in (4, 7) or (form, route) == (3, 1):
        nodes = [dict(kind=k, state=states[k-1]) for k in kinds]
    pattern = {'class': 'Structural' if form in (6, 7) or (form, route) == (3, 1) else 'Contact',
               'kind': 0, 'ends': [0, 1]}
    return {'id': identity, 'nodes': nodes, 'edges': [pattern] if len(nodes) == 2 else [],
            'absent': [{'class': 'Structural', 'kind': 0, 'ends': [0, 1]}] if form == 5 else [],
            'ops': tables[form]}


def expected(req):
    reads = [[0, 'child_kind_by_donor', i, 3, k - 1] for i, k in enumerate(req['map'])]
    reads.extend([0, 'role_state_by_kind', i, 3, s] for i, s in enumerate(req['state_map']))
    raw_rules = [(req['rule_id'], req['fields'])] if req['mode'] == 'rule' else list(enumerate(req['rule_fields']))
    rules = []
    for identity, row in raw_rules:
        reads.extend([0, name, identity, n, row[name]] for name, n in DOMAINS.items())
        rules.append(oracle_rule(row, req['map'], req['state_map'], identity))
    if req['mode'] == 'rule':
        return rules[0], reads
    inp = req['initial_fields']
    nodes = {}
    for i, (k, state) in enumerate(zip(inp['node_kind'], inp['node_state'])):
        nodes[str(i)] = {'kind': k + 1, 'state': state, 'matter': 8, 'activation': 8}
        reads.extend([[req['initial_id'], 'node_kind', i, 3, k],
                      [req['initial_id'], 'node_state', i, 3, state]])
    edges = {str(i): {'class': 'Contact', 'kind': 0, 'ends': [i, (i + 1) % 8]} for i in range(8)}
    for i, present in enumerate(inp['structural']):
        reads.append([req['initial_id'], 'structural', i, 2, present])
        if present:
            edges[str(len(edges))] = {'class': 'Structural', 'kind': 0, 'ends': [i, (i + 1) % 8]}
    reads.append([req['initial_id'], 'scheduler', 0, 2**64 - 1, inp['scheduler']])
    # Independent global inventory identities, not execution of any operation.
    matter = sum(n['matter'] + 1 for n in nodes.values()) + len(edges)
    activation = sum(n['activation'] for n in nodes.values())
    env = {'profile': 'p00c-local-driven-v1', 'channels': [], 'initial_activation': activation,
           'injected': 0, 'extracted': 0, 'native': {'profile': 'p00a-local-closed-v1',
           'seed': inp['scheduler'], 'rules': rules,
           'limits': {'max_candidates': 4096, 'max_bindings': 65536, 'max_nodes': 128, 'max_edges': 256},
           'world': {'nodes': nodes, 'edges': edges, 'next_node': len(nodes), 'next_edge': len(edges),
                     'matter_total': matter, 'activation_total': activation,
                     'epoch': 0, 'dissipated': 0, 'next_event': 0, 'writers': {}}}}
    return env, reads


def check_response(req, result):
    require(result.get('case_id') == req['case_id'], 'missing/reordered case: ' + req['case_id'])
    if req['case_id'].startswith('invalid-'):
        require(canonical(result) == canonical({'case_id': req['case_id'], 'ok': False, 'error': 'invalid_literal_input'}),
                'invalid literal accepted: ' + req['case_id'])
        return
    value, reads = expected(req)
    want = {'case_id': req['case_id'], 'ok': True, 'value': value, 'field_reads': reads}
    require(canonical(want) == canonical(result), 'independent invariant mismatch: ' + req['case_id'])


def guarded(command, inputs, stdout, stderr, wall, cap, deadline):
    """Bound both captured streams together; kill/reap the whole child group."""
    start = time.monotonic()
    expiry = min(start + wall, deadline)
    if start >= expiry:
        return {'status': 'not_started_aggregate_deadline', 'wall_seconds': 0, 'output_bytes': 0}
    total = 0
    status = 'complete'
    with inputs.open('rb') as src, stdout.open('xb') as out, stderr.open('xb') as err:
        try:
            child = subprocess.Popen(command, cwd=ROOT, stdin=src, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, start_new_session=True)
        except OSError as error:
            return dict(status='launch_failure', error=str(error), command=command,
                        wall_seconds=time.monotonic()-start, output_bytes=0)
        sel = selectors.DefaultSelector()
        try:
            for pipe, target in [(child.stdout, out), (child.stderr, err)]:
                os.set_blocking(pipe.fileno(), False)
                sel.register(pipe, selectors.EVENT_READ, target)
            while sel.get_map():
                if time.monotonic() >= expiry:
                    status = 'wall_limit'
                    break
                for key, _ in sel.select(min(0.01, max(0, expiry - time.monotonic()))):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        sel.unregister(key.fileobj)
                        continue
                    available = cap - total
                    key.data.write(data[:available])
                    total += min(len(data), available)
                    if len(data) > available:
                        status = 'output_limit'
                        break
                if status != 'complete':
                    break
            if status == 'complete':
                try:
                    code = child.wait(timeout=max(0.001, expiry - time.monotonic()))
                    if code != 0:
                        status = 'nonzero_exit'
                except subprocess.TimeoutExpired:
                    status = 'wall_limit'
            if status != 'complete':
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            child.wait()
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
            sel.close()
            child.stdout.close()
            child.stderr.close()
    return {'status': status, 'returncode': child.returncode,
            'wall_seconds': time.monotonic() - start, 'output_bytes': total,
            'wall_ceiling_seconds': wall, 'output_ceiling_bytes': cap,
            'command': command}


def check_streams(inputs, python_output, rust_output, deadline):
    counts = {'rule': 0, 'assembly': 0, 'invalid': 0, 'probe': 0}
    records = 0
    laws = {}
    probes = {}
    with inputs.open() as ins, python_output.open() as py, rust_output.open() as rs:
        for ordinal, rows in enumerate(itertools.zip_longest(ins, py, rs)):
            require(time.monotonic() < deadline, 'aggregate deadline during comparison')
            require(all(row is not None for row in rows), 'missing/extra output at ordinal ' + str(ordinal))
            req, a, b = (json.loads(row) for row in rows)
            require(canonical(a) == canonical(b), 'cross-language mismatch: ' + req['case_id'])
            check_response(req, a)
            check_response(req, b)
            records += len(a.get('field_reads', []))
            kind = req['case_id'].split('-')[0]
            counts[kind] += 1
            if kind == 'assembly':
                group = (counts[kind] - 1) // 4
                law = canonical([req['map'], req['state_map'], a['value']['native']['rules']])
                require(laws.setdefault(group, law) == law, 'law changed across initial IDs')
            if kind == 'probe':
                group = req['case_id'].split('-')[1]
                value = canonical(a['value'])
                require(probes.setdefault(group, value) == value, 'ignored field changed output')
    require(counts == {'rule': 14337, 'assembly': 2916, 'invalid': 79, 'probe': 395}, 'complete fixed counts')
    require(len(laws) == 729 and len(probes) == 37, 'law/probe groups')
    require(records == 597448, 'complete field records')
    return counts


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    result = {'schema': 'p01n-literal-field-readiness-v1', 'status': 'started',
              'scientific_status': 'untested', 'law_sampling_admitted': False,
              'world_transitions': 0, 'hash_sampler_calls': 0, 'stages': {}}
    write(out / 'started.json', result)
    try:
        protocol = load(ROOT / 'docs/p01n_protocol.json')
        limits = protocol['future_validation_limits']
        deadline = started + limits['aggregate_wall_seconds']
        freeze = load(ROOT / 'docs/p01n_registration_freeze.json')
        for name, digest in {**freeze['files'], **freeze['prior_public_receipts']}.items():
            require(sha(ROOT / name) == digest, 'frozen source changed: ' + name)
        inventory = load(ROOT / 'docs/evidence/publication_inventory.json')['files']
        for row in inventory:
            require(sha(ROOT / row['file']) == row['sha256'], 'historical receipt changed: ' + row['file'])
        sources = ['src/bin/generator-v4-fields.rs', 'scripts/generator_v4_fields.py',
                   'scripts/validate_p01n.py', 'scripts/test_p01n_readiness.py',
                   'docs/p01n_protocol.json', 'docs/p01n_literal_fields.json',
                   'docs/p01n_registration_freeze.json', 'scripts/audit_p01n_readiness.py',
                   'Cargo.toml', 'Cargo.lock']
        (out / 'sources').mkdir()
        for name in sources:
            target = out / 'sources' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        binary = ROOT / 'target/release/generator-v4-fields'
        identities = {'files': {name: sha(ROOT / name) for name in sources},
                      'rust_binary_sha256': sha(binary), 'python_executable': str(Path(sys.executable).resolve()),
                      'python_executable_sha256': sha(Path(sys.executable).resolve()),
                      'registration_files_verified': len(freeze['files']), 'prior_public_receipts_verified': len(inventory)}
        (out / 'rust_binary').write_bytes(binary.read_bytes())
        result['source_identities'] = identities
        registry = load(ROOT / protocol['registry'])
        inputs = out / 'inputs.jsonl'
        with inputs.open('x') as f:
            from audit_p01n_readiness import registered_input
            for ordinal, request in enumerate(requests(registry)):
                require(time.monotonic() < deadline, 'aggregate deadline during preparation')
                registered_input(request, ordinal, registry)
                f.write(canonical(request) + '\n')
        identities['literal_inputs_sha256'] = sha(inputs)
        write(out / 'identities.json', identities)
        conditions = []
        for row in registry['local_conditions']:
            verdict = condition_verdict(row)
            require(canonical(verdict) == canonical(row['expected']), 'local condition: '+row['name'])
            conditions.append(dict(case_id='condition-'+row['name'], verdict=verdict, scope=row['scope']))
        write(out / 'local_conditions.json', conditions)
        commands = {'python': [sys.executable, str(ROOT / 'scripts/generator_v4_fields.py')], 'rust': [str(binary)]}
        for name, command in commands.items():
            stage = guarded(command, inputs, out / (name + '.jsonl'), out / (name + '.stderr'),
                            limits['wall_seconds_per_adapter'], limits['combined_stdout_stderr_bytes_per_adapter'], deadline)
            result['stages'][name] = stage
            write(out / (name + '_guard.json'), stage)
        require(all(s['status'] == 'complete' for s in result['stages'].values()), 'adapter guard failed')
        result['case_counts'] = check_streams(inputs, out / 'python.jsonl', out / 'rust.jsonl', deadline)
        require(time.monotonic() < deadline, 'aggregate deadline before sealing')
        result.update(status='pass', engineering_gate_pass=True, source_identities=identities,
                      full_law_initial_groups_verified=729, ignored_field_groups_verified=37,
                      successful_field_records_per_adapter=597448, local_condition_cases_verified=13,
                      scope='authored literal fields only; no finite hash sampler or native reachability admission')
    except Exception as error:
        result.update(status='fail', engineering_gate_pass=False, error=str(error), error_type=type(error).__name__)
    for name in ('python', 'rust'):
        if name not in result['stages']:
            stage = dict(status='not_started_preceding_failure', wall_seconds=0, output_bytes=0)
            result['stages'][name] = stage
            write(out / (name+'_guard.json'), stage)
    result['wall_seconds_through_checks'] = time.monotonic() - started
    write(out / 'assessment.json', result)
    # Inventory includes source snapshots, complete inputs/outputs and failures.
    files = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    write(out / 'checksums.json', files)
    write(out / 'seal.json', {'schema': 'p01n-readiness-seal-v1', 'checksums_sha256': sha(out / 'checksums.json')})
    elapsed = time.monotonic() - started
    write(out / 'completion.json', {'wall_seconds_including_sealing': elapsed,
          'aggregate_wall_ceiling_seconds': 300, 'aggregate_wall_pass': elapsed <= 300,
          'seal_sha256': sha(out / 'seal.json')})
    print(json.dumps({'status': result['status'], 'directory': str(out), 'wall_seconds': elapsed,
                      'error': result.get('error')}, sort_keys=True))
    if result['status'] != 'pass' or elapsed > 300:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
