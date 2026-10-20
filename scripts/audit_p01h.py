#!/usr/bin/env python3
"""Independent saved-record checks for P01h, without sampling or evolution."""
import collections
import json
import sys
from pathlib import Path
import audit
import audit_p01g_receipts
from check_p01g_registration import load,sha
from diagnose_p01g import read_only

if not __debug__:raise RuntimeError('Read-only audit requires assertions')


def kind_matrix(rules):
    # Direct tag/slot extraction; do not use the diagnostic's form classifier,
    # compatibility test, state-invariance analysis or operation conditions.
    births=[];funding=[];recycling=[]
    for r in rules:
        tags=tuple(op['op'] for op in r['ops'])
        if tags==('CreateNode','CreateEdge','Transfer','Burn'):
            births.append((r['id'],r['nodes'][0]['kind'],r['ops'][0]['kind']))
        elif tags==('Transfer',) and r['edges'][0]['class']=='Structural':
            funding.append((r['id'],r['nodes'][0]['kind'],r['nodes'][1]['kind']))
        elif tags==('DeleteEdge','DeleteNode','Burn'):
            recycling.append((r['id'],r['nodes'][0]['kind'],r['nodes'][1]['kind']))
    def pairs(other):return [[b[0],r[0]] for b in births for r in other if b[1:]==r[1:]]
    return {'birth_rules':len(births),'funding_rules':len(funding),'recycling_rules':len(recycling),
            'birth_funding_pairs':len(births)*len(funding),'birth_recycling_pairs':len(births)*len(recycling),
            'kind_compatible_funding_pairs':pairs(funding),'kind_compatible_recycling_pairs':pairs(recycling)}


def verify(bundle,analysis):
    inventory=load(analysis/'checksums.json')
    assert {str(p.relative_to(analysis)) for p in analysis.rglob('*') if p.is_file()}==set(inventory)|{'checksums.json'}
    for name,h in inventory.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(analysis/name)==h,name
    manifest=load(analysis/'manifest.json');findings=load(analysis/'findings.json')
    assert manifest['execution_status']=='complete' and manifest['processed_cells']==64
    for name,h in manifest['source_files'].items():assert sha(analysis/'source'/name)==h
    source=audit_p01g_receipts.verify(bundle)
    assert source==load(analysis/'input_receipt_audit.json') and source['engineering_gate_pass'] and not source['mechanism_gate_pass']
    assert findings['input_manifest_sha256']==sha(bundle/'manifest.json')==manifest['input_manifest_sha256']
    assert findings['input_seal_sha256']==sha(bundle/'seal.json')==manifest['input_seal_sha256']
    assert findings['analysis_plan_sha256']==sha(analysis/'source/docs/p01h_analysis_plan.md')
    cells=load(analysis/'cell_diagnoses.json');laws=load(analysis/'law_diagnoses.json')
    rows=load(bundle/'manifest.json')['rows'];assert len(cells)==len(rows)==64 and len(laws)==16
    matrix=[];seen={};events=collections.Counter();totals=collections.Counter();bcounts=collections.Counter()
    for row,cell in zip(rows,cells):
        assert all(row[k]==cell[k] for k in ('slot','proposal','initial_state','law_digest'))
        assert cell['full_horizon_ap']==row['observation']['full_horizon_ap']
        path=bundle/'runs'/str(row['slot']);rules=load(path/'request.json')['initial']['native']['rules']
        digest=audit.digest([{k:v for k,v in r.items() if k!='id'} for r in rules]);assert digest==row['law_digest']
        if row['proposal'] not in seen:
            seen[row['proposal']]=digest;matrix.append({'proposal':row['proposal'],**kind_matrix(rules)})
        assert seen[row['proposal']]==digest
        events.update(cell['event_forms']);totals.update(cell['base_opportunities'])
        assert cell['epochs']==128
        receipt=load(path/'python_audit/stdout.bin')
        assert len(cell['newborn_histories'])==receipt['prefix_counts']['births']
        assert sum(v['ever_jointly_visible'] for v in cell['birth_visibility'])==receipt['prefix_counts']['visibility']
        for k,c in cell['mechanism_exposures'].items():
            assert sum(c['first_blocker'].values())==c['exposures']
            bcounts[k+'_exposures']+=c['exposures']
            assert not any(c['first_blocker'].get(reason,0) for reason in ('committed','scheduler_conflict'))
        for h in cell['newborn_histories']:
            assert h['matter']==[1] and set(h['activation'])<={0,1} and h['construction_resources_pre_epochs']==0
    assert [l['proposal'] for l in laws]==list(range(4000,4016))
    for m,l in zip(matrix,laws):
        assert m['proposal']==l['proposal']
        for k in ('funding','recycling'):
            assert not m['kind_compatible_'+k+'_pairs'], 'A compatible pair invalidates the fixed-table kind exclusion'
            assert m['birth_'+k+'_pairs']==len(l['birth_pair_compatibility'][k])
            assert all(set(p['excluded_by'])&{'donor_kind','target_kind'} for p in l['birth_pair_compatibility'][k])
    assert dict(events)==findings['committed_event_forms'] and sum(events.values())==7453
    for k,v in totals.items():assert findings['totals'][k]==v
    assert sum(c['epochs'] for c in cells)==findings['totals']['epochs']==8192
    for k in ('funding','recycling','descendant_birth'):assert bcounts[k+'_exposures']==findings['mechanism_exposures'][k]['exposures']
    inc=[c for c in cells if c['full_horizon_ap']=='inconclusive']
    assert inc==load(analysis/'inconclusive_cases.json') and [c['slot'] for c in inc]==[29,31]
    assert all(findings[k]==manifest[k]==0 for k in ('new_world_runs','sampler_calls','transition_applications'))
    return {'schema':'p01h-independent-record-audit-v1','status':'pass',
            'input_manifest_sha256':sha(bundle/'manifest.json'),'input_seal_sha256':sha(bundle/'seal.json'),
            'analysis_manifest_sha256':sha(analysis/'manifest.json'),'analysis_checksums_sha256':sha(analysis/'checksums.json'),
            'law_kind_matrices':matrix,'matched_birth_funding_pairs':sum(len(m['kind_compatible_funding_pairs']) for m in matrix),
            'matched_birth_recycling_pairs':sum(len(m['kind_compatible_recycling_pairs']) for m in matrix),
            'cells':64,'epochs':8192,'events':7453,'inconclusive_slots_preserved':[29,31],
            'new_world_runs':0,'sampler_calls':0,'transition_applications':0,'scientific_status':'untested',
            'scope':'saved-record identities, counts and independent kind-matrix check; conditional source argument is not a formal proof assistant result'}

if __name__=='__main__':
    with read_only():result=verify(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
    print(json.dumps(result,sort_keys=True,indent=2))
