"""TLDR: Freeze experiment 15's prospective forecast once with rl4cv.forecast.freeze_forecast, before any IRT fit or statistic is computed on the real validation-split files; the frozen file is append-only."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from rl4cv.forecast import freeze_forecast, verify_forecast  # noqa: E402

FINAL = "kernel_binary|log1p_ratio|1.0|"

FORECAST = {
    "experiment": "15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation",
    "protocol": "PROTOCOL.md revision 1 (locked by the commit before this file)",
    "forecaster": "Claude Code, claude-fable-5-1, effort max, ultracode worker for Brando (10-14-2026)",
    "seen_before_freeze": [
        "experiment 08 README status lines (8B step 658 and 14B step 334 pass the 0.05 mixed-share gate; 1.7B and 4B never pass a rung)",
        "experiment 05 summary (Base gives essentially zero RL signal at 1.7B/4B/8B); rung token counts; file headers and two rows of three files",
        "synthetic 2PL-generated stand-in runs only; no real per-rung aggregate, matrix, fit or statistic",
    ],
    "reasoning": (
        "Carrying the last rung forward is a strong baseline because the 75% and 100% rungs are close in log tokens and the policy barely "
        "moves between them, but it copies the sampling noise of k/8 per task, which an IRT forecast smooths through pooled item parameters; "
        "so I expect a modest 2PL win over B1 whose interval may or may not exclude 0. The scalar curve ignores task difficulty on a heavily "
        "zero-inflated matrix, so I expect a large and clear 2PL win over B2. 1.7B is likely degenerate at every rung and therefore ineligible; "
        "4B is probably eligible with few successes. The 2PL mixed-share forecast should run slightly high (small p on many unsolved tasks adds up)."
    ),
    "decision_rule_thresholds": {"min_eligible_sizes": 2, "min_rungs_per_size": 3, "degenerate_target_share_max": 0.10,
                                 "interval": "95% paired task bootstrap, 10,000 draws, seed 20261014", "source": "agent-suggested, frozen here"},
    "predictions": [
        {"id": "verdict_success", "path": ["success"], "probability": 0.45},
        {"id": "verdict_inconclusive", "path": ["inconclusive"], "probability": 0.20},
        {"id": "primary_mae_diff_vs_b1", "path": ["primary", "b1_last_rung", "point"], "point": 0.008, "interval80": [-0.004, 0.020]},
        {"id": "primary_mae_diff_vs_b1_excludes_zero", "path": ["primary", "b1_last_rung", "excludes_zero"], "probability": 0.55},
        {"id": "primary_mae_diff_vs_b2", "path": ["primary", "b2_scalar_curve", "point"], "point": 0.06, "interval80": [0.02, 0.12]},
        {"id": "primary_mae_diff_vs_b2_excludes_zero", "path": ["primary", "b2_scalar_curve", "excludes_zero"], "probability": 0.90},
        {"id": "n_eligible_sizes", "path": ["eligibility", "n_eligible"], "point": 3, "interval80": [2, 3]},
        {"id": "size_1p7b_eligible", "path": ["eligibility", "sizes", "1.7B", "eligible"], "probability": 0.45},
        {"id": "size_4b_eligible", "path": ["eligibility", "sizes", "4B", "eligible"], "probability": 0.75},
        {"id": "size_8b_eligible", "path": ["eligibility", "sizes", "8B", "eligible"], "probability": 0.98},
        {"id": "size_14b_eligible", "path": ["eligibility", "sizes", "14B", "eligible"], "probability": 0.98},
        {"id": "degenerate_target_share", "path": ["eligibility", "degenerate_target_share"], "point": 0.05, "interval80": [0.0, 0.17]},
        {"id": "realized_mixed_share_8b_final", "path": ["per_rung", FINAL + "8B", "truth", "realized_mixed_share"], "point": 0.08, "interval80": [0.05, 0.15]},
        {"id": "realized_mixed_share_14b_final", "path": ["per_rung", FINAL + "14B", "truth", "realized_mixed_share"], "point": 0.15, "interval80": [0.08, 0.25]},
        {"id": "realized_mixed_share_4b_final", "path": ["per_rung", FINAL + "4B", "truth", "realized_mixed_share"], "point": 0.02, "interval80": [0.0, 0.05]},
        {"id": "realized_mixed_share_1p7b_final", "path": ["per_rung", FINAL + "1.7B", "truth", "realized_mixed_share"], "point": 0.005, "interval80": [0.0, 0.03]},
        {"id": "irt_2pl_mae_8b_final", "path": ["per_rung", FINAL + "8B", "arms", "irt_2pl", "mae"], "point": 0.05, "interval80": [0.03, 0.08]},
        {"id": "b1_mae_8b_final", "path": ["per_rung", FINAL + "8B", "arms", "b1_last_rung", "mae"], "point": 0.06, "interval80": [0.035, 0.09]},
        {"id": "b2_mae_8b_final", "path": ["per_rung", FINAL + "8B", "arms", "b2_scalar_curve", "mae"], "point": 0.12, "interval80": [0.07, 0.20]},
        {"id": "irt_2pl_mixed_share_error_8b_final", "path": ["per_rung", FINAL + "8B", "arms", "irt_2pl", "mixed_share_error"], "point": 0.02, "interval80": [-0.03, 0.06]},
        {"id": "irt_2pl_mixed_share_error_14b_final", "path": ["per_rung", FINAL + "14B", "arms", "irt_2pl", "mixed_share_error"], "point": 0.02, "interval80": [-0.04, 0.07]},
        {"id": "b1_mixed_share_error_8b_final", "path": ["per_rung", FINAL + "8B", "arms", "b1_last_rung", "mixed_share_error"], "point": -0.01, "interval80": [-0.05, 0.03]},
        {"id": "pooled_rate_decreases_8b", "path": ["monotonicity", "8B", "pooled_rate_decreases"], "point": 0.5, "interval80": [0.0, 1.0]},
        {"id": "pooled_rate_decreases_14b", "path": ["monotonicity", "14B", "pooled_rate_decreases"], "point": 0.5, "interval80": [0.0, 1.0]},
        {"id": "all_fits_converge", "path": ["fits", "all_converged"], "probability": 0.85},
    ],
}


def main() -> None:
    entry = freeze_forecast(FORECAST, HERE / "forecasts", "e15_forecast", outcomes_observed=False)
    assert verify_forecast(HERE / "forecasts" / "e15_forecast.json")
    print(entry)


if __name__ == "__main__":
    main()
