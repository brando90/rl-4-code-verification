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


def test_suite_1a_unseen_scale_14b_extrapolation():
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    s1a = data["suite_1_rsi_lean_code_verification"]["task_1a_unseen_scale_14b"]
    # Verify that the law trained only on 1.7B, 4B, 8B accurately predicts 14B curves
    assert s1a["law_rmse_pp"] < 2.0, f"RMSE {s1a['law_rmse_pp']} exceeds 2.0 pp"
    assert s1a["law_pearson_r"] > 0.90, f"Pearson r {s1a['law_pearson_r']} below 0.90"
    assert len(s1a["points"]) == 5


def test_suite_1c_rsi_horizon_extrapolation():
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    s1c = data["suite_1_rsi_lean_code_verification"]["task_1c_rsi_horizon_extrapolation"]
    # The law extrapolation from <=50% budget must substantially beat carrying the last observed rung forward
    assert s1c["law_extrapolation_rmse_pp"] < s1c["last_observed_rmse_pp"]
    assert s1c["relative_rmse_reduction_pct"] > 30.0, f"Error reduction {s1c['relative_rmse_reduction_pct']}% below 30%"


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
