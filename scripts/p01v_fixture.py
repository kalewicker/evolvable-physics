"""Three inert receipt roles. Standard library only; no simulation imports."""
import hashlib
import json
import math
import sys

ROLES=('native_stub','report_stub','audit_stub')
FIELDS={'schema','inert','role','slot','proposal','initial','input_request_sha256','previous_stdout_sha256'}


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(data):return hashlib.sha256(data).hexdigest()


def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def load(data):
    def pairs(items):
        require(len(items)==len({key for key,value in items}),'duplicate')
        return dict(items)
    def finite(value):
        if isinstance(value,dict):
            for child in value.values():finite(child)
        elif isinstance(value,list):
            for child in value:finite(child)
        elif isinstance(value,float):require(math.isfinite(value),'nonfinite')
    value=json.loads(data,object_pairs_hook=pairs);finite(value);return value


def receipt(role,slot,proposal,initial,request_sha,previous):
    return dict(schema='p01v-inert-stage-receipt-v1',inert=True,role=role,slot=slot,
                proposal=proposal,initial=initial,input_request_sha256=request_sha,previous_stdout_sha256=previous)


def main(args):
    require(len(args)==5,'arguments')
    role,slot,proposal,initial,expected=args;slot=int(slot);proposal=int(proposal);initial=int(initial)
    require(role in ROLES and 0<=slot<128 and proposal==6000+slot//4 and initial==slot%4,'identity')
    require(len(expected)==64 and all(c in '0123456789abcdef' for c in expected),'digest')
    data=sys.stdin.buffer.read(1048576);require(len(data)<1048576,'input cap')
    previous=None
    if role=='native_stub':request=data
    else:
        envelope=load(data)
        require(set(envelope)=={'schema','request_utf8','previous_stdout_utf8'} and envelope['schema']=='p01v-stage-input-v1','input envelope')
        require(type(envelope['request_utf8']) is str and type(envelope['previous_stdout_utf8']) is str,'input strings')
        request=envelope['request_utf8'].encode();prior_bytes=envelope['previous_stdout_utf8'].encode();prior=load(prior_bytes)
        predecessor=ROLES[ROLES.index(role)-1]
        require(set(prior)==FIELDS and prior['schema']=='p01v-inert-stage-receipt-v1' and prior['inert'] is True,'predecessor schema')
        require(type(prior['slot']) is int and type(prior['proposal']) is int and type(prior['initial']) is int,'predecessor types')
        require([prior['slot'],prior['proposal'],prior['initial']]==[slot,proposal,initial] and prior['role']==predecessor and prior['input_request_sha256']==expected,'predecessor identity')
        prior_previous=prior['previous_stdout_sha256']
        require((predecessor=='native_stub' and prior_previous is None) or (predecessor=='report_stub' and type(prior_previous) is str and len(prior_previous)==64),'predecessor chain')
        previous=digest(prior_bytes)
    require(len(request)<524288 and digest(request)==expected,'request bytes')
    require(type(load(request)) is dict,'request object')
    output=encode(receipt(role,slot,proposal,initial,expected,previous))+b'\n'
    sys.stdout.buffer.write(output)


if __name__=='__main__':
    try:main(sys.argv[1:])
    except Exception:
        sys.stderr.write('p01v_fixture_rejected\n')
        sys.exit(2)
