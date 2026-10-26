"""TLDR: Freeze experiment 19's predictions of its gold-check-target outcomes (protocol revision 2) with rl4cv.forecast.freeze_forecast before the real-data run; revision 1's forecast (e18_forecast.json) is unchanged."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from rl4cv.forecast import freeze_forecast  # noqa: E402

FORECAST = {
    "experiment": "19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013",
    "revision": 2,
    "forecaster": "Claude Code session local_268be283 (claude-opus-5-5, max effort)",
    "basis": "priors before any real-data fit; disclosed marginal gold-check cell accounting (PROTOCOL.md section 2) and "
             "VeriBench 111's published 896-task per-system gold-check rates only",
    "scoring": "numeric predictions: inside the 80% interval or not; events: Brier score",
    "numeric": [
        {"id": "E1_gold_m1_minus_m2", "quantity": "mean validation log loss, additive baseline minus random-intercept 2PL (gold-check cells)",
         "point": 0.005, "interval80": [-0.010, 0.030]},
        {"id": "E1c_gold_mae_smooth_calibrated", "quantity": "system-level MAE, calibrated train smooth SCSC forecasting validation gold-check pass@1",
         "point": 0.035, "interval80": [0.015, 0.070]},
        {"id": "E1c_gold_mae_rate_calibrated", "quantity": "system-level MAE, calibrated train gold-check rate forecasting validation gold-check pass@1",
         "point": 0.030, "interval80": [0.012, 0.060]},
    ],
    "events": [
        {"id": "E1_gold_irt_beats_baselines", "event": "M1-M2 and M0-M2 intervals above 0 (gold-check)", "p": 0.35},
        {"id": "E1_gold_smooth_worse", "event": "smooth-calibrated MAE worse than rate-calibrated, interval below 0 (gold-check)", "p": 0.20},
        {"id": "E1_gold_smooth_better", "event": "smooth-calibrated MAE better than rate-calibrated, interval above 0 (gold-check)", "p": 0.08},
        {"id": "E2_gold_features_predict_unseen", "event": "E2c gold-check: no-features minus features interval above 0", "p": 0.70},
    ],
}


def main() -> None:
    print(freeze_forecast(FORECAST, HERE / "forecasts", "e19_forecast_gold_target", outcomes_observed=False))


if __name__ == "__main__":
    main()
