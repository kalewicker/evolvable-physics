#!/usr/bin/env python3
"""P01w registration metadata and byte custody only; never import a runtime."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def equal(a,b):return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)
def cells(p):return [(s,pr,i) for s,(pr,i) in enumerate((pr,i) for pr in p['proposal_ids'] for i in p['initial_ids'])]
def expected():
    q=load(ROOT/'docs/p01q_protocol.json');v=load(ROOT/'docs/p01v_protocol.json')
    p={'accounting_contract': {'byte_ledger': 'Track every actual emitted byte including partial syscalls, copies, '
                                            'snapshots, logs, temporary files, metadata, checksums and seal; '
                                            'deletions never refund emitted-byte allowance. Also report final '
                                            'retained bytes separately. Unknown exact totals are null with '
                                            'conservative bounds and integrity failure.',
                             'cpu': 'Controller process CPU plus all live and reaped child/process-group CPU, '
                                    'without double counting. Include sampling/probe helpers launched inside the '
                                    'attempt. Use conservative live growth between observations; inability to '
                                    'bound live CPU fails closed. Record sampled and reaped peak RSS with '
                                    'limitations.',
                             'custody_passes_inside_attempt': 1,
                             'launch_cpu_reserve_seconds': 5,
                             'launch_cpu_stage_wall_multiplier': 2,
                             'launch_wall_reserve_seconds': 5,
                             'no_forecast': 'Original ceilings are unchanged; accounting fixes are not a '
                                            'performance result or permission to increase budgets.',
                             'output_tree_scans_at_empty_initialization': 1,
                             'output_tree_scans_during_closeout': 0,
                             'output_tree_scans_per_budget_poll': 0,
                             'output_tree_scans_per_stage_poll': 0,
                             'stage_retries': 0,
                             'terminal': 'Reserve closure capacity before work. Keep first work error and later '
                                         'closeout errors distinct. Do not repeat full custody during terminal '
                                         'closeout. Post-seal read-only custody cannot erase within-attempt '
                                         'failures.'},
     'additional_semantic_sources': {'scripts/audit_p01q_events.py': 'a5e8607c5a0f0c6d4fad4e298ed3a6525fa43c0145915e3c2577ebdb7e30433f',
                                     'scripts/audit_single_pass.py': '8d9e6a2a45e6aabed4336ae2da6da641deba4ff3b7363a0945e0b4223f58b369',
                                     'scripts/p01q_cell.py': '0d42f146dd577beb59a53391661b5fba197a0195396414e9dfc858a7f2dd040b',
                                     'scripts/pilot_reporting.py': '86d34d9bd0ba2f894d6e32d2c71e0969ca2579792a8afce2dc188fe6de6117eb',
                                     'src/bin/pilot-report.rs': '2d058eeac0bc6f4d243a0050b51d5b3c9dc4312d3223331bf374b00e5b57b2b0',
                                     'src/environment_analysis.rs': 'e1700e7cd4f72cf2e84a905e2ed30f986c4270ba12ceef8600fe945d45a5b26a'},
     'behavioral_missing_reason': 'not_executed',
     'behavioral_outcomes': None,
     'candidate_matching_admitted_now': False,
     'consumed_attempt_repair_admitted': False,
     'controls': {'aggregate_accounting': ['wall_cpu_bytes_launch_reservations_below_equal_above',
                                           'controller_live_reaped_and_helper_cpu_no_double_count',
                                           'conservative_live_cpu_growth_or_fail_closed',
                                           'full_stage_and_terminal_capacity_reserved',
                                           'all_partial_copy_snapshot_log_metadata_and_seal_bytes',
                                           'no_recursive_budget_poll_or_terminal_scan',
                                           'independent_spies_reconcile_counters_and_final_bytes'],
                  'execution_freeze': ['complete_source_dependency_tool_binary_input_membership',
                                       'existing_stdlib_and_project_bytecode_pinned_or_rejected',
                                       'changed_unlisted_missing_or_extra_file_rejected',
                                       'capability_probe_failure_before_output_creation',
                                       'original_seals_and_prior_native_inert_receipts'],
                  'full_pipeline': ['invented128_cells_384_production_contract_records',
                                    'wrong_hash_or_failure_before_cell0',
                                    'each_role_failure_cell0',
                                    'report_failure_cell63',
                                    'audit_failure_cell127',
                                    'all128_statuses_initialized_and_suffix_unstarted'],
                  'independent_receipt_audit': ['missing_duplicate_extra_reordered_cells_and_stages',
                                                'changed_request_trace_report_or_event_identity',
                                                'false_gate_or_duplicate_table_count',
                                                'false_cost_counter_inventory_or_seal',
                                                'censored_failed_and_unstarted_metrics_not_zero',
                                                'auditor_no_primary_extractor_or_campaign_imports_or_execution'],
                  'original_verification': ['actual attached funded birth versus rule availability',
                                            'initial node is not newborn',
                                            'birth-internal Transfer is not additional funding',
                                            'funding recipient and descendant donor must be the same '
                                            'earlier-born node',
                                            'same-kind roles still require distinct node IDs; reused rule bodies '
                                            'allowed',
                                            'visibility requires both eligible proposal types at same retained '
                                            'sample while node live',
                                            'different nodes, cells or tables cannot be pooled into a loop',
                                            'cleanup6 removes exact creation edge and preserves grandchild; '
                                            'cleanup7 also deletes leaf and refunds',
                                            'wrong edge direction, missing creation edge or nonleaf deletion '
                                            'rejected',
                                            'exact refund and activation burn; no free activation restoration',
                                            'ordered branch event IDs, ancestry and resource deltas; unrelated '
                                            'events cannot fill branch phases',
                                            'whole-epoch cap or truncated output keeps verified prefix but full '
                                            'horizon null',
                                            'Rust/Python detector disagreement remains inconclusive',
                                            'input hash/type/slot mismatch fails; no sampler fallback',
                                            'duplicate table digest counts once without dropping rows',
                                            'stage failure, watchdog, launch reservation and seal failure '
                                            'preserve all128 statuses with no retry'],
                  'production_stage_contract': ['worker_run_argv_and_exact_stdout_stderr_mapping',
                                                'reporter_request_and_run_directory_cli',
                                                'canonical_full_newline_json_and_strict_duplicate_key_rejection',
                                                'complete_censored_or_malformed_result_bindings',
                                                'no_stub_inert_receipts_or_plumbing_status',
                                                'optimized_python_replay_rejected'],
                  'replay_and_event_independence': ['original_full_python_replay_and_single_pass_required',
                                                    'independent_event_oracle_no_primary_imports',
                                                    'ordered_branch_cleanup6_vs7_exact_ids_and_intervening_balances',
                                                    'detector_disagreement_inconclusive',
                                                    'no_world_execution_during_invented_tests'],
                  'saved_request_loader': ['all128_exact_order_hashes_and_typed_stream_equality',
                                           'real_loader_end_to_end_not_mocked_away',
                                           'nested_environment_native_not_wrapper',
                                           'no_regeneration_normalization_or_zero_horizon',
                                           'four_initial_table_equality_and_duplicate_table_count_once'],
                  'stage_guards': ['each_stage_wall_output_and_rss_below_equal_above',
                                   'separate_stdout_stderr_and_combined_caps',
                                   'first_rss_sample_before_input',
                                   'nonzero_exit_and_whole_process_group_kill',
                                   'partial_streams_and_reaped_peak_preserved',
                                   'no_retry_or_later_stage_after_failure'],
                  'terminal_integrity': ['first_and_closeout_errors_distinct',
                                         'partial_write_and_terminal_io_failure_retained',
                                         'unknown_totals_null_with_conservative_bound',
                                         'no_false_complete_or_silent_missing_full_horizon',
                                         'attempt_creation_consumes_even_pretransition_failure',
                                         'existing_output_and_resumption_rejected']},
     'date': '2026-10-24',
     'e01_authorized': False,
     'epochs_executed': 0,
     'execution_admitted_only_after_separate_committed_pushed_freeze': True,
     'execution_output': 'artifacts/p01w-001',
     'failure_policy': 'Probe process/RSS/CPU capability before creating the attempt directory. Creation '
                       'consumes the one attempt even before transitions. Initialize all128 rows and384 stage '
                       'slots before launch. Stop on first stage/cell/reservation/integrity failure; preserve '
                       'complete prefix, failed/censored cell, unstarted suffix, partial streams and '
                       'missingness. No retry, resume, extension, replacement, input repair, regeneration, law '
                       'selection or changed threshold. Preserve P01q unchanged.',
     'future_paths': {'campaign': 'scripts/p01w_campaign.py',
                      'cell': 'scripts/p01w_cell.py',
                      'event_audit': 'scripts/audit_p01w_events.py',
                      'execution_check': 'scripts/check_p01w_execution.py',
                      'execution_tests': 'scripts/test_p01w_execution.py',
                      'guard': 'scripts/p01w_guard.py',
                      'receipt_audit': 'scripts/audit_p01w_receipts.py',
                      'tests': 'scripts/test_p01w.py'},
     'implementation_admitted_after_commit_push': True,
     'implementation_started': False,
     'keyed_evaluation_admitted': False,
     'law_denominator': 32,
     'original_protocol': 'docs/p01q_protocol.json',
     'original_protocol_sha256': 'a1088536ee54ec2fb7688cda98c79ce94677db5974abb141d3d672e54c1bc639',
     'performance_assay_admitted': False,
     'plan': 'docs/p01w_campaign_plan.md',
     'prerequisite_receipts': {'artifacts/p01v-002/completion.json': '855397847dc7ed4d87a988439991282abc09ee73784c623a681ac43006e14637',
                               'artifacts/p01v-audit-002/audit.json': 'bfd402e67fcbe6fba57df55deb3e0fc78c44b7fc6a895cfc5b95fe8906ba48d1',
                               'artifacts/p01v-build-001/closure-002.json': '37e3e9fe2a71c727f724d11325259a442adabbfb4df519c002522ac37b63f37e',
                               'docs/p01t_closure.json': '2cbaa139b9c063e2963d7e2c14bcb49144f27ecc06b38426cf50dfc1e8027b55',
                               'docs/p01u_closure.json': 'a7e4b4e491184f2e0a0ac6b2b5810512ac4039db8bd41d89c672ff81396652a7',
                               'docs/p01v_closure.json': '730700571097b87083aa3e3a8e5a2f1d6c13f1c7fb437e6f7274879a2ed91384'},
     'prior_knowledge': 'P01p found a conditional cleanup7 branch in law6011; P01q failed before any native '
                        'stage. P01t/u/v establish request transport, validator acceptance and inert '
                        'orchestration only. All32 laws remain included. Finite closed activation limits '
                        'constructive turnover; no reproduction or causal necessity claim.',
     'production_binaries': {'target/release/pilot-report': 'c7b0b4a97104a91b77cab81b2b23e3b69d6307c5be94ecfc346a66bb090ff9c9',
                             'target/release/pilot-worker': 'c72bef814a04aa4582193868c23b9a5701de6a24998c21c7fa9bba252473b8ff'},
     'production_contracts': {'inert_receipts_accepted': False,
                              'loader': 'Verify existing P01t request bytes and both original saved streams; '
                                        'initial is the entire environment containing native, never the saved '
                                        'wrapper. Never call P01q saved_initial, verify or main.',
                              'manifest_schema': 'p01w-saved-panel-dynamics-manifest-v1',
                              'native': {'argv': ['PINNED_WORKER', 'run', 'UNCHANGED_REQUEST_FILE'],
                                         'result_schema': 'p01-worker-result-v1',
                                         'stderr': 'worker.json',
                                         'stderr_cap_bytes': 262144,
                                         'stdout': 'trace.jsonl',
                                         'stdout_cap_bytes': 4194304},
                              'python_audit': {'argv': ['PINNED_PYTHON',
                                                        '-I',
                                                        '-B',
                                                        'PINNED_P01W_CELL',
                                                        'UNCHANGED_REQUEST_FILE',
                                                        'CELL_RUN_DIRECTORY'],
                                               'assertions_required': True,
                                               'stderr_cap_bytes': 65536,
                                               'stdout_cap_bytes': 983040,
                                               'stdout_schema': 'p01w-cell-audit-v1'},
                              'report_cap_justification': 'Rust reporter and Python replay may compute the next '
                                                          'epoch on censored inputs; these calls are world '
                                                          'execution and are forbidden before execution '
                                                          'admission.',
                              'rust_report': {'argv': ['PINNED_REPORTER',
                                                       'UNCHANGED_REQUEST_FILE',
                                                       'CELL_RUN_DIRECTORY'],
                                              'inputs': ['trace.jsonl', 'worker.json'],
                                              'stderr_cap_bytes': 65536,
                                              'stdout_cap_bytes': 4128768,
                                              'stdout_schema': 'p01-detector-report-v1'}},
     'registration_only_now': True,
     'requirements_before_execution': ['Commit/push P01w registration and its source/input freeze before '
                                       'implementing only the listed new paths.',
                                       'Freeze authored expected controls before tests. Test only invented '
                                       'descriptors and inert/mock process contracts, normal and optimized '
                                       'rejection paths. No retained request parsing, candidate enumeration, '
                                       'transition interpreter, worker/reporter/replay execution or keyed calls '
                                       'during implementation tests.',
                                       'Retain all implementation/test attempts with source identities. '
                                       'Implementation corrections may repeat only invented controls into fresh '
                                       'directories before the productive attempt; they never permit repeating a '
                                       'consumed dynamics attempt.',
                                       'Require all registered production contracts, original mechanism '
                                       'controls, guard/accounting/missingness tests and independent '
                                       'receipt-audit mutations to pass. Preserve original full independent '
                                       'Python replay plus single-pass verification; detector disagreement stays '
                                       'inconclusive.',
                                       'Separately freeze full source, all transitive Python dependencies '
                                       'including existing bytecode, tools, dynamic libraries, unchanged '
                                       'production binaries, all fixed input bytes and complete memberships. '
                                       'Verify tests used that closure. Commit/push execution freeze/admission '
                                       'and exact command/output before any candidate or transition computation.',
                                       'Read-only execution admission verifies all128 request hashes, both '
                                       'streams per cell, original seals and prior native/inert receipts. '
                                       'Capability probes precede output creation; custody/snapshots/copies '
                                       'after creation count inside campaign limits.',
                                       'After the one attempt, independently audit preserved '
                                       'receipts/inventories and arithmetic without world replay, generator '
                                       'calls, campaign imports or subprocesses; retain an '
                                       'inconclusive/integrity-failed outcome on disagreement.'],
     'schema': 'p01w-saved-panel-dynamics-registration-v1',
     'scientific_status': 'untested',
     'scope': 'Register one new bounded unfiltered dynamics attempt over all128 unchanged P01t requests; '
              'preserve consumed P01q.',
     'stage_denominator': 384,
     'stage_order': ['native', 'rust_report', 'python_audit'],
     'trajectory_denominator': 128,
     'world_execution_admitted_now': False}
    p['receipt_audit_limits']={'wall_seconds':180,'output_bytes':134217728,'terminal_reserve_seconds':5,'terminal_reserve_bytes':1048576,'world_replay_admitted':False}
    p.update({k:q[k] for k in ['proposal_ids', 'initial_ids', 'epochs', 'worker_request', 'campaign', 'per_process', 'closed_environment_limits', 'engineering_gate', 'mechanism_gate', 'observables', 'decision', 'reporting', 'verification_controls', 'control_policy']})
    p.update({k:v[k] for k in ['source_bundles', 'request_bundle', 'request_bundle_completion_sha256', 'saved_requests', 'request_contract', 'semantic_sources']})
    return p

def validate(p):
    e=expected();require(set(p)==set(e),'protocol field membership')
    for k,v in e.items():require(equal(p[k],v),'protocol: '+k)
    return dict(schema='p01w-registration-review-v1',status='pass',fixed_laws=32,fixed_cells=128,
        requests_pinned=128,planned_production_stages=384,control_families=len(p['controls']),
        named_control_cases=sum(map(len,p['controls'].values())),retained_payloads_parsed=0,
        native_worker_invocations=0,reporter_invocations=0,world_transitions=0,keyed_evaluations=0,
        implementation_started=False,world_execution_admitted_now=False,scientific_status='untested')

def bundle_check(name,completion_hash):
    b=ROOT/name;inv=load(b/'checksums.json');completion=load(b/'completion.json')
    require(sha(b/'completion.json')==completion_hash,'completion: '+name)
    require({str(x.relative_to(b)) for x in b.rglob('*') if x.is_file()}==set(inv)|{'checksums.json','completion.json'},'bundle membership: '+name)
    for n,e in inv.items():require(sha(b/n)==e['sha256'] and (b/n).stat().st_size==e['size'],'bundle bytes: '+n)
    require(sha(b/'checksums.json')==completion['checksums_sha256'],'inventory link: '+name)
    require(sum(x.stat().st_size for x in b.rglob('*') if x.is_file())==completion['output_bytes'],'bundle bytes total: '+name)
    return load(b/'manifest.json')

def review():
    f=load(ROOT/'docs/p01w_registration_freeze.json')
    for section in ('files','inputs','prior_public_receipts'):
        for n,h in f[section].items():require(sha(ROOT/n)==h,section+': '+n)
    p=load(ROOT/'docs/p01w_protocol.json');result=validate(p)
    expected_inputs=set(load(ROOT/'docs/p01v_registration_freeze.json')['inputs'])|set(load(ROOT/'docs/p01v_closure.json')['receipts'])|{'artifacts/p01v-build-001/closure-002.json'}
    require(set(f['inputs'])==expected_inputs,'complete prior custody input membership')
    for section in ('semantic_sources','additional_semantic_sources','production_binaries','prerequisite_receipts'):
        for n,h in p[section].items():require(sha(ROOT/n)==h,section+': '+n)
    old=load(ROOT/'docs/p01q_execution_freeze.json')['binaries']
    require(p['production_binaries']=={v['path']:v['sha256'] for v in old.values()},'original production binary identities')
    require(sha(ROOT/p['original_protocol'])==p['original_protocol_sha256'],'original protocol')
    for letter in ('t','u','v'):require(load(ROOT/f'docs/p01{letter}_closure.json')['independent_audit_pass'] is True,'prior gate: '+letter)
    transport=bundle_check(p['request_bundle'],p['request_bundle_completion_sha256'])
    vp=load(ROOT/'docs/p01v_protocol.json')
    native=bundle_check(vp['prior_validation_bundle'],vp['prior_validation_completion_sha256'])
    inert=bundle_check('artifacts/p01v-002',p['prerequisite_receipts']['artifacts/p01v-002/completion.json'])
    for label,m in [('transport',transport),('native',native),('inert',inert)]:
        require(m['status']=='pass' and len(m['rows'])==128,'prior manifest: '+label)
    for (s,pr,i),t,n,v in zip(cells(p),transport['rows'],native['rows'],inert['rows']):
        name=f"{p['request_bundle']}/requests/{s:03}.json";h=p['saved_requests'][name]
        require(h==f['inputs'][name]==sha(ROOT/name),'request identity')
        for row in (t,n,v):require((row['slot'],row['proposal'],row['initial'])==(s,pr,i),'fixed prior row')
        require(t['status']=='complete' and t['request_sha256']==h,'transport row')
        require(n['status']=='complete' and n['native_accepted'] is True and n['input_sha256']==h,'native row')
        require(v['status']=='plumbing_complete' and v['input_sha256']==h and len(v['stages'])==3,'inert row')
        for lang in ('rust_generation','python_generation'):
            require(f'artifacts/p01o-001/runs/{s}/{lang}/stdout.bin' in f['inputs'],'saved stream omitted')
    counts={}
    for name,h in p['source_bundles'].items():
        b=ROOT/name;inv=load(b/'checksums.json');seal=load(b/'seal.json')
        require(sha(b/'seal.json')==h,'original seal')
        require({str(x.relative_to(b)) for x in b.rglob('*') if x.is_file()}==set(inv)|{'checksums.json','seal.json'},'original membership')
        for n,digest in inv.items():require(sha(b/n)==digest,'original bytes: '+n)
        require(sha(b/'manifest.json')==seal['manifest_sha256'] and sha(b/'checksums.json')==seal['checksums_sha256'],'original seal links')
        counts[name]=len(inv)
    m=load(ROOT/'artifacts/p01q-001/manifest.json')
    require(m['execution_status']=='failed' and m['error']=="KeyError('native')" and m['provenance_error']=="AssertionError('aggregate CPU reserve')",'consumed failure')
    require(len(m['rows'])==128,'consumed denominator')
    for plan,row in zip(cells(p),m['rows']):require((row['slot'],row['proposal'],row['initial_state'])==plan and not row['stages'],'consumed cells/no stages')
    require(m['rows'][0]['status']=='failed' and all(x['status']=='unstarted' for x in m['rows'][1:]),'consumed statuses')
    for n in p['future_paths'].values():require(not (ROOT/n).exists(),'implementation before registration: '+n)
    require(not (ROOT/p['execution_output']).exists(),'attempt before execution admission')
    result.update(frozen_files=len(f['files']),custody_inputs=len(f['inputs']),prior_public_receipts=len(f['prior_public_receipts']),
        original_inventory_counts=counts,freeze_sha256=sha(ROOT/'docs/p01w_registration_freeze.json'))
    return result
if __name__=='__main__':
    result=review();out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    (out/'static_review.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
