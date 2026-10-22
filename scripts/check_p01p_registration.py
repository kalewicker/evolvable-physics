#!/usr/bin/env python3
"""Registration descriptors and file custody only; no retained rule parsing."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ['birth_funding_pairs', 'birth_recycle_pairs', 'child_next_birth_pairs',
          'funded_descendant_triples', 'joined_quadruples', 'cleanup_annotated_quintuples']
CONTROLS = ['missing_body', 'zero_matter_counterfactual', 'unary_drift_and_i32_bounds',
            'phase_order_filtering', 'wrong_cleanup_kind_or_state', 'grandchild_nonleaf_for_recycle',
            'creation_edge_removed_before_parent_recycle', 'edge_only_cleanup_orphans_grandchild',
            'recycled_cleanup_refunds_free_resources', 'same_kind_distinct_roles_and_reused_body',
            'initial_state_absence_is_scenario_only']


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
    require(p['schema'] == 'p01p-read-only-analysis-registration-v1', 'schema')
    require(equal(p['proposal_ids'], list(range(6000, 6032))) and equal(p['initial_ids'], list(range(4))), 'fixed IDs')
    require(equal([p[k] for k in ('law_denominator', 'initial_denominator', 'slots_per_law', 'epochs')],
                  [32, 128, 8, 0]), 'fixed denominators')
    for k, v in [('registration_only_now', True), ('read_only_analysis_admitted_after_commit_push', True),
                 ('diagnosis_executed_now', False), ('sampling_admitted', False),
                 ('world_execution_admitted', False), ('e01_authorized', False), ('scientific_status', 'untested')]:
        require(equal(p[k], v), 'admission: '+k)
    require(p['source_bundle'] == 'artifacts/p01o-001' and p['source_closure'] == 'docs/p01o_closure.json' and
            p['source_seal_sha256'] == 'fa6fb28cefdf3f253227fc1de2096246a9c1bf30bd6c7ce2d1b8deef72fdfd00', 'consumed source')
    require(p['body_groups'] == GROUPS and p['verification_controls'] == CONTROLS, 'complete groups/controls')
    require(p['phases'] == dict(parent=['birth', 'funding', 'parent_recycling'],
        child=['newborn', 'funding', 'next_birth', 'outgoing_edge_cleanup', 'parent_recycling'],
        grandchild=['newborn', 'outgoing_edge_cleanup'], cleanup_forms=[6, 7],
        order=['birth_P_to_C', 'funding_P_to_C_twice', 'birth_C_to_G', 'cleanup_C_to_G', 'recycle_C_to_P']), 'ordered phases and cleanup')
    r = p['resource_contract']
    require(equal([r[k] for k in ('initial_original', 'newborn', 'birth_requirement', 'structural_funding_matter',
                                  'activation_amounts', 'transfers')], [[8, 8], [1, 1], [3, 2], 1, [1, 2], 2]), 'resource premises')
    require(len(p['conditional_budget_cases']) == 4, 'four conditional ledgers')
    for case, (amount, cleanup) in zip(p['conditional_budget_cases'], itertools.product((1, 2), (6, 7))):
        want = dict(name=f'activation_{amount}_cleanup_{cleanup}', activation_per_funding=amount, cleanup_form=cleanup,
            parent_after_funding=[3, 6-2*amount], child_after_funding=[3, 1+2*amount],
            child_after_descendant_birth=[0, 2*amount-1], grandchild_at_birth=[1, 1],
            child_after_cleanup=[1 if cleanup == 6 else 3, 2*amount-1],
            parent_after_recycling=[6 if cleanup == 6 else 8, 4],
            grandchild_after_cleanup=[1, 1] if cleanup == 6 else None,
            total_dissipated_activation=3 if cleanup == 6 else 4)
        require(equal(case, want), 'conditional ledger: '+case['name'])
        # Global free activation plus declared burns must account for the original8.
        orphan_activation = 0 if case['grandchild_after_cleanup'] is None else case['grandchild_after_cleanup'][1]
        require(case['parent_after_recycling'][1]+orphan_activation+case['total_dissipated_activation'] == 8,
                'activation conservation')
    v = p['verification_policy']
    require(equal([v[k] for k in ('state_schema_count', 'writer_sets_zero_one_two_with_replacement',
                                 'state_closure_comparisons')], [20, 231, 924]) and
            v['starts'] == ['singleton0', 'singleton1', 'singleton2', 'wildcard_i32'], 'state oracle census')
    require(p['reporting']['classification'] == ['local_condition_excluded', 'permitted_by_abstraction', 'unresolved'] and
            p['reporting']['behavioral_outcomes'] is None and p['reporting']['behavioral_missing_reason'] == 'not_executed' and
            p['reporting']['chemistry_continuation_gate'] is None, 'reporting scope')
    require(equal([p['development_limits'][k] for k in ('wall_seconds_per_tool', 'output_bytes_per_tool')],
                  [120, 134217728]), 'development limits')
    require(p['future_paths'] == dict(review='scripts/review_p01p.py', independent_audit='scripts/audit_p01p.py',
                                    tests='scripts/test_p01p.py'), 'new paths')
    return dict(schema='p01p-static-registration-review-v1', status='pass', fixed_laws=32, fixed_initial_records=128,
        slots_per_law=8, registered_body_groups=6, conditional_budget_controls=4, registered_negative_controls=11,
        planned_state_closure_comparisons=924, retained_rule_bodies_parsed=0, diagnosis_executed=False,
        keyed_evaluations=0, world_transitions=0, scientific_status='untested')


def main(out):
    p = load(ROOT/'docs/p01p_protocol.json')
    result = validate(p)
    freeze = load(ROOT/'docs/p01p_analysis_freeze.json')
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
        historical_file_counts=historical_counts, analysis_freeze_sha256=sha(ROOT/'docs/p01p_analysis_freeze.json'))
    out.mkdir(parents=True, exist_ok=False)
    (out/'static_review.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
