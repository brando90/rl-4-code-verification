"""Tests for the Eq. 7 utility model, including an exact reproduction of the paper's frozen 14B forecast scores."""

import numpy as np
import pytest

from rl4cv.utility_model import (
    BUDGET_SCALE_ONLY,
    RHO_H,
    Observation,
    _cell_standardizers,
    allocation_regret,
    curve_envelope,
    fit_utility_model,
    fixed_label_rule,
    leave_one_scale_out,
    model_rule,
    pairwise_rank_accuracy,
    paper_frozen_14b_model,
    uniform_portfolio_regret,
)

# Paper Appendix D, Table 5: pre-RL coordinates (rho per million generated tokens, H) per scale and cell.
TABLE5 = {
    1.7: {"HH": (28.34, 0.621), "HL": (13.52, 0.603), "LH": (8.02, 0.201), "LL": (3.85, 0.145)},
    4.0: {"HH": (35.22, 0.744), "HL": (20.44, 0.754), "LH": (4.62, 0.125), "LL": (2.22, 0.107)},
    8.0: {"HH": (32.43, 0.781), "HL": (20.11, 0.783), "LH": (5.92, 0.180), "LL": (2.27, 0.114)},
    14.0: {"HH": (29.13, 0.743), "HL": (18.63, 0.776), "LH": (5.24, 0.183), "LL": (2.94, 0.149)},
}
# Paper Table 4, panel A: observed 14B utility (pass@1 percentage points) per budget (million tokens).
OBS14 = {
    8: {"HH": -0.23, "HL": 2.61, "LH": -1.16, "LL": 2.28},
    16: {"HH": -3.01, "HL": 2.92, "LH": -0.56, "LL": 3.78},
    24: {"HH": -0.11, "HL": 3.53, "LH": -2.76, "LL": -0.21},
}


def _obs14():
    return [Observation(14.0, e, C, u / 100, *TABLE5[14.0][e]) for C, row in OBS14.items() for e, u in row.items()]


def test_table5_reproduces_paper_training_fold_standardizers():
    train = [Observation(s, e, 1.0, 0.0, *TABLE5[s][e]) for s in (1.7, 4.0, 8.0) for e in TABLE5[s]]
    lr_m, lr_s, h_m, h_s = _cell_standardizers(train)
    # Paper: (2.280467, 0.975934) for log rho and (0.429913, 0.290342) for H; Table 5 is rounded.
    assert lr_m == pytest.approx(2.280467, abs=1e-3)
    assert lr_s == pytest.approx(0.975934, abs=1e-3)
    assert h_m == pytest.approx(0.429913, abs=1e-3)
    assert h_s == pytest.approx(0.290342, abs=1e-3)


def test_paper_frozen_14b_forecast_scores_reproduce_section_7_2():
    m = paper_frozen_14b_model()
    obs = _obs14()
    preds = [m.predict_obs(o) for o in obs]
    rmse_pp = 100 * np.sqrt(np.mean((np.array(preds) - np.array([o.utility for o in obs])) ** 2))
    assert rmse_pp == pytest.approx(2.29, abs=0.01)  # paper: 2.29-point curve RMSE
    assert pairwise_rank_accuracy(obs, preds) == pytest.approx(14 / 18)  # paper: 77.8%
    regret_pp = 100 * allocation_regret(obs, model_rule(m))
    assert regret_pp == pytest.approx(0.288, abs=0.002)  # paper: 0.288 (Table 4 is rounded)
    # The model selects HL at all three budgets, like the fixed-HL rule (paper Table 4, panel B).
    assert allocation_regret(obs, fixed_label_rule("HL")) == pytest.approx(allocation_regret(obs, model_rule(m)))
    order = sorted(TABLE5[14.0], key=lambda e: -m.env_term(*TABLE5[14.0][e]))
    assert order[0] == "HL"


def _synthetic(true_beta, scales=(1.7, 4.0, 8.0, 14.0), budgets=(4.0, 8.0, 12.0, 16.0), noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    cells = {}
    for s in scales:
        for e in ("HH", "HL", "LH", "LL"):
            cells[(s, e)] = (float(np.exp(rng.normal(2.3, 1.0))), float(rng.uniform(0.1, 0.8)))
    ref = paper_frozen_14b_model()
    lr = np.log([v[0] for v in cells.values()])
    hh = np.array([v[1] for v in cells.values()])
    ref.logrho_mean, ref.logrho_sd, ref.H_mean, ref.H_sd = lr.mean(), lr.std(), hh.mean(), hh.std()
    ref.C0 = float(np.median(budgets))
    ref.beta = np.array(true_beta)
    out = []
    for (s, e), (rho, H) in cells.items():
        for C in budgets:
            out.append(Observation(s, e, C, ref.predict(s, C, rho, H) + noise * rng.normal(), rho, H))
    return out


def test_fit_recovers_coefficients_without_noise():
    beta = [0.01, -0.005, 0.02, -0.03, 0.05]
    obs = _synthetic(beta)
    m = fit_utility_model(obs, RHO_H)
    assert np.allclose(m.beta, beta, atol=1e-9)


def test_loso_prefers_rho_H_when_environment_terms_matter():
    obs = _synthetic([0.0, 0.0, 0.02, -0.03, 0.06], noise=0.002, seed=1)
    full = leave_one_scale_out(obs, RHO_H)
    base = leave_one_scale_out(obs, BUDGET_SCALE_ONLY)
    assert full.rmse < base.rmse
    assert full.rank_accuracy > 0.8
    assert base.rank_accuracy == pytest.approx(0.5)  # no environment terms: every within-decision pair ties
    assert full.mean_regret <= full.uniform_regret


def test_regret_tie_handling_and_uniform_portfolio():
    obs = [Observation(1.7, "A", 1.0, 0.03, 1, 0.5), Observation(1.7, "B", 1.0, 0.01, 1, 0.5)]
    assert allocation_regret(obs, lambda g: ["A", "B"]) == pytest.approx(0.01)
    assert uniform_portfolio_regret(obs) == pytest.approx(0.01)


def test_curve_envelope_uses_worst_budget_per_cell():
    residuals = [(1.7, "HH", 1, 0.01), (1.7, "HH", 2, -0.05), (1.7, "HL", 1, 0.02)]
    assert curve_envelope(residuals, quantile=1.0) == pytest.approx(0.05)


def test_nonpositive_rho_is_rejected():
    m = paper_frozen_14b_model()
    with pytest.raises(ValueError):
        m.predict(4.0, 8.0, 0.0, 0.2)
