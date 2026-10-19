"""Resume saved diagnostic responses with twelve workers; preserve the frozen scorer."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'expt_v6')]
import run_jobs as jobs
import check_diagnostic as checker

def main():
    root = checker.ROOT
    execution = jobs.RUN / 'execution/diagnostic_seen_fresh_v7'
    identity = json.loads((root / 'model_identity.json').read_text())
    expected = identity['source_hashes']['check_diagnostic.py']
    assert hashlib.sha256((HERE / 'check_diagnostic.py').read_bytes()).hexdigest() == expected
    if '--worker' in sys.argv:
        executor = concurrent.futures.ThreadPoolExecutor
        def pool(*args, **kwargs):
            kwargs['max_workers'] = 12
            return executor(*args, **kwargs)
        checker.concurrent = SimpleNamespace(futures=SimpleNamespace(
            ThreadPoolExecutor=pool, as_completed=concurrent.futures.as_completed))
        checker.await_capacity = lambda: None
        sys.argv = [sys.argv[0]]
        checker.main()
        return
    old_path = execution / 'checking_cpu_admission.json'
    old = json.loads(old_path.read_text())
    assert old['status'] == 'RUNNING', old
    pid = old['pid']
    stat = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
    assert stat[19] == old['start_ticks'] and os.getpgid(pid) == pid
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == old['boot_id']
    before = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (root / 'checks').glob('*/result.json')}
    jobs.write(root / 'parallel_transition.json', dict(
        status='TRANSITION', requested_workers=12, prior_workers=2,
        reason='user requested greater parallelism; resource admission only',
        observed_unix=time.time(), preserved_results=before,
        cpu_count=os.cpu_count(), load_average=os.getloadavg(),
        meminfo=Path('/proc/meminfo').read_text(),
        scorer_sha256=expected,
        raw_sha256=hashlib.sha256((root / 'raw.jsonl').read_bytes()).hexdigest()))
    os.killpg(pid, signal.SIGTERM)
    deadline = time.monotonic() + 20
    while json.loads(old_path.read_text())['status'] == 'RUNNING':
        assert time.monotonic() < deadline, 'previous coordinator did not record terminal state'
        time.sleep(.2)
    archived = []
    for folder in (root / 'checks').iterdir():
        if folder.is_dir() and not (folder / 'result.json').exists():
            target = root / 'parallel_transition_interrupted' / folder.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(folder), str(target))
            archived.append(folder.name)
    for tid, digest in before.items():
        assert hashlib.sha256((root / 'checks' / tid / 'result.json').read_bytes()).hexdigest() == digest
    original = json.loads((execution / 'checking.json').read_text())
    remaining = original['started_unix'] + 7200 - time.time()
    assert remaining > 0
    jobs.write(root / 'parallel_continuation.json', dict(
        workers=12, completed_preserved=len(list((root / 'checks').glob('*/result.json'))),
        interrupted_archived=archived, retry_reason='infrastructure worker resize only',
        original_deadline_unix=original['started_unix'] + 7200,
        scoring_and_generation_unchanged=True))
    jobs.write(root / 'status.json', dict(phase='CHECKING', workers=12, updated_unix=time.time()))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
               TINY_RUN_ROOT=str(jobs.RUN), PATH=str(jobs.RUN / 'bin') + ':' + os.environ['PATH'])
    try:
        jobs.run_stage('diagnostic_seen_fresh_v7', 'checking_parallel12',
                       [jobs.PYTHON, str(HERE / 'parallel_checking.py'), '--worker'], env, remaining)
        summary = json.loads((root / 'summary.json').read_text())
        jobs.write(root / 'status.json', dict(phase=summary['status'], workers=12,
                   updated_unix=time.time(), summary=str(root / 'summary.json')))
    except BaseException as exc:
        jobs.write(root / 'status.json', dict(phase='FAILED', updated_unix=time.time(), error=repr(exc)))
        raise

if __name__ == '__main__':
    main()
