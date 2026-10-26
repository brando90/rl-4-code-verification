"""TLDR: Unit tests for experiment 20's IRT layer: the binomial-count objective matches finite differences and recovers simulated item parameters, the 1PL holds slopes at one, grouped cell folds and task folds keep groups together, prior selection and gate G0 run end to end on synthetic data where the start policy's ability is recoverable, the graded pseudo-respondent fit converges, and the factored-reward categories are the pre-registered bins."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1"
spec = importlib.util.spec_from_file_location("irt_e20", E / "irt_e20.py")
M = importlib.util.module_from_spec(spec)
sys.modules["irt_e20"] = M
spec.loader.exec_module(M)
I = M.I


def simulate(seed=0, persons=12, items=120, trials=None):
    rng = np.random.default_rng(seed)
    theta = rng.normal(0, 1, persons)
    a = np.exp(rng.normal(0, 0.3, items))
    d = rng.normal(-1.0, 1.2, items)
    n = np.full((persons, items), 1.0) if trials is None else np.broadcast_to(np.asarray(trials, float), (persons, items)).copy()
    p = expit(a[None, :] * theta[:, None] + d[None, :])
    k = rng.binomial(n.astype(int), p).astype(float)
    return theta, a, d, k, n


def test_count_objective_gradient_matches_finite_differences():
    _, a, d, k, n = simulate(1, persons=6, items=15, trials=np.full((6, 15), 8.0))
    y, m = M._fraction(k, n), n
    X = I.random_intercept(15)
    x0 = np.concatenate([np.log(a) * 0.5, d * 0.5, [0.1]])
    v, g = I.objective_2pl(x0, y, m, X, 1.0, 0.5, I.BASE)
    for j in [0, 7, 15, 22, 30]:
        e = np.zeros_like(x0)
        e[j] = 1e-5
        num = (I.objective_2pl(x0 + e, y, m, X, 1.0, 0.5, I.BASE)[0] - I.objective_2pl(x0 - e, y, m, X, 1.0, 0.5, I.BASE)[0]) / 2e-5
        assert abs(num - g[j]) < 1e-5 * max(1.0, abs(g[j]))


def test_recovery_with_binomial_counts_and_1pl():
    theta, a, d, k, n = simulate(2, persons=12, items=150, trials=np.where(np.arange(12)[:, None] == 11, 8.0, 1.0))
    fit = M.fit_2pl_counts(k, n, X=I.random_intercept(150), sigma_e=2.0, slope_sd=0.5)
    assert fit["converged"]
    a_hat, d_hat = M.item_params(fit)
    assert np.corrcoef(d_hat, d)[0, 1] > 0.85
    post = M.posterior_theta(fit, k, n)
    mean, sd = M.eap(post)
    assert np.corrcoef(mean, theta)[0, 1] > 0.85 and np.all(sd > 0)
    one = M.fit_2pl_counts(k, n, X=I.random_intercept(150), sigma_e=2.0, slope_sd=0.5, fixed_slope=True)
    assert one["converged"] and np.allclose(M.item_params(one)[0], 1.0)


def test_folds_keep_groups_together():
    groups = np.array([f"g{i // 3}" for i in range(30)])
    cf = M.cell_folds(4, groups, 5, seed=1)
    assert cf.shape == (4, 30) and set(np.unique(cf)) <= set(range(5))
    for i in range(4):
        for g in np.unique(groups):
            assert len(set(cf[i, groups == g])) == 1
    tf = M.task_folds(groups, 5, seed=1)
    for g in np.unique(groups):
        assert len(set(tf[groups == g])) == 1
    assert len(set(tf)) == 5


def test_prior_selection_and_gate_g0_on_synthetic_data():
    rng = np.random.default_rng(5)
    items = 160
    theta, a, d, k, n = simulate(3, persons=12, items=items, trials=np.where(np.arange(12)[:, None] == 11, 8.0, 1.0))
    groups = np.array([f"g{i // 2}" for i in range(items)])
    feats = np.column_stack([np.ones(items), (d - d.mean()) / d.std() + rng.normal(0, 0.3, items)])
    folds = M.cell_folds(12, groups, 5, seed=2)
    sel = M.select_priors(k, n, folds, I.random_intercept(items), slope_grid=(0.25, 1.0), sigma_grid=(1.0, 4.0), workers=2)
    assert len(sel["table"]) == 4 and sel["chosen"]["slope_sd"] in (0.25, 1.0)
    priors = {"random_intercept": {"slope_sd": 0.5, "sigma_e": 2.0}, "explanatory": {"slope_sd": 0.5, "sigma_e": 1.0}}
    inp = M.G0Inputs(k_sp=k[11], n_sp=n[11], panel_k=k[:11], panel_n=n[:11], X=feats, group_ids=groups, task_ids=[f"t{i}" for i in range(items)])
    g0 = M.gate_g0(inp, priors, draws=200)
    assert set(g0["models"]) == {"random_intercept", "explanatory", "features_only", "baseline", "panel_strict_rate"}
    assert g0["models"]["random_intercept"]["auc"] > 0.6
    assert abs(g0["models"]["baseline"]["auc"] - 0.5) < 0.1  # a per-fold constant forecast cannot rank tasks
    assert g0["gate"]["log_loss"] < g0["gate"]["baseline_log_loss"]
    assert len(g0["per_task"]["p_active_random_intercept"]) == items and g0["bootstrap"]["draws"] == 200
    thetas = [t["theta"] for t in g0["theta_by_fold"] if t["model"] == g0["selected_model"]]
    assert abs(np.mean(thetas) - theta[11]) < 1.0


def test_graded_pseudo_fit_and_categories():
    assert [M.factored_category(v) for v in (0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0)] == [0, 1, 1, 2, 2, 3, 4]
    rng = np.random.default_rng(7)
    items = 40
    cat = rng.integers(0, 5, size=(8, items))
    mc = np.ones((8, items))
    fit = M.fit_graded_pseudo(cat, mc, slope_sd=0.5, sigma_e=2.0)
    assert fit["converged"] and fit["cuts"].shape == (items, 4) and np.all(np.diff(fit["cuts"], axis=1) < 0)
