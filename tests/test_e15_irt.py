"""Unit tests for experiment 15's binomial IRT models and analysis: gradients, parameter recovery, baseline correctness, bootstrap plumbing, the validation-split restriction, degenerate-rung accounting, the decision rule and a synthetic end-to-end run."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.special import expit

REPO = Path(__file__).resolve().parents[1]
EXPT = REPO / "experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/expt_v1"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def irt():
    sys.path.insert(0, str(EXPT))
    return _load("irt_e15", EXPT / "irt_e15.py")


@pytest.fixture(scope="module")
def a15(irt):
    return _load("analyze_e15", EXPT / "analyze_e15.py")


def _counts(n_per=12, j=20, n=8, seed=0):
    rng = np.random.default_rng(seed)
    p = expit(rng.normal(0, 1, n_per)[:, None] - rng.normal(0, 1, j))
    k = rng.binomial(n, p).astype(float)
    return k, np.full((n_per, j), float(n))


@pytest.mark.parametrize("kind", ["1pl", "2pl"])
def test_gradient_matches_finite_differences(irt, kind):
    k, n = _counts()
    n[0, :3] = 0  # missing cells contribute nothing
    k[0, :3] = 0
    x0 = irt.initial_params(kind, k, n)
    x = x0 + np.random.default_rng(3).normal(0, 0.2, x0.size)
    _, grad = irt.objective(x, kind, k, n)
    num = np.empty_like(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = 1e-6
        num[i] = (irt.objective(x + e, kind, k, n)[0] - irt.objective(x - e, kind, k, n)[0]) / 2e-6
    assert np.allclose(grad, num, rtol=1e-4, atol=1e-7)


def test_binomial_objective_equals_expanded_bernoulli(irt):
    """k-of-n counts give the same marginal log posterior as n Bernoulli items with the same parameters."""
    k, n = _counts(n_per=5, j=4, n=3)
    x = irt.initial_params("2pl", k, n)
    v_count, _ = irt.objective(x, "2pl", k, n)
    # Expand each item into 3 copies of itself with 0/1 responses: same parameters, so tie the copies' parameters.
    k_exp = np.concatenate([(k[:, j][:, None] > np.arange(3)[None, :]).astype(float) for j in range(4)], axis=1)
    a, d = irt.unpack("2pl", x, 4)
    x_exp = np.concatenate([np.log(np.repeat(a, 3)), np.repeat(d, 3)])
    v_exp, _ = irt.objective(x_exp, "2pl", k_exp, np.ones_like(k_exp))
    # The priors differ (12 items against 4), so compare the data terms: subtract each prior.
    lp_c = irt._log_prior("2pl", x, 4)[0]
    lp_e = irt._log_prior("2pl", x_exp, 12)[0]
    assert np.isclose(-(v_count * 5) - lp_c, -(v_exp * 5) - lp_e, rtol=1e-10, atol=1e-9)


def test_2pl_recovers_generating_parameters_from_counts(irt):
    rng = np.random.default_rng(5)
    n_per, j, n = 40, 135, 8
    theta, a, b = rng.normal(0, 1, n_per), np.exp(rng.normal(0.2, 0.3, j)), rng.normal(0, 1.2, j)
    k = rng.binomial(n, expit(a * (theta[:, None] - b))).astype(float)
    nn = np.full((n_per, j), float(n))
    fitted = irt.fit("2pl", k, nn)
    assert fitted["converged"] and fitted["check_grid_max_abs_grad"] <= irt.GRAD_TOL
    a_hat, d_hat = irt.unpack("2pl", fitted["x"], j)
    assert np.corrcoef(b, -d_hat / a_hat)[0, 1] > 0.95
    assert np.corrcoef(a, a_hat)[0, 1] > 0.6
    post = irt.posterior(fitted, k, nn)
    assert np.corrcoef(theta, irt.eap(post)[0])[0, 1] > 0.95
    assert irt.endpoint_mass(post).max() < 1e-8


def test_fit_rejects_invalid_counts(irt):
    k, n = _counts(n_per=3, j=3)
    k[0, 0] = 9
    with pytest.raises(ValueError):
        irt.fit("2pl", k, n)


def test_covariate_forms(a15):
    assert a15.covariate(0, "log1p_ratio") == 0.0
    assert a15.covariate(a15.T1, "log1p_ratio") == pytest.approx(np.log(2))
    assert np.isnan(a15.covariate(0, "log_tokens")) and a15.covariate(a15.T1, "log_tokens") == pytest.approx(np.log(a15.T1))


def test_baselines_are_what_the_protocol_says(a15):
    data = a15.synthetic_data(0)
    s, r_idx = "8B", 3  # forecast the 50% rung from Base, 12.5% and 25%
    b1 = a15.baseline_b1(data, s, r_idx, "kernel_binary")
    assert np.array_equal(b1, data["k"][s]["0.25"] / data["n"][s]["0.25"])
    b2 = a15.baseline_b2(data, s, r_idx, "log1p_ratio", "kernel_binary")
    assert np.ptp(b2) == 0  # no task difficulty: one value for every task
    xs, ys = [], []
    for f in ("0", "0.125", "0.25"):
        k, n = data["k"][s][f], data["n"][s][f]
        rate = (k.sum() + 0.5) / (n.sum() + 1)
        xs.append(a15.covariate(a15.TOKENS[f], "log1p_ratio"))
        ys.append(np.log(rate / (1 - rate)))
    slope, intercept = np.polyfit(xs, ys, 1)
    assert b2[0] == pytest.approx(expit(intercept + slope * a15.covariate(a15.TOKENS["0.5"], "log1p_ratio")))
    # log_tokens form: the Base rung is not in the trend, so with one SFT rung the curve carries that rung's rate forward.
    assert a15.baseline_b2(data, s, 2, "log_tokens", "kernel_binary")[0] == pytest.approx(expit(ys[1]))
    assert a15.fit_linear(np.array([1.0]), np.array([0.3]), 5.0) == (0.3, None)


def test_per_task_errors_brier_and_mixed_share(a15):
    truth = {"truth": np.array([0.0, 0.5, 1.0]), "valid": np.array([True, True, True]), "realized_mixed_share": 1 / 3, "pooled_rate": 0.5}
    e = a15.per_task_errors(np.array([0.0, 0.5, 1.0]), truth)
    assert e["mae"] == 0.0 and e["brier_mean"] == pytest.approx((0 + 0.25 + 0) / 3)
    assert e["expected_mixed_share"] == pytest.approx((0 + (1 - 2 * 0.5**8) + 0) / 3)
    assert e["pooled_error"] == pytest.approx(0.0)


def test_task_bootstrap_plumbing(a15):
    rng = np.random.default_rng(0)
    d = {"4B": np.full(135, 0.02), "8B": np.full(135, 0.04)}
    out = a15.task_bootstrap(d, rng, draws=37)
    assert out["draws"] == 37 and "37 draws" in out["test"] and out["n_tasks"] == 135
    assert out["point"] == pytest.approx(0.03) and out["lo"] == pytest.approx(0.03) and out["hi"] == pytest.approx(0.03)
    assert out["excludes_zero"] and out["per_size"]["8B"]["point"] == pytest.approx(0.04)
    zero = a15.task_bootstrap({"4B": np.zeros(135)}, rng, draws=10)
    assert zero["point"] == 0.0 and not zero["excludes_zero"]


def test_real_split_lists_are_disjoint_and_no_test_file_is_an_input(a15):
    root = a15.E08
    val = set((root / "split/vbv1_validation_task_ids.txt").read_text().split())
    test = set((root / "split/vbv1_test_task_ids.txt").read_text().split())
    assert len(val) == 135 and len(test) == 222 and not (val & test)
    pins = json.loads(a15.PINS.read_text())["sha256"]
    assert not any("test" in Path(f).name for f in pins if f.startswith("ladder/"))
    for size in a15.SIZES:
        for frac in a15.FRACS:
            assert "test" not in Path(a15.file_for(size, frac)).name


def test_load_real_rejects_a_test_task_id(a15, tmp_path):
    """A per-task file with a test-split id must raise before any outcome is used."""
    root = tmp_path
    (root / "split").mkdir()
    (root / "ladder").mkdir()
    real = a15.E08
    val_ids = sorted((real / "split/vbv1_validation_task_ids.txt").read_text().split())
    test_ids = sorted((real / "split/vbv1_test_task_ids.txt").read_text().split())
    (root / "split/vbv1_validation_task_ids.txt").write_text("\n".join(val_ids) + "\n")
    (root / "split/vbv1_test_task_ids.txt").write_text("\n".join(test_ids) + "\n")
    header = "task_id,samples_known,k_kernel_binary,mixed,k_ic_tests,k_extracted,k_capped,mean_proof_fraction,mean_generated_tokens\n"
    rows = [f"{t},8,0,0,0,8,0,0.0,100.0" for t in val_ids]
    rows[0] = f"{test_ids[0]},8,0,0,0,8,0,0.0,100.0"  # one smuggled test task
    for size in a15.SIZES:
        for frac in a15.FRACS:
            (root / a15.file_for(size, frac)).write_text(header + "\n".join(rows) + "\n")
    with pytest.raises(a15.SplitViolation):
        a15.load_real(root=root, pins=None)


def test_eligibility_and_decision_rules(a15):
    data = a15.synthetic_data(2, degenerate_size="1.7B")
    fc = a15.all_forecasts(data)
    el = a15.eligibility(data, fc)
    assert not el["sizes"]["1.7B"]["eligible"] and el["sizes"]["1.7B"]["final_rung_degenerate"]
    assert "1.7B" not in el["eligible_sizes"] and len(el["sizes"]["1.7B"]["degenerate_rungs"]) == 6
    good = {"b1_last_rung": {"point": 0.01, "lo": 0.002, "hi": 0.02}, "b2_scalar_curve": {"point": 0.03, "lo": 0.01, "hi": 0.05}}
    assert a15.decide(good, el)[0] == "SUCCESS"
    bad = dict(good, b1_last_rung={"point": 0.01, "lo": -0.002, "hi": 0.02})
    assert a15.decide(bad, el)[0] == "NO ADVANTAGE"
    thin = dict(el, eligible_sizes=["8B"])
    assert a15.decide(good, thin)[0] == "INCONCLUSIVE"
    deg = dict(el, degenerate_target_share=0.2)
    assert a15.decide(good, deg)[0] == "INCONCLUSIVE"


def test_synthetic_end_to_end_writes_outputs_and_irt_beats_the_scalar_curve(a15, tmp_path):
    analysis = a15.run(synthetic=3, out_dir=tmp_path, draws=200, check_forecast=False)
    assert analysis["verdict"] in ("SUCCESS", "NO ADVANTAGE", "INCONCLUSIVE")
    assert analysis["fits"]["n_converged"] == analysis["fits"]["n"]
    assert analysis["primary"]["b2_scalar_curve"]["point"] > 0  # per-task difficulty exists in the generator
    rows = list(csv.DictReader((tmp_path / "per_rung_e15.csv").open()))
    assert {r["frac"] for r in rows if r["trend_form"] == "log1p_ratio"} == {"0.25", "0.5", "0.75", "1.0"}
    assert {r["frac"] for r in rows if r["trend_form"] == "log_tokens"} == {"0.5", "0.75", "1.0"}
    assert (tmp_path / "analysis_e15.json").exists() and (tmp_path / "results_tables_e15.md").exists()
    assert "forecast_evaluation" not in analysis


def test_forecast_lookup(a15):
    analysis = {"primary": {"b1_last_rung": {"point": 0.012}}, "success": True}
    pred = {"predictions": [{"id": "x", "path": ["primary", "b1_last_rung", "point"], "point": 0.0, "interval80": [-0.01, 0.01]},
                            {"id": "y", "path": ["success"], "probability": 0.4}]}
    rows = a15.evaluate_forecast(analysis, pred)
    assert rows[0]["outcome"] == 0.012 and rows[0]["inside_interval80"] is False
    assert rows[1]["brier"] == pytest.approx(0.36)
