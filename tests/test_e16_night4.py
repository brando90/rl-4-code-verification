"""Night 4 (expt_v4): alpha construction, strength rule, law+alpha fit and regret bookkeeping."""
from importlib import import_module
import numpy as np
import pytest

torch = pytest.importorskip('torch')
n4 = import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v4.night4')
from rl4cv.utility_model import Observation


def test_alpha_is_mean_of_within_scale_zscores():
    cos, drop = [0.1, 0.2, 0.3], [3.0, 1.0, 2.0]
    a = n4.alpha_from_components(cos, drop)
    assert np.allclose(a, 0.5 * (n4.zscore(cos) + n4.zscore(drop)))
    assert np.isclose(a.mean(), 0)
    assert np.allclose(n4.zscore([1.0, 1.0]), 0)


def test_f_ratio_large_when_envs_differ_and_seeds_agree():
    clear = {'a': [0.0, 0.01], 'b': [1.0, 1.01], 'c': [2.0, 2.01]}
    noisy = {'a': [0.0, 1.0], 'b': [1.0, 0.0], 'c': [0.5, 0.5]}
    assert n4.f_ratio(clear)[0] > 1000 > n4.f_ratio(noisy)[0]


def test_law_alpha_recovers_alpha_coefficient():
    rng = np.random.default_rng(0)
    obs, alpha = [], {}
    for scale in (100., 1000., 10000.):
        for j in range(12):
            e = f'e{j}'
            rho, H, a = float(np.exp(rng.normal())), float(rng.uniform()), float(rng.normal())
            alpha[scale, e] = a
            for b in (10., 20., 40.):
                obs.append(Observation(scale, e, b, 0.5 * a, rho, H))
    model, predict = n4.fit_law_alpha(obs, alpha, (100., 10000.))
    assert model['beta'][-1] * 1 / model['a_sd'] == pytest.approx(0.5, rel=1e-6)
    o = obs[0]
    assert predict(o.scale, o.budget, o.rho, o.H, alpha[o.scale, o.env]) == pytest.approx(o.utility, abs=1e-9)


def test_regret_averages_ties_and_budgets():
    util = {'a': [1.0, 0.0, 0.0], 'b': [0.0, 1.0, 1.0]}
    ch = {'pick-a': {str(b): ['a'] for b in n4.BUDGETS}, 'both': {str(b): ['a', 'b'] for b in n4.BUDGETS}}
    r = n4.regrets(ch, util, ['a', 'b'])
    assert r['pick-a'] == pytest.approx(2 / 3)
    assert r['both'] == pytest.approx(0.5)


def test_alpha_probe_runs_on_a_tiny_model():
    torch.manual_seed(0)
    model = n4.pol.TinyLM(*n4.SCALES['n1'])
    row = n4.alpha_probe(model, n4.g.BASE[0], n4.SETTINGS['S1'])
    assert -1 <= row['grad_cos'] <= 1
    assert np.isfinite(row['dev_nll_drop']) and len(row['dev_nll_drop_per_seed']) == 2
    assert row['probe_generated_tokens'] == 256 * 8 * 4 + 2 * 10 * 16 * 8 * 4
