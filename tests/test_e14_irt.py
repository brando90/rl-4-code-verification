"""Unit tests for experiment 14's IRT models and analysis helpers: gradients, sufficiency, recovery, experiment 07 split replay, ranks and gates."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.special import expit
from scipy.stats import rankdata

REPO = Path(__file__).resolve().parents[1]
EXPT = REPO / "experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def irt():
    sys.path.insert(0, str(EXPT))
    return _load("irt_e14", EXPT / "irt_e14.py")


@pytest.fixture(scope="module")
def a14(irt):
    return _load("analyze_e14", EXPT / "analyze_e14.py")


def _binary(n=60, j=8, seed=0):
    rng = np.random.default_rng(seed)
    x = (rng.random((n, j)) < expit(rng.normal(0, 1, n)[:, None] - rng.normal(0, 1, j))).astype(float)
    return [1 - x, x]


def _graded(n=60, j=8, seed=1):
    rng = np.random.default_rng(seed)
    c = rng.integers(0, 3, (n, j))
    return [(c == k).astype(float) for k in range(3)]


@pytest.mark.parametrize("kind", ["1pl", "2pl", "grm3"])
def test_gradient_matches_finite_differences(irt, kind):
    cats = _graded() if kind == "grm3" else _binary()
    rng = np.random.default_rng(3)
    x = irt.initial_params(kind, cats) + rng.normal(0, 0.2, irt.initial_params(kind, cats).size)
    _, grad = irt.objective(x, kind, cats)
    num = np.empty_like(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = 1e-6
        num[i] = (irt.objective(x + e, kind, cats)[0] - irt.objective(x - e, kind, cats)[0]) / 2e-6
    assert np.allclose(grad, num, rtol=1e-4, atol=1e-7)


def test_graded_categories_sum_to_one_and_middle_is_stable(irt):
    a, d = np.array([0.7, 2.0]), np.array([0.5, -1.0])
    d2 = d - np.array([1e-3, 3.0])
    probs = np.exp(irt.node_logprobs("grm3", a, d, d2))
    assert np.allclose(probs.sum(0), 1.0)
    direct = expit(a[:, None] * irt.GRID + d[:, None]) - expit(a[:, None] * irt.GRID + d2[:, None])
    assert np.allclose(probs[1], direct, rtol=1e-6, atol=1e-15)


def test_rasch_posterior_depends_only_on_the_count(irt):
    cats = _binary(n=40, j=10)
    sc = irt.Scorer(irt.fit("1pl", cats))
    items = np.arange(10)
    post = sc.posterior(cats, items)
    log_joint = sum(c @ lp for c, lp in zip(cats, sc.lps)) + irt.LOG_PRIOR_W
    full = np.exp(log_joint - log_joint.max(1, keepdims=True))
    assert np.allclose(post, full / full.sum(1, keepdims=True), atol=1e-12)
    x = np.zeros((2, 10))
    x[0, :3] = 1
    x[1, -3:] = 1  # same count, different items
    p = sc.posterior([1 - x, x], items)
    assert np.array_equal(p[0], p[1])


def test_2pl_recovers_generating_parameters(irt):
    rng = np.random.default_rng(5)
    n, j = 500, 30
    theta, a, b = rng.normal(0, 1, n), np.exp(rng.normal(0.3, 0.3, j)), rng.normal(0, 1, j)
    x = (rng.random((n, j)) < expit(a * (theta[:, None] - b))).astype(float)
    fitted = irt.fit("2pl", [1 - x, x])
    assert fitted["converged"]
    a_hat, d_hat, _ = irt.unpack("2pl", fitted["x"], j)
    assert np.corrcoef(b, -d_hat / a_hat)[0, 1] > 0.95
    assert np.corrcoef(a, a_hat)[0, 1] > 0.7
    post = irt.Scorer(fitted).posterior([1 - x, x], np.arange(j))
    assert np.corrcoef(theta, irt.eap(post)[0])[0, 1] > 0.85


def test_replay_matches_experiment_07_bootstrap_stream(a14):
    e07 = a14.load_e07_module()
    n_tasks, n_sys, boot = 12, 5, 3
    rng = np.random.default_rng(7)
    xy = (np.arange(n_sys, dtype=float), np.arange(n_sys, dtype=float) ** 2)
    for _ in range(2):  # 07 ran the H1 and then the H1b bootstrap before drawing its H2 splits
        e07.bootstrap_corr(lambda i: xy, n_tasks, n_sys, rng, boot)
    expected = [rng.permutation(n_tasks) for _ in range(4)]
    replay = a14.burn_e07_bootstraps(np.random.default_rng(7), n_tasks, n_sys, boot=boot)
    assert all(np.array_equal(e, replay.permutation(n_tasks)) for e in expected)


def test_rank_rows_equals_scipy_average_ranks(a14):
    m = np.random.default_rng(2).integers(0, 6, (50, 30)) / 5
    assert np.array_equal(a14.rank_rows(m), rankdata(m, axis=1))


def test_top_n_takes_exactly_n_valid_pairs(a14):
    z = np.array([[np.nan, 2.0, 1.0], [1.0, np.nan, 5.0], [1.0, -np.inf, np.nan]])
    mask = ~np.eye(3, dtype=bool)
    sel = a14.top_n(z, mask, 3)
    assert sel.sum() == 3 and sel[1, 2] and sel[0, 1] and sel[0, 2] and not sel[1, 0]
    assert a14.top_n(z, mask, 10).sum() == 5  # never selects invalid pairs


def test_gate_paired_standard_error_and_harm(a14):
    xa = np.array([[1, 1, 0, 0, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 1]], float)
    p1a = xa.mean(1)
    acc = a14.GateAccumulator(3)
    acc.add(xa, p1a, np.array([0.5, 0.6, 0.9]), np.array([0.0, -1.0, 2.0]), np.full(3, 0.5))
    diff = xa[0] - xa[1]
    z = diff.mean() / (diff.std(ddof=1) / np.sqrt(5))  # incumbent 1 -> candidate 0
    assert z > 1
    assert acc.acc["G1_pass1_1se"]["prom"][1, 0] == 1 and acc.acc["G1_pass1_1se"]["harm"][1, 0] == 1  # held-out 0.5 < 0.6
    assert acc.acc["G0_scalar"]["prom"].sum() == 3 and np.trace(acc.acc["G0_scalar"]["prom"]) == 0


def test_forecast_lookup_and_rule(a14):
    analysis = {"sizes": {"50": {"arms": {"2pl": {"rank": {"delta_median": 0.002}}}}}}
    pred = {"predictions": [{"id": "x", "path": ["sizes", "50", "arms", "2pl", "rank", "delta_median"], "point": 0.0, "interval80": [-0.001, 0.001]}]}
    row = a14.evaluate_forecast(analysis, pred)[0]
    assert row["outcome"] == 0.002 and row["inside_interval80"] is False
