"""P01o custody/admission helpers. Hashing here identifies files, never draws fields."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plans(protocol):
    return [dict(slot=n, proposal=p, initial=i) for n, (p, i) in enumerate(
        (p, i) for p in protocol['proposal_ids'] for i in protocol['initial_state_ids'])]


def fixed_protocol(p):
    require(p['schema'] == 'p01o-v4-static-census-registration-v1' and
            p['generator'] == 'p01-generator-v4' and p['proposal_ids'] == list(range(6000, 6032)) and
            p['initial_state_ids'] == list(range(4)) and p['environment_denominator'] == 128 and
            p['epochs'] == 0 and p['world_execution_admitted'] is False, 'wrong static protocol')


def verify_closure(root=ROOT):
    p = load(root / 'docs/p01o_protocol.json')
    fixed_protocol(p)
    freeze = load(root / 'docs/p01o_execution_freeze.json')
    admission = load(root / 'docs/p01o_execution_admission.json')
    require(admission['schema'] == 'p01o-static-execution-admission-v1' and
            admission['sampling_admitted'] is True and admission['world_execution_admitted'] is False and
            admission['e01_authorized'] is False and admission['fixed_cells'] == 128 and
            admission['protocol_sha256'] == sha(root / 'docs/p01o_protocol.json') and
            admission['registration_freeze_sha256'] == sha(root / 'docs/p01o_registration_freeze.json') and
            admission['execution_freeze_sha256'] == sha(root / 'docs/p01o_execution_freeze.json'), 'sampling not admitted')
    for name, digest in freeze['files'].items():
        require(sha(root / name) == digest, 'source identity: ' + name)
    for section in ('dependencies', 'tools'):
        for name, digest in freeze[section].items():
            require(sha(name) == digest, section + ' identity: ' + name)
    for item in freeze['binaries'].values():
        require(sha(root / item['path']) == item['sha256'], 'binary identity')
    return p, freeze, admission


def authorize(bundle, stage, slot=None, root=ROOT):
    """Fail before field hashing unless the frozen runner has this exact stage active."""
    bundle = Path(bundle).resolve()
    p = load(root / 'docs/p01o_protocol.json')
    fixed_protocol(p)
    a = load(root / 'docs/p01o_execution_admission.json')
    fpath = root / 'docs/p01o_execution_freeze.json'
    require(a['schema'] == 'p01o-static-execution-admission-v1' and a['sampling_admitted'] is True and
            a['world_execution_admitted'] is False and a['e01_authorized'] is False and a['fixed_cells'] == 128 and
            a['protocol_sha256'] == sha(root / 'docs/p01o_protocol.json') and
            a['registration_freeze_sha256'] == sha(root / 'docs/p01o_registration_freeze.json') and
            a['execution_freeze_sha256'] == sha(fpath), 'sampling not admitted')
    require(bundle == Path(a['output_absolute']), 'wrong output path')
    f = load(fpath)
    # The runner verifies the complete closure before/after execution. Each child
    # additionally verifies all executable Python sources and the running binary copy.
    for name, digest in f['files'].items():
        if name.startswith('scripts/') and name.endswith('.py'):
            require(sha(root / name) == digest, 'child source identity: ' + name)
    require(sha(bundle / 'bin/generator-v4') == f['binaries']['generator-v4']['sha256'], 'child binary identity')
    m = load(bundle / 'manifest.json')
    require(m['execution_status'] == 'running' and m['active_stage'] == {'name': stage, 'slot': slot} and
            m['execution_admission_sha256'] == sha(root / 'docs/p01o_execution_admission.json'), 'inactive sampled stage')
    require(len(m['rows']) == 128 and all(all(row[k] == v for k, v in plan.items())
            for row, plan in zip(m['rows'], plans(p))), 'missing/reordered manifest')
    if slot is not None:
        require(type(slot) is int and 0 <= slot < 128 and stage in ('rust_generation', 'python_generation'), 'wrong sampled cell')
    else:
        require(stage == 'independent_audit' and all(r['status'] == 'complete' for r in m['rows']), 'incomplete audit panel')
    return p
