#!/usr/bin/env python3
"""Literal-field JSONL adapter only. No hash source, matcher or transitions."""
import json
import sys

DOMAINS = {'form': 8, 'kind0': 3, 'kind1': 3, 'new_kind': 3,
           'state0': 4, 'state1': 4, 'value': 3, 'sign': 2,
           'amount': 2, 'matter': 2, 'route': 2}


def integer(value, modulus):
    if type(value) is not int or not 0 <= value < modulus:
        raise ValueError('invalid_literal_input')
    return value


class LiteralSource:
    def __init__(self, request):
        self.request = request
        self.reads = []
        mapping = request['map']
        if type(mapping) is not list or len(mapping) != 3:
            raise ValueError('invalid_literal_input')
        for k in mapping:
            integer(k, 4)
            if k == 0:
                raise ValueError('invalid_literal_input')
        states = request['state_map']
        if type(states) is not list or len(states) != 3:
            raise ValueError('invalid_literal_input')
        for state in states:
            integer(state, 3)
        if request['mode'] == 'assembly':
            integer(request['initial_id'], 4)
            initial = request['initial_fields']
            if type(initial['id']) is not int or initial['id'] != request['initial_id']:
                raise ValueError('invalid_literal_input')
            for name, n in [('node_kind', 3), ('node_state', 3), ('structural', 2)]:
                if type(initial[name]) is not list or len(initial[name]) != 8:
                    raise ValueError('invalid_literal_input')
                for value in initial[name]:
                    integer(value, n)
            integer(initial['scheduler'], 2**64 - 1)
            fields = request['rule_fields']
            if type(fields) is not list or len(fields) != 8:
                raise ValueError('invalid_literal_input')
        else:
            integer(request['rule_id'], 8)
            fields = [request['fields']]
        for row in fields:
            if type(row) is not dict or set(row) != set(DOMAINS):
                raise ValueError('invalid_literal_input')
            for key, n in DOMAINS.items():
                integer(row[key], n)

    def __call__(self, initial, field, index, modulus):
        r = self.request
        if field == 'child_kind_by_donor':
            if initial != 0 or modulus != 3 or index not in range(3):
                raise ValueError('invalid_literal_input')
            value = r['map'][index] - 1
        elif field == 'role_state_by_kind':
            if initial != 0 or modulus != 3 or index not in range(3):
                raise ValueError('invalid_literal_input')
            value = r['state_map'][index]
        elif field in DOMAINS:
            if initial != 0 or modulus != DOMAINS[field] or index not in range(8):
                raise ValueError('invalid_literal_input')
            if r['mode'] == 'rule':
                if index != r['rule_id']:
                    raise ValueError('invalid_literal_input')
                row = r['fields']
            else:
                row = r['rule_fields'][index]
            value = row[field]
        else:
            if r['mode'] != 'assembly' or initial != r['initial_id']:
                raise ValueError('invalid_literal_input')
            domains = {'node_kind': 3, 'node_state': 3, 'structural': 2, 'scheduler': 2**64 - 1}
            if field not in domains or modulus != domains[field]:
                raise ValueError('invalid_literal_input')
            if field == 'scheduler':
                if index != 0:
                    raise ValueError('invalid_literal_input')
                value = r['initial_fields'][field]
            else:
                if index not in range(8):
                    raise ValueError('invalid_literal_input')
                value = r['initial_fields'][field][index]
        integer(value, modulus)
        self.reads.append([initial, field, index, modulus, value])
        return value


def build_rule(rule_id, mapping, states, source):
    f = {key: source(0, key, rule_id, n) for key, n in DOMAINS.items()}
    form = f['form']
    pair = form in (3, 5, 6, 7)
    coherent = form == 7 or (form == 3 and f['route'] == 1)
    parent = f['kind0'] + 1
    kinds = [parent, mapping[parent - 1] if coherent else f['kind1'] + 1]
    nodes = [{'kind': kinds[i], 'state': None if f['state'+str(i)] == 3 else f['state'+str(i)]}
             for i in range(2 if pair else 1)]
    if coherent or form == 4:
        for node in nodes:
            node['state'] = states[node['kind'] - 1]
    structural = {'class': 'Structural', 'kind': 0, 'ends': [0, 1]}
    edges = []
    if pair:
        edges = [dict(structural, **{'class': 'Structural' if form >= 6 or coherent else 'Contact'})]
    if form == 0:
        ops = [{'op': 'SetState', 'node': 0, 'value': f['value']}]
    elif form == 1:
        ops = [{'op': 'AddState', 'node': 0, 'delta': -1 if f['sign'] == 0 else 1}]
    elif form == 2:
        ops = [{'op': 'Burn', 'node': 0, 'amount': f['amount'] + 1}]
    elif form == 3:
        ops = [{'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1 if coherent else f['matter'], 'activation': f['amount'] + 1}]
    elif form == 4:
        ops = [{'op': 'CreateNode', 'account': 0, 'kind': mapping[parent - 1], 'state': states[mapping[parent - 1] - 1]},
               {'op': 'CreateEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]},
               {'op': 'Transfer', 'from': 0, 'to': 1, 'matter': 1, 'activation': 1},
               {'op': 'Burn', 'node': 0, 'amount': 1}]
    elif form in (5, 6):
        ops = [{'op': 'CreateEdge' if form == 5 else 'DeleteEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]}]
    else:
        ops = [{'op': 'DeleteEdge', 'account': 0, 'kind': 0, 'ends': [0, 1]},
               {'op': 'DeleteNode', 'node': 1, 'recipient': 0}, {'op': 'Burn', 'node': 0, 'amount': 1}]
    return {'id': rule_id, 'nodes': nodes, 'edges': edges,
            'absent': [structural] if form == 5 else [], 'ops': ops}


def assemble(initial_id, source):
    mapping = [1 + source(0, 'child_kind_by_donor', i, 3) for i in range(3)]
    states = [source(0, 'role_state_by_kind', i, 3) for i in range(3)]
    rules = [build_rule(i, mapping, states, source) for i in range(8)]
    nodes = {str(i): {'kind': 1 + source(initial_id, 'node_kind', i, 3),
                      'state': source(initial_id, 'node_state', i, 3), 'matter': 8, 'activation': 8}
             for i in range(8)}
    edges = {str(i): {'class': 'Contact', 'kind': 0, 'ends': [i, (i + 1) % 8]} for i in range(8)}
    for i in range(8):
        if source(initial_id, 'structural', i, 2):
            edges[str(len(edges))] = {'class': 'Structural', 'kind': 0, 'ends': [i, (i + 1) % 8]}
    return {'profile': 'p00c-local-driven-v1', 'channels': [], 'initial_activation': 64,
            'injected': 0, 'extracted': 0,
            'native': {'profile': 'p00a-local-closed-v1', 'seed': source(initial_id, 'scheduler', 0, 2**64 - 1),
                       'rules': rules, 'limits': {'max_candidates': 4096, 'max_bindings': 65536,
                                                  'max_nodes': 128, 'max_edges': 256},
                       'world': {'nodes': nodes, 'edges': edges, 'next_node': 8, 'next_edge': len(edges),
                                 'epoch': 0, 'dissipated': 0, 'matter_total': 72 + len(edges),
                                 'activation_total': 64, 'next_event': 0, 'writers': {}}}}


def respond(request):
    identity = request.get('case_id') if type(request) is dict else None
    try:
        if request['mode'] not in ('rule', 'assembly'):
            raise ValueError('invalid_literal_input')
        source = LiteralSource(request)
        if request['mode'] == 'assembly':
            value = assemble(request['initial_id'], source)
        else:
            mapping = [1 + source(0, 'child_kind_by_donor', i, 3) for i in range(3)]
            states = [source(0, 'role_state_by_kind', i, 3) for i in range(3)]
            value = build_rule(request['rule_id'], mapping, states, source)
        return {'case_id': identity, 'ok': True, 'value': value, 'field_reads': source.reads}
    except (ValueError, KeyError, TypeError, IndexError):
        return {'case_id': identity, 'ok': False, 'error': 'invalid_literal_input'}


if __name__ == '__main__':
    for line in sys.stdin:
        try:
            result = respond(json.loads(line))
        except (ValueError, AttributeError):
            result = {'case_id': None, 'ok': False, 'error': 'invalid_literal_input'}
        print(json.dumps(result, separators=(',', ':'), ensure_ascii=False))
