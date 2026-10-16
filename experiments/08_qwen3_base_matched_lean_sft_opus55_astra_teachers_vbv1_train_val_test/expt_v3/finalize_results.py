"""Check every frozen cell and training receipt before preparing final publication and mail."""
from __future__ import annotations
import csv
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo
from assess_forecast import assess
from recovery_watch import read, write
from remote_generation import validate_raw, digest, SHARED
from failure_taxonomy import KINDS

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')


def validate_original_errors(errors, taxonomy, primary, raw):
    """Reproduce the frozen sample and compare its original native evidence."""
    failed = [r for r in taxonomy if r['category'] == 'compile_error']
    selected = sorted(failed, key=lambda r: hashlib.sha256(
        f"rl4cv-e08-v3-taxonomy-sample:{r['task_id']}#{r['sample_idx']}".encode()).hexdigest())[:24]
    receipts = errors['receipts']
    key = lambda r: (r['task_id'], int(r['sample_idx']))
    assert [key(r) for r in receipts] == [key(r) for r in selected], 'Original error sample selection differs'
    assert errors['compile_error_population'] == len(failed)
    assert errors['sampled_cells'] == len(receipts) == min(24, len(failed))
    assert errors['kind_counts'] == dict(Counter(r['kind'] for r in receipts))
    native_files = {}; lines = timeouts = 0
    for row, receipt in zip(selected, receipts):
        path = Path(receipt['path']); native = path.with_suffix('.json')
        assert read(native) == receipt, 'Retained native error receipt differs'
        assert path.read_text() == raw[key(receipt)]['lean'], 'Original error source differs from generation'
        assert digest(path) == receipt['original_sha256'] == row['lean_sha256'] == primary[
            receipt['task_id'], str(receipt['sample_idx'])]['lean_sha256']
        compiled = receipt['compile']
        message = compiled['errors'][0]['msg'] if compiled['errors'] else ''
        assert receipt['first_error'] == message, 'First native error message differs'
        kind = ('timeout' if compiled['timeout'] else 'recheck_success' if compiled['success'] else
                next((name for name, regex in KINDS if re.search(regex, message)),
                     'other' if message else 'no_error_line'))
        assert receipt['kind'] == kind, 'Native error classification differs'
        lines += len(compiled['errors']); timeouts += int(compiled['timeout'])
        native_files.update({str(path): digest(path), str(native): digest(native)})
    return {'error_population': len(failed), 'sampled': len(receipts),
            'selection_and_original_hashes_match': True, 'recorded_native_errors_match': True,
            'recorded_error_lines': lines, 'native_timeouts': timeouts}, native_files


def validate(checksum_runner=None):
    manifest = read(HERE / 'results/ladder_manifest_v3.json')
    summary = read(HERE / 'results/validation_summary_v3.json', {})
    assert summary.get('known_cells') == summary.get('declared_cells') == 17280, 'Validation remains incomplete'
    expected_labels = {s['label'] for s in manifest['systems']}
    assert len(expected_labels) == 16 and set(summary['systems']) == expected_labels
    validate_metrics(summary, manifest)
    pairs = summary['paired_E_minus_R']
    assert set(pairs) == {f'{s}_{f}' for s in ('1p7b', '4b', '8b', '14b') for f in ('f0p5', 'f1p0')}
    for value in pairs.values():
        validate_bootstrap(value)
    expected = {(c['system'], c['task_id'], c['sample_idx']) for c in manifest['cells']}
    seen = set(); namespace = {}; files = {}; error_audits = {}
    for system in manifest['systems']:
        label = system['label']; result = summary['systems'][label]
        raw = WORK / f'ladder/validation/raw/gen_{label}_g8.jsonl'
        model_paths = [system['hf_path'], str(SHARED / 'sft_v3' / Path(system['hf_path']).relative_to(WORK))]
        validate_raw(raw, label, manifest['task_ids'], read(HERE / 'results/generation_prompt_hashes_v3.json'), model_paths)
        scored = WORK / f'ladder/validation/scored/scored_{label}_g8.jsonl'
        assert digest(scored) == result['scored_sha256']
        scored_rows = [json.loads(line) for line in scored.read_text().splitlines() if line.strip()]
        scored_keys = [(label, r['task_id'], r['sample_idx']) for r in scored_rows]
        assert len(scored_keys) == len(set(scored_keys)) == 1080
        assert set(scored_keys) == {k for k in expected if k[0] == label}
        assert all(r.get('status') == 'scored' for r in scored_rows)
        files[str(raw)] = digest(raw); files[str(scored)] = digest(scored)
        path = HERE / result['cells_csv']
        rows = list(csv.DictReader(path.open()))
        keys = [(label, r['task_id'], int(r['sample_idx'])) for r in rows]
        assert len(keys) == len(set(keys)) == 1080 and all(r['known'] == 'True' for r in rows)
        seen.update(keys)
        tasks_path = HERE / result['per_task_csv']
        task_rows = list(csv.DictReader(tasks_path.open()))
        assert len(task_rows) == 135 and {r['task_id'] for r in task_rows} == set(manifest['task_ids'])
        assert all(int(r['samples_known']) == 8 for r in task_rows)
        taxonomy = HERE / f'results/ladder/{label}_taxonomy.csv'
        tr = list(csv.DictReader(taxonomy.open()))
        assert {(label, r['task_id'], int(r['sample_idx'])) for r in tr} == set(keys) and len(tr) == 1080
        assert dict(Counter(r['category'] for r in tr)) == result['failure_taxonomy']
        diag_path = HERE / f'results/namespace_diagnostic/{label}.json'
        diag = read(diag_path)
        cells = HERE / f'results/namespace_diagnostic/{label}_cells.csv'
        dr = list(csv.DictReader(cells.open()))
        assert len(dr) == 1080 and {(label, r['task_id'], int(r['sample_idx'])) for r in dr} == set(keys)
        primary = {(r['task_id'], r['sample_idx']): r for r in rows}
        assert all(r['original_sha256'] == primary[r['task_id'], r['sample_idx']]['lean_sha256'] for r in dr)
        validate_namespace(diag, dr, primary)
        if not diag['unknown_cells']:
            deltas = [sum(float(r['diagnostic_kernel_binary']) - float(r['original_kernel_binary'])
                          for r in dr if r['task_id'] == task) / 8 for task in manifest['task_ids']]
            validate_bootstrap(diag['paired_task_bootstrap_delta'], deltas)
        errors = diag['original_first_error_sample']
        assert errors['compile_error_population'] == result['failure_taxonomy'].get('compile_error', 0)
        raw_rows = [json.loads(line) for line in raw.read_text().splitlines() if line.strip()]
        audit, native_files = validate_original_errors(errors, tr, primary,
            {(r['task_id'], int(r['sample_idx'])): r for r in raw_rows})
        error_audits[label] = {**audit, 'diagnostic_sha256': digest(diag_path)}
        files.update(native_files)
        namespace[label] = {k: v for k, v in diag.items() if k != 'changed_receipts'}
        for p in (path, tasks_path, taxonomy, cells, diag_path):
            files[str(p.relative_to(HERE))] = hashlib.sha256(p.read_bytes()).hexdigest()
    assert seen == expected and len(seen) == 17280
    training = {}
    for condition in ('E', 'R'):
        schedule = read(HERE / f'results/sft_schedule_v3_{condition}.json')
        for short in ('1p7b', '4b', '8b', '14b'):
            label = f'v3_{condition}_{short}'
            receipt = read(HERE / f'results/train_logs/{label}_summary.json')
            steps_path = HERE / f'results/train_logs/{label}_steps.csv'
            validate_training(receipt, list(csv.DictReader(steps_path.open())), schedule)
            schedule_path = HERE / f'results/sft_schedule_v3_{condition}.json'
            assert receipt['schedule_sha256'] == digest(schedule_path)
            for p in (steps_path, HERE / f'results/train_logs/{label}_summary.json'):
                files[str(p.relative_to(HERE))] = digest(p)
            for fraction in ('f0p5', 'f1p0'):
                step = schedule['checkpoints'][fraction]['step']
                export = WORK / f'ckpt/{label}/hf/step_{step}'
                command = ['sha256sum', '--check', '--quiet', 'SHA256SUMS']
                if checksum_runner is None:
                    subprocess.run(command, cwd=export, check=True, timeout=3600)
                else:
                    checksum_runner(command, export)
                checksum = HERE / f'results/train_logs/{label}_{fraction}_SHA256SUMS'
                checksum.write_bytes((export / 'SHA256SUMS').read_bytes())
                files[str(checksum.relative_to(HERE))] = hashlib.sha256(checksum.read_bytes()).hexdigest()
            training[label] = receipt
    forecast = assess(summary)
    assert all(forecast[k]['outcome']['status'] == 'COMPLETE' for k in ('primary', 'sensitivity'))
    write(HERE / 'results/forecast_assessment_v3.json', forecast)
    write(HERE / 'results/namespace_summary_v3.json', namespace)
    error_path = HERE / 'results/error_samples_recovery02.json'
    error_audit = {'status': 'PASS', 'systems': error_audits, 'known_primary_cells': len(seen),
                   'verified_error_receipts': sum(x['sampled'] for x in error_audits.values()),
                   'recorded_error_lines': sum(x['recorded_error_lines'] for x in error_audits.values()),
                   'native_timeouts': sum(x['native_timeouts'] for x in error_audits.values()),
                   'recorded_native_errors_match': True, 'no_new_compilations': True,
                   'model_calls': 0, 'test_split_opened': False,
                   'evidence_limit': 'Compiler helper retains parsed error header lines (240-character cap), '
                                     'not complete stdout/stderr transcripts. All recorded messages match.'}
    write(error_path, error_audit); files[str(error_path.relative_to(HERE))] = digest(error_path)
    receipt = {'status': 'VALIDATED', 'known_cells': len(seen), 'declared_cells': 17280,
               'systems': 16, 'training_verified': True, 'namespace_complete': True,
               'namespace_diagnostic_executed': True,
               'namespace_unknown_cells': sum(s['unknown_cells'] for s in namespace.values()),
               'namespace_paired_delta_available': all(s['unknown_cells'] == 0 for s in namespace.values()),
               'forecast_assessed': True, 'training': training, 'artifact_sha256': files,
               'original_error_receipts_verified': error_audit['verified_error_receipts'],
               'original_error_audit_sha256': digest(error_path),
               'paid_model_spend_usd': 0, 'test_split_opened': False,
               'validated_local': datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%m-%d-%Y %H:%M %Z')}
    write(HERE / 'results/completion_validation_v3.json', receipt)
    return receipt, summary, forecast


def validate_bootstrap(value, values=None):
    assert value['draws'] == 10000 and value['seed'] == 0
    assert value['unit'] == 'task with eight attempts together'
    assert len(value['ci95']) == 2 and -1 <= value['ci95'][0] <= value['ci95'][1] <= 1
    assert -1 <= value['mean'] <= 1
    if values is not None:
        import numpy as np
        values = np.asarray(values, dtype=float)
        draws = np.random.default_rng(0).integers(0, len(values), (10000, len(values)))
        expected = np.quantile(values[draws].mean(axis=1), [.025, .975])
        assert np.allclose(value['ci95'], expected, atol=1e-12, rtol=0), 'Bootstrap interval differs from cell evidence'
        assert abs(value['mean'] - values.mean()) < 1e-12, 'Bootstrap mean differs from cell evidence'


def validate_training(receipt, rows, schedule):
    assert receipt['status'] == 'PASS' and receipt['token_counts_match']
    assert receipt['steps'] == len(rows) == len(schedule['steps'])
    for row, step in zip(rows, schedule['steps']):
        for key in ('step', 'loss_tokens', 'cumulative_loss_tokens'):
            assert int(row[key]) == step[key], f'Training {key} mismatch'
        assert int(row['processed_tokens']) == step['prompt_tokens'] + step['loss_tokens']
    assert receipt['loss_tokens'] == sum(int(r['loss_tokens']) for r in rows)
    assert receipt['processed_real_tokens'] == sum(int(r['processed_tokens']) for r in rows)


def validate_metrics(summary, manifest):
    """Recompute reported gates and intervals from the committed cell tables."""
    from analyze_validation import base, decision
    vectors = {}
    for label, result in summary['systems'].items():
        rows = list(csv.DictReader((HERE / result['cells_csv']).open()))
        native, notes = base.cells_for(result['system'], manifest['task_ids'], 'validation')
        assert not notes['duplicates_rejected'] and not notes['extras_rejected'] and not notes['n_missing']
        grouped = {task: [] for task in manifest['task_ids']}
        for row in rows:
            assert row['known'] == 'True' and float(row['kernel_binary']) in (0, 1)
            source = native[row['task_id'], int(row['sample_idx'])]
            assert source['known'] and float(row['kernel_binary']) == source['kernel_binary']
            assert row['lean_sha256'] == (source['lean_sha256'] or '')
            assert row['extracted'] == str(source['extracted']) and row['capped'] == str(source['capped'])
            grouped[row['task_id']].append(row)
        assert all(len(v) == 8 and {int(r['sample_idx']) for r in v} == set(range(8)) for v in grouped.values())
        tasks = list(csv.DictReader((HERE / result['per_task_csv']).open()))
        assert [r['task_id'] for r in tasks] == manifest['task_ids']
        counts = [sum(float(r['kernel_binary']) for r in grouped[t]) for t in manifest['task_ids']]
        assert all(int(r['k_kernel_binary']) == count and int(r['samples_known']) == 8 for r, count in zip(tasks, counts))
        values = [count / 8 for count in counts]; vectors[label] = values
        for key, vals in [('pass_rate', values), ('pass_at_8', [v > 0 for v in values]),
                          ('mixed_share', [0 < v < 1 for v in values])]:
            validate_bootstrap(result['task_bootstrap'][key], vals)
        gates = result['gates']
        for key, count, passed in [
            ('a_extraction', sum(r['extracted'] == 'True' for r in rows), sum(r['extracted'] == 'True' for r in rows) >= 972),
            ('b_capped', sum(r['capped'] == 'True' for r in rows), sum(r['capped'] == 'True' for r in rows) <= 108),
            ('c_mixed', sum(0 < v < 1 for v in values), sum(0 < v < 1 for v in values) >= 7)]:
            assert gates[key]['n'] == count and gates[key]['pass'] == passed
        assert gates['pass'] == all(gates[k]['pass'] for k in ('a_extraction', 'b_capped', 'c_mixed'))
    for short in ('1p7b', '4b', '8b', '14b'):
        for fraction in ('f0p5', 'f1p0'):
            key = f'{short}_{fraction}'
            if f'v3_E_{key}' not in vectors or f'v3_R_{key}' not in vectors:
                assert key not in summary['paired_E_minus_R']
                continue
            e, r = vectors[f'v3_E_{key}'], vectors[f'v3_R_{key}']
            validate_bootstrap(summary['paired_E_minus_R'][key], [a - b for a, b in zip(e, r)])
    assert summary['primary'] == decision(summary['systems'], ('1p7b', '4b', '8b', '14b'), summary['paired_E_minus_R'])
    assert summary['sensitivity'] == decision(summary['systems'], ('4b', '8b', '14b'), summary['paired_E_minus_R'])


def validate_namespace(diag, rows, primary):
    # Complete diagnostic coverage may include a native timeout at the frozen cap.
    # Such an unknown is retained, never retried or silently converted to zero.
    assert diag['declared_cells'] == len(rows) == 1080, 'Namespace diagnostic remains incomplete'
    values = [None if r['diagnostic_kernel_binary'] == '' else float(r['diagnostic_kernel_binary']) for r in rows]
    assert diag['unknown_cells'] == values.count(None)
    if diag['unknown_cells']:
        assert 'paired_task_bootstrap_delta' not in diag, 'Unknown diagnostic values cannot have a point estimate'
    else:
        validate_bootstrap(diag['paired_task_bootstrap_delta'])
    changed = {(r['task_id'], int(r['sample_idx'])): r for r in rows if r['changed'] == 'True'}
    receipts = {(r['task_id'], r['sample_idx']): r for r in diag['changed_receipts']}
    assert len(receipts) == len(diag['changed_receipts']) == diag['changed_cells'] == len(changed)
    assert set(receipts) == set(changed)
    for key, row in changed.items():
        receipt = receipts[key]
        if receipt['compile_timeout']:
            assert receipt['kernel_binary'] is None and row['diagnostic_kernel_binary'] == ''
            assert receipt['compiles'] is False
        else:
            assert receipt['kernel_binary'] in (0, 1)
            assert float(row['diagnostic_kernel_binary']) == receipt['kernel_binary']
        assert receipt['original_sha256'] == row['original_sha256']
        assert receipt['transformed_sha256'] == row['transformed_sha256'] == digest(receipt['path'])
        assert read(Path(receipt['path']).with_suffix('.json')) == receipt
    assert all(v is None or v in (0, 1) for v in values)
    assert all(r['diagnostic_kernel_binary'] != '' for r in rows if r['changed'] != 'True')
    assert all(float(r['diagnostic_kernel_binary']) == float(r['original_kernel_binary'])
               and r['transformed_sha256'] == r['original_sha256'] for r in rows if r['changed'] != 'True')
    assert all(float(r['original_kernel_binary']) == float(primary[r['task_id'], r['sample_idx']]['kernel_binary']) for r in rows)
    assert diag['original_successes'] == sum(float(r['original_kernel_binary']) for r in rows)
    assert diag['diagnostic_successes_known'] == sum(v or 0 for v in values)


def replace_block(text, name, body):
    start, end = f'<!-- {name} -->', f'<!-- /{name} -->'
    block = start + '\n' + body.strip() + '\n' + end
    if start in text:
        assert end in text, f'Unterminated owned section: {name}'
        before, remainder = text.split(start, 1)
        _, after = remainder.split(end, 1)
        return before + block + after
    return text.rstrip() + '\n\n' + block + '\n'


def main(checksum_runner=None):
    receipt, summary, forecast = validate(checksum_runner=checksum_runner)
    report = HERE / 'results.md'
    text = report.read_text()
    block = 'Final checks: 17,280/17,280 exact cells, all eight training receipts and sixteen exports verified. '
    block += '[Completion evidence](results/completion_validation_v3.json); [namespace diagnostic](results/namespace_summary_v3.json); '
    block += '[frozen forecast assessment](results/forecast_assessment_v3.json).'
    block += f" Namespace diagnostics executed for every changed cell; {receipt['namespace_unknown_cells']} native timeout outcomes remain unknown. Paired diagnostic deltas are reported only for fully known rungs."
    report.write_text(replace_block(text, 'E08_V3_FINAL_CHECKS', block))
    parent = HERE.parent / 'results.md'
    block = f'''## Matched replay versus expansion continuation: expt_v3

**Last updated:** {receipt['validated_local']}. Numerical validation is complete for all 17,280 declared cells across sixteen systems; all eight training token schedules and sixteen export checksums pass. [Full table and paired task-bootstrap intervals](expt_v3/results.md), [namespace diagnostic](expt_v3/results/namespace_summary_v3.json), [frozen forecast assessment](expt_v3/results/forecast_assessment_v3.json).

Primary four-size result: `{json.dumps(summary['primary'])}`.

Pre-registered 4B/8B/14B sensitivity: `{json.dumps(summary['sensitivity'])}`.

Forecast assessment under the original earliest-selected-winner interpretation: primary hit={forecast['primary']['hit']}; sensitivity hit={forecast['sensitivity']['hit']}. The frozen question also asks which condition reaches a common checkpoint: earliest fraction within each condition is reported separately, with primary predicted checkpoint reached={forecast['primary']['common_checkpoint_assessment']['predicted_common_checkpoint_reached']} and sensitivity predicted checkpoint reached={forecast['sensitivity']['common_checkpoint_assessment']['predicted_common_checkpoint_reached']}. Both interpretations are retained when they disagree. Namespace repairs are diagnostic only; all changed cells were executed, with {receipt['namespace_unknown_cells']} native timeout outcomes retained as unknown and no point estimate for affected rungs. Zero paid model/judge calls; the test split remains unopened and hosted coverage judging remains deferred.
'''
    original = parent.read_text()
    parent.write_text(replace_block(original, 'E08_V3_FINAL_RESULTS', block))
    body = f'''Completed 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3.

All 17,280 declared primary validation cells, eight training schedules, sixteen exports, paired task bootstraps and the frozen forecast assessment are checked. Namespace diagnostics executed every changed cell; {receipt['namespace_unknown_cells']} native timeout outcomes remain unknown, with no point estimate for affected rungs.
Primary: {json.dumps(summary['primary'])}
Sensitivity: {json.dumps(summary['sensitivity'])}
Report: https://github.com/brando90/rl-4-code-verification/blob/main/{HERE.relative_to(HERE.parents[2])}/results.md

Zero paid model/judge calls; test split unopened. Hosted coverage judging remains deferred.
CC: brandojazz@gmail.com, brando9@stanford.edu, brando@vals.ai as requested.
drafted with Codex (gpt-6-astra)
'''
    (WORK / 'completion_email_body.txt').write_text(body)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('training', 'artifact_sha256')}, indent=2))


if __name__ == '__main__':
    main()
