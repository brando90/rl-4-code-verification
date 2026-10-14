"""Score each declared train anchor once with frozen extraction and the independent official oracle."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

import psutil

from panel import digest, validate_manifest, validate_generation, write_new
from lp1 import cleanup

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
sys.path.insert(0, str(V2 / 'R0_attempt_2'))
from declaration_adapter_v2 import inspect_source

POLICIES = {'base': 'base_4B', 'half': 'sft_4B_f0p5',
            'full1': 'sft_4B_f1p0', 'full2': 'sft_4B_f1p0'}
ADDRESS_SPACE = 64 * 1024**3
P99_PEAK = 6928265707.52  # Frozen R1 complete-cell process-tree bytes.


def score_one(row, root, config):
    """No model calls: capped source is scored normally; missing source is empty."""
    from rl4cv.veribench.exp103 import extract_lean
    if row['split'] != 'train' or row['batch'] not in POLICIES:
        raise ValueError('anchor scoring is train-only')
    root = Path(root)
    extraction = extract_lean(row['completion'], tuple(row['required_paths']), root=config['veribench'])
    source = root / 'solution.lean'
    with source.open('x', encoding='utf-8') as out:
        out.write(extraction.lean or '')
    value = inspect_source(source, lake_dir=Path(config['lake']), scorer_root=Path(config['scorer']),
                           evidence=root/'evidence', expected_sha256=digest(source),
                           family='ladder', known=True, truncated=row['at_token_cap'])
    old = json.loads((root/'evidence/oracle/oracle.json').read_text())
    scored = old['scored_response']
    q1 = bool(value['e'] and value['n_examples'] and value['p']['denominator']
              and not value['raw_vacuity_hits'] and not old['vacuity']['unparseable'])
    honest = bool(scored['n_theorems_stated'] > 0
                  and scored['n_theorems_stated'] == scored['n_theorems_proved'])
    return {'status': 'measured', **value, 'q1': q1, 'compile': old['compile'], 'honest': honest,
            'extraction': extraction.method, 'unmapped_paths': list(extraction.unmapped),
            'source_sha256': digest(source), 'at_token_cap': row['at_token_cap']}


def worker(job_path):
    job = json.loads(Path(job_path).read_text())
    root = Path(job['root'])
    for binding in job['bindings']:
        if digest(binding['path']) != binding['sha256']:
            raise ValueError('scoring input changed before worker read')
    row = json.loads(Path(job['generation']).read_text())
    for name in ('cell_id', 'task_id', 'sample', 'split'):
        if row[name] != job['cell'][name]: raise ValueError('generation identity changed')
    validate_generation(job['cell'], row, job['manifest_contract'])
    row.update(batch=job['batch'], required_paths=job['cell']['required_paths'])
    result = dict(job['identity']); start = time.monotonic()
    peak = [0]; stop = threading.Event(); process = psutil.Process()
    def monitor():
        while not stop.is_set():
            total = 0
            for child in [process, *process.children(recursive=True)]:
                try: total += child.memory_info().rss
                except psutil.Error: pass
            peak[0] = max(peak[0], total)
            stop.wait(.25)
    thread = threading.Thread(target=monitor, daemon=True); thread.start()
    try:
        result.update(score_one(row, root, job['config']))
    except (subprocess.TimeoutExpired, MemoryError) as exc:
        result.update(status='deterministic_resource_limit', error_type=type(exc).__name__)
    except Exception as exc:
        result.update(status='unresolved_measurement', error_type=type(exc).__name__, error=str(exc))
    finally:
        stop.set(); thread.join()
        result.update(wall_seconds=time.monotonic()-start, peak_tree_rss_bytes=peak[0])
        write_new(root/'worker_result.json', result)
    return result


def summarize(rows, declared):
    if len(rows) != declared or len({r['cell_id'] for r in rows}) != declared:
        raise ValueError('scoring denominator changed')
    measured = [r for r in rows if r['status'] == 'measured']
    successes = sum(r['strict'] for r in measured)
    return {'status': 'COMPLETE' if len(measured) == declared else 'INCOMPLETE',
            'declared': declared, 'measured': len(measured), 'missing': declared-len(measured),
            'strict_successes_measured': successes,
            'strict_full_denominator_bounds': [successes/declared, (successes+declared-len(measured))/declared],
            'capped_measured': sum(r['at_token_cap'] for r in measured), 'retries': 0}


def run(plan_path):
    """Run only a published input-bound scoring plan; the immutable ledger forbids replay."""
    plan = json.loads(Path(plan_path).read_text())
    repo = Path(plan['repository']); lock_path = Path(plan['lock'])
    lock = json.loads(lock_path.read_text())
    if lock['gate'] != 'ANCHOR_SCORE' or lock['status'] != 'FROZEN':
        raise ValueError('scoring lock is not final')
    subprocess.run(['git','merge-base','--is-ancestor',plan['published_revision'],'origin/main'],cwd=repo,check=True)
    published = subprocess.check_output(['git','show',plan['published_revision']+':'+str(lock_path.relative_to(repo))],cwd=repo)
    if published != lock_path.read_bytes(): raise ValueError('scoring lock is not published')
    for binding in lock['bindings']:
        if digest(binding['path']) != binding['sha256']: raise ValueError('scoring binding changed')
    config = lock['configuration']
    required = {str(Path(__file__).resolve()), str(HERE/'panel.py'), str(HERE/'lp1.py'),
                str(V2/'R0_attempt_2/declaration_adapter_v2.py'),
                str(V2/'R0_attempt_2/DeclarationProbe_v2.lean'), str(V2/'historical_oracle_v2.py'),
                config['manifest'], config['train_ids'], config['LP1_result']}
    if not required <= {b['path'] for b in lock['bindings']}:
        raise ValueError('scoring lock omits required implementation/input bindings')
    if json.loads(Path(config['LP1_result']).read_text())['status'] != 'PASS':
        raise ValueError('anchor scoring requires LP-1 PASS')
    manifest = json.loads(Path(config['manifest']).read_text())
    cells = validate_manifest(manifest, Path(config['train_ids']).read_text().splitlines())
    if manifest['batch'] not in POLICIES: raise ValueError('probe is not an anchor batch')
    root = Path(config['root']); root.mkdir(parents=True, exist_ok=True)
    write_new(root/'attempt.json', {'declared':len(cells), 'retries':0, 'lock_sha256':digest(lock_path)})
    slots = threading.Condition(); active = [0]
    def score(index, cell):
        identity = {'cell_id':cell['cell_id'], 'task_id':cell['task_id'], 'sample_idx':cell['sample'],
                    'policy':POLICIES[manifest['batch']], 'batch':manifest['batch'], 'split':'train'}
        cell_root = root / f'{index:05d}'; cell_root.mkdir(exist_ok=False)
        generation = Path(config['generation_root']) / f'{index:05d}.generation.json'
        write_new(cell_root/'attempt.json', {**identity, 'retries':0})
        if not generation.exists():
            receipt = {**identity, 'status':'missing_generation', 'cleanup_verified':True}
            write_new(cell_root/'result.json', receipt)
            return receipt
        if str(generation) not in {b['path'] for b in lock['bindings']}:
            raise ValueError('generation receipt absent from published scoring lock')
        marker = 'e13v2-score-'+uuid.uuid4().hex
        job = {'identity':identity, 'cell':cell, 'batch':manifest['batch'], 'root':str(cell_root),
               'generation':str(generation), 'manifest_contract':manifest,
               'bindings':[{'path':str(generation),'sha256':digest(generation)}], 'config':config}
        # Store the token contract only; never replicate an entire 4312-cell manifest.
        job['manifest_contract'] = {k:manifest[k] for k in ('terminal_token_ids','max_model_len')}
        write_new(cell_root/'job.json', job)
        with slots:
            while True:
                mem = psutil.virtual_memory()
                ceiling = min(48, int(.5*mem.available/P99_PEAK))
                if active[0] < ceiling and mem.available >= .25*mem.total:
                    active[0] += 1; break
                slots.wait(1)
        started = time.monotonic(); result = {**identity, 'status':'unresolved_measurement'}
        try:
            with (cell_root/'execution.log').open('x') as log:
                command = ['prlimit',f'--as={ADDRESS_SPACE}','--',sys.executable,str(Path(__file__)),
                           '--job',str(cell_root/'job.json')]
                child = subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                                         env={**os.environ,'E13_EXECUTION_ID':marker})
                write_new(cell_root/'process.json', {'pid':child.pid, 'marker':marker,
                    'start_ticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],
                    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                code = child.wait(timeout=3600)
            if (cell_root/'worker_result.json').exists():
                result = json.loads((cell_root/'worker_result.json').read_text())
            result['worker_exit_code'] = code
            if code != 0 and result['status'] == 'measured': result['status'] = 'unresolved_measurement'
        except subprocess.TimeoutExpired:
            result.update(status='deterministic_resource_limit', error_type='supervisor_timeout')
        finally:
            cleaned = cleanup(marker)
            result.update(cleanup_verified=cleaned['verified'], supervisor_seconds=time.monotonic()-started)
            if not cleaned['verified']: result['status'] = 'unresolved_cleanup'
            write_new(cell_root/'cleanup.json', cleaned)
            write_new(cell_root/'result.json', result)
            with slots: active[0] -= 1; slots.notify_all()
        return result
    rows = []
    with (root/'results.jsonl').open('x') as out, ThreadPoolExecutor(max_workers=48) as pool:
        pending = {pool.submit(score,i,c):c for i,c in enumerate(cells)}
        for future in as_completed(pending):
            try: row = future.result()
            except Exception as exc:
                cell = pending[future]
                row = {'cell_id':cell['cell_id'], 'task_id':cell['task_id'], 'sample_idx':cell['sample'],
                       'policy':POLICIES[manifest['batch']], 'batch':manifest['batch'], 'split':'train',
                       'status':'integrity_defect', 'error_type':type(exc).__name__, 'error':str(exc)}
            rows.append(row)
            out.write(json.dumps(row,allow_nan=False)+'\n');out.flush();os.fsync(out.fileno())
    result = summarize(rows,len(cells));write_new(root/'terminal.json',result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--job',type=Path);group.add_argument('--plan',type=Path)
    args = parser.parse_args()
    print(json.dumps(worker(args.job) if args.job else run(args.plan)))
