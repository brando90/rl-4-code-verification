"""Unit tests for experiment 14's IRT models and analysis helpers: gradients, sufficiency, recovery, numerical gates, experiment 07 split replay, ranks, gates, decision bounds and the STOP path."""

from __future__ import annotations

import importlib.util
import json
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
    x0 = irt.initial_params(kind, cats)
    x = x0 + np.random.default_rng(3).normal(0, 0.2, x0.size)
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
    theta = irt.BASE.nodes
    direct = expit(a[:, None] * theta + d[:, None]) - expit(a[:, None] * theta + d2[:, None])
    assert np.allclose(probs[1], direct, rtol=1e-6, atol=1e-15)


def test_rasch_posterior_depends_only_on_the_count(irt):
    cats = _binary(n=40, j=10)
    sc = irt.Scorer(irt.fit("1pl", cats))
    items = np.arange(10)
    post = sc.posterior(cats, items)
    log_joint = sum(c @ lp for c, lp in zip(cats, sc.lps)) + irt.BASE.log_w
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
    assert fitted["converged"] and fitted["check_grid_max_abs_grad"] <= irt.GRAD_TOL
    a_hat, d_hat, _ = irt.unpack("2pl", fitted["x"], j)
    assert np.corrcoef(b, -d_hat / a_hat)[0, 1] > 0.95
    assert np.corrcoef(a, a_hat)[0, 1] > 0.7
    sc = irt.Scorer(fitted)
    assert np.corrcoef(theta, sc.eap(sc.posterior([1 - x, x], np.arange(j)))[0])[0, 1] > 0.85


def test_review_finding1_support_counterexample_now_passes_the_gates(irt):
    """Reviewer's case: all-zero reference panel, all-one target. The old [-6, 6] grid put 41% of the posterior on its
    end node and moved the forecast by 0.30; on the frozen base grid the endpoint mass and rescoring change are tiny."""
    z = np.zeros((148, 424))
    fitted = irt.fit("2pl", [1 - z, z], maxiter=2000)
    target = np.ones((1, 424))
    sc, sc_c = irt.Scorer(fitted), irt.Scorer(fitted, irt.CHECK)
    post, post_c = sc.posterior([1 - target, target], np.arange(50)), sc_c.posterior([1 - target, target], np.arange(50))
    assert irt.endpoint_mass(post)[0] <= irt.ENDPOINT_TOL
    f, f_c = sc.forecast(post, np.arange(50, 424)), sc_c.forecast(post_c, np.arange(50, 424))
    assert abs(f[0] - f_c[0]) <= irt.RESCORE_TOL and abs(sc.eap(post)[0][0] - sc_c.eap(post_c)[0][0]) <= irt.RESCORE_TOL


def test_review_finding2_nan_gradient_is_a_failure(irt):
    assert np.isnan(irt.max_abs(np.array([0.0, np.nan])))
    assert not (irt.max_abs(np.array([np.nan])) <= irt.GRAD_TOL)


def test_review_finding2_failed_split_cannot_decide_the_rank_rule(a14):
    """Reviewer's case: 1,199 positive, one failed (provisionally positive), 800 negative splits."""
    summary = {"2pl_within_A": {"rank": {"delta_median": 0.001, "share_delta_positive": 0.6}},
               "2pl": {"level": {"vs_pass1_A": {"mae_difference": -0.001, "ci95": [-0.002, 0.0]}}}}
    deltas = [0.01] * 1199 + [None] + [-0.01] * 800  # the failed split is undefined in the point estimate
    gates = {"valid": True, "reason": None}
    v = a14.primary_verdicts(summary, {}, "2pl_within_A", "2pl", rank_deltas=deltas, failed_splits=[1199], level_gates=gates)
    assert v["rank_bounds_failed_splits_worst_best"] == [False, True]
    assert v["rank_status"].startswith("inconclusive") and not v["rank_holds"]
    assert a14.q1_verdict(v, False).startswith("INCONCLUSIVE")
    ok = a14.primary_verdicts(summary, {}, "2pl_within_A", "2pl", rank_deltas=[0.01] * 1300 + [-0.01] * 700, failed_splits=[], level_gates=gates)
    assert ok["rank_status"] == "holds" and a14.q1_verdict(ok, False).startswith("CONTINUE")


def test_q1_attribution_text_follows_the_control(a14):
    v = {"rank_status": "fails", "level_status": "holds"}
    assert "credited to using the reference panel" in a14.q1_verdict(v, False)
    assert "also exceeds the non-IRT linear-regression" in a14.q1_verdict(v, True)
    assert a14.q1_verdict({"rank_status": "fails", "level_status": "fails"}, False).startswith("NO ADVANTAGE")


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


def test_review_finding7_bootstrap_uses_the_requested_draws(a14):
    rng = np.random.default_rng(0)
    F = rng.random((5, 12))
    F[2] = np.nan  # a failed split stays undefined in every draw
    out = a14.bootstrap_rank({"x": F}, rng.random((5, 12)), rng.random((5, 12)), np.random.default_rng(1), draws=7)["x"]
    assert out["draws"] == 7 and "(7 draws)" in out["test"]


def test_review_finding3_saturated_and_identical_pairs_and_exact_matching(a14):
    assert list(a14.signed_ratio(np.array([1.0, -1.0, 0.0, 2.0]), np.array([0.0, 0.0, 0.0, 4.0]))) == [np.inf, -np.inf, 0.0, 0.5]
    z = np.array([[np.nan, np.inf, 1.0], [0.0, np.nan, 5.0], [1.0, -np.inf, np.nan]])
    mask = ~np.eye(3, dtype=bool)
    sel = a14.top_n(z, mask, 3)
    assert sel.sum() == 3 and sel[0, 1] and sel[1, 2] and sel[0, 2]  # +inf kept and ranked first; ties by index
    assert a14.top_n(z, mask, 6).sum() == 6  # every valid pair, including -inf, can be selected
    xa = np.vstack([np.zeros(50), np.ones(50)])  # reviewer's saturated pair: paired SE 0, gain +1
    acc = a14.GateAccumulator(2)
    acc.add(xa, xa.mean(1), np.array([0.8, 0.2]), np.array([-2.0, 2.0]), np.array([0.1, 0.1]))
    assert acc.acc["G1_pass1_1se"]["prom"][0, 1] == 1 and acc.acc["G1m_pass1_top_matched_to_G2"]["prom"][0, 1] == 1
    assert acc.match_failures == 0
    summ = acc.summary(np.random.default_rng(0))
    assert summ["matched_G1m-G2"]["hpr_difference_pass1_minus_irt"] == 0.0


def test_zero_promotions_give_undefined_rates(a14):
    acc = a14.GateAccumulator(2)
    same = np.vstack([np.ones(10), np.ones(10)])
    acc.add(same, same.mean(1), np.array([0.5, 0.5]), np.zeros(2), np.full(2, 0.5))
    summ = acc.summary(np.random.default_rng(0))
    assert summ["G0_scalar"]["harmful_promotion_rate"] is None
    assert summ["matched_G1m-G2"]["hpr_difference_pass1_minus_irt"] is None and not summ["matched_G1m-G2"]["available"]


def test_gate_paired_standard_error_and_harm(a14):
    xa = np.array([[1, 1, 0, 0, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 1]], float)
    acc = a14.GateAccumulator(3)
    acc.add(xa, xa.mean(1), np.array([0.5, 0.6, 0.9]), np.array([0.0, -1.0, 2.0]), np.full(3, 0.5))
    diff = xa[0] - xa[1]
    assert diff.mean() / (diff.std(ddof=1) / np.sqrt(5)) > 1  # incumbent 1 -> candidate 0
    assert acc.acc["G1_pass1_1se"]["prom"][1, 0] == 1 and acc.acc["G1_pass1_1se"]["harm"][1, 0] == 1  # held-out 0.5 < 0.6
    assert acc.acc["G0_scalar"]["prom"].sum() == 3 and np.trace(acc.acc["G0_scalar"]["prom"]) == 0


def test_review_finding4_level_p_value_targets_the_mean(a14):
    rng = np.random.default_rng(17)
    out = a14.level_compare(np.full(164, 0.05), np.full(164, 0.04), rng)
    assert out["mae_difference"] == pytest.approx(0.01) and out["p_value"] < 0.01
    assert "null: zero mean difference" in out["test"] and "symmetric" in out["test"]


def test_review_finding5_stop_path_writes_receipt_without_outcomes(a14, tmp_path, monkeypatch):
    def failing_run(*args, **kwargs):
        raise a14.RaschCheckFailed(50, 3)
    monkeypatch.setattr(a14, "run", failing_run)
    monkeypatch.setattr(sys, "argv", ["analyze_e14.py", "--synthetic", "1", "--splits", "2", "--boot", "5", "--out-dir", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        a14.main()
    assert exc.value.code == 2
    receipt = json.loads((tmp_path / "analysis_e14.json").read_text())
    assert receipt["status"].startswith("STOP") and "q1_verdict" not in receipt and "q1_continue" not in receipt
    forecast = {"predictions": [{"id": "q", "path": ["q1_continue"], "probability": 0.9}]}
    assert a14.evaluate_forecast(receipt, forecast)[0]["outcome"] is None


def test_forecast_lookup_and_interval(a14):
    analysis = {"status": "PRIMARY ANALYSES COMPUTED", "sizes": {"50": {"arms": {"2pl": {"rank": {"delta_median": 0.002}}}}}}
    pred = {"predictions": [{"id": "x", "path": ["sizes", "50", "arms", "2pl", "rank", "delta_median"], "point": 0.0, "interval80": [-0.001, 0.001]}]}
    row = a14.evaluate_forecast(analysis, pred)[0]
    assert row["outcome"] == 0.002 and row["inside_interval80"] is False
