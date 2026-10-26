"""Evaluate the complete frozen primary panel with hash-checked module reuse and durable bounded retries."""
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
from runtime_v2 import Runtime
from support_v2 import PHASE, V1, WORK, V1_WORK, digest, verify_inputs, atomic_json, workers_allowed
from evaluate_e12 import cell_key, recover_jsonl, infra_failure, archive_logs, summary
from adapter_v2 import cell_outcome, per_test_plan


def runtime_hashes():
    return {name: digest(PHASE/'scripts'/name) for name in
            ('adapter_v2.py', 'runtime_v2.py', 'evaluate_v2.py', 'support_v2.py')}


def reuse_module(rt, row, module, v1_work=V1_WORK):
    """Copy a successful v1 module only when its source matches the frozen candidate bytes."""
    key = hashlib.sha256((row['task_id']+':'+row['sha256']).encode()).hexdigest()
    old = Path(v1_work)/'evaluation_A2/modules'/(module+'.lean')
    prior = Path(v1_work)/'evaluation_A2'/(key+'.json')
    if not old.exists() or not old.with_suffix('.olean').exists() or not prior.exists():
        return None
    receipt = json.loads(prior.read_text())
    if digest(old) != row['sha256'] or receipt.get('input_sha256') != row['sha256'] or receipt['compile']['status'] != 'ok':
        return None
    target = rt.root/'modules'/old.name
    shutil.copyfile(old, target)
    shutil.copyfile(old.with_suffix('.olean'), target.with_suffix('.olean'))
    assert digest(target) == row['sha256']
    assert digest(target.with_suffix('.olean')) == digest(old.with_suffix('.olean'))
    return {'status':'ok', 'returncode':0, 'seconds':0, 'reused':True,
            'source':str(old), 'source_sha256':row['sha256'],
            'olean_sha256':digest(target.with_suffix('.olean')), 'v1_receipt':str(prior)}


def make_record(row, suite, result=None, receipt=None):
    status = ('no_tests' if not suite['n_tests'] else row['join_status']
              if row['join_status'] in ('file_missing','join_ambiguous') else 'noncompiling'
              if row['recorded_compiles'] is False else 'unmeasured_compile')
    outcome = cell_outcome(suite['n_tests'], {}, per_test_plan(suite['tests'], {}))
    diag = []
    if result is not None:
        outcome = {k: result[k] for k in outcome}
        diag = result['diagnostics']
        status = ('evaluated' if outcome['applicable'] else 'recompile_unknown'
                  if result['compile']['status'] != 'ok' else 'not_applicable')
    elif status == 'noncompiling':
        outcome.update(hidden_all_pass=0, hidden_pass_rate=0)
    return {**row, **outcome, 'compiles':row['recorded_compiles'], 'status':status,
            'n_applicable':outcome['n_evaluable'], 'n_unknown':outcome['n_unmapped']+outcome['n_type_unknown'],
            'mapping_steps':[d['step'] for d in diag if d['status']=='mapped'],
            'all_mappings_unambiguous':bool(diag) and all(d.get('step') in (1,'2a','2b') for d in diag),
            'mapping':result['mapping'] if result else {}, 'diagnostics':diag,
            'n_examples':result.get('n_examples') if result else None,
            'n_eval_commands':result.get('n_eval_commands') if result else None,
            'receipt':receipt}


def evaluate_group(rt, item, suites, v1_work=V1_WORK):
    key, group = item
    row = group[0]; destination = rt.root/(key+'.json'); pins = runtime_hashes()
    if destination.exists():
        result = json.loads(destination.read_text())
        assert result['runtime_hashes'] == pins and result['input_sha256'] == row['sha256']
        assert result['task_id'] == row['task_id']
        return key, result
    raw = Path(row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
    module = 'E12Eval'+key[:24]
    attempt = rt.root/(key+'.attempt0.json')
    if attempt.exists():
        result = json.loads(attempt.read_text())
        assert result['runtime_hashes'] == pins and result['input_sha256'] == row['sha256']
    else:
        compiled = reuse_module(rt, row, module, v1_work)
        result = rt.evaluate(suites[row['task_id']], raw.decode(), module, compiled)
        result.update(task_id=row['task_id'], input_sha256=row['sha256'], runtime_hashes=pins)
        atomic_json(attempt, result)
    if infra_failure(result):
        retry_path = rt.root/(key+'.attempt1.json')
        if retry_path.exists():
            result = json.loads(retry_path.read_text())
        else:
            # Receipt is durable before retry; at most one retry per identical group.
            previous = archive_logs(result, rt.root/(key+'_attempt0'))
            marker = rt.root/(key+'.retry_started')
            if marker.exists():
                # An interrupted retry is terminal missing; never silently restart its budget.
                result = {**result, 'retry_interrupted':True, 'infrastructure_retries':[previous]}
            else:
                marker.write_text(row['sha256']+'\n')
                result = rt.evaluate(suites[row['task_id']], raw.decode(), module)
                result.update(task_id=row['task_id'], input_sha256=row['sha256'], runtime_hashes=pins,
                              infrastructure_retries=[previous])
                atomic_json(retry_path, result)
    atomic_json(destination, result)
    return key, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, default=WORK)
    parser.add_argument('--panels', choices=['primary'], default='primary')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args(); args.work = args.work.resolve(); args.work.mkdir(parents=True, exist_ok=True)
    lock = (args.work/'evaluation_v2.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    workers_allowed(args.workers)
    frozen = verify_inputs()
    controls = json.loads((PHASE/'results/controls_v2.json').read_text())
    assert controls['all_controls_pass'] and controls['complete']
    for name, expected in controls['source_hashes'].items():
        assert digest(PHASE/'scripts'/name) == expected
    rows = json.loads((V1/'results/input_manifest_A1.json').read_text())['cells']
    assert len(rows) == len({cell_key(r) for r in rows}) == 9856
    assert len({r['system'] for r in rows}) == 11 and len({r['task_id'] for r in rows}) == 896
    suites = {r['task_id']:r for r in json.loads((V1/'results/hidden_tests_manifest.json').read_text())['tasks']}
    groups = {}
    for row in rows:
        if row['recorded_compiles'] is True and suites[row['task_id']]['n_tests'] and row['join_status'] not in ('file_missing','join_ambiguous'):
            assert digest(row['path']) == row['sha256'], row['path']
            key = hashlib.sha256((row['task_id']+':'+row['sha256']).encode()).hexdigest()
            groups.setdefault(key, []).append(row)
    assert len(groups) == sum(map(len, groups.values())) == 4626
    provenance = {'inputs':frozen, 'runtime_hashes':runtime_hashes(), 'n_declared':9856,
                  'n_unique_groups':4626, 'infrastructure_retry_limit':1,
                  'controls_sha256':digest(PHASE/'results/controls_v2.json')}
    manifest = args.work/'evaluation_run_manifest_v2.json'
    if manifest.exists():
        assert json.loads(manifest.read_text()) == provenance
    else:
        atomic_json(manifest, provenance)
    dest = args.work/'cells_v2.jsonl'; records = {}
    if dest.exists():
        for r in recover_jsonl(dest):
            assert cell_key(r) not in records
            records[cell_key(r)] = r
    assert set(records) <= {cell_key(r) for r in rows}
    all_groups = groups
    evaluated_keys = {cell_key(r) for g in groups.values() for r in g}
    groups = {k:g for k,g in groups.items() if any(cell_key(r) not in records for r in g)}
    rt = Runtime(args.work/'evaluation_v2')
    with dest.open('a') as stream:
        def emit(record):
            assert cell_key(record) not in records
            stream.write(json.dumps(record, separators=(',',':'))+'\n'); stream.flush(); os.fsync(stream.fileno())
            records[cell_key(record)] = record
        for row in rows:
            if cell_key(row) not in records and cell_key(row) not in evaluated_keys:
                emit(make_record(row, suites[row['task_id']]))
        done = len(all_groups)-len(groups)
        def progress():
            report = summary(list(records.values()), len(rows))
            report.update(unique_jobs_completed=done, n_unique_jobs=4626,
                          n_fully_applicable=sum(r['fully_applicable'] for r in records.values()))
            atomic_json(PHASE/'results/evaluation_progress_v2.json', report)
            print(json.dumps(report), flush=True)
        progress()
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(evaluate_group, rt, item, suites) for item in groups.items()]
            for future in concurrent.futures.as_completed(futures):
                key, result = future.result()
                for row in groups[key]:
                    if cell_key(row) not in records:
                        emit(make_record(row, suites[row['task_id']], result, str(rt.root/(key+'.json'))))
                done += 1
                if done % 10 == 0 or done == 4626:
                    progress()
    final = summary(list(records.values()), 9856)
    assert final['complete'] and done == 4626
    final.update(outcomes_sha256=digest(dest), outcomes_path=str(dest), n_unique_groups=done)
    atomic_json(PHASE/'results/evaluation_complete_v2.json', final)


if __name__ == '__main__':
    main()
