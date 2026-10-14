"""Compare prospective bounds to exhaustive synthetic target completions."""
import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import pearsonr
from scipy.stats import spearmanr, kendalltau, rankdata

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


def test_failed_candidate_still_reports_available_strict_model():
    y=np.array([0.,1.,0.,1.,0.,1.]);p=np.array([.1,.8,.3,.7,.2,.9])
    result=MOD.assess_g1_a3(y,{'selected':np.full(6,np.nan),'M0':p,'M1':p,'M2':p},
                           ['a','a','b','b','c','c'],['small','small','mid','mid','large','large'],
                           implementation_admitted=False,draws=11)
    assert result['status']=='INCONCLUSIVE' and result['disable_arm_C']
    assert 'log_loss' in result['metrics']['M2']
    assert result['metrics']['selected']['status']=='UNAVAILABLE'


@pytest.mark.parametrize('metric', ['auc', 'pearson', 'spearman', 'kendall'])
@pytest.mark.parametrize('p', [[.1, .1, .5, .5, .9, .9], [.5]*6, [.1,.2,.3,.4,.5,.6]])
def test_nonlinear_point_bounds_match_all_binary_completions(metric, p):
    y = np.array([0., np.nan, np.nan, 1., np.nan, 0.])
    out = MOD.bound_binary_association(y, p, metric)
    values = []
    for c in completions(y):
        if metric == 'auc':
            k = c.sum(); v = (rankdata(p)[c == 1].sum()-k*(k+1)/2)/(k*(len(c)-k))
        elif np.ptp(p) == 0: continue
        else: v = {'pearson': pearsonr, 'spearman': spearmanr, 'kendall': kendalltau}[metric](c, p).statistic
        values.append(v)
    if values:
        assert out['minimum'] == pytest.approx(min(values), abs=1e-12)
        assert out['maximum'] == pytest.approx(max(values), abs=1e-12)
    else:
        assert out['minimum'] is None and out['undefined_possible']


@pytest.mark.parametrize('metric', ['auc', 'pearson', 'spearman', 'kendall'])
def test_bootstrap_relaxation_encloses_consistent_cell_completions(metric):
    y = np.array([0., np.nan, 1., np.nan, 0., 1.]); p = np.array([.1,.4,.8,.3,.2,.9])
    groups = np.array(['a','a','b','b','c','c'])
    bound = MOD.bound_association_interval(y, p, groups, metric, draws=41)
    for complete in completions(y):
        exact = MOD.bound_association_interval(complete, p, groups, metric, draws=41)
        for key in ('bootstrap_lower_endpoint_range', 'bootstrap_upper_endpoint_range'):
            assert bound[key][0] <= exact[key][0]+1e-12 <= exact[key][1]+1e-12 <= bound[key][1]+2e-12
