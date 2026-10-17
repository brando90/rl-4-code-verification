"""Reject sparse or misidentified pilot summaries and retain exact A6 reward and extension thresholds."""
import importlib.util
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / 'phase2/pilot_metrics.py'
spec = importlib.util.spec_from_file_location('v3_pilot_metrics', PATH)
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def rows(horizon=30, gain=.02):
    return [dict(arm='B', seed=seed, update=i, split='train',
                 rewards=[.1 if i <= 10 else .1 + gain] * 256)
            for seed in (1301, 1302) for i in range(1, horizon + 1)]


def test_exact_continuous_threshold():
    data = rows()
    for r in data:
        if r['update'] > 10: r['rewards'] = [.12] * 256
    result = metrics.t5(data, horizon=30)
    assert result['status'] == 'PASS'
    assert result['seeds']['1301']['improvement_bounds'] == [.02, .02]


def test_missing_values_cannot_manufacture_pass():
    data = rows()
    data[0]['rewards'] = [None] * 256
    assert metrics.t5(data, horizon=30)['status'] == 'EXTEND_TO_60'


def test_one_extension_then_failure():
    assert metrics.t5(rows(gain=0), horizon=30)['status'] == 'EXTEND_TO_60'
    assert metrics.t5(rows(60, gain=0), horizon=60)['status'] == 'FAIL'
    with pytest.raises(ValueError): metrics.t5(rows(), horizon=90)


def test_replication_cannot_rescue_failed_gating_seed():
    data = rows(gain=0)
    for r in data:
        if r['seed'] == 1302 and r['update'] > 10: r['rewards'] = [.9] * 256
    result = metrics.t5(data, horizon=30)
    assert result['status'] == 'EXTEND_TO_60'
    assert result['seeds']['1302']['status'] == 'PASS'


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'strict_arm', 'validation'])
def test_full_paired_train_inventory_required(change):
    data = rows()
    if change == 'missing': data.pop()
    elif change == 'duplicate': data[-1] = data[0]
    elif change == 'strict_arm': data[0]['arm'] = 'A'
    else: data[0]['split'] = 'validation'
    with pytest.raises(ValueError): metrics.t5(data, horizon=30)
