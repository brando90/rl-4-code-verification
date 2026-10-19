# New prospective coordinator derived from the frozen completed V20/V23 coordinator.
# Every new scorer child MUST use logged_scorer.py; old coordinator files are unchanged.
"""Adopt the existing scoring partition and fill a shared 32-process CPU pool.

Run only after the previous parallel coordinator has been retired. Active scorer
children are adopted without interruption; their exit status is explicitly
unobserved. Completed measurements are reconstructed with the frozen cache
adapter. No previously started cell is automatically retried.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import csv
import fcntl
import json
import os
from pathlib import Path
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
FROZEN_HELPERS = HERE.parent.parent / 'expt_v20'
sys.path.insert(0, str(FROZEN_HELPERS))
from parallel_scoring import RUN, REPO, EXP, PY, SCORER, sha, read, write, proc, live, load
import parallel_score_cache as cache_helper


def scorer_command(cell, destination, gold_dir, lake_dir):
    """Mandatory durable launcher used by every new worker in this coordinator."""
    return [PY, str(HERE / 'logged_scorer.py'), '--scorer', str(SCORER),
        '--evidence-root', str(Path(destination) / 'compiler_diagnostics'),
        '--lean-executable', '/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin/lean',
        '--', '--job-dir', cell['job'], '--pack', str(RUN / 'validation_pack'),
        '--name', cell['key'], '--gold-dir', str(gold_dir), '--lake-dir', str(lake_dir),
        '--skip-tc', '--out-dir', str(destination)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same_process(pid, ticks):
    current = proc(pid)
    return bool(current and current['state'] != 'Z' and current['start_ticks'] == str(ticks))


def csv_matches(typed, recorded):
    """Compare the actual CSV representation of every frozen typed row field."""
    mismatches = []
    for key, value in typed.items():
        text = recorded.get(key, '')
        if isinstance(value, (dict, list)):
            try:
                equal = ast.literal_eval(text) == value
            except (ValueError, SyntaxError):
                equal = False
        elif value is None:
            equal = text == ''
        elif type(value) in (int, float):
            try:
                equal = float(text) == value
            except (ValueError, TypeError):
                equal = False
        else:
            equal = str(value) == text
        if not equal:
            mismatches.append(key)
    require(not mismatches, f'Published CSV differs from typed frozen cache reconstruction: {mismatches}')
    require(recorded.get('missing_output', '') in ('', 'False', 'false'), 'One-cell result is a missing-output placeholder')


class Slots:
    """Every active scorer, including adopted children, occupies one shared lock."""
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else RUN / 'lean_scoring_cpu32'
        self.root.mkdir(exist_ok=True)

    def _try(self):
        for n in range(32):
            handle = (self.root / f'{n:02d}.lock').open('a')
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return handle, n
            except BlockingIOError:
                handle.close()
        return None

    def acquire(self):
        while True:
            with (self.root / 'adoption.lock').open('a') as gate:
                fcntl.flock(gate, fcntl.LOCK_SH)
                slot = self._try()
            if slot:
                return slot
            time.sleep(.2)

    def reserve_existing(self, count):
        reserved = []
        with (self.root / 'adoption.lock').open('a') as gate:
            fcntl.flock(gate, fcntl.LOCK_EX)
            try:
                for _ in range(count):
                    slot = self._try()
                    require(slot is not None, 'Not enough shared slots to account for existing active scorers; no new work launched')
                    reserved.append(slot)
            except BaseException:
                for handle, _ in reserved:
                    handle.close()
                raise
        return reserved


def validate_partition(partition):
    cells, legacy = partition['cells'], partition.get('legacy', [])
    require(partition['all_generated_cells'] == 1080, 'Declared validation manifest changed')
    require(len({cell['key'] for cell in cells}) == len(cells), 'Repeated partition cell key')
    require(len({(cell['sample'], cell['td']) for cell in cells}) == len(cells), 'Repeated sample/task cell')
    require(len(cells) + sum(len(item['prefix']) for item in legacy) == 1080, 'Partition does not account for exactly 1080 cells')
    require(len({row['sample'] for row in legacy}) == len(legacy), 'Repeated legacy sample')
    for sample in range(8):
        suffix = [cell['td'] for cell in cells if cell['sample'] == sample]
        prefix = [td for row in legacy if row['sample'] == sample for td in row['prefix']]
        require(len(prefix) + len(suffix) == len(set(prefix + suffix)) == 135,
                f'Sample {sample} is not a disjoint 135-task partition')
    require(all(0 <= cell['sample'] < 8 for cell in cells)
            and all(0 <= row['sample'] < 8 for row in legacy), 'Unexpected sample index')
    return cells, legacy


def running_cell_processes(cells):
    """Find even a child started just before its retired parent wrote RUNNING."""
    by_job = {str(Path(cell['job'])):cell['key'] for cell in cells}
    found = {}
    listing = subprocess.run(['ps', '-eo', 'pid=,args='], capture_output=True, text=True, check=True).stdout
    for line in listing.splitlines():
        if str(SCORER) not in line or '--job-dir' not in line:
            continue
        pid = int(line.strip().split(None, 1)[0])
        actual = proc(pid)
        if not actual or actual['state'] == 'Z':
            continue
        try:
            args = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
            arguments = [arg.decode() for arg in args if arg]
            job = arguments[arguments.index('--job-dir') + 1]
        except (OSError, ValueError, IndexError, UnicodeDecodeError):
            continue
        if job in by_job:
            key = by_job[job]
            require(key not in found, f'More than one active scorer for {key}')
            found[key] = dict(pid=pid, start_ticks=actual['start_ticks'], command=actual['command'])
    return found


def restore_sentinel(sentinel):
    source, held = Path(sentinel['source']), Path(sentinel['held'])
    if held.exists():
        require(sha(held) == sentinel['sha256'], 'Held boundary source changed')
        if source.exists():
            require(sha(source) == sentinel['sha256'], 'Restored boundary source differs')
            held.unlink()
        else:
            os.replace(held, source)
    else:
        require(source.exists() and sha(source) == sentinel['sha256'], 'Boundary source is neither held nor correctly restored')


def main(version):
    require(version >= 25, 'This prospective logged entry is only for new versions >=25; completed historical phases are immutable')
    root = RUN / f'corpus_training_v{version}'
    label = f'v{version}_base'
    out = root / 'scoring_parallel_v1'
    partition_path = out / 'partition.json'
    require(partition_path.is_file(), 'A frozen partition is required; this driver never repartitions')
    lock = (out / 'owner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(not (out / 'terminal.json').exists(), 'Completed scoring phase is immutable')
    previous_dispatch = read(out / 'dispatch.json') if (out / 'dispatch.json').exists() else {}
    previous_pid = previous_dispatch.get('owner_pid')
    require(not previous_pid or previous_pid == os.getpid() or not live(previous_pid),
            'Previous parallel coordinator is still alive; retire only that coordinator before adoption')
    partition = read(partition_path)
    cells, legacy = validate_partition(partition)
    sentinels = partition.get('sentinels', [])
    epoch = out / 'resume_epochs' / f'{int(time.time())}_{os.getpid()}'
    epoch.mkdir(parents=True)
    (epoch / 'partition.json').write_bytes(partition_path.read_bytes())
    (epoch / 'driver_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (epoch / 'cache_adapter.py').write_bytes((FROZEN_HELPERS / 'parallel_score_cache.py').read_bytes())
    cli = load('resume_frozen_scorer', SCORER)
    S = cli.S
    S.GOLD_DIR = str(REPO / 'external/veribench_scorer/veribench_dataset/lean_src/veribench')
    S.LAKE_DIR = str(RUN / 'grading')
    cache_helper.assert_frozen_scorer(S)
    gold = S.discover_gold_files(S.GOLD_DIR)
    goldidx = cli.build_gold_index(gold)
    expected_ids = cli.pack_task_ids(RUN / 'validation_pack')
    expected_keys = {cli.task_id_to_gold_key(tid, goldidx) for tid in expected_ids}
    require(len(expected_ids) == len(expected_keys) == 135 and None not in expected_keys, 'Frozen validation mapping differs')
    by_key = {cell['key']:cell for cell in cells}
    existing, unstarted = [], []
    observed_running = running_cell_processes(cells)
    for cell in cells:
        require(0 <= cell['sample'] < 8, 'Unexpected sample index')
        require(cli.task_id_to_gold_key(cell['task_id'], goldidx) == cell['gold_key'], 'Partition reference mapping differs')
        record_path = out / 'cells' / f'{cell["key"]}.json'
        record = read(record_path) if record_path.exists() else None
        if record:
            require(record.get('cell') == cell, 'Persisted cell differs from frozen partition')
            snapshot = epoch / 'original_cell_records' / record_path.name
            snapshot.parent.mkdir(exist_ok=True)
            snapshot.write_bytes(record_path.read_bytes())
        actual = observed_running.get(cell['key'])
        if actual:
            require(not record or record['state'] != 'COMPLETE', 'Completed cell still has an active scorer')
            existing.append((cell, record, actual))
        elif record is not None:
            existing.append((cell, record, None))
        else:
            require(not (out / 'logs' / f'{cell["key"]}.log').exists(),
                    f'Unrecorded attempted cell {cell["key"]}; do not infer it was never started')
            unstarted.append(cell)
    legacy_live = []
    legacy_ticks = {}
    for row in legacy:
        actual = proc(row['pid'])
        if actual and actual['state'] != 'Z':
            require('score_scsc.py' in actual['command'] and row['job'] in actual['command'], 'Legacy PID identity differs')
            if row.get('stage') and Path(row['stage']).is_file():
                stage = read(row['stage'])
                require(str(stage['start_ticks']) == actual['start_ticks'], 'Legacy PID start time differs')
            legacy_live.append((row['sample'], actual['start_ticks']))
            legacy_ticks[row['sample']] = actual['start_ticks']
    slots = Slots()
    reservations = slots.reserve_existing(len(observed_running) + len(legacy_live))
    legacy_slots, adopted_slots = {}, {}
    for sample, ticks in legacy_live:
        legacy_slots[sample] = reservations.pop()
    for key in observed_running:
        adopted_slots[key] = reservations.pop()
    require(not reservations, 'Unassigned adopted-process slot')
    write(epoch / 'adoption.json', dict(version=version, partition_sha256=sha(partition_path),
        retired_parallel_owner_pid=previous_pid, adopted_running=observed_running,
        legacy_running=legacy_live, existing_records=len(existing), unstarted=len(unstarted),
        driver_sha256=sha(__file__), adapter_sha256=sha(FROZEN_HELPERS / 'parallel_score_cache.py'),
        global_process_limit=32, compile_timeout_seconds=600, kernel_timeout_seconds=900,
        observed_unix=time.time()))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(REPO / 'src'),
        PATH=str(RUN / 'bin') + ':' + os.environ['PATH'], OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    for key in list(env):
        if any(marker in key for marker in ('API_KEY', 'AUTH_TOKEN', 'ACCESS_TOKEN', 'BEARER_TOKEN')):
            env.pop(key)
    pending = queue.Queue()
    for cell in sorted(unstarted, key=lambda item:(-item.get('source_size', 0), item['sample'], item['task_id'])):
        pending.put(cell)
    mutex = threading.Lock()
    completed, failures, active = {}, {}, {}
    prefix_rows, prefix_caches, boundary_done = {}, {}, set()

    def collect(cell, exit_code, exit_observed):
        destination = out / 'scores' / cell['key']
        csv_paths = list(destination.glob('*_per_task.csv'))
        require(len(csv_paths) == 1, 'Expected exactly one completed one-cell CSV')
        with csv_paths[0].open() as stream:
            matching = [record for record in csv.DictReader(stream) if record['gold_key'] == cell['gold_key']]
        require(len(matching) == 1, 'One-cell output reference missing/ambiguous')
        cachepath = destination / (Path(cell['job']).name + '_cache.json')
        cache = read(cachepath)
        require(cell['td'] in cache, 'One-cell cache lacks its measured task')
        tasks = S.discover_agent_tasks(cell['job'])
        require(set(tasks) == {cell['td']}, 'One-cell source view changed')
        source = tasks[cell['td']]
        require(sha(source) == cell['source_sha256'], 'One-cell evaluated source bytes changed')
        recovered = cache_helper.reconstruct_completed_cache(S, td_name=cell['td'], agent_lean_path=source,
            gold_info=gold[cell['gold_key']], gold_key=cell['gold_key'], cache_entry=cache[cell['td']],
            cache_path=str(cachepath), cache_file_sha256=sha(cachepath))
        csv_matches(recovered['row'], matching[0])
        require(not exit_observed or exit_code == 0, 'Observed scorer exit code was nonzero')
        result = dict(cell=cell, row=recovered['row'], cache=cache[cell['td']], state='COMPLETE',
            exit_code=exit_code, exit_status_observed=exit_observed,
            exit_status_note=None if exit_observed else 'Original parent retired; validated complete CSV and measured cache, process exit status unavailable.',
            reconstruction=recovered['provenance'], ended_unix=time.time())
        write(out / 'cells' / f'{cell["key"]}.json', result)
        with mutex:
            completed[cell['key']] = result
        return result

    def failed(cell, exc, where):
        result = dict(cell=cell, state='FAILED', error=repr(exc), location=where,
                      no_automatic_retry=True, ended_unix=time.time())
        write(out / 'cells' / f'{cell["key"]}.json', result)
        with mutex:
            failures[cell['key']] = result

    def adopt(cell, record, actual):
        slot = adopted_slots.get(cell['key'])
        key = cell['key']
        try:
            if actual:
                with mutex:
                    active[key] = dict(actual, kind='ADOPTED', slot=slot[1])
                while same_process(actual['pid'], actual['start_ticks']):
                    time.sleep(.5)
                collect(cell, None, False)
            else:
                observed = bool(record.get('exit_status_observed', record.get('exit_code') is not None))
                collect(cell, record.get('exit_code'), observed)
        except BaseException as exc:
            failed(cell, exc, 'adopt_existing')
        finally:
            if slot:
                slot[0].close()
            with mutex:
                active.pop(key, None)

    def worker(lane):
        while True:
            try:
                cell = pending.get_nowait()
            except queue.Empty:
                return
            key = cell['key']
            slot = slots.acquire()
            try:
                destination = out / 'scores' / key
                destination.mkdir(parents=True, exist_ok=True)
                log = out / 'logs' / f'{key}.log'
                log.parent.mkdir(exist_ok=True)
                command = scorer_command(cell, destination, S.GOLD_DIR, S.LAKE_DIR)
                with log.open('x') as stream:
                    process = subprocess.Popen(command, env=env, cwd=REPO, stdout=stream,
                        stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
                    identity = proc(process.pid)
                    require(identity is not None, 'New scorer PID disappeared before identity receipt')
                    info = dict(pid=process.pid, start_ticks=identity['start_ticks'], key=key,
                                slot=slot[1], kind='NEW', started_unix=time.time())
                    with mutex:
                        active[key] = info
                    write(out / 'cells' / f'{key}.json', dict(state='RUNNING', pid=process.pid,
                        start_ticks=identity['start_ticks'], command=command, cell=cell,
                        cpu_slot=slot[1], started_unix=info['started_unix'], resume_owner_pid=os.getpid()))
                    try:
                        code = process.wait(timeout=8 * 3600)
                    except subprocess.TimeoutExpired:
                        if same_process(process.pid, identity['start_ticks']):
                            os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            if same_process(process.pid, identity['start_ticks']):
                                os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        raise
                collect(cell, code, True)
            except BaseException as exc:
                failed(cell, exc, 'new_unstarted_cell')
            finally:
                slot[0].close()
                with mutex:
                    active.pop(key, None)
                pending.task_done()

    def preserve_prefix(row):
        sample = row['sample']
        cachepath = root / 'validation' / label / 'scores' / f'{label}_s{sample}' / f'{label}_s{sample}_cache.json'
        frozen = out / 'prefix_cache' / f's{sample}.json'
        frozen.parent.mkdir(exist_ok=True)
        if not frozen.exists():
            require(cachepath.is_file(), f'Legacy process exited without its finally cache: sample {sample}')
            shutil.copyfile(cachepath, frozen)
        boundary = out / 'boundaries' / f's{sample}.json'
        if boundary.exists():
            require(read(boundary)['cache_sha256'] == sha(frozen), 'Frozen prefix cache differs from prior boundary receipt')
        cached = read(frozen)
        rows, kept = [], {}
        try:
            for td in row['prefix']:
                task = cli.trial_task_id(Path(row['job']) / td)
                gk = cli.task_id_to_gold_key(task, goldidx)
                require(gk is not None, 'Legacy prefix reference identity differs')
                recovered = cache_helper.reconstruct_completed_cache(S, td_name=td,
                    agent_lean_path=row['tasks'][td], gold_info=gold[gk], gold_key=gk,
                    cache_entry=cached.get(td), cache_path=str(frozen), cache_file_sha256=sha(frozen))
                rows.append(recovered['row'])
                kept[td] = cached[td]
        finally:
            for sentinel in sentinels:
                if sentinel['sample'] == sample:
                    restore_sentinel(sentinel)
        prefix_rows[sample], prefix_caches[sample] = rows, kept
        write(boundary, dict(state='PREFIX_PRESERVED', cells=len(rows), cache_sha256=sha(frozen),
                            resume_owner_pid=os.getpid(), observed_unix=time.time()))

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=64)
    futures = [pool.submit(adopt, *item) for item in existing]
    futures += [pool.submit(worker, lane) for lane in range(32)]
    write(out / 'dispatch.json', dict(state='RUNNING', owner_pid=os.getpid(), version=version,
        mode='RESUME_ADOPT_32_SHARED_SLOTS', epoch=str(epoch), adopted_running=len(observed_running),
        legacy_running=len(legacy_live), max_total_workers=32, observed_unix=time.time()))
    owner_resumed = not legacy
    while any(not future.done() for future in futures) or len(boundary_done) < len(legacy):
        for row in legacy:
            sample = row['sample']
            if sample in boundary_done:
                continue
            if sample in legacy_ticks and same_process(row['pid'], legacy_ticks[sample]):
                continue
            try:
                preserve_prefix(row)
            except BaseException as exc:
                failures[f'prefix_{sample}'] = dict(state='FAILED', sample=sample, error=repr(exc), no_automatic_retry=True)
                write(epoch / f'prefix_{sample}_failure.json', failures[f'prefix_{sample}'])
            finally:
                boundary_done.add(sample)
                if sample in legacy_slots:
                    legacy_slots.pop(sample)[0].close()
        if len(boundary_done) == len(legacy) and not owner_resumed:
            owner = partition.get('owner_pid')
            actual = proc(owner) if owner else None
            if actual and actual['state'] != 'Z':
                require('recover_evaluation.py' in actual['command'], 'Paused original recovery owner identity differs')
                if actual['state'] == 'T':
                    os.kill(owner, signal.SIGCONT)
            write(epoch / 'original_recovery_owner_released.json', dict(pid=owner, after_all_legacy_finished=True,
                                                                         observed_unix=time.time()))
            owner_resumed = True
        with mutex:
            write(out / 'progress.json', dict(state='SCORING', owner_pid=os.getpid(), version=version,
                active=dict(active), new_active=sum(row['kind'] == 'NEW' for row in active.values()),
                adopted_active=sum(row['kind'] == 'ADOPTED' for row in active.values()),
                completed=len(completed), failed=len(failures), queued=pending.qsize(),
                prefix_shards_preserved=len(prefix_rows), legacy_still_running=len(legacy_slots),
                shared_process_limit=32, observed_unix=time.time()))
        time.sleep(1)
    pool.shutdown()
    for future in futures:
        future.result()
    require(not failures, f'Scoring measurements incomplete; no retries guessed: {list(failures)}')
    require(len(completed) == len(cells), 'Not every partition cell has a measured result')
    for sample in range(8):
        records = list(prefix_rows.get(sample, []))
        cache = dict(prefix_caches.get(sample, {}))
        owned = {row['task'] for row in records}
        for result in completed.values():
            if result['cell']['sample'] == sample:
                row = result['row']
                require(row['task'] not in owned, 'Duplicate measured sample/task during merge')
                owned.add(row['task'])
                records.append(row)
                cache[result['cell']['td']] = result['cache']
        require(len(records) == 135 and {row['gold_key'] for row in records} == expected_keys,
                'Canonical sample is not exactly the frozen 135 references')
        target = root / 'validation' / label / 'scores' / f'{label}_s{sample}'
        target.mkdir(parents=True, exist_ok=True)
        backup = epoch / 'original_score_outputs' / f's{sample}'
        backup.mkdir(parents=True)
        for path in target.iterdir():
            if path.is_file():
                shutil.copyfile(path, backup / path.name)
        records.sort(key=lambda row:row['task'])
        split_scores = {}
        for record in records:
            require(all(type(record[key]) in (int, float) for key in S.FACTOR_NAMES), 'Untyped CSV factor reached aggregation')
            split_scores.setdefault(record['split'], []).append({key:record[key] for key in S.FACTOR_NAMES})
        agg = cli.add_missing_zero_rows(S._aggregate(records, split_scores), RUN / 'validation_pack', gold)
        require(len(agg['per_task']) == 135 and agg['n_missing_output'] == 0, 'Merge inserted an unmeasured placeholder')
        destination = target / f'scsc_{label}_s{sample}_{label}_s{sample}_per_task.csv'
        temporary = destination.with_suffix('.csv.resume_tmp')
        with temporary.open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=sorted({key for row in agg['per_task'] for key in row}), lineterminator='\n')
            writer.writeheader(); writer.writerows(agg['per_task'])
        os.replace(temporary, destination)
        write(target / f'{label}_s{sample}_cache.json', cache)
        write(target / f'scsc_{label}_s{sample}_{label}_s{sample}.json', dict(
            row=cli.paper_row(f'{label}_s{sample}', agg), per_split=agg['per_split'], overall=agg['overall'],
            n_missing_output=0, mapping=dict(mapped=135, distinct=135, unmapped=[], no_config_json=[]),
            judge=dict(model='claude-sonnet-4-6', k=3, distribution=None),
            pack=str(RUN / 'validation_pack'), job_dir=str(root / 'validation' / label / 'jobs' / f'{label}_s{sample}'),
            reconstruction_epoch=str(epoch)))
    command = [PY, str(EXP / f'expt_v{version}' / 'summarize.py'), '--condition', 'base']
    with (out / 'analysis.log').open('w') as stream:
        subprocess.run(command, env=dict(env, TINY_RUN_ROOT=str(root)), check=True, stdout=stream, stderr=subprocess.STDOUT)
    summary = read(root / 'analysis' / f'{label}_summary.json')
    require(summary['declared_cells'] == summary['scored_cells'] == 1080, 'Frozen final analysis does not account for 1080 cells')
    write(out / 'terminal.json', dict(status='COMPLETE', declared_cells=1080, scored_cells=1080,
        partition_cells=len(completed), preserved_prefix_measurements=sum(map(len, prefix_rows.values())),
        adopted_exit_status_unobserved=sum(not result['exit_status_observed'] for result in completed.values()),
        epoch=str(epoch), driver_sha256=sha(__file__), cache_adapter_sha256=sha(FROZEN_HELPERS / 'parallel_score_cache.py'),
        global_process_limit=32, training_restarted=False, test_split_opened=False, ended_unix=time.time()))


def controls():
    import tempfile
    typed = dict(task='t', gold_key='g', IC_ap=0., IC_pp=0., TC=0., agent_compiles=False,
                 kernel_theorems=[dict(name='x')], optional=None, count=2)
    csv_matches(typed, dict(task='t', gold_key='g', IC_ap='0.0', IC_pp='0.0', TC='0.0',
        agent_compiles='False', kernel_theorems="[{'name': 'x'}]", optional='', count='2', missing_output=''))
    for recorded in (dict(task='different'), dict(task='t', missing_output='True')):
        try:
            csv_matches(typed, recorded)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid CSV control accepted')
    cells = [dict(key=f's{s}_{t}', sample=s, td=f't{t}') for s in range(8) for t in range(135)]
    validate_partition(dict(cells=cells, legacy=[], all_generated_cells=1080))
    prefixes = [dict(sample=s,prefix=[f't{t}' for t in range(10)]) for s in range(8)]
    validate_partition(dict(cells=[cell for cell in cells if int(cell['td'][1:]) >= 10], legacy=prefixes, all_generated_cells=1080))
    for invalid in (cells[:-1], cells[:-1]+[cells[0]]):
        try:
            validate_partition(dict(cells=invalid,legacy=[],all_generated_cells=1080))
        except ValueError:
            pass
        else:
            raise AssertionError('Incomplete/duplicate partition control accepted')
    with tempfile.TemporaryDirectory(prefix='scoring_slots_control_') as directory:
        slots = Slots(directory)
        held = slots.reserve_existing(5)
        held.extend(slots.acquire() for _ in range(27))
        require(slots._try() is None, 'Shared pool allowed a 33rd active slot')
        held.pop()[0].close()
        replacement = slots._try()
        require(replacement is not None and slots._try() is None, 'Freed shared slot was not refilled exactly once')
        held.append(replacement)
        for handle, _ in held:
            handle.close()
    print(json.dumps(dict(passed=True, typed_csv_roundtrip=True, rejection_controls=4,
                         fresh_v23_partition=True, legacy_prefix_partition=True, shared_32_slot_refill=True,
                         compiler_calls=0, model_calls=0, process_actions=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', type=int)
    parser.add_argument('--controls', action='store_true')
    args = parser.parse_args()
    if args.controls:
        controls()
    else:
        require(args.version is not None, '--version is required')
        try:
            main(args.version)
        except BaseException as exc:
            target = RUN / f'corpus_training_v{args.version}' / 'scoring_parallel_v1'
            if target.exists():
                write(target / f'resume_failure_{os.getpid()}.json', dict(status='FAILED', error=repr(exc),
                    owner_pid=os.getpid(), observed_unix=time.time(), no_automatic_retries=True))
            raise
