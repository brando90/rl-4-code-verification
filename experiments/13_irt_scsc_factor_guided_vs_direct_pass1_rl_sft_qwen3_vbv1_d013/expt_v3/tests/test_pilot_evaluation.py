"""Preserve pilot identities, historical evaluation seeds, and missing outcomes."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'phase2'))
from pilot_evaluation import identities, summarize


def population(**kwargs):
    return identities([f't{i:03d}' for i in range(135)], 'validation',
                      **({'arm': 'B', 'run_seed': 1301, 'boundary': 30} | kwargs))


def test_complete_pilot_validation_population():
    cells = population()
    assert len(cells) == len({c['cell_id'] for c in cells}) == 1080
    assert {c['seed'] for c in cells} == {91 * 100003 + i for i in range(8)}
    assert {c['run_seed'] for c in cells} == {1301}
    assert {c['boundary'] for c in cells} == {30}
    assert {c['cell_id'] for c in cells}.isdisjoint(c['cell_id'] for c in population(run_seed=1302))


@pytest.mark.parametrize('kwargs', [{'run_seed': 13011}, {'boundary': 1}, {'arm': 'C'}, {'arm': 'A', 'boundary': 60}])
def test_unregistered_pilot_conditions_rejected(kwargs):
    with pytest.raises(ValueError): population(**kwargs)


def test_sealed_test_is_not_admitted():
    with pytest.raises(ValueError):
        identities([f't{i:03d}' for i in range(135)], 'test', arm='B', run_seed=1301, boundary=30)


def test_unknown_strict_and_coverage_stay_missing():
    cells = population()
    rows = [{**c, 'strict': None if i == 0 else 0} for i, c in enumerate(cells)]
    result = summarize({'cells': cells}, {'rows': rows})
    assert result['missing'] == 1 and result['measured'] == 1079
    assert result['strict_mean_bounds'] == [0, 1 / 1080]
    assert result['official_SCSC'] is None
    assert result['task_bootstrap_95_interval'] is None


def test_bootstrap_respects_frozen_groups():
    cells = [{**c, 'group_id': str(i // 16)} for i, c in enumerate(population())]
    rows = [{**c, 'strict': i % 2} for i, c in enumerate(cells)]
    result = summarize({'cells': cells}, {'rows': rows})
    assert result['resampling_groups'] == 68
    assert result['strict_mean_observed'] == .5
    assert result['task_bootstrap_95_interval'] == [.5, .5]
