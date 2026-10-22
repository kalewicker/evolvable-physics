#!/usr/bin/env python3
"""Admitted P01o keyed source; --literal uses only frozen injected-field construction."""
import hashlib
import json
import sys
from pathlib import Path
import generator_v4_fields as literal
from p01o_contract import authorize, canonical, plans, require

NAMESPACE = 'p01-generator-v4'


def message(proposal, initial, field, index):
    return json.dumps([NAMESPACE, proposal, initial, field, index],
                      ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def reduce_prefix(prefix, modulus):
    require(len(prefix) == 16 and 0 < modulus <= 2**64 - 1, 'invalid prefix/range')
    return int(prefix, 16) % modulus


def construct_with_source(cell, source):
    """Only injected callbacks; there is deliberately no default keyed source."""
    records = []
    def checked(initial, field, index, n):
        raw, metadata = source(initial, field, index, n)
        require(type(raw) is int and 0 <= raw < n, 'injected raw field range')
        records.append(dict(metadata, namespace=NAMESPACE, proposal=cell['proposal'],
                            initial=initial, field=field, index=index, modulus=n, raw=raw))
        return raw
    env = literal.assemble(cell['initial'], checked)
    require(len(records) == 119, 'field census')
    mapping = [r['raw'] + 1 for r in records[:3]]
    return dict(schema='p01o-generated-environment-v1', **cell, map=mapping, state_map=[r['raw'] for r in records[3:6]], environment=env, draws=records)


def sample(bundle, slot):
    protocol = authorize(bundle, 'python_generation', slot)
    cell = plans(protocol)[slot]
    def keyed(initial, field, index, n):
        raw_message = message(cell['proposal'], initial, field, index)
        digest = hashlib.sha256(raw_message).hexdigest()
        return reduce_prefix(digest[:16], n), dict(preimage=raw_message.decode(), digest=digest,
                                                  prefix=int(digest[:16], 16))
    return construct_with_source(cell, keyed)


def mock_record(request):
    cell = request['cell']
    literal_source = literal.LiteralSource(request)
    require(request['mode'] == 'assembly' and request['initial_id'] == cell['initial'], 'mock initial ID')
    def source(i, field, index, n):
        raw = literal_source(i, field, index, n)
        return raw, dict(preimage=message(cell['proposal'], i, field, index).decode(),
                         digest=f'{raw:016x}' + '0' * 48, prefix=raw)
    return construct_with_source(cell, source)


if __name__ == '__main__':
    if sys.argv[1:] == ['--record-literal']:
        for line in sys.stdin:
            print(canonical(mock_record(json.loads(line))))
    elif sys.argv[1:] == ['--literal']:
        for line in sys.stdin:
            try:
                response = literal.respond(json.loads(line))
            except (ValueError, AttributeError):
                response = {'case_id': None, 'ok': False, 'error': 'invalid_literal_input'}
            print(canonical(response))
    else:
        try:
            require(len(sys.argv) == 3, 'usage: generator_v4.py BUNDLE SLOT or --literal')
            print(canonical(sample(Path(sys.argv[1]), int(sys.argv[2]))))
        except (ValueError, KeyError, OSError) as error:
            print(str(error), file=sys.stderr)
            raise SystemExit(1)
