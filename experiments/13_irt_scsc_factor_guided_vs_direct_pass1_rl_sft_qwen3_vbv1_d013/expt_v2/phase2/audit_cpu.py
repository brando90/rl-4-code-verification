"""Measure frozen train mutations and independent hidden tests once, reusing original anchor scores."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'phase1'))
from g1_driver import verify_publication
from score_anchor_ledger import MemorySlots, finish_attempt
from score_anchor import inspect_source, ADDRESS_SPACE
from hidden_runtime import measure_cell
from training_checkpoint import digest, write_new
from costs import snapshot, stage_cost
from audit_inputs import checked, VARIANTS


def measure(job, *, inspector=inspect_source, hidden=measure_cell):
    """Run only named immutable inputs; persist strict evidence before independent hidden checking."""
    cell = job['cell']; config = job['configuration']; root = Path(job['root'])
    allowed = set(Path(config['train_ids']).read_text().splitlines())
    if cell['split'] != 'train' or cell['task_id'] not in allowed:
        raise ValueError('audit measurement is train-only')
    for key in ('source', 'original_score'):
        if cell.get(key): checked(cell[key])
    result = {**job['identity'], 'condition': 'v2-S2', 'status': 'ACCOUNTED',
              'strict': None, 'compile': None, 'components': None,
              'hidden_test_coverage': None, 'new_strict_measurement': False}
    if cell['source'] is None:
        return {**result, 'status': 'MISSING_INPUT', 'reason': cell['reason']}
    source = checked(cell['source'])
    strict_path = root/'strict_result.json'
    if strict_path.exists():
        raise RuntimeError('prior partial audit measurement requires receipt reconciliation, never rerun')
    if cell['variant'] == 'original':
        old = json.loads(checked(cell['original_score']).read_text()) if cell.get('original_score') else {}
        if old.get('status') == 'measured':
            if (old.get('source_sha256') != digest(source) or old.get('task_id') != cell['task_id']
                    or old.get('sample_idx') != 0 or old.get('batch') != 'full1'):
                raise ValueError('original audit measurement provenance changed')
            strict = {**old, 'measurement_reused': True}
        else:
            strict = {'status': 'unresolved_original', 'measurement_reused': False}
    else:
        try:
            value = inspector(source, lake_dir=Path(config['lake']), scorer_root=Path(config['scorer']),
                evidence=root/'evidence', expected_sha256=digest(source), family='ladder', known=True, truncated=False)
            oracle = json.loads((root/'evidence/oracle/oracle.json').read_text())
            strict = {'status': 'measured', **value, 'compile': oracle['compile'], 'measurement_reused': False}
        except (subprocess.TimeoutExpired, MemoryError) as exc:
            strict = {'status': 'deterministic_resource_limit', 'error_type': type(exc).__name__}
        except Exception as exc:
            strict = {'status': 'unresolved_measurement', 'error_type': type(exc).__name__, 'error': str(exc)}
        result['new_strict_measurement'] = True
    write_new(strict_path, strict)
    result.update(strict_receipt={'path': str(strict_path), 'sha256': digest(strict_path)},
                  strict_status=strict['status'])
    if strict['status'] == 'measured':
        result.update(strict=strict['strict'], compile=strict['compile'], components=strict)
    suite = job['suite']; checked(suite)
    hidden_cell = {k: cell[k] for k in ('cell_id', 'task_id', 'split')}
    hidden_cell.update(source=str(source), suite=suite['path'])
    hidden_config = {**config, 'root': str(root/'hidden')}
    bindings = {str(source): digest(source), suite['path']: suite['sha256'],
                config['train_ids']: digest(config['train_ids'])}
    try:
        independent = hidden(hidden_cell, hidden_config, bindings, job['execution_sha256'])
    except Exception as exc:
        independent = {'status': 'unresolved_measurement', 'hidden_pass_rate': None,
                       'error_type': type(exc).__name__, 'error': str(exc)}
    write_new(root/'hidden_summary.json', independent)
    result.update(hidden_status=independent['status'], hidden_test_coverage=(independent.get('hidden_pass_rate')
                      if independent.get('fully_applicable') or independent['status'] == 'compile_failure' else None),
                  hidden_receipt={'path': str(root/'hidden_summary.json'), 'sha256': digest(root/'hidden_summary.json')})
    return result


def worker(path):
    job = json.loads(Path(path).read_text()); started = time.monotonic()
    result = measure(job)
    result['wall_seconds'] = time.monotonic()-started
    write_new(Path(job['root'])/'worker_result.json', result)
    return result


def execute(job, root, marker, slots):
    write_new(root/'job.json', job); code = None; error = None
    with slots:
        try:
            with (root/'execution.log').open('x') as log:
                child = subprocess.Popen(['prlimit', f'--as={ADDRESS_SPACE}', '--', sys.executable,
                    str(Path(__file__).resolve()), '--job', str(root/'job.json')], stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True, env={**os.environ, 'E13_EXECUTION_ID': marker})
                write_new(root/'process.json', {'pid': child.pid, 'marker': marker,
                    'start_ticks': Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
                    'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                code = child.wait(timeout=3600)
        except subprocess.TimeoutExpired: error = 'supervisor_timeout'
        except OSError as exc: error = type(exc).__name__
        return finish_attempt(root, job['identity'], marker, code, error)


def score_cell(cell, index, config, suite, execution_sha, slots, executor=execute):
    root = Path(config['root'])/f'{index:03d}'; root.mkdir(parents=True, exist_ok=True)
    identity = {k: cell[k] for k in ('cell_id', 'audit_id', 'task_id', 'group_id', 'split', 'variant')}
    expected = {'identity': identity, 'execution_sha256': execution_sha, 'cell': cell, 'suite': suite}
    attempt = root/'attempt.json'; final = root/'result.json'
    if attempt.exists():
        previous = json.loads(attempt.read_text())
        if any(previous.get(k) != v for k, v in expected.items()): raise ValueError('audit execution binding changed')
        result = json.loads(final.read_text()) if final.exists() else finish_attempt(root, identity, previous['marker'])
        if any(result.get(k) != v for k, v in identity.items()): raise ValueError('audit receipt identity changed')
        return result
    if final.exists(): raise ValueError('audit result has no attempt binding')
    marker = 'e13v2-audit-'+uuid.uuid4().hex
    write_new(attempt, {**expected, 'marker': marker, 'automatic_retry': False, 'started_unix': time.time()})
    job = {**expected, 'root': str(root), 'configuration': config}
    return executor(job, root, marker, slots)


def authorize(plan):
    lock = verify_publication(plan['lock'], plan['repository'], plan['published_revision'])
    if (lock.get('gate'), lock.get('condition'), lock.get('status')) != ('TRAIN_AUDIT_CPU', 'v2-S2', 'FROZEN'):
        raise ValueError('published train audit execution lock required')
    bound = {b['path']: b['sha256'] for b in lock['bindings']}
    for path, sha in bound.items():
        if digest(path) != sha: raise ValueError('audit executable or input changed')
    config = lock['configuration']; manifest = json.loads(Path(config['inputs']).read_text())
    required = {str(HERE/name) for name in ('audit_cpu.py', 'audit_inputs.py', 'audit_mutations.py',
                'hidden_runtime.py', 'training_checkpoint.py', 'costs.py')}
    required |= {str(HERE.parent/'phase1'/name) for name in ('score_anchor.py', 'score_anchor_ledger.py', 'lp1.py', 'g1_driver.py')}
    required.add(str(HERE.parent/'watchdog_e13v2.py'))
    required |= {config[k] for k in ('inputs', 'train_ids', 'cohort_lock', 'anchor_scoring_lock', 'anchor_scoring_report', 'anchor_rows', 'hidden_controls_lock', 'hidden_controls_result')}
    if not required <= set(bound): raise ValueError('audit execution dependencies are unbound')
    prior_locks = {}
    for key in ('cohort_lock', 'anchor_scoring_lock', 'hidden_controls_lock'):
        prior = verify_publication(config[key], plan['repository'], config[key+'_revision'])
        prior_locks[key] = prior
        for b in prior['bindings']:
            if digest(b['path']) != b['sha256']: raise ValueError('prior scoring/cohort binding changed')
    report = verify_publication(config['anchor_scoring_report'], plan['repository'], config['anchor_scoring_report_revision'])
    if report.get('batch') != 'full1' or report.get('accounted') != 4312 or report.get('condition') != 'v2-S2':
        raise ValueError('full1 scoring must close before audit inputs')
    if digest(config['anchor_rows']) != report.get('cells_sha256'):
        raise ValueError('audit baseline differs from the published full1 scoring rows')
    anchor_rows = [json.loads(line) for line in Path(config['anchor_rows']).read_text().splitlines()]
    anchor_table = {(row['task_id'], row['sample_idx']): (i, row) for i, row in enumerate(anchor_rows)}
    if len(anchor_rows) != 4312 or len(anchor_table) != 4312:
        raise ValueError('baseline scoring inventory is not the complete anchor panel')
    controls = verify_publication(config['hidden_controls_result'], plan['repository'], config['hidden_controls_result_revision'])
    if controls.get('status') != 'PASS' or controls.get('condition') != 'v2-S2': raise ValueError('hidden controls did not pass')
    if manifest['declared_tasks'] != 32 or manifest['declared_variants'] != 128 or len(manifest['cells']) != 128:
        raise ValueError('audit declared denominator changed')
    cohort = json.loads(Path(config['cohort_lock']).read_text())
    original = json.loads(Path(cohort['private_cohort']).read_text())['cells']
    expected = {(c['audit_id'], v): c for c in original for v in VARIANTS}
    if len({(c['audit_id'], c['variant']) for c in manifest['cells']}) != 128: raise ValueError('audit variants duplicated')
    if set(config['suites']) != {c['task_id'] for c in original}: raise ValueError('complete train hidden-suite inventory required')
    for cell in manifest['cells']:
        wanted = expected.get((cell['audit_id'], cell['variant']))
        if wanted is None or any(cell[k] != wanted[k] for k in ('task_id', 'group_id', 'split')):
            raise ValueError('audit cohort identity changed')
        index, anchor = anchor_table[(cell['task_id'], 0)]
        original_root = Path(prior_locks['anchor_scoring_lock']['configuration']['root'])/f'{index:05d}'/f"attempt_{anchor['attempts']}"
        for key, name in [('original_source', 'solution.lean'), ('original_score', 'worker_result.json'),
                          ('original_frontend', 'evidence/components/frontend.json')]:
            if cell.get(key) and Path(cell[key]['path']).resolve() != (original_root/name).resolve():
                raise ValueError('audit original is detached from the published full1 inventory')
        if cell['variant'] == 'original' and cell.get('source') and cell.get('original_source'):
            if cell['source']['sha256'] != cell['original_source']['sha256']:
                raise ValueError('original audit source bytes changed')
        for ref in [cell.get(k) for k in ('source', 'original_source', 'original_score', 'original_frontend')] + [config['suites'][cell['task_id']]]:
            if ref and bound.get(ref['path']) != ref['sha256']: raise ValueError('audit source provenance is unbound')
    return lock, config, manifest


def run(plan_path):
    plan = json.loads(Path(plan_path).read_text()); lock, config, manifest = authorize(plan)
    root = Path(config['root']); root.mkdir(parents=True, exist_ok=True)
    lock_sha = digest(plan['lock']); terminal = root/'terminal.json'
    Path(config['controller_fence']).parent.mkdir(parents=True, exist_ok=True)
    with Path(config['controller_fence']).open('a') as fence:
        fcntl.flock(fence, fcntl.LOCK_EX)
        if terminal.exists():
            result = json.loads(terminal.read_text())
            if result['execution_sha256'] != lock_sha or result['rows_sha256'] != digest(root/'rows.json'):
                raise ValueError('completed audit result changed')
            return result
        subprocess.run([sys.executable, str(HERE.parent/'watchdog_e13v2.py'), '--root', plan['watchdog_root'],
            '--run', plan['watchdog_run'], 'register', '--role', 'train-audit-cpu', '--pid', str(os.getpid())], check=True)
        before = snapshot(root); slots = MemorySlots()
        with ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(lambda pair: score_cell(pair[1], pair[0], config,
                config['suites'][pair[1]['task_id']], lock_sha, slots), enumerate(manifest['cells'])))
        write_new(root/'rows.json', rows)
        write_new(root/'cost.json', stage_cost(before, snapshot(root), stage='train_mutation_cpu'))
        result = {'condition': 'v2-S2', 'stage': 'TRAIN_AUDIT_CPU', 'status': 'ACCOUNTED',
            'execution_sha256': lock_sha, 'declared': 128, 'accounted': len(rows),
            'strict_known': sum(r.get('strict') is not None for r in rows),
            'hidden_known': sum(r.get('hidden_test_coverage') is not None for r in rows),
            'rows_sha256': digest(root/'rows.json'), 'automatic_retries': 0,
            'cleanup_unresolved': sum(not r.get('cleanup_verified', False) for r in rows),
            'unresolved_cells': sum(r.get('status') not in ('ACCOUNTED', 'MISSING_INPUT') for r in rows),
            'coverage_judge_calls': 0, 'learning_admitted': False}
        write_new(terminal, result); return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--job', type=Path); choice.add_argument('--plan', type=Path)
    args = parser.parse_args()
    print(json.dumps(worker(args.job) if args.job else run(args.plan), sort_keys=True))
