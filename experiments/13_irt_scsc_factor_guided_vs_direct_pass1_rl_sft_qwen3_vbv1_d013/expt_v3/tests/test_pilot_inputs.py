"""Verify identical A/B/P task and rollout streams, fixed placebo draws, and training split exclusion."""
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'phase2'))
from pilot_inputs import prefix


def templates():
    return {f't{i:03d}': {'task_id': f't{i:03d}', 'split': 'train', 'prompt_token_ids': [1, 2]}
            for i in range(539)}


def test_paired_prompt_and_rollout_streams():
    pool = templates()
    runs = {arm: prefix(arm, 1301, 1, pool, [0., .1, .5]) for arm in ('A', 'B', 'P')}
    expected = [(c['task_id'], c['sample'], c['seed'], c['group_index']) for c in runs['A'][1]]
    assert len(expected) == 256
    for arm in ('B', 'P'):
        assert [(c['task_id'], c['sample'], c['seed'], c['group_index']) for c in runs[arm][1]] == expected
    assert runs['P'] == prefix('P', 1301, 1, pool, [0., .1, .5])
    assert all(p['placebo_draws'] is None for p in runs['B'][0])
    assert all(len(p['placebo_draws']) == 8 for p in runs['P'][0])


def test_update_advances_cumulative_group_stream():
    plans, cells = prefix('B', 1302, 2, templates(), [0.])
    assert [p['group_index'] for p in plans] == list(range(32, 64))
    assert len({c['cell_id'] for c in cells}) == 256


def test_heldout_prompt_rejected():
    pool = templates(); pool['t000']['split'] = 'validation'
    with pytest.raises(ValueError): prefix('B', 1301, 1, pool, [0.])


def test_only_b_has_extension():
    with pytest.raises(ValueError): prefix('A', 1301, 31, templates(), [0.])
    with pytest.raises(ValueError): prefix('P', 1301, 31, templates(), [0.])
    assert len(prefix('B', 1301, 60, templates(), [0.])[1]) == 256
