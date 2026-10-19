"""Bounded P00b checks, invoked by validate.py inside its preserved evidence bundle."""
import copy
import json
import subprocess
import audit_interventions as checker

def validate(binary, out, run):
    directory = out/'interventions'
    run([str(binary), 'intervention-fixtures', str(directory)], out/'interventions.txt')
    suite = json.loads((directory/'suite.json').read_text())
    receipt = checker.audit_suite(suite)
    (out/'intervention_audit.json').write_text(json.dumps(receipt, indent=2)+'\n')
    mutations = ('receipt', 'source', 'operation', 'rescue', 'label', 'writer', 'warmup', 'law')
    rejected = []
    for mutation in mutations:
        case = copy.deepcopy(suite['cases'][0])
        target = case['arms'][2]['chain'][0]
        if mutation == 'receipt': target['receipt']['parents'] = []
        elif mutation == 'source': target['request']['expected_source'] = '0'*64
        elif mutation == 'operation': target['request']['operations'][0]['value'] = 8
        elif mutation == 'rescue': case['arms'][4]['chain'].pop()
        elif mutation == 'label': case['arms'][2]['name'] = 'unrelated'
        elif mutation == 'writer': target['experiment']['world']['writers']['node:0'] = 0
        elif mutation == 'warmup': case['warmup'][0]['world']['nodes']['0']['state'] = 9
        else: target['experiment']['rules'][0]['ops'][0]['value'] = 7
        try:
            checker.verify_case(case)
        except AssertionError:
            rejected.append(mutation)
        else:
            raise AssertionError(f'Intervention audit accepted {mutation}')
    receipt['tamper_rejections'] = rejected
    for family in checker.FAMILIES:
        case = next(c for c in suite['cases'] if c['family'] == family and c['initial']['seed'] == 0)
        source_path = directory/f'{family}-source.json'
        original = source_path.read_bytes()
        branch_path = out/f'{family}-branch'
        run([str(binary), 'branch', str(source_path), str(directory/f'{family}-request.json'), str(branch_path)], out/f'{family}-branch.txt')
        target = checker.verify_bundle(branch_path)
        assert target == case['arms'][2]['chain'][0]['experiment']
        run([str(binary), 'resume', str(branch_path/'checkpoint.json'), '8', str(out/f'{family}-resumed.json')], out/f'{family}-resume.txt')
        assert json.loads((out/f'{family}-resumed.json').read_text()) == json.loads((directory/f'{family}-expected.json').read_text())
        # Rescue is a second intervention on the perturbed checkpoint, not a reload of the source.
        rescue_request = out/f'{family}-rescue-request.json'
        rescue_request.write_text(json.dumps(case['arms'][4]['chain'][1]['request']))
        rescue_path = out/f'{family}-rescue'
        run([str(binary), 'branch', str(branch_path/'checkpoint.json'), str(rescue_request), str(rescue_path)], out/f'{family}-rescue.txt')
        rescued = checker.verify_bundle(rescue_path)
        assert rescued == case['arms'][4]['chain'][1]['experiment']
        run([str(binary), 'resume', str(rescue_path/'checkpoint.json'), '8', str(out/f'{family}-rescue-resumed.json')], out/f'{family}-rescue-resume.txt')
        expected = copy.deepcopy(rescued); expected['world'] = case['arms'][4]['frames'][-1]['world']
        assert json.loads((out/f'{family}-rescue-resumed.json').read_text())['payload'] == expected
        assert source_path.read_bytes() == original
        # Existing branch directories must remain untouched.
        protected = {str(p.relative_to(branch_path)):p.read_bytes() for p in branch_path.rglob('*') if p.is_file()}
        result = subprocess.run([str(binary),'branch',str(source_path),str(directory/f'{family}-request.json'),str(branch_path)], capture_output=True, text=True)
        (out/f'{family}-overwrite-rejected.txt').write_text(result.stdout+result.stderr)
        assert result.returncode != 0
        assert protected == {str(p.relative_to(branch_path)):p.read_bytes() for p in branch_path.rglob('*') if p.is_file()}
    # Failure after an earlier valid staged operation must not publish a branch.
    source_path = directory/'state_arrest-source.json'
    source_bytes = source_path.read_bytes()
    good = suite['cases'][0]['arms'][2]['chain'][0]['request']
    for name in ('stale', 'partial_failure', 'unknown_field'):
        req = copy.deepcopy(good)
        if name == 'stale': req['expected_source'] = '0'*64
        elif name == 'partial_failure': req['operations'].append({'op':'MoveResources','from':0,'to':1,'matter':999,'activation':0})
        else: req['unexpected'] = True
        path = out/f'{name}-request.json'; path.write_text(json.dumps(req))
        dest = out/f'{name}-branch'
        result = subprocess.run([str(binary),'branch',str(source_path),str(path),str(dest)], capture_output=True, text=True)
        (out/f'{name}-branch-rejected.txt').write_text(result.stdout+result.stderr)
        assert result.returncode != 0 and not dest.exists()
        assert source_path.read_bytes() == source_bytes
    receipt['fresh_process_target_and_rescue'] = 'pass'
    receipt['source_immutable_and_failed_requests_unpublished'] = 'pass'
    receipt['branch_overwrite_rejected'] = 'pass'
    (out/'intervention_audit.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt
