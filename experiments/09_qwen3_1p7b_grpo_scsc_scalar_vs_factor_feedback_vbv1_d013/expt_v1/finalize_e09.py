"""TLDR: Publish fail-closed accounting for the failed probability gate, never fabricate training."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO.parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publication-commit', help='Set only after this full results commit is on origin/main')
    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    run = read(ROOT / 'run_identity.json')
    gate = read(HERE / 'results/technical_gate.json')
    assert gate['status'] == 'FAILED_TECHNICAL_GATE'
    assert gate['probabilities']['outside_recomputed_support'] == 4
    assert read(ROOT / 'child_receipts.json')['processes'] == []
    resource = read(ROOT / 'receipts/resource_audit.json')
    cleanup = read(ROOT / 'receipts/cleanup_audit.json')
    assert not cleanup['after']
    assert not any(r['active'] for r in resource['leases'])
    judge_path = ROOT / 'receipts/judge_e09/controls_check.json'
    scorer_path = ROOT / 'receipts/scorer_adapter_e09.json'
    judge, scorer = read(judge_path), read(scorer_path)
    assert judge['verdict'] == 'PASS' and len(scorer['files']) == 14
    assert all(r['expectations_met'] for r in scorer['files'])
    assert sum(r['status_counts']['measured'] for r in judge['configs'].values()) == 50
    assert abs(sum(r['charges_usd'] for r in judge['configs'].values()) - 3.0558) < 1e-8
    write(HERE / 'results/completed_controls.json', {
        'provenance': 'Read existing completed native receipts; no rerun or new calls',
        'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (judge_path, scorer_path)},
        'judge': {key: judge[key] for key in ('configs', 'verdict', 'written_utc')},
        'scorer': {'declared': 14, 'expectations_met': 14,
                   'files': [{key: row[key] for key in ('task_id', 'kind', 'sha256', 'expected', 'got', 'expectations_met')}
                             for row in scorer['files']]},
        'warning': '50/50 is rating completion, not expected-label accuracy; two half-deletion scores fall outside the expected interval but the frozen category thresholds pass.'})
    resource['filesystem_headroom'] = []
    for path in (ROOT, Path('/tmp')):
        fs = os.statvfs(path)
        resource['filesystem_headroom'].append({'path': str(path), 'available_bytes': fs.f_bavail * fs.f_frsize,
            'total_bytes': fs.f_blocks * fs.f_frsize, 'free_fraction': fs.f_bavail / fs.f_blocks,
            'minimum_fraction': .05, 'passed': fs.f_bavail / fs.f_blocks >= .05})
    resource.update(finalized_utc=now, cleanup=cleanup, cap_exhausted=False,
                    uncertain_device_order_incident='results/device_order_incident.json; initial failed context unverified, no generation, reserved interval charged',
                    accounting='Reserved lease durations, not utilization; whole shared uv cache conservatively included because attempt-1 increment is unknown.')
    write(HERE / 'results/resource_closeout.json', resource)
    attempts = []
    for directory in sorted((ROOT / 'technical_control').iterdir()):
        if not directory.is_dir():
            continue
        entry = {'name': directory.name}
        for name in ('identity.json', 'prospective_budget.json', 'exit.json', 'batch_0_audit.json',
                     'probability_diagnostic.json'):
            path = directory / name
            if path.is_file():
                entry[name] = read(path)
        entry['artifact_sha256'] = {p.name: sha(p) for p in directory.iterdir()
                                   if p.is_file() and p.name in ('resolved_config.json', 'lease.json',
                                                                'release.json', 'failure.json')}
        entry['scientific_responses'] = 0
        entry['optimizer_updates'] = 0
        entry['technical_responses'] = 64 if directory.name == 'profile_scope_fix' else 0
        attempts.append(entry)
    write(HERE / 'results/technical_attempts.json', {'run_id': run['run_id'], 'attempts': attempts,
        'separate_inherited_forward_preflight': {'responses': 1, 'generated_tokens': 18, 'optimizer_updates': 0},
        'duplicate_healthy_children_launched': False, 'completed_controls_rerun': False})
    analysis = read(HERE / 'results/aligned/analysis.json')
    # Validate every published cell, not just aggregate counters or a sample.
    aligned = HERE / 'results/aligned'
    rows = [json.loads(line) for line in (aligned / 'aligned_task_factors.jsonl').read_text().splitlines()]
    split = REPO / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split'
    policies = ['baseline'] + [f'{a}_{s}' for s in (20261008, 20261009) for a in 'ABC']
    expected = {(s, task, policy) for s in ('validation', 'test')
                for task in (split / f'vbv1_{s}_task_ids.txt').read_text().splitlines() for policy in policies}
    assert len(rows) == len(expected) == 2499
    assert {(r['split'], r['task_id'], r['policy']) for r in rows} == expected
    for row in rows:
        assert row['status'] == 'not_run' and row['error'] == 'failed_probability_support_gate'
        assert all(row[k] is None for k in ('IC_tests', 'IC_proofs', 'FSC', 'S', 'H', 'kernel_binary',
                                          'compiles', 'extracted', 'truncated', 'cost_usd', 'checkpoint_sha256'))
    with (aligned / 'aligned_task_factors.csv').open() as source:
        reader = csv.DictReader(source)
        assert reader.fieldnames.index('H') == reader.fieldnames.index('S') + 1
        csv_rows = list(reader)
    assert len(csv_rows) == len(rows)
    assert all({k: '' if v is None else str(v) for k, v in row.items()} == cell
               for row, cell in zip(rows, csv_rows))
    before = [json.loads(line) for line in (aligned / 'before_after.jsonl').read_text().splitlines()]
    assert len(before) == 2142 and {(r['split'], r['task_id'], r['policy']) for r in before} == {key for key in expected if key[2] != 'baseline'}
    assert all(r['regression'] is None and r['H_transition'] is None for r in before)
    calibration = [json.loads(line) for line in (aligned / 'calibration_cells.jsonl').read_text().splitlines()]
    assert len(calibration) == 512 and all(r['status'] == 'not_run' and r['S'] is None and r['H'] is None for r in calibration)
    counts = {'calibration_rollouts': {'declared': 256, 'completed': 0, 'missing': 256},
              'calibration_responses': {'declared': 512, 'measured': 0, 'missing': 512},
              'training_trajectories': {'declared': 6, 'admitted': 0, 'completed': 0, 'missing': 6},
              'main_training_responses': {'maximum_plan': 12288, 'admitted_denominator': None, 'measured': 0},
              'validation': analysis['counts']['validation'], 'test': analysis['counts']['test'],
              'before_after_rows': {'declared': 2142, 'paired_measured': 0, 'missing': 2142}}
    manifest = {'schema_version': 1, 'run_id': run['run_id'], 'written_utc': now,
        'status': 'NOT_ADMITTED_FAILED_TECHNICAL_GATE', 'frozen_for_main_training': False,
        'reason': 'failed_probability_support_gate', 'run_identity': run,
        'actual_owner': {'client': 'native Codex personal subscription', 'model': 'gpt-6-astra',
                        'effort': 'ultra', 'coordinator_attempt': 2, 'approval_policy': 'never',
                        'sandbox': 'danger-full-access', 'evidence': 'results/recovery_attempt_2.json'},
        'scientific_contract_sha256': sha(HERE.parent / 'PROTOCOL.md'),
        'arms': {'A': 'Exact gated conjunction of IC_tests=IC_proofs=FSC=1',
                 'B': 'Same gated factors, geometric-mean reward S',
                 'C': 'Same S as B; disclose named factor vector in addition to identical scalar/compiler feedback'},
        'feedback': 'All arms receive S, H and capped compiler output; only C additionally receives named factors',
        'reward_turns': [0, 'chosen terminal reward'], 'assistant_turns': 2,
        'sampling': {'temperature': .6, 'top_p': .95, 'top_k': 20, 'max_new_tokens_per_turn': 8192},
        'seeds': [20261008, 20261009], 'train_tasks': 539, 'prompt_groups_per_update': 4,
        'trajectories_per_prompt': 8, 'permitted_horizons': [32, 16, 8], 'chosen_horizon': None,
        'optimizer_configuration_frozen_for_science': False,
        'candidate_control_configuration_sha256': sha(ROOT / 'technical_control/profile_scope_fix/resolved_config.json'),
        'candidate_configuration_warning': 'Private exact configuration preserved; 64-token disposable fixture is not the scientific 8192-token response cap. Optimizer, full-context and save/reload controls did not pass.',
        'trajectory_manifest': read(HERE / 'results/aligned/training_trajectories.json'),
        'endpoint_hashes': {f'{a}_{s}': None for s in (20261008, 20261009) for a in 'ABC'},
        'held_out_source_or_outcomes_opened': False, 'counts': counts,
        'matrix_sha256': {p.name: sha(p) for p in (HERE / 'results/aligned').iterdir() if p.is_file()},
        'identity_receipt_sha256': sha(HERE / 'results/resolved_identity.json'),
        'judge': {'route': 'unchanged vb103_judge Valkyrie CLI, recorded Vals configuration',
                  'member_settings': ['H2_sol_high', 'H2_opus55_max'],
                  'ratings_per_eligible_scientific_file': 6, 'missing_required_rating_blocks_batch': True,
                  'scientific_ratings': 0, 'fixed_control_ratings_measured': 50,
                  'fixed_category_gates': 'PASS both suites, not 50/50 expected-label accuracy',
                  'observed_control_cost_usd': 3.0558, 'expected_train_eligibility_fraction': None},
        'scientific_effects': None, 'regressions': None, 'no_learning_claim': True}
    write(HERE / 'execution_manifest.json', manifest)
    dispatch = read(HERE / 'dispatch_manifest.json')
    dispatch.update(status='FAILED_TECHNICAL_GATE', terminal_reason=manifest['reason'],
                    execution_manifest='execution_manifest.json', scientific_completion=False)
    dispatch['model_under_training'] = 'Qwen3 Base 1.7B step-658; all ten initialization manifest hashes verified in results/resolved_identity.json'
    write(HERE / 'dispatch_manifest.json', dispatch)
    estimate = read(HERE / 'judge_call_estimate.json')
    estimate['post_control_observation'] = {'written_utc': now, 'measured_ratings': 50,
        'observed_cost_usd': 3.0558, 'control_category_gates': 'PASS both frozen suites',
        'expected_label_accuracy': None, 'new_scientific_ratings': 0,
        'expected_train_eligibility_fraction': None,
        'reason_no_forecast': 'calibration not admitted',
        'billing_limit_or_credits_changed': False,
        'payer_evidence_limit': 'Recorded approved Vals-managed route; native constituent receipts do not independently expose payer/organization fields. Historical pre-call estimate below is preserved.'}
    write(HERE / 'judge_call_estimate.json', estimate)
    ack = read(ROOT / 'supervisor_mailbox_ack.json')
    assert ack['sha256'] == sha(ROOT / 'supervisor_mailbox.md'), 'Read and explicitly acknowledge changed parent mailbox before finalizing'
    ack.update(written_utc=now)
    write(ROOT / 'supervisor_mailbox_ack.json', ack)
    progress = {'run_id': run['run_id'], 'attempt': 2, 'written_utc': now,
        'phase': 'finalizing_failed_technical_gate', 'status': 'publishing',
        'completed': 0, 'declared': 6, 'calibration_responses': 0,
        'validation_measured': 0, 'test_measured': 0, 'counts': counts,
        'reason': manifest['reason'], 'gate_receipt': str(HERE / 'results/technical_gate.json'),
        'native_adapter_tests': {'passed': 42}, 'repository_tests': {'passed': 158, 'skipped': 4},
        'active_children': 0, 'active_gpu_leases': 0,
        'original_deadline_exhausted': False, 'scientific_completion': False}
    write(ROOT / 'progress.json', progress)
    if args.publication_commit:
        commit = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', args.publication_commit + '^{commit}'], text=True).strip()
        subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', commit, 'origin/main'], check=True)
        terminal = {**progress, 'written_utc': now, 'phase': 'terminal_failed_technical_gate',
            'status': 'FAILED_TECHNICAL_GATE', 'publication_commit': commit,
            'publication_commit_contains': 'complete failed-gate results, reproducible evidence and full missing-cell matrices',
            'publication_remote': 'https://github.com/brando90/rl-4-code-verification',
            'reason_detail': '4/4077 generated actions outside recomputed old-policy support; 367/4073 finite actions exceed predeclared .05 absolute log-probability tolerance. No optimizer update admitted.',
            'not_completed': gate['not_passed'], 'original_deadline_utc': run['deadline_utc'],
            'controls': manifest['judge'], 'reserved_device_hours': resource['total_reserved_device_hours'],
            'terminal_gate_not_scientific_completion': True}
        write(HERE / 'results/terminal_receipt.json', terminal)
        write(ROOT / 'terminal_receipt.json', terminal)
        write(ROOT / 'progress.json', terminal)
    print(json.dumps({'phase': 'terminal_failed_technical_gate' if args.publication_commit else 'finalizing_failed_technical_gate',
                      'counts': counts, 'reserved_device_hours': resource['total_reserved_device_hours']}))


if __name__ == '__main__':
    main()
