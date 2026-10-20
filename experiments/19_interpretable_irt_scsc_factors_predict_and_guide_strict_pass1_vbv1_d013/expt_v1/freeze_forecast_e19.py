"""TLDR: Freeze experiment 19's predictions of its own primary outcomes (point values with 80% intervals, and event probabilities) with rl4cv.forecast.freeze_forecast before the real-data run; no outcome of the analyses has been computed when this runs."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from rl4cv.forecast import freeze_forecast  # noqa: E402

FORECAST = {
    # Frozen under the provisional number 18 (renumbered 19 before publication; the frozen bytes keep "18").
    "experiment": "18_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013",
    "forecaster": "Claude Code session local_268be283 (claude-opus-5-5, max effort)",
    "basis": "priors before any real-data fit: the panel's published per-system factor means, the start policy's marginal "
             "validation counts (32 mixed of 135) and synthetic-data runs only (PROTOCOL.md section 2 disclosures)",
    "scoring": "numeric predictions: inside the 80% interval or not; events: Brier score",
    "numeric": [
        {"id": "G1_auc_primary", "quantity": "AUC(q8 from random-intercept 2PL, observed mixed group) on 135 validation tasks",
         "point": 0.72, "interval80": [0.62, 0.81]},
        {"id": "G1_auc_panel_strict_rate", "quantity": "AUC(panel strict rate, mixed)", "point": 0.71, "interval80": [0.61, 0.80]},
        {"id": "G1_auc_panel_mean_smooth", "quantity": "AUC(panel mean smooth SCSC, mixed)", "point": 0.68, "interval80": [0.58, 0.78]},
        {"id": "G1_auc_features_only", "quantity": "AUC(q8 from task features only, mixed)", "point": 0.65, "interval80": [0.55, 0.75]},
        {"id": "G1_topk_mixed_share_primary", "quantity": "mixed share in the top 34 tasks by q8 (uniform share 0.237)",
         "point": 0.44, "interval80": [0.30, 0.58]},
        {"id": "E1_strict_m1_minus_m2", "quantity": "mean validation log loss, additive baseline minus random-intercept 2PL",
         "point": 0.005, "interval80": [-0.010, 0.025]},
        {"id": "E1_strict_m2_minus_m3", "quantity": "mean validation log loss, 2PL minus two-skill model (strict cells)",
         "point": 0.000, "interval80": [-0.005, 0.008]},
        {"id": "E3_rho_median", "quantity": "median over 11 folds of the fitted strict-FSC skill correlation",
         "point": 0.35, "interval80": [0.00, 0.70]},
        {"id": "E3b_spearman_strict_vs_fsc1", "quantity": "Spearman correlation of item intercepts, strict vs FSC = 1",
         "point": 0.40, "interval80": [0.20, 0.60]},
    ],
    "events": [
        {"id": "G1_pass", "event": "G1 AUC >= 0.70", "p": 0.60},
        {"id": "G1_irt_specific", "event": "G1 verdict PASS, IRT-SPECIFIC", "p": 0.08},
        {"id": "E1_strict_irt_beats_baselines", "event": "M1-M2 and M0-M2 intervals above 0 (strict)", "p": 0.40},
        {"id": "E1_harsh_irt_beats_baselines", "event": "M1-M2 and M0-M2 intervals above 0 (harsh)", "p": 0.35},
        {"id": "E1_strict_fsc_skill_adds", "event": "M2-M3 interval above 0 (strict)", "p": 0.12},
        {"id": "E1_harsh_fsc_skill_adds", "event": "M2-M3 interval above 0 (harsh)", "p": 0.45},
        {"id": "E1_strict_smooth_worse", "event": "smooth-calibrated MAE worse than rate-calibrated, interval below 0 (strict)", "p": 0.25},
        {"id": "E1_strict_smooth_better", "event": "smooth-calibrated MAE better than rate-calibrated, interval above 0 (strict)", "p": 0.05},
        {"id": "E2_strict_features_predict_unseen", "event": "E2c strict: no-features minus features interval above 0", "p": 0.85},
        {"id": "E2_harsh_features_predict_unseen", "event": "E2c harsh: no-features minus features interval above 0", "p": 0.75},
        {"id": "E3_two_skills", "event": "E3a untied minus tied interval above 0", "p": 0.70},
    ],
}


def main() -> None:
    entry = freeze_forecast(FORECAST, HERE / "forecasts", "e18_forecast", outcomes_observed=False)
    print(entry)


if __name__ == "__main__":
    main()
