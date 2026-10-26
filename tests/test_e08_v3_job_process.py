"""Check exact child adoption and full-cell completion across scheduler replacement."""
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import os
import signal
import time

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_job_process', HERE / 'job_process.py')
jobs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jobs)


def test_generation_requires_exact_cells(tmp_path):
    path = tmp_path / 'ladder/validation/raw/gen_demo_g8.jsonl'
    path.parent.mkdir(parents=True)
    rows = [{'task_id': 't', 'sample_idx': i} for i in range(8)]
    for bad in [rows[:-1], rows + rows[:1], rows[:-1] + [{'task_id': 'extra', 'sample_idx': 7}]]:
        path.write_text(''.join(json.dumps(r) + '\n' for r in bad))
        assert not jobs.generation_complete(tmp_path, 'demo', ['t'])
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    assert jobs.generation_complete(tmp_path, 'demo', ['t'])


def test_live_adopted_child_not_completed_by_old_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, 'alive', lambda _: True)
    job = {'pid': 1, 'identity': {'pid': 1}, 'key': 'train_E_4b'}
    assert jobs.AdoptedProcess(job, tmp_path, []).poll() is None


def test_exit_requires_matching_start_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, 'alive', lambda _: False)
    receipt = tmp_path / 'exit.json'
    job = {'pid': 1, 'identity': {'pid': 1, 'start_ticks': 'new'},
           'key': 'train_E_4b', 'exit_receipt': str(receipt)}
    receipt.write_text(json.dumps({'identity': {'pid': 1, 'start_ticks': 'old'}, 'exit_code': 0}))
    assert jobs.AdoptedProcess(job, tmp_path, []).poll() == 125
    receipt.write_text(json.dumps({'identity': job['identity'], 'exit_code': 3}))
    assert jobs.AdoptedProcess(job, tmp_path, []).poll() == 3


def test_legacy_generation_adopted_only_after_exact_merge(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, 'alive', lambda _: False)
    job = {'pid': 1, 'identity': {'pid': 1}, 'key': 'gen_demo'}
    process = jobs.AdoptedProcess(job, tmp_path, ['t'])
    assert process.poll() == 125
    path = tmp_path / 'ladder/validation/raw/gen_demo_g8.jsonl'
    path.parent.mkdir(parents=True)
    path.write_text(''.join(json.dumps({'task_id': 't', 'sample_idx': i}) + '\n' for i in range(8)))
    assert process.poll() == 0


def test_detached_job_survives_scheduler_session_hangup(tmp_path):
    receipt = tmp_path / 'job.exit.json'
    parent_code = '''import subprocess,sys,time
p=subprocess.Popen(sys.argv[1:], start_new_session=True, stdout=subprocess.DEVNULL)
print(p.pid, flush=True)
time.sleep(20)
'''
    parent = subprocess.Popen([sys.executable, '-c', parent_code, sys.executable, str(HERE / 'job_process.py'),
                               '--receipt', str(receipt), '--', sys.executable, '-c', 'import time; time.sleep(.2)'],
                              stdout=subprocess.PIPE, text=True, start_new_session=True)
    try:
        child_pid = int(parent.stdout.readline())
        os.killpg(parent.pid, signal.SIGHUP)
        parent.wait(timeout=5)
        for _ in range(100):
            if receipt.exists() and 'exit_code' in json.loads(receipt.read_text()):
                break
            time.sleep(.02)
        result = json.loads(receipt.read_text())
        assert result['identity']['pid'] == child_pid
        assert result['exit_code'] == 0
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait()
