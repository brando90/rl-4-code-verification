"""Compare prospective bounds to exhaustive synthetic target completions."""
import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import pearsonr

PATH = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/g1_bounds.py'
SPEC = importlib.util.spec_from_file_location('e13_g1_bounds', PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def completions(y):
    holes = np.isnan(y)
    for bits in itertools.product((0, 1), repeat=int(holes.sum())):
        out = y.copy(); out[holes] = bits; yield out


@pytest.mark.parametrize('metric', ['log_loss', 'log_loss_contrast', 'mean_bias',
                                    'mean_absolute_error', 'brier', 'predicted_mean', 'observed_mean'])
def test_linear_point_and_interval_extrema_match_full_enumeration(metric):
    y = np.array([0, np.nan, 1, np.nan, np.nan, 0.])
    p = np.array([.1, .3, .9, .7, .5, .2]); baseline = 1-p
    groups = np.array(['a', 'b', 'b', 'c', 'd', 'd'])
    a, b = MOD.coefficients(p, metric, baseline)
    bound, _ = MOD.bound_linear(y, a, b, groups, draws=101)
    complete = [MOD.bound_linear(c, a, b, groups, draws=101)[0] for c in completions(y)]
    assert bound['minimum'] == pytest.approx(min(c['minimum'] for c in complete))
    assert bound['maximum'] == pytest.approx(max(c['maximum'] for c in complete))
    for key in ('bootstrap_lower_endpoint_range', 'bootstrap_upper_endpoint_range'):
        assert bound[key] == pytest.approx([min(c[key][0] for c in complete), max(c[key][1] for c in complete)])


def test_policy_mean_integer_search_matches_cell_completions():
    y = np.array([0, np.nan, 1, np.nan, np.nan, 0.])
    p = np.array([.1, .1, .7, .7, .3, .3]); policies = np.repeat(['a', 'b', 'c'], 2)
    out = MOD.bound_policy_pearson(y, p, policies)
    values = []
    for c in completions(y):
        means = c.reshape(3, 2).mean(axis=1)
        if np.ptp(means): values.append(pearsonr(means, p.reshape(3, 2).mean(axis=1)).statistic)
    assert out['minimum'] == pytest.approx(min(values))
    assert out['maximum'] == pytest.approx(max(values))
    assert out['undefined_possible']
    outer = MOD.bound_policy_pearson(y, p, policies, limit=1)
    assert not outer['exact'] and outer['minimum'] <= out['minimum'] <= out['maximum'] <= outer['maximum']


def test_missing_predictions_are_never_imputed():
    with pytest.raises(ValueError):
        MOD.bound_policy_pearson([0, 1, np.nan], [.1, np.nan, .2], ['a', 'b', 'c'])
