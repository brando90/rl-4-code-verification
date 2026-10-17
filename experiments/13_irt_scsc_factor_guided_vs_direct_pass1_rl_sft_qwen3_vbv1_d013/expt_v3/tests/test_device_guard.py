"""Reject protected GPUs, online mode and foreign GPU occupants before model construction."""
import importlib.util
import json
import os
from pathlib import Path
import time
import pytest

PATH = Path(__file__).resolve().parents[1] / 'phase2/device_guard.py'
spec = importlib.util.spec_from_file_location('v3_device_guard', PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def setup(tmp_path, monkeypatch, device=0):
    lease = dict(owner='e13v3', status='ACTIVE', index=device, id='unit-test', uuid='GPU-unit',
                 expires_unix=time.time() + 60)
    path = tmp_path / 'lease.json'
    path.write_text(json.dumps(lease))
    monkeypatch.setattr(guard.socket, 'gethostname', lambda: 'skampere1.stanford.edu')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', str(device))
    monkeypatch.setenv('HF_HUB_OFFLINE', '1')
    monkeypatch.setenv('E13_EXECUTION_ID', 'unit-test')
    return {'lease_path': str(path)}


@pytest.mark.parametrize('device', [1, 2, 3, 4, 6])
def test_protected_devices(tmp_path, monkeypatch, device):
    config = setup(tmp_path, monkeypatch, device)
    with pytest.raises(RuntimeError, match='invalid offline'): guard.check(config)


def test_offline_required(tmp_path, monkeypatch):
    config = setup(tmp_path, monkeypatch)
    monkeypatch.setenv('HF_HUB_OFFLINE', '0')
    with pytest.raises(RuntimeError, match='invalid offline'): guard.check(config)


def test_uuid_mapping_required(tmp_path, monkeypatch):
    config = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(guard.subprocess, 'check_output', lambda *a, **k: '0, GPU-other\n')
    with pytest.raises(RuntimeError, match='mapping changed'): guard.check(config)


def test_foreign_process_rejected(tmp_path, monkeypatch):
    config = setup(tmp_path, monkeypatch)
    replies = iter(['0, GPU-unit\n', f'GPU-unit, {os.getpid()}\n'])
    monkeypatch.setattr(guard.subprocess, 'check_output', lambda *a, **k: next(replies))
    # /proc captures the actual process-launch environment, which has no unit-test marker.
    with pytest.raises(RuntimeError, match='foreign process'): guard.check(config)
