"""Unit tests for experiment 19's IRT models and analysis: analytic gradients, parameter recovery, ability calibration, unseen-item curves, AUC, the test-split guards, the real-input loaders and the mechanical decision rules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import approx_fprime
from scipy.special import expit

REPO = Path(__file__).resolve().parents[1]
EXPT = REPO / "experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/expt_v1"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mods():
    sys.path.insert(0, str(EXPT))
    sys.path.insert(0, str(REPO / "src"))
    irt = _load("irt_e19", EXPT / "irt_e19.py")
    D = _load("data_e19", EXPT / "data_e19.py")
    FE = _load("features_e19", EXPT / "features_e19.py")
    A = _load("analyze_e19", EXPT / "analyze_e19.py")
    return irt, D, FE, A


def _small(seed=0, N=7, J=9, C=5):
    rng = np.random.default_rng(seed)
    y = (rng.random((N, J)) < 0.5).astype(float)
    m = (rng.random((N, J)) < 0.85).astype(float)
    cat = rng.integers(0, C, size=(N, J))
    mc = (rng.random((N, J)) < 0.8).astype(float)
    return rng, y, m, cat, mc


@pytest.mark.parametrize("design", ["weak", "random_intercept", "explanatory"])
def test_2pl_gradient_matches_finite_differences(mods, design):
    irt = mods[0]
    rng, y, m, _, _ = _small()
    J = y.shape[1]
    X = {"weak": None, "random_intercept": irt.random_intercept(J),
         "explanatory": np.column_stack([np.ones(J), rng.normal(size=(J, 2))])}[design]
    se = None if X is None else 1.3
    x = rng.normal(scale=0.5, size=2 * J + (0 if X is None else X.shape[1]))
    g = irt.Grid(-6, 6, 121)
    f = lambda v: irt.objective_2pl(v, y, m, X, se, 0.5, g)[0]  # noqa: E731
    assert np.max(np.abs(approx_fprime(x, f, 1e-6) - irt.objective_2pl(x, y, m, X, se, 0.5, g)[1])) < 1e-5


@pytest.mark.parametrize("tied", [True, False])
def test_two_skill_gradient_matches_finite_differences(mods, tied):
    irt = mods[0]
    rng, y, m, cat, mc = _small(1)
    C = 5
    oh = irt.onehot_categories(cat, mc, C)
    x = rng.normal(scale=0.4, size=irt._layout(y.shape[1], C, tied)["size"])
    g = irt.Grid(-6, 6, 121)
    f = lambda v: irt.objective_two_skill(v, y, m, oh, C, tied, g, 0.5, 1.3)[0]  # noqa: E731
    ana = irt.objective_two_skill(x, y, m, oh, C, tied, g, 0.5, 1.3)[1]
    assert np.max(np.abs(approx_fprime(x, f, 1e-6) - ana)) < 1e-5


def test_2pl_recovers_intercepts_and_feature_coefficients(mods):
    irt = mods[0]
    rng = np.random.default_rng(3)
    N, J = 150, 40
    Z = rng.normal(size=(J, 2))
    w = np.array([0.8, -0.6])
    d = Z @ w + rng.normal(0, 0.5, J)
    a = np.exp(rng.normal(0, 0.3, J))
    th = rng.normal(size=N)
    y = (rng.random((N, J)) < expit(a * th[:, None] + d)).astype(float)
    X = np.column_stack([np.ones(J), Z])
    f = irt.fit_2pl(y, np.ones_like(y), X=X, sigma_e=1.0, slope_sd=0.5)
    assert f["converged"]
    assert np.corrcoef(irt.item_params(f)[1], d)[0, 1] > 0.95
    assert np.allclose(irt.coefficients(f)[1:], w, atol=0.35)


def test_calibrate_theta_hits_target_rate(mods):
    irt = mods[0]
    rng = np.random.default_rng(4)
    a, d = np.exp(rng.normal(0, 0.5, 50)), rng.normal(-1, 2, 50)
    t = irt.calibrate_theta(a, d, 0.0968)
    assert abs(np.mean(expit(a * t + d)) - 0.0968) < 1e-9
    with pytest.raises(ValueError):
        irt.calibrate_theta(a, d, 1.0)


def test_new_item_curves_are_monotone_and_shift_with_features(mods):
    irt = mods[0]
    rng = np.random.default_rng(5)
    N, J = 40, 30
    y = (rng.random((N, J)) < 0.5).astype(float)
    X = np.column_stack([np.ones(J), rng.normal(size=J)])
    f = irt.fit_2pl(y, np.ones_like(y), X=X, sigma_e=1.0, slope_sd=0.5, check=None)
    Xn = np.array([[1.0, -2.0], [1.0, 2.0]])
    c = irt.new_item_curves(f, Xn, 2)
    assert c.shape == (2, irt.BASE.count)
    assert np.all(np.diff(c, axis=1) >= -1e-12)
    w = irt.coefficients(f)
    assert (c[1, 600] > c[0, 600]) == (w[1] > 0)


def test_two_skill_tied_and_untied_fit_converge_on_small_problem(mods):
    irt = mods[0]
    rng = np.random.default_rng(6)
    N, J, C = 30, 15, 5
    th = rng.multivariate_normal([0, 0], [[1, 0.6], [0.6, 1]], size=N)
    d = rng.normal(0, 1.5, J)
    ys = (rng.random((N, J)) < expit(th[:, [0]] + d)).astype(float)
    cuts = np.sort(rng.normal(0.5, 1.0, (J, C - 1)), axis=1)[:, ::-1]
    cat = (rng.random((N, J))[:, :, None] < expit(th[:, 1][:, None, None] + cuts[None])).sum(2)
    ms = np.ones((N, J))
    small, check = irt.Grid(-6, 6, 121), irt.Grid(-8, 8, 241)
    for tied in (True, False):
        f = irt.fit_two_skill(ys, ms, cat, ms, C, tied=tied, slope_sd=0.5, sigma_e=1.0, grid=small, check=check)
        assert f["converged"]
        pr = irt.two_skill_predict(f, ys[:2], ms[:2] * 0, cat[:2], ms[:2] * 0, np.arange(J))
        assert pr["strict"].shape == (2, J) and np.all((pr["both"] <= pr["strict"] + 1e-12))
        assert np.allclose(pr["cat_probs"].sum(2), 1.0, atol=1e-9)


def test_auc_matches_pairwise_definition_with_ties(mods):
    A = mods[3]
    rng = np.random.default_rng(7)
    s = rng.integers(0, 5, 60).astype(float)
    y = (rng.random(60) < 0.4).astype(float)
    pos, neg = s[y == 1], s[y == 0]
    ref = np.mean([(p > q) + 0.5 * (p == q) for p in pos for q in neg])
    assert abs(A.auc(s, y) - ref) < 1e-12
    assert np.isnan(A.auc(s, np.zeros(60)))


def test_fsc_categories(mods):
    D = mods[1]
    assert [D.fsc_category(v) for v in (0.0, 0.1, 0.5, 0.55, 0.8, 0.85, 0.9, 1.0)] == [0, 1, 1, 2, 2, 3, 3, 4]


def test_real_loaders_never_return_test_tasks(mods):
    D = mods[1]
    split = D.load_split()
    assert len(split.train) == 539 and len(split.validation) == 135
    panel = D.load_panel(split)
    assert panel.strict.shape == (11, 674)
    assert not set(panel.tasks) & split.test_ids
    assert np.all(panel.harsh <= panel.strict)
    start = D.load_start_policy(split)
    assert start.n.sum() == 1080 and np.all((start.k >= 0) & (start.k <= 8))
    a6 = D.load_a6_rate()
    assert (a6["successes"], a6["measured"]) == (48, 496)
    rc = D.load_rc(split)
    assert rc["RC_fspecs"].shape == (11, 674)
    assert len(D.load_features(split)) == 674


def test_gold_check_target_follows_veribench_111_rules(mods):
    D = mods[1]
    split = D.load_split()
    panel = D.load_panel(split)
    info = D.attach_gold_target(panel, split)
    assert info["consistency_violations"]["ic_tests_1_without_typecheck_row"] == 0
    assert info["withheld_tasks_in_train_validation"] == 18
    assert set(np.unique(panel.gold[panel.gold_mask > 0])) <= {0.0, 1.0}
    assert np.all(panel.gold[panel.gold_mask == 0] == 0)
    # every strict success compiles, so it can never be a "does not typecheck" zero
    i = panel.systems.index("codex")
    assert np.all(panel.gold_mask[i][panel.status[i] == "measured"].sum() > 0)
    n = sum(v for k, v in info["cell_reasons"].items())
    assert n == panel.strict.size


def test_split_guard_rejects_test_rows(mods, tmp_path):
    D = mods[1]
    split = D.load_split()
    test_id = sorted(split.test_ids)[0]
    bad = tmp_path / "features.csv"
    bad.write_text("task_id,split\n" + f"{test_id},test\n")
    with pytest.raises(D.SplitViolation):
        D.load_features(split, bad)


def test_g3_task_draw_matches_experiment_13_v4(mods):
    D = mods[1]
    g3 = _load("freeze_g3_forecast_e19", EXPT / "freeze_g3_forecast_e19.py")
    e13 = REPO / "experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/phase2/group_selection.py"
    if not e13.exists():
        pytest.skip("experiment 13 v4 group selection not present")
    sel = _load("e13_v4_group_selection", e13)
    train = D.load_split().train
    assert g3.g0_tasks(train) == sel.select_tasks(train)


def test_verdicts_apply_the_rules(mods):
    A = mods[3]
    yes = {"estimate": 0.1, "ci95": [0.01, 0.2]}
    no = {"estimate": 0.0, "ci95": [-0.1, 0.1]}
    neg = {"estimate": -0.1, "ci95": [-0.2, -0.01]}
    e1 = {"contrasts": {"m1_minus_m2": yes, "m0_minus_m2": yes, "m2_minus_m3": no}}
    r = {"E1": {"strict": e1, "harsh": {"contrasts": {"m1_minus_m2": yes, "m0_minus_m2": no, "m2_minus_m3": yes}},
                "gold": {"contrasts": {"m1_minus_m2": yes, "m0_minus_m2": yes}}},
         "E1_system": {"strict": {"mae_contrasts": {"rate_calibrated_minus_smooth_calibrated": neg}},
                       "harsh": {"mae_contrasts": {"rate_calibrated_minus_smooth_calibrated": no}},
                       "gold": {"mae_contrasts": {"rate_calibrated_minus_smooth_calibrated": yes}}},
         "E2": {"new_task": {"strict": {"nofeat_minus_feat": yes}, "harsh": {"nofeat_minus_feat": no},
                             "gold": {"nofeat_minus_feat": yes}}},
         "E3": {"heldout": {"untied_minus_tied": no}},
         "G1": {"auc_primary_vs_gate": {"estimate": 0.72},
                "auc_contrasts": {"q8_irt_2pl_minus_panel_strict_rate": yes, "q8_irt_2pl_minus_panel_mean_smooth": no},
                "estimates": {"auc_mixed": {"panel_strict_rate": 0.71, "panel_mean_smooth": 0.6}}}}
    v = A.verdicts(r)
    assert v["E1_strict_irt_beats_baselines"] and not v["E1_harsh_irt_beats_baselines"]
    assert v["E1_harsh_fsc_skill_adds"] and v["E1_strict_smooth_vs_rate"] == "smooth worse"
    assert v["E2_strict_features_predict_unseen_tasks"] and not v["E3_two_skills"]
    assert v["E1_gold_irt_beats_baselines"] and v["E1_gold_smooth_vs_rate"] == "smooth better"
    assert "E1_gold_fsc_skill_adds" not in v
    assert v["G1"] == "PASS, NOT IRT-SPECIFIC"
    r["G1"]["auc_primary_vs_gate"]["estimate"] = 0.65
    assert A.verdicts(r)["G1"] == "FAIL FOR IRT, HEURISTIC PASSES"
