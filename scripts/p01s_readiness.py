"""Fixed invented-fixture readiness. No retained payload parsing or processes."""
import copy
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch
from p01s_boundary import request_from_streams
from p01s_accounting import Ledger, terminal, require
ROOT = Path(__file__).resolve().parents[1]


def raw(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture():
    return dict(schema='p01o-generated-environment-v1', slot=0, proposal=6000, initial=0,
                map=[0, 1, 2], state_map=[2, 1, 0], draws=[dict(authored='inert')],
                environment=dict(profile='invented-not-native-validated', native=dict(
                    rules=[dict(inert=True)], world=dict(resource=7))))


def packet():
    """Declare all subcases before running any implementation control."""
    p = json.loads((ROOT/'docs/p01s_protocol.json').read_bytes())
    names = [
        ['valid', 'malformed', 'duplicate_key', 'nan', 'infinity', 'overflow', 'wrong_hash'],
        ['unwrapped'], ['absent', 'non_object'], ['absent', 'non_object'], ['wrong'],
        ['slot', 'proposal', 'initial', 'bool_id'], ['bool_resource'], ['metadata'],
        ['extra'], ['resource', 'rule'], ['create_append_truncate_delete'], ['replace'],
        ['partial_write', 'partial_copy'], ['register_twice'], ['snapshot'], ['seal'],
        ['below', 'equal', 'above'],
        ['wall_below', 'wall_equal', 'wall_above', 'byte_below', 'byte_equal', 'byte_above'],
        ['input_failure', 'partial_write_failure'], ['equal_size_mutation', 'unlisted', 'missing'],
        ['one_hundred_polls'], ['valid', 'unknown', 'oversize', 'too_many', 'repeat'],
        ['exhausted_reserve', 'terminal_io_error'], ['traversal', 'absolute', 'symlink', 'external_mutation']]
    return dict(schema='p01s-fixtures-v1', controls=dict(zip(p['controls'], names)), envelope=fixture())


class Spy:
    """Observe actual filesystem API calls independently of ledger increments."""
    def __enter__(self):
        self.counts = dict(stat_calls=0, hash_read_bytes=0, write_bytes=0, scandir_calls=0, discovered_entries=0)
        self.patches = []
        old_stat, old_read, old_write, old_scan = os.lstat, Path.read_bytes, os.write, os.scandir
        def lstat(*a, **kw):
            self.counts['stat_calls'] += 1
            return old_stat(*a, **kw)
        def read(p):
            data = old_read(p)
            self.counts['hash_read_bytes'] += len(data)
            return data
        def write(*a, **kw):
            n = old_write(*a, **kw)
            self.counts['write_bytes'] += n
            return n
        class Scan:
            def __init__(inner, *a, **kw):
                self.counts['scandir_calls'] += 1
                inner.handle = old_scan(*a, **kw)
            def __enter__(inner):
                items = list(inner.handle)
                self.counts['discovered_entries'] += len(items)
                return iter(items)
            def __exit__(inner, *args):inner.handle.close()
        for obj, name, fn in [(os, 'lstat', lstat), (Path, 'read_bytes', read), (os, 'write', write), (os, 'scandir', Scan)]:
            x = patch.object(obj, name, fn);x.start();self.patches.append(x)
        return self
    def __exit__(self, *args):
        for x in reversed(self.patches):x.stop()


def caught(fn):
    try:
        fn()
        return False
    except (ValueError, OSError, KeyError):
        return True


def interface_cases(control, subcases, base):
    rows = []
    for sub in subcases:
        a, b = copy.deepcopy(base), copy.deepcopy(base)
        bad_hash = False
        if control == 1:a = b = a['environment']
        if control in (2, 3):
            parent_a, parent_b = (a, b) if control == 2 else (a['environment'], b['environment'])
            key = 'environment' if control == 2 else 'native'
            if sub == 'absent':parent_a.pop(key);parent_b.pop(key)
            else:parent_a[key] = parent_b[key] = []
        if control == 4:a['schema'] = b['schema'] = 'wrong'
        if control == 5:
            key = 'slot' if sub == 'bool_id' else sub
            a[key] = b[key] = False if sub == 'bool_id' else 999
        if control == 6:b['environment']['native']['world']['resource'] = True
        if control == 7:b['draws'].append('changed')
        if control == 8:a['extra'] = b['extra'] = dict(keep=[False, 0, None, 'metadata'])
        if control == 9:
            if sub == 'resource':b['environment']['native']['world']['resource'] += 1
            else:b['environment']['native']['rules'][0]['inert'] = False
        streams = [raw(a), raw(b)]
        if control == 0 and sub != 'valid':
            if sub == 'malformed':streams = [b'{', b'{']
            elif sub == 'duplicate_key':streams = [raw(a).replace(b'"slot": 0', b'"slot": 0, "slot": 0')]*2
            elif sub in ('nan', 'infinity', 'overflow'):
                token = {'nan':b'NaN', 'infinity':b'Infinity', 'overflow':b'1e999'}[sub]
                streams = [raw(a).replace(b'"resource": 7', b'"resource": '+token)]*2
            else:bad_hash = True
        hashes = list(map(digest, streams))
        if bad_hash:hashes[1] = '0'*64
        result, error = None, None
        try:result = request_from_streams(streams, hashes, (0, 6000, 0))
        except (ValueError, TypeError) as exc:error = str(exc)
        expected = (control == 0 and sub == 'valid') or control == 8
        require((error is None) == expected, 'interface case '+sub)
        rows.append(dict(subcase=sub, kind='interface', streams=[x.decode() for x in streams], hashes=hashes,
                         cell=[0, 6000, 0], expected_accept=expected, accepted=error is None, result=result, error=error))
    return rows


def accounting_case(index, sub, root):
    root = Path(root).absolute()
    # Each isolated fixture has its own initial scan and at most one reconciliation.
    data = dict(subcase=sub, kind='accounting', expected_rejection=False)
    with Spy() as spy:
        ledger = Ledger(root, cap=2097152)
        rejected = False
        if index == 10:
            ledger.write('a', b'ab');ledger.write('a', b'cd', append=True)
            ledger.write('a', b'x');ledger.write('gone', b'12');ledger.delete('gone')
        elif index == 11:
            ledger.write('a', b'old');ledger.write('tmp', b'newer')
            data['transient_bytes'] = ledger.total
            ledger.rename('tmp', 'a')
        elif index == 12:
            if sub == 'partial_write':rejected = caught(lambda:ledger.write('a', b'abcdef', fail_after=3))
            else:
                ledger.write('source', b'abcdef')
                rejected = caught(lambda:ledger.copy(root/'source', 'a', fail_after=3))
            data['expected_rejection'] = True
        elif index == 13:
            ledger.write('a', b'abc');ledger.register('a');ledger.register('a')
        elif index == 14:
            ledger.write('source', b'invented source snapshot');ledger.copy(root/'source', 'snapshot')
        elif index == 15:
            ledger.write('data', b'abc')
            inv = dict(ledger.files)
            ledger.write('checksums.json', raw(inv))
            ledger.write('completion.json', raw(dict(checksums_sha256=ledger.files['checksums.json']['sha256'])))
        elif index in (16, 17):
            args = dict(wall=0, cpu=0, wall_cap=120, cpu_cap=600, seconds_reserve=5)
            offset = {'below':-1, 'equal':0, 'above':1}[sub.split('_')[-1]]
            if index == 16:args['cpu'] = 595+offset
            elif sub.startswith('wall'):args['wall'] = 115+offset
            else:ledger.cap = ledger.reserve-offset  # total=0 vs cap-reserve: 1,0,-1
            rejected = caught(lambda:ledger.budget(**args))
            data.update(kind='budget', args=args, cap=ledger.cap, reserve=ledger.reserve, expected_rejection=offset >= 0)
        elif index in (18, 22):
            first = 'input failure'
            if sub == 'partial_write_failure':
                require(caught(lambda:ledger.write('partial', b'12345', fail_after=2)), 'partial failure')
                first = 'partial write failure'
            if sub == 'exhausted_reserve':
                require(caught(lambda:ledger.budget(cpu=595)), 'exhausted reserve')
                first = 'cpu reserve'
            data['terminal'] = terminal(ledger, first, write_failure=sub == 'terminal_io_error')
            data['first_error'] = first
            data['kind'] = 'terminal'
        elif index == 19:
            ledger.write('a', b'abc')
            if sub == 'equal_size_mutation':(root/'a').write_text('xyz')
            elif sub == 'unlisted':(root/'unknown').write_text('x')
            else:(root/'a').unlink()
            rejected = caught(ledger.reconcile)
            data['expected_rejection'] = True
        elif index == 20:
            ledger.write('a', b'abc')
            before = dict(spy.counts)
            for _ in range(100):ledger.budget()
            data['poll_spy_delta'] = {k:spy.counts[k]-v for k,v in before.items()}
            require(not any(data['poll_spy_delta'].values()), 'poll filesystem work')
        elif index == 21:
            if sub == 'too_many':
                rejected = caught(lambda:ledger.declare_stage('stage', [str(i) for i in range(17)]))
            else:
                ledger.declare_stage('stage', ['a'], allowance=4)
                data['reserved_before'] = ledger.reserved
                ledger.budget()
                # Simulated external stage output intentionally bypasses owned writer.
                (root/'stage'/('unknown' if sub == 'unknown' else 'a')).write_text('12345' if sub == 'oversize' else 'abc')
                rejected = caught(lambda:ledger.reconcile_stage('stage'))
                if sub == 'repeat':rejected = caught(lambda:ledger.reconcile_stage('stage'))
            data['expected_rejection'] = sub != 'valid'
        elif index == 23:
            ledger.write('a', b'abc')
            if sub == 'traversal':rejected = caught(lambda:ledger.write('../escape', b'x'))
            elif sub == 'absolute':rejected = caught(lambda:ledger.write(str(root/'absolute'), b'x'))
            elif sub == 'symlink':
                (root/'link').symlink_to('a');rejected = caught(lambda:ledger.write('link', b'x'))
            else:
                (root/'a').write_text('xyz');rejected = caught(lambda:ledger.register('a'))
                require(ledger.invalid and caught(ledger.budget), 'external mutation invalidates ledger')
            data['expected_rejection'] = True
        require(rejected == data['expected_rejection'], 'accounting rejection '+sub)
        # Failure scenarios deliberately omit final full scan.
        if not rejected and data['kind'] != 'terminal':ledger.reconcile()
        data.update(rejected=rejected, files=copy.deepcopy(ledger.files), total=ledger.total,
                    counters=dict(ledger.counts), spy=dict(spy.counts), events=list(ledger.events),
                    reserved=ledger.reserved, root=root.name, invalid=ledger.invalid)
        for key in ('stat_calls', 'hash_read_bytes', 'write_bytes', 'discovered_entries'):
            require(data['counters'][key] == data['spy'][key], 'counter spy '+key)
    return data


def run_suite(out, declared):
    out = Path(out);out.mkdir()
    results = []
    for index, (control, subs) in enumerate(declared['controls'].items()):
        if index < 10:cases = interface_cases(index, subs, declared['envelope'])
        else:
            cases = [accounting_case(index, sub, out/(str(index)+'-'+sub)) for sub in subs]
        results.append(dict(control=control, cases=cases))
    return results


def prohibit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in ('os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('P01s forbids process creation')


def main(out, test_receipt):
    """Outer receipt writer accounts all fixture bytes, including failed writes."""
    sys.addaudithook(prohibit)
    start = time.monotonic()
    out = Path(out);out.mkdir(parents=True, exist_ok=False)
    with os.scandir(out) as entries:
        require(not list(entries), 'initial empty output')
    index = {}
    fixture_reservation = 0
    def emit(name, value, terminal=False):
        require(time.monotonic()-start < (120 if terminal else 115), 'cooperative deadline')
        data = value if isinstance(value, bytes) else raw(value)
        require(sum(x['size'] for x in index.values())+fixture_reservation+len(data) < (134217728 if terminal else 133169152), 'output reserve')
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        index[name]=dict(size=len(data),sha256=digest(data))
    result=dict(status='fail', world_transitions=0,keyed_evaluations=0,retained_payloads_parsed=0)
    try:
        protocol=json.loads((ROOT/'docs/p01s_protocol.json').read_bytes())
        freeze=json.loads((ROOT/'docs/p01s_registration_freeze.json').read_bytes())
        checked={}
        for section in ('files','inputs','prior_public_receipts'):
            for n,h in freeze[section].items():
                require(time.monotonic()-start < 115, 'custody deadline')
                if n not in checked:
                    content=(ROOT/n).read_bytes();require(digest(content)==h,'custody '+n);checked[n]=len(content)
        tests=json.loads(Path(test_receipt).read_bytes())
        sources={n:digest((ROOT/n).read_bytes()) for n in protocol['future_paths'].values()}
        require(tests['status']=='pass' and tests['returncodes']==[0,0] and tests['sources']==sources, 'test gate')
        declared=packet()
        require(tests['packet_sha256']==digest(raw(declared)), 'fixture packet identity')
        emit('packet.json',declared);emit('tests.json',Path(test_receipt).read_bytes())
        for n in sources:emit('sources/'+n,(ROOT/n).read_bytes())
        emit('custody.json',dict(files=len(freeze['files']),inputs=len(freeze['inputs']),prior_receipts=len(freeze['prior_public_receipts']),unique_reads=len(checked),hash_read_bytes=sum(checked.values()),input_full_scans=0,sources=sources,freeze_sha256=digest((ROOT/'docs/p01s_registration_freeze.json').read_bytes())))
        # Each isolated accounting fixture is capped at 2 MiB. Reserve all of
        # them before work; a failed fixture need not be scanned to bound usage.
        fixture_reservation = sum(len(declared['controls'][n]) for n in protocol['controls'][10:])*2097152
        require(sum(x['size'] for x in index.values())+fixture_reservation < 133169152, 'fixture reservation')
        records=run_suite(out/'fixtures',declared)
        # Known fixture paths are enumerated from the fixed packet, not a tree scan.
        for record in records:
            for case in record['cases']:
                if 'root' not in case:continue
                root=out/'fixtures'/case['root']
                names=set(case['files'])
                sub=case['subcase']
                if sub=='unlisted':names.add('unknown')
                if record['control']=='bounded_stage_reconciliation' and sub in ('unknown','oversize'):names.add('stage/'+('unknown' if sub=='unknown' else 'a'))
                for n in names:
                    p=root/n
                    if sub=='missing' and n=='a':continue
                    content=p.read_bytes();index[str(p.relative_to(out))]=dict(size=len(content),sha256=digest(content))
                # Symlink fixture is retained, listed separately and never followed in the seal.
                if sub=='symlink':index[str((root/'link').relative_to(out))]=dict(symlink='a',size=0)
        fixture_reservation = 0
        emit('results.json',records)
        result.update(status='pass',controls=len(records),subcases=sum(len(r['cases']) for r in records))
    except Exception as error:result['error']=repr(error)
    # Terminal accounting uses known entries; no recursive custody/output scan.
    emit('assessment.json',result,terminal=True)
    payload=raw(index);(out/'checksums.json').write_bytes(payload)
    completion=dict(status=result['status'],checksums_sha256=digest(payload),wall_seconds=time.monotonic()-start,
                    output_bytes=0 if result['status']=='pass' else None,known_path_bytes=0,usage_upper_bound_bytes=0,fixture_reservation_bytes=fixture_reservation,inventory_scope='known_paths',reconciliation='pending_independent_audit' if result['status']=='pass' else 'incomplete')
    while True:
        content=raw(completion);known=sum(x['size'] for x in index.values())+len(payload)+len(content)
        upper=known+fixture_reservation
        if completion['known_path_bytes']==known and completion['usage_upper_bound_bytes']==upper:break
        completion['known_path_bytes']=known
        completion['usage_upper_bound_bytes']=upper
        if result['status']=='pass':completion['output_bytes']=known
    require(upper<134217728 and time.monotonic()-start<120,'terminal limits')
    (out/'completion.json').write_bytes(content)
    print(json.dumps(result))
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1],sys.argv[2]))
