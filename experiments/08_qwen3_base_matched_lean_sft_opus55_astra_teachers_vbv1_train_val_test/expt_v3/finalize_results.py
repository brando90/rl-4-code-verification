"""Check every frozen cell and training receipt before preparing final publication and mail."""
from __future__ import annotations
import csv
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo
from assess_forecast import assess
from recovery_watch import read, write
from remote_generation import validate_raw, digest, SHARED

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')


def validate():
    manifest = read(HERE / 'results/ladder_manifest_v3.json')
    summary = read(HERE / 'results/validation_summary_v3.json', {})
    assert summary.get('known_cells') == summary.get('declared_cells') == 17280, 'Validation remains incomplete'
    expected_labels = {s['label'] for s in manifest['systems']}
    assert len(expected_labels) == 16 and set(summary['systems']) == expected_labels
    pairs = summary['paired_E_minus_R']
    assert set(pairs) == {f'{s}_{f}' for s in ('1p7b', '4b', '8b', '14b') for f in ('f0p5', 'f1p0')}
    for value in pairs.values():
        validate_bootstrap(value)
    expected = {(c['system'], c['task_id'], c['sample_idx']) for c in manifest['cells']}
    seen = set(); namespace = {}; files = {}
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
        errors = diag['original_first_error_sample']
        assert errors['compile_error_population'] == result['failure_taxonomy'].get('compile_error', 0)
        assert errors['sampled_cells'] == min(24, errors['compile_error_population']) == len(errors['receipts'])
        assert errors['kind_counts'] == dict(Counter(r['kind'] for r in errors['receipts']))
        for error in errors['receipts']:
            assert error['original_sha256'] == digest(error['path']) == primary[error['task_id'], str(error['sample_idx'])]['lean_sha256']
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
            assert receipt['status'] == 'PASS' and receipt['token_counts_match']
            assert receipt['steps'] == len(schedule['steps'])
            assert receipt['loss_tokens'] == schedule['steps'][-1]['cumulative_loss_tokens']
            for fraction in ('f0p5', 'f1p0'):
                step = schedule['checkpoints'][fraction]['step']
                export = WORK / f'ckpt/{label}/hf/step_{step}'
                subprocess.run(['sha256sum', '--check', '--quiet', 'SHA256SUMS'], cwd=export, check=True)
                checksum = HERE / f'results/train_logs/{label}_{fraction}_SHA256SUMS'
                checksum.write_bytes((export / 'SHA256SUMS').read_bytes())
                files[str(checksum.relative_to(HERE))] = hashlib.sha256(checksum.read_bytes()).hexdigest()
            training[label] = receipt
    forecast = assess(summary)
    assert all(forecast[k]['outcome']['status'] == 'COMPLETE' for k in ('primary', 'sensitivity'))
    write(HERE / 'results/forecast_assessment_v3.json', forecast)
    write(HERE / 'results/namespace_summary_v3.json', namespace)
    receipt = {'status': 'VALIDATED', 'known_cells': len(seen), 'declared_cells': 17280,
               'systems': 16, 'training_verified': True, 'namespace_complete': True,
               'namespace_diagnostic_executed': True,
               'namespace_unknown_cells': sum(s['unknown_cells'] for s in namespace.values()),
               'namespace_paired_delta_available': all(s['unknown_cells'] == 0 for s in namespace.values()),
               'forecast_assessed': True, 'training': training, 'artifact_sha256': files,
               'paid_model_spend_usd': 0, 'test_split_opened': False,
               'validated_local': datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%m-%d-%Y %H:%M %Z')}
    write(HERE / 'results/completion_validation_v3.json', receipt)
    return receipt, summary, forecast


def validate_bootstrap(value):
    assert value['draws'] == 10000 and value['seed'] == 0
    assert value['unit'] == 'task with eight attempts together'
    assert len(value['ci95']) == 2 and -1 <= value['ci95'][0] <= value['ci95'][1] <= 1
    assert -1 <= value['mean'] <= 1


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


def main():
    receipt, summary, forecast = validate()
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

Forecast assessment: primary hit={forecast['primary']['hit']}; sensitivity hit={forecast['sensitivity']['hit']}. Namespace repairs are diagnostic only; all changed cells were executed, with {receipt['namespace_unknown_cells']} native timeout outcomes retained as unknown and no point estimate for affected rungs. Zero paid model/judge calls; the test split remains unopened and hosted coverage judging remains deferred.
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
