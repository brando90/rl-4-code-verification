"""Device monitoring must never turn busy/unknown hardware into an allocation."""
import copy
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/device_watch.py'
SPEC = importlib.util.spec_from_file_location('e13_device_watch', PATH)
WATCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WATCH)


def fixture():
    return {'host': 'fixture', 'checked_utc': 'fixture',
            'devices': '0, GPU-abc, A100, 81920, 0, 0\n1, GPU-def, A100, 81920, 30000, 0\n',
            'processes': 'GPU-def, 123, 30000\n', 'process_owners': {'123': 'another_owner'},
            'local_storage': {'total_bytes': 100, 'available_bytes': 10}}


def test_busy_zero_utilization_device_is_not_idle():
    out = WATCH.classify(fixture())
    assert out['idle_device_indices'] == [0]
    assert out['candidate_indices_pending_lease_checks'] == [0]
    assert out['device_claims'] == 0


@pytest.mark.parametrize('change', [
    {'processes': 'GPU-unknown, 123, 30\n'},
    {'process_owners': {}},
    {'devices': ''},
    {'devices': '0, GPU-abc, A100, 81920, 0, N/A\n'},
    {'devices': '0, GPU-abc, A100, 81920, 0, 0\n0, GPU-def, A100, 81920, 0, 0\n'},
    {'local_storage': {'total_bytes': 0, 'available_bytes': 0}},
])
def test_incomplete_inventory_is_rejected(change):
    raw = fixture(); raw.update(copy.deepcopy(change))
    with pytest.raises((ValueError, KeyError)):
        WATCH.classify(raw)


def test_low_storage_does_not_become_default_route():
    raw = fixture(); raw['local_storage']['available_bytes'] = 1
    out = WATCH.classify(raw)
    assert out['idle_device_indices'] == [0]
    assert not out['default_storage_headroom']
    assert out['candidate_indices_pending_lease_checks'] == []
