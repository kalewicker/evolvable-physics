"""Fixed authored transport controls. Persist every fixture before execution."""
import ast
import copy
import json
import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import p01t_readiness as p
import audit_p01t as a


def envelope(slot=0):
    return dict(schema='p01o-generated-environment-v1',slot=slot,proposal=6000+slot//4,initial=slot%4,
        map=[0,1,2],state_map=[2,1,0],draws=[dict(authored=True)],extra=dict(keep=['é',False,0,None]),
        environment=dict(profile='inert-authored',native=dict(world=dict(resource=7),rules=[dict(inert=True)])))


def declared():
    names=json.loads((p.ROOT/'docs/p01t_protocol.json').read_bytes())['controls']
    subs=[['exact_request_parse_back'],['all128_first_last'],
        ['bool_int','int_float','object_order','array_order'],
        ['malformed','duplicate','nan','infinity','overflow'],
        ['hash','schema','slot','proposal','initial','boolean_id'],
        ['missing_environment','nonobject_environment','missing_native','nonobject_native','unwrapped'],
        ['extra_metadata_maps_draws'],['resource','rule','schema','epochs','max_events','max_trace_bytes'],
        ['relative','absolute'],['partial_syscall'],['exhausted_reserve','terminal_io_error'],
        ['wall_below','wall_equal','wall_above','bytes_below','bytes_equal','bytes_above','100_polls'],
        ['missing','duplicate','reordered','extra','boolean_id'],
        ['changed_bytes','unlisted','missing_file','scan_counter','write_counter','ledger_counter','partial_false_total']]
    return dict(schema='p01t-invented-controls-v1',controls=dict(zip(names,subs)),envelope=envelope())


class Transport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['P01T_TEST_OUT']);cls.root.mkdir(parents=True,exist_ok=False)
        cls.packet=declared();(cls.root/'packet.json').write_bytes(p.encoded(cls.packet))
        cls.cache={};cls.hashes={}
        for i in range(128):
            raw=p.encoded(envelope(i))
            for n in p.paths(i):cls.cache[n]=raw;cls.hashes[n]=p.sha(raw)
        (cls.root/'inputs.json').write_bytes(p.encoded({n:b.decode() for n,b in cls.cache.items()}))
        out=p.Output(cls.root/'panel');p.run_panel(out,cls.cache,cls.hashes);cls.finish=out.finish()
        cls.data,cls.scan=a.output_inventory(cls.root/'panel')
        cls.rows=json.loads(cls.data['manifest.json'])['rows']

    def pair(self,x,y=None):
        raw=[p.encoded(x),p.encoded(x if y is None else y)]
        return raw,list(map(p.sha,raw))
    def reject_pair(self,streams,hashes):
        with self.assertRaises((ValueError,TypeError)):p.convert(streams,hashes,(0,6000,0))
        with self.assertRaises((ValueError,TypeError)):a.oracle(streams,hashes,(0,6000,0))

    def test_01_complete_envelope(self):
        s,h=self.pair(envelope());raw,row=p.convert(s,h,(0,6000,0))
        self.assertTrue(a.verify_request(raw,s,h,(0,6000,0),row))
        self.assertEqual(json.loads(raw)['initial'],envelope()['environment'])

    def test_02_all128(self):
        self.assertEqual(self.finish['status'],'pass')
        self.assertEqual(a.verify_panel(self.data,self.cache,self.hashes)['cells'],128)
        self.assertEqual(self.rows[0]['proposal'],6000);self.assertEqual(self.rows[-1]['proposal'],6031)
        self.assertEqual(self.rows[-1]['initial'],3)

    def test_03_typed_equality(self):
        for v in (True,7.0):
            b=envelope();b['environment']['native']['world']['resource']=v
            self.reject_pair(*self.pair(envelope(),b))
        x=envelope();y=dict(reversed(list(x.items())))
        s=[json.dumps(x).encode(),json.dumps(y).encode()];h=list(map(p.sha,s))
        raw,_=p.convert(s,h,(0,6000,0));self.assertTrue(a.verify_request(raw,s,h,(0,6000,0)))
        b=envelope();b['map'].reverse();self.reject_pair(*self.pair(envelope(),b))

    def test_04_invalid_json(self):
        raw=p.encoded(envelope())
        bad=[b'{',raw.replace(b'"slot":0',b'"slot":0,"slot":0')]
        bad.extend(raw.replace(b'"resource":7',b'"resource":'+token) for token in (b'NaN',b'Infinity',b'1e999'))
        for b in bad:self.reject_pair([b,b],[p.sha(b)]*2)

    def test_05_identity_and_hash(self):
        s,h=self.pair(envelope());self.reject_pair(s,['0'*64,h[1]])
        for key,value in [('schema','wrong'),('slot',1),('proposal',6001),('initial',1),('slot',False)]:
            e=envelope();e[key]=value;self.reject_pair(*self.pair(e))

    def test_06_objects(self):
        for key,parent in [('environment',False),('native',True)]:
            for remove in (True,False):
                e=envelope();obj=e['environment'] if parent else e
                if remove:obj.pop(key)
                else:obj[key]=[]
                self.reject_pair(*self.pair(e))
        self.reject_pair(*self.pair(envelope()['environment']))

    def test_07_metadata(self):
        e=envelope();e['unknown']={'draws':[1,False,2.0]};e['draws'].append({'keep':'yes'})
        s,h=self.pair(e);raw,row=p.convert(s,h,(0,6000,0))
        self.assertEqual(row['envelope_canonical_sha256'],a.sha(a.encoded(e)))
        self.assertTrue(a.verify_request(raw,s,h,(0,6000,0),row))

    def test_08_request_mutations(self):
        s,h=self.pair(envelope());raw,_=p.convert(s,h,(0,6000,0));base=json.loads(raw)
        for key in ('resource','rule','schema','epochs','max_events','max_trace_bytes'):
            v=copy.deepcopy(base)
            if key=='resource':v['initial']['native']['world']['resource']=8
            elif key=='rule':v['initial']['native']['rules'][0]['inert']=False
            elif key=='schema':v[key]='wrong'
            else:v[key]+=1
            with self.assertRaises(ValueError):a.verify_request(p.encoded(v),s,h,(0,6000,0))

    def test_09_paths(self):
        for name,path in [('relative',(self.root/'relative').relative_to(Path.cwd())),('absolute',self.root/'absolute')]:
            out=p.Output(path);p.run_panel(out,self.cache,self.hashes);self.assertEqual(out.finish()['status'],'pass')
            data,_=a.output_inventory(path);self.assertEqual(a.verify_panel(data,self.cache,self.hashes)['cells'],128)
            for i in range(128):self.assertEqual(data[f'requests/{i:03}.json'],self.data[f'requests/{i:03}.json'])

    def test_10_partial_write(self):
        out=p.Output(self.root/'partial');original=os.write;calls=[]
        def short(fd,data):
            if calls:raise OSError('injected syscall error')
            calls.append(True);return original(fd,data[:3])
        with patch('os.write',side_effect=short):p.run_panel(out,self.cache,self.hashes)
        result=out.finish();self.assertEqual(result['status'],'fail');self.assertEqual(out.ledger.files['requests/000.json']['size'],3)
        self.assertEqual((out.ledger.root/'requests/000.json').stat().st_size,3)
        self.assertEqual([r['status'] for r in result['rows']],['failed']+['unstarted']*127)
        (self.root/'partial_receipt.json').write_bytes(p.encoded(result))

    def test_11_terminal(self):
        now=[0];out=p.Output(self.root/'reserve_failure',clock=lambda:now[0]);now[0]=115
        p.run_panel(out,self.cache,self.hashes);first=out.first_error
        result=out.finish();self.assertEqual(result['first_error'],first);self.assertEqual(result['terminal_receipt'],'written')
        out=p.Output(self.root/'terminal_failure');out.first_error='original input error'
        with patch('os.open',side_effect=OSError('injected terminal I/O')):result=out.finish()
        self.assertEqual(result['first_error'],'original input error');self.assertEqual(result['terminal_receipt'],'missing')
        self.assertEqual(len(result['rows']),128);self.assertTrue(result['closeout_errors'])
        (self.root/'terminal_receipt.json').write_bytes(p.encoded(result))

    def test_12_reserves_and_spies(self):
        for k in ('wall','bytes'):
            for delta in (-1,0,1):
                now=[0];out=p.Output(self.root/f'{k}-{delta}',clock=lambda:now[0])
                if k=='wall':now[0]=115+delta
                else:out.ledger.cap=out.ledger.reserve-delta
                if delta<0:out.poll()
                else:
                    with self.assertRaises(ValueError):out.poll()
        out=p.Output(self.root/'poll_traps')
        with ExitStack() as stack:
            for target in ('os.stat','os.lstat','os.scandir','builtins.open','io.open','os.open'):
                stack.enter_context(patch(target,side_effect=RuntimeError('filesystem forbidden')))
            for _ in range(100):out.poll()
        self.assertEqual(out.ledger.counts['budget_polls'],100)
        # Independent observers see actual calls, including the initial empty scan.
        spies={k:0 for k in ('stat_calls','write_bytes','scans')};statfn=os.lstat;writefn=os.write;scanfn=os.scandir
        def st(*args,**kw):spies['stat_calls']+=1;return statfn(*args,**kw)
        def wr(*args,**kw):n=writefn(*args,**kw);spies['write_bytes']+=n;return n
        def sc(*args,**kw):spies['scans']+=1;return scanfn(*args,**kw)
        with patch('os.lstat',st),patch('os.write',wr),patch('os.scandir',sc):
            out=p.Output(self.root/'spy');out.write('requests/test.json',b'{}');out.finish()
        self.assertEqual(spies['stat_calls'],out.ledger.counts['stat_calls']);self.assertEqual(spies['write_bytes'],out.ledger.counts['write_bytes']);self.assertEqual(spies['scans'],1)
        (self.root/'spy_receipt.json').write_bytes(p.encoded(dict(observed=spies,ledger=out.ledger.counts)))

    def test_13_row_mutations(self):
        versions=[self.rows[:-1],self.rows[:1]+self.rows,self.rows[::-1],self.rows+[self.rows[-1]]]
        v=copy.deepcopy(self.rows);v[0]['slot']=False;versions.append(v)
        for v in versions:
            with self.assertRaises(ValueError):a.validate_rows(v)

    def test_14_inventory_mutations(self):
        for action in ('changed','unlisted','missing','scan','write','ledger','false_total'):
            data=dict(self.data)
            if action=='changed':data['requests/000.json']+=b' '
            elif action=='unlisted':data['unknown']=b'x'
            elif action=='missing':data.pop('requests/000.json')
            else:
                c=json.loads(data['completion.json'])
                if action=='false_total':c['output_bytes']=None
                else:c['counts_before_completion'][{'scan':'output_full_scans','write':'write_bytes','ledger':'ledger_updates'}[action]]+=1
                data['completion.json']=p.encoded(c)
                # Keep total consistent for counter mutations so the counter gate must reject.
                if action!='false_total':
                    while True:
                        total=sum(map(len,data.values()))
                        if c['output_bytes']==total:break
                        c['output_bytes']=total;data['completion.json']=p.encoded(c)
            with self.assertRaises(ValueError):a.verify_inventory(data)
        # No native/process imports; auditor stays independent.
        tree=ast.parse((p.ROOT/'scripts/audit_p01t.py').read_text())
        modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any(n and n.startswith(('p01s_','p01t_')) for n in modules))
        for event in ('subprocess.Popen','os.system','os.fork'):
            with self.assertRaises(RuntimeError):p.prohibit(event,())


if __name__=='__main__':unittest.main()
