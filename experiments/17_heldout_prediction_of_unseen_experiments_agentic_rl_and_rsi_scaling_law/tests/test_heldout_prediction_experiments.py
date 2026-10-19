"""Unit tests for Experiment 17: Held-Out Prediction of Unseen Experiments."""

import json
from pathlib import Path
import pytest

from rl4cv.utility_model import (
    Observation,
    fit_utility_model,
    RHO_H,
    BUDGET_SCALE_ONLY,
    pairwise_rank_accuracy,
    paper_frozen_14b_model,
)

EXPERIMENT_DIR = Path(__file__).resolve().parent.parent
RESULTS_FILE = EXPERIMENT_DIR / "results/heldout_prediction_summary.json"


def test_heldout_summary_file_exists_and_valid():
    assert RESULTS_FILE.exists(), f"Summary file missing at {RESULTS_FILE}"
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    assert data["experiment"] == "17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law"
    assert "suite_1_rsi_lean_code_verification" in data
    assert "suite_2_agentic_rl_swebench_verified" in data
    assert "suite_3_math_rlvr_loeo" in data


def test_budget_curve_predicts_final_rung_without_leaking_it():
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    corrected = data["corrected_no_target_leakage"]
    horizon = corrected["horizon_from_50pct_features"]
    assert corrected["budget_scale_beats_last_observed"]
    assert horizon["budget_scale"]["rmse_pp"] < corrected["last_observed_50pct_rmse_pp"]
    assert corrected["budget_scale_error_reduction_vs_last_observed_pct"] > 30.0
    assert not corrected["rho_H_beats_budget_scale_on_horizon"]
    assert not corrected["rho_H_beats_budget_scale_on_14b"]


def test_suite_2_agentic_swebench_prediction():
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    s2 = data["suite_2_agentic_rl_swebench_verified"]
    assert s2["rank_evaluation"]["median_spearman_irt_vs_heldout"] > 0.95
    assert s2["rank_evaluation"]["share_splits_irt_beats_empirical"] > 0.80
    assert s2["level_evaluation_mae"]["mae_gain_over_raw_pass1"] > 0.020


def test_suite_3_math_loeo():
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    s3 = data["suite_3_math_rlvr_loeo"]
    assert s3["overall_loeo_rmse_pp"] < 2.5, f"LOEO RMSE {s3['overall_loeo_rmse_pp']} exceeds 2.5 pp"
    assert s3["decision_regret"]["law_regret_pp"] < s3["decision_regret"]["random_candidate_regret_pp"]
