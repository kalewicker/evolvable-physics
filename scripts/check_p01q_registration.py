#!/usr/bin/env python3
"""Registration descriptors and file custody only; no retained rule parsing."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def equal(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def cells(p):
    return [dict(slot=n, proposal=proposal, initial=initial)
            for n, (proposal, initial) in enumerate(itertools.product(p['proposal_ids'], p['initial_ids']))]


def validate(p):
    require(p['schema'] == 'p01q-saved-panel-dynamics-registration-v1', 'schema')
    require(equal(p['proposal_ids'], list(range(6000,6032))) and equal(p['initial_ids'], list(range(4))), 'fixed panel')
    require(equal([p[k] for k in ('law_denominator','trajectory_denominator','epochs')], [32,128,128]), 'denominators/horizon')
    for key, value in [('registration_only_now',True), ('implementation_admitted_after_commit_push',True),
        ('world_execution_admitted_now',False), ('keyed_evaluation_admitted',False), ('e01_authorized',False),
        ('scientific_status','untested'), ('behavioral_outcomes',None), ('behavioral_missing_reason','not_executed')]:
        require(equal(p[key],value), 'admission: '+key)
    require(p['source_bundle']=='artifacts/p01o-001' and p['source_seal_sha256']==
        'fa6fb28cefdf3f253227fc1de2096246a9c1bf30bd6c7ce2d1b8deef72fdfd00', 'original source')
    g=load(ROOT/'docs/p01g_protocol.json')
    for key in ('worker_request','mechanism_gate','decision','closed_environment_limits'):
        require(equal(p[key],g[key]), 'unchanged P01g: '+key)
    require(equal(p['per_process'],{k:v for k,v in g['per_process'].items() if k!='generation'}), 'stage budgets')
    for key, value in [('wall_seconds',1200),('total_process_cpu_seconds',600),('artifact_bytes',2147483648),
        ('metadata_reserve_bytes',67108864),('poll_seconds',0.01)]:
        require(equal(p['campaign'][key],value), 'campaign budget: '+key)
    for key,value in g['observables'].items():
        require(p['observables'][key]==value,'unchanged observable: '+key)
    require(set(p['observables'])==set(g['observables'])|{'cleanup_events','ordered_branch'}, 'endpoint membership')
    require(len(p['verification_controls'])==16 and len(set(p['verification_controls']))==16, 'controls')
    require(p['future_paths']==dict(campaign='scripts/p01q_campaign.py',cell='scripts/p01q_cell.py',
        independent_events='scripts/audit_p01q_events.py',receipt_audit='scripts/audit_p01q_receipts.py',
        tests='scripts/test_p01q.py'), 'new implementation paths')
    require(p['execution_output']=='artifacts/p01q-001', 'single output')
    # The freeze binds all textual definitions, not only the numeric checks above.
    return dict(schema='p01q-static-registration-review-v1',status='pass',fixed_laws=32,
        fixed_initial_records=128,planned_epochs_per_cell=128,registered_controls=16,
        retained_rule_bodies_parsed=0,keyed_evaluations=0,world_transitions=0,
        behavioral_outcomes=None,scientific_status='untested')


def main(out):
    p = load(ROOT/'docs/p01q_protocol.json')
    result = validate(p)
    freeze = load(ROOT/'docs/p01q_registration_freeze.json')
    for section in ('files', 'inputs', 'prior_public_receipts'):
        for name, digest in freeze[section].items():
            require(sha(ROOT/name) == digest, section+': '+name)
    bundle = ROOT/p['source_bundle']
    inventory = load(bundle/'checksums.json')
    require({str(f.relative_to(bundle)) for f in bundle.rglob('*') if f.is_file()} ==
            set(inventory)|{'checksums.json', 'seal.json'}, 'original inventory membership')
    for name, digest in inventory.items():
        require(sha(bundle/name) == digest, 'original inventory: '+name)
    seal = load(bundle/'seal.json')
    require(sha(bundle/'seal.json') == p['source_seal_sha256'] and seal['engineering_gate_pass'] is True and
        seal['manifest_sha256'] == sha(bundle/'manifest.json') and
        seal['checksums_sha256'] == sha(bundle/'checksums.json'), 'original seal')
    manifest = load(bundle/'manifest.json')
    require(manifest['execution_status'] == 'complete' and len(manifest['rows']) == 128, 'original denominator')
    expected_inputs = {p['source_bundle']+'/'+n for n in ('manifest.json', 'checksums.json', 'seal.json',
        'analysis/static_report/stdout.bin', 'analysis/independent_audit/stdout.bin')}
    expected_inputs.update(['artifacts/p01o-001-receipt-audit.json', 'artifacts/p01o-001-cost-audit.json',
                            'artifacts/p01o-closeout-001/summary.json'])
    for plan, row in zip(cells(p), manifest['rows']):
        require(equal({k: row[k] for k in plan}, plan) and row['status'] == 'complete', 'original cell identity')
        expected_inputs.update(p['source_bundle']+'/runs/'+str(plan['slot'])+'/'+language+'/stdout.bin'
                               for language in ('rust_generation', 'python_generation'))
    require(set(freeze['inputs']) == expected_inputs, 'complete analysis input set')
    for name, digest in load(ROOT/'docs/p01p_closure.json')['receipts'].items():
        require(sha(ROOT/name)==digest, 'P01p receipt: '+name)
    for name in p['future_paths'].values():
        require(not (ROOT/name).exists(), 'analysis implementation before plan commit: '+name)
    historical_counts = {}
    for name in freeze['historical_freezes']:
        historical = load(ROOT/name)['files']
        for file, digest in historical.items():
            require(sha(ROOT/file) == digest, 'historical source: '+file)
        historical_counts[name] = len(historical)
    result.update(registration_files_verified=len(freeze['files']), analysis_inputs_verified=len(freeze['inputs']),
        original_inventory_entries_verified=len(inventory), prior_public_receipts_verified=len(freeze['prior_public_receipts']),
        historical_file_counts=historical_counts, registration_freeze_sha256=sha(ROOT/'docs/p01q_registration_freeze.json'))
    out.mkdir(parents=True, exist_ok=False)
    (out/'static_review.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
