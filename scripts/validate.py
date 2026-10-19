#!/usr/bin/env python3
"""Run a bounded, immutable evidence bundle; no scientific campaign is launched."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
import audit
import validate_interventions
import validate_environment
import validate_environment_branches
import validate_detectors
import validate_generalization

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, log):
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log.write_text(p.stdout)
    if p.returncode:
        raise RuntimeError(f'Failed ({p.returncode}); retained output: {log}')
    return p.stdout

def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'stage': 'P00f', 'execution_status': 'running', 'scientific_status': 'untested',
                'p00_complete': False, 'source_files': {}, 'checks': {}}
    manifest_path = out / 'manifest.json'
    def save():
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    save()
    try:
        validate_generalization.check_freeze()
        source = out / 'source'; source.mkdir()
        files = [ROOT / 'Cargo.toml', ROOT / 'Cargo.lock', ROOT / 'README.md']
        for folder in ('src', 'tests', 'docs', 'scripts'):
            files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        for p in sorted(files):
            relative = p.relative_to(ROOT)
            dest = source / relative; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            manifest['source_files'][str(relative)] = hashlib.sha256(p.read_bytes()).hexdigest()
        run(['rustc', '--version'], out/'rustc.txt')
        run(['cargo', 'test', '--locked', '--offline'], out/'tests.txt')
        manifest['checks']['rust_tests'] = 'pass'; save()
        run(['cargo', 'clippy', '--locked', '--offline', '--all-targets', '--', '-D', 'warnings'], out/'clippy.txt')
        run(['cargo', 'fmt', '--check'], out/'format.txt')
        run(['cargo', 'build', '--locked', '--offline'], out/'build.txt')
        binary = ROOT/'target/debug/causal-alife'
        manifest['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        run([str(binary), 'fixtures', str(out/'fixtures')], out/'fixtures.txt')
        suite = json.loads((out/'fixtures/suite.json').read_text())
        receipt = audit.audit(suite)
        (out/'independent_audit.json').write_text(json.dumps(receipt, indent=2)+'\n')
        manifest['checks']['independent_replay'] = receipt
        optimized = subprocess.run([sys.executable, '-O', str(ROOT/'scripts/audit.py'), str(out/'fixtures/suite.json')], capture_output=True, text=True)
        (out/'assertions_required.txt').write_text(optimized.stdout + optimized.stderr)
        assert optimized.returncode != 0
        manifest['checks']['audit_requires_assertions'] = 'pass'
        # Reject corrupted traces: altered candidate priority, world, parentage, event omission, and rule.
        rejected = []
        base = next(c for c in suite['cases'] if c['name'] == 'oscillator')
        for mutation in ('priority', 'state', 'parents', 'events', 'rule'):
            c = copy.deepcopy(base)
            if mutation == 'priority': c['frames'][0]['candidates'][0]['priority'] = '0'*64
            elif mutation == 'state': c['frames'][0]['world']['nodes']['0']['state'] = 9
            elif mutation == 'parents': c['frames'][1]['events'][0]['parents'] = []
            elif mutation == 'events': c['frames'][0]['events'] = []
            else: c['initial']['rules'][0]['ops'][0]['value'] = 8
            try:
                audit.verify_case(c)
            except AssertionError:
                rejected.append(mutation)
            else:
                raise AssertionError(f'Auditor accepted {mutation}')
        manifest['checks']['audit_tamper_rejections'] = rejected
        cp = out/'fixtures/checkpoint.json'
        run([str(binary), 'resume', str(cp), '7', str(out/'resumed.json')], out/'resume.txt')
        assert json.loads((out/'resumed.json').read_text()) == json.loads((out/'fixtures/expected.json').read_text())
        run([str(binary), 'resume', str(cp), '0', str(out/'noop.json')], out/'noop.txt')
        assert json.loads((out/'noop.json').read_text()) == json.loads(cp.read_text())
        manifest['checks']['fresh_process_continuation'] = 'pass'
        manifest['checks']['noop_checkpoint_branch'] = 'pass'
        for name, data in [('truncated', cp.read_bytes()[:100]), ('tampered', cp.read_bytes().replace(b'"seed": 7', b'"seed": 8'))]:
            bad = out/f'{name}.json'; bad.write_bytes(data)
            result = subprocess.run([str(binary), 'resume', str(bad), '1', str(out/f'{name}-accepted.json')], capture_output=True, text=True)
            (out/f'{name}.txt').write_text(result.stdout + result.stderr)
            assert result.returncode != 0 and not (out/f'{name}-accepted.json').exists()
        manifest['checks']['damaged_checkpoints_rejected'] = 'pass'
        # Existing destinations are never overwritten.
        original = cp.read_bytes()
        result = subprocess.run([str(binary), 'resume', str(cp), '1', str(cp)], capture_output=True, text=True)
        (out/'overwrite.txt').write_text(result.stdout + result.stderr)
        assert result.returncode != 0 and cp.read_bytes() == original
        manifest['checks']['checkpoint_overwrite_rejected'] = 'pass'
        manifest['checks']['interventions'] = validate_interventions.validate(binary, out, run)
        manifest['checks']['environment'] = validate_environment.validate(binary, out, run)
        manifest['checks']['environment_branches'] = validate_environment_branches.validate(binary, out, run)
        manifest['checks']['detectors'] = validate_detectors.validate(binary, out, run)
        manifest['checks']['generalization'] = validate_generalization.validate(binary, out, run)
        manifest['execution_status'] = 'complete'
    except Exception as error:
        manifest['execution_status'] = 'failed'
        manifest['error'] = str(error)
        raise
    finally:
        save()
        inventory = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'checksums.json'}
        (out/'checksums.json').write_text(json.dumps(inventory, indent=2)+'\n')
    print(json.dumps(manifest['checks'], indent=2))

if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Verification requires Python assertions enabled; do not use -O')
    main()
