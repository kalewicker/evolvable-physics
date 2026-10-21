#!/usr/bin/env python3
"""Descriptive aggregation of retained census predicates; no sampler or dynamics."""
import json
import sys
from pathlib import Path
from p01k_contract import canonical, load, require, sha


def summarize(bundle):
    census = load(bundle / 'analysis/static_report/stdout.bin')
    require(len(census['laws']) == 32 and len(census['cells']) == 128, 'fixed census denominator')
    rows = []
    for law in census['laws']:
        funding, recycling, descendants = (law[name] for name in ('birth_funding_pairs', 'birth_recycle_pairs', 'child_donor_pairs'))
        immediate = lambda p: p['kind_match'] and p['donor_state_intersection'] and p['child_birth_state_acceptance']
        metrics = dict(
            birth_bodies=sum(p['form'] == 4 for p in law['template_slots']),
            birth_funding_pairs=len(funding), funding_kind_matches=sum(p['kind_match'] for p in funding),
            funding_kind_and_immediate_states=sum(immediate(p) for p in funding),
            funding_kind_states_and_material=sum(immediate(p) and p['material_funding'] for p in funding),
            birth_recycle_pairs=len(recycling), recycle_kind_matches=sum(p['kind_match'] for p in recycling),
            recycle_kind_and_immediate_states=sum(immediate(p) for p in recycling),
            child_donor_pairs=len(descendants), child_donor_kind_matches=sum(p['kind_match'] for p in descendants),
            child_donor_kind_and_birth_state=sum(p['kind_match'] and p['child_birth_state_acceptance'] for p in descendants),
            closed_type_paths=sum(p['closed_type_path'] for p in law['type_paths']))
        for flag in ('type_only', 'immediate_state_aligned', 'matter_bearing', 'immediate_state_aligned_and_material'):
            metrics['joined_' + flag] = sum(p[flag] for p in law['joined_motifs'])
        require(all(v == {'value': None, 'reason': 'not_executed'} for v in law['behavioral_outcomes'].values()), 'behavioral endpoint scope')
        rows.append(dict(proposal=law['proposal'], law_digest=law['law_digest'], map=law['map'],
                         state_write_bodies=law['state_write_bodies'], metrics=metrics))
    keys = list(rows[0]['metrics'])
    return dict(schema='p01k-descriptive-census-summary-v1', law_cells=32, initial_environments=128,
                distinct_tables=census['distinct_tables'], laws=rows,
                totals_by_proposal_cell={k: sum(r['metrics'][k] for r in rows) for k in keys},
                positive_law_cells={k: sum(r['metrics'][k] > 0 for r in rows) for k in keys},
                positive_distinct_tables={k: len({r['law_digest'] for r in rows if r['metrics'][k] > 0}) for k in keys},
                scope='descriptive counts of preregistered local schema predicates; no chemistry gate or behavioral observations',
                chemistry_continuation_gate=None, behavioral_outcomes=None, behavioral_missing_reason='not_executed',
                census_sha256=sha(bundle / 'analysis/static_report/stdout.bin'), seal_sha256=sha(bundle / 'seal.json'),
                keyed_hash_evaluations=0, world_transitions=0, scientific_status='untested')


if __name__ == '__main__':
    result = summarize(Path(sys.argv[1]))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'summary.json').open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(canonical({k: v for k, v in result.items() if k not in ('laws', 'positive_law_cells', 'positive_distinct_tables')}))
