"""Transport-only boundary for invented P01s envelopes. No native execution."""
import copy
import hashlib
import json


def strict_load(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite number: '+value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    # Reject overflow to infinity as well as explicit NaN/Infinity tokens.
    json.dumps(value, allow_nan=False)
    return value


def typed(value):
    if isinstance(value, dict):
        return ('dict', tuple(sorted((k, typed(v)) for k, v in value.items())))
    if isinstance(value, list):
        return ('list', tuple(map(typed, value)))
    return (type(value).__name__, value)


def request_from_streams(streams, hashes, cell):
    if len(streams) != 2 or len(hashes) != 2:
        raise ValueError('two streams required')
    if any(type(x) is not int for x in cell) or len(cell) != 3:
        raise ValueError('integer cell identity')
    slot, proposal, initial = cell
    if not (0 <= slot < 128 and proposal == 6000+slot//4 and initial == slot % 4):
        raise ValueError('fixed cell identity')
    envelopes = []
    for raw, expected in zip(streams, hashes):
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('stream digest')
        env = strict_load(raw)
        if type(env) is not dict or env.get('schema') != 'p01o-generated-environment-v1':
            raise ValueError('envelope schema')
        if typed([env.get(k) for k in ('slot', 'proposal', 'initial')]) != typed(list(cell)):
            raise ValueError('envelope cell')
        if type(env.get('environment')) is not dict or type(env['environment'].get('native')) is not dict:
            raise ValueError('environment/native objects')
        envelopes.append(env)
    if typed(envelopes[0]) != typed(envelopes[1]):
        raise ValueError('typed stream disagreement')
    envelope = copy.deepcopy(envelopes[0])
    request = dict(schema='p01-worker-request-v1', initial=copy.deepcopy(envelope['environment']),
                   epochs=128, max_events=16384, max_trace_bytes=4194304)
    return dict(envelope=envelope, request=request)
