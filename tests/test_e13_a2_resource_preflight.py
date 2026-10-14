"""Validate the exact page representation of A2's unchanged resource cap without historical data."""
import importlib.util
import json
from pathlib import Path

import pytest

V2 = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2'
spec = importlib.util.spec_from_file_location('e13_a2_resource_test', V2 / 'reproduction/a2_resource_launcher.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


@pytest.mark.parametrize('requested,actual,page', [(8192, 8192, 4096), (10240, 8192, 4096),
                                                   (1044624427008, 1044624424960, 4096)])
def test_exact_kernel_page_representation(requested, actual, page):
    assert runtime.validate_memory_limit(requested, actual, page) == actual


@pytest.mark.parametrize('actual', [4096, 10240, 12288])
def test_changed_limit_is_never_admitted(actual):
    with pytest.raises(RuntimeError, match='effective A2 memory limit changed'):
        runtime.validate_memory_limit(10240, actual, 4096)


def test_only_resource_representation_error_is_handled(tmp_path, monkeypatch):
    lock = {'requested_memory_max_bytes': 10240, 'effective_memory_max_bytes': 8192, 'page_size': 4096}
    monkeypatch.setattr(runtime, 'verify_supplement', lambda: lock)
    monkeypatch.setattr(runtime, 'kernel_memory_limit', lambda: 8192)
    monkeypatch.setattr(runtime.os, 'sysconf', lambda _: 4096)
    (tmp_path / 'execution_lock.json').write_text(json.dumps({'aggregate_memory_max_bytes': 10240}))
    def fail_resource(_):
        raise RuntimeError(runtime.RESOURCE_ERROR)
    monkeypatch.setattr(runtime, 'ORIGINAL_VERIFY', fail_resource)
    assert runtime.verify_bindings(tmp_path) == {'aggregate_memory_max_bytes': 10240}
    def fail_integrity(_):
        raise RuntimeError('frozen implementation/input changed')
    monkeypatch.setattr(runtime, 'ORIGINAL_VERIFY', fail_integrity)
    with pytest.raises(RuntimeError, match='frozen implementation/input changed'):
        runtime.verify_bindings(tmp_path)


def test_wrong_effective_cap_after_original_check_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, 'verify_supplement', lambda: {
        'requested_memory_max_bytes': 8192, 'effective_memory_max_bytes': 8192, 'page_size': 4096})
    monkeypatch.setattr(runtime, 'ORIGINAL_VERIFY', lambda _: {'aggregate_memory_max_bytes': 8192})
    monkeypatch.setattr(runtime, 'kernel_memory_limit', lambda: 12288)
    monkeypatch.setattr(runtime.os, 'sysconf', lambda _: 4096)
    with pytest.raises(RuntimeError, match='effective A2 memory limit changed'):
        runtime.verify_bindings(tmp_path)


def test_route_uses_original_reconciliation_without_replacing_measurement(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, 'verify_supplement', lambda: {})
    calls = []
    def reconcile(route, resume):
        calls.append((route, resume))
        assert runtime.a2.verify_bindings is runtime.verify_bindings
        return {'admitted': True}
    monkeypatch.setattr(runtime.a2, 'reconcile_route', reconcile)
    monkeypatch.setattr(runtime.a2, 'verify_bindings', runtime.a2.verify_bindings)
    assert runtime.main(['--route', 'opaque', '--resume']) == 0
    assert calls == [('opaque', True)]
