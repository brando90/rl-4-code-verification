"""Check reward substitution, missing-group masking and rejection of corrupt paired identities."""
import copy
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'phase2/cohort.py'
spec = importlib.util.spec_from_file_location('v3_cohort', PATH)
cohort = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cohort)


def fixture():
    rows = [dict(cell_id=f'g/{i}', task_id='t', split='train', sample=i, slot=i,
                 group_index=0, arm='technical', run_seed=1302201, update=1, reward=0.)
            for i in range(8)]
    scores = [{**r, 'status': 'measured', 'strict': 0., 'factored_reward': .5 if i == 0 else 0.}
              for i, r in enumerate(rows)]
    return [{'group_index': 0, 'task_id': 't', 'rows': rows}], scores


def test_only_reward_and_status_change():
    groups, scores = fixture()
    saved = copy.deepcopy(groups)
    result, summary = cohort.factored_groups(groups, scores)
    assert groups == saved
    assert [r['reward'] for r in result[0]['rows']] == [.5] + [0.] * 7
    assert summary['active_groups'] == 1
    assert summary['nonzero_advantage_slots'] == 8
    for before, after in zip(groups[0]['rows'], result[0]['rows']):
        assert {k: v for k, v in before.items() if k != 'reward'} == {
            k: v for k, v in after.items() if k not in ('reward', 'score_status')}


def test_missing_score_kept_and_whole_group_masked():
    groups, scores = fixture()
    scores[2].update(status='resource_limit', factored_reward=None)
    result, summary = cohort.factored_groups(groups, scores)
    assert result[0]['rows'][2]['reward'] is None
    assert summary['declared_slots'] == 8
    assert summary['measured_rewards'] == 7
    assert summary['usable_groups'] == summary['active_groups'] == summary['nonzero_advantage_slots'] == 0


@pytest.mark.parametrize('value', [None, True, float('nan'), float('inf'), -.1, 1.1, '0.5'])
def test_bad_measured_reward_rejected(value):
    groups, scores = fixture()
    scores[0]['factored_reward'] = value
    with pytest.raises(ValueError): cohort.factored_groups(groups, scores)


@pytest.mark.parametrize('change', ['duplicate', 'missing', 'task', 'split', 'sample'])
def test_identity_corruption_rejected(change):
    groups, scores = fixture()
    if change == 'duplicate': scores.append(scores[0])
    elif change == 'missing': scores.pop()
    elif change == 'task': scores[0]['task_id'] = 'other'
    elif change == 'split': scores[0]['split'] = 'validation'
    else: scores[0]['sample'] = 2
    with pytest.raises(ValueError): cohort.factored_groups(groups, scores)


def test_constant_positive_reward_has_zero_advantage():
    groups, scores = fixture()
    for row in scores: row['factored_reward'] = .5
    _, summary = cohort.factored_groups(groups, scores)
    assert summary['positive_rewards'] == 8
    assert summary['active_groups'] == summary['nonzero_advantage_slots'] == 0
