"""Require completed preflight and eight free devices before remote TP8 admission."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_remote_training', HERE / 'remote_training.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'SHARED', tmp_path)
    monkeypatch.setattr(m.socket, 'gethostname', lambda: 'skampere2.stanford.edu')
    (tmp_path / 'sft_v3').mkdir()
    monkeypatch.setattr(m.subprocess, 'Popen', lambda *a, **k: (_ for _ in ()).throw(AssertionError('unexpected launch')))
    return argparse.Namespace(condition='E', probe=False)


def test_partial_environment_never_launches(tmp_path, monkeypatch, capsys):
    args = setup(tmp_path, monkeypatch)
    assert m.remote(args) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'WAITING_PREFLIGHT'


def test_busy_device_prevents_full_node_admission(tmp_path, monkeypatch, capsys):
    args = setup(tmp_path, monkeypatch)
    (tmp_path / 'sft_v3/remote_ready.json').write_text(json.dumps({'status': 'PASS', 'verified_hosts': ['skampere2']}))
    def query(command, **kwargs):
        output = 'GPU-0\n' if 'apps' in command[1] else ''.join(f'{i}, 140000, GPU-{i}\n' for i in range(8))
        return subprocess.CompletedProcess(command, 0, output, '')
    monkeypatch.setattr(m.subprocess, 'run', query)
    assert m.remote(args) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'WAITING_DEVICES'


def test_existing_remote_record_fences_relaunch(tmp_path, monkeypatch, capsys):
    args = setup(tmp_path, monkeypatch)
    record = {'status': 'RUNNING', 'identity': {'pid': 12, 'start_ticks': 'known'}, 'host': 'skampere2'}
    (tmp_path / 'sft_v3/remote_E_14b.json').write_text(json.dumps(record))
    assert m.remote(args) == 0
    assert json.loads(capsys.readouterr().out) == record


def test_priority_replay_preserves_one_device_layout(tmp_path, monkeypatch, capsys):
    args = setup(tmp_path, monkeypatch); args.size = '1p7b'; args.condition = 'R'
    (tmp_path / 'sft_v3/remote_ready.json').write_text(json.dumps({
        'status': 'PASS', 'verified_hosts': ['skampere2'], 'verified_sizes': ['1p7b'],
        'host_environments': {'skampere2': '/owned/verified/nemo_rl'}}))
    def query(command, **kwargs):
        output = 'GPU-0\nGPU-1\n' if 'apps' in command[1] else ''.join(f'{i}, 140000, GPU-{i}\n' for i in range(8))
        return subprocess.CompletedProcess(command, 0, output, '')
    monkeypatch.setattr(m.subprocess, 'run', query)
    from types import SimpleNamespace
    monkeypatch.setattr(m.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=2000, f_frsize=1024**3))
    launched = []
    monkeypatch.setattr(m.subprocess, 'Popen', lambda command, **kwargs: launched.append((command, kwargs)) or SimpleNamespace(pid=42))
    monkeypatch.setattr(m, 'identity', lambda _: {'pid': 42, 'boot_id': 'boot', 'start_ticks': '123'})
    assert m.remote(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['gpus'] == '2' and result['tensor_parallel_size'] == 1
    assert launched[0][0][-3:] == ['R', '1p7b', '2']
    assert launched[0][1]['env']['E08_NEMO_ROOT'] == '/owned/verified/nemo_rl'
    assert launched[0][1]['env']['CUDA_VISIBLE_DEVICES'] == '2'
    assert launched[0][1]['env']['E08_CACHE_ROOT'] == '/owned/verified/cache'
