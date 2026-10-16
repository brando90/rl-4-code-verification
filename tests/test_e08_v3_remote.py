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
        output = '12345\n' if 'apps' in command[1] else ''.join(f'{i}, 140000\n' for i in range(8))
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
