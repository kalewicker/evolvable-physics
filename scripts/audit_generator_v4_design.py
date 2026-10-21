#!/usr/bin/env python3
"""Read saved abstract profiles independently; no design checker import."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def audit(bundle):
    receipt = load(bundle / 'static_review.json')
    inventory = load(bundle / 'checksums.json')
    require({str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file()} == set(inventory) | {'checksums.json'}, 'inventory membership')
    for name, digest in inventory.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'inventory path')
        require(sha(bundle / name) == digest, 'file identity: ' + name)
    root = Path(__file__).resolve().parents[1]
    for name, digest in receipt['source_sha256'].items():
        require(sha(root / name) == sha(bundle / 'source' / name) == digest, 'source identity')
    seen, partition, minimum = set(), Counter(), Counter()
    feasible = local = funded = 0
    for line in (bundle / 'profiles.jsonl').read_text().splitlines():
        p = json.loads(line)
        mapping = p['type_map']
        masks = [p[k] for k in ('birth_mask', 'funding_mask', 'recycling_mask')]
        require(len(mapping) == 3 and all(k in (1, 2, 3) for k in mapping) and
                all(type(m) is int and 0 <= m < 8 for m in masks), 'profile domain')
        identity = (tuple(mapping), *masks)
        require(identity not in seen, 'duplicate profile')
        seen.add(identity)
        b, f, r = [{i + 1 for i in range(3) if mask & 2**i} for mask in masks]
        direct = {x for x in b if x in f and mapping[x - 1] in b}
        require(sorted(direct) == p['funded_descendant_starts'] and
                sorted(direct & r) == p['local_recycling_starts'], 'local set predicates')
        for group, key in [(b & f, 'recurrent_birth_funding_starts'), (b & f & r, 'recurrent_all_three_role_starts')]:
            # Explicit adjacency elimination for three rounds, independently
            # of the checker's orbit walk and stable-set implementation.
            adjacency = {(i, j) for i in group for j in group if mapping[i - 1] == j}
            keep = set(group)
            for _ in range(3):
                keep = {i for i in keep if any(a == i and z in keep for a, z in adjacency)}
            require(sorted(keep) == p[key], 'independent recurrent-set check')
        needed = sum(len(g) for g in (b, f, r))
        require(needed == p['minimum_bodies'] and (needed <= 8) == p['fits_eight_slots'], 'slot predicate')
        reason = ('no_birth_donor' if not b else 'no_local_funded_descendant' if not direct else
                  'funded_descendant_without_local_recycle' if not direct & r else 'local_joined_labels_available')
        require(reason == p['reason'], 'exclusive reason')
        feasible += needed <= 8
        funded += bool(direct)
        local += bool(direct & r)
        minimum[needed] += 1
        partition[reason] += 1
    require(len(seen) == 27 * 8**3 == 13824 and feasible == 13797, 'complete profile domain')
    expected = receipt['availability']
    require(dict(partition) == expected['exclusive_partition'] and
            {str(k): v for k, v in minimum.items()} == expected['minimum_bodies_histogram'], 'profile aggregates')
    require(funded == expected['local_funded_profile_count'] and local == expected['local_joined_profile_count'], 'local totals')
    require(sha(bundle / 'profiles.jsonl') == receipt['profiles_sha256'], 'profile link')
    require(receipt['behavioral_outcomes'] is None and receipt['behavioral_missing_reason'] == 'not_executed' and
            not receipt['generator_implemented'] and not receipt['sampling_admitted'] and not receipt['world_execution_admitted'] and
            receipt['keyed_hash_evaluations'] == receipt['world_transitions'] == 0, 'scope')
    return dict(schema='p01m-independent-saved-profile-audit-v1', status='pass', profiles_verified=len(seen),
                slot_feasible_profiles=feasible, all_profile_membership_and_cycles_checked=True,
                review_sha256=sha(bundle / 'static_review.json'), analysis_checksums_sha256=sha(bundle / 'checksums.json'),
                audit_source_sha256=sha(Path(__file__)), keyed_hash_evaluations=0, world_transitions=0,
                scope='saved profile/domain/custody audit; label-state equalities verified separately by design checker')


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]))
    with Path(sys.argv[2]).open('x') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps(result, sort_keys=True))
