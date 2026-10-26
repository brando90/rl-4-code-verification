"""TLDR: Unit tests for experiment 20's statistics helpers: the cluster bootstrap resamples whole task groups, the paired difference recovers a known effect with a near-nominal interval, the sign-swap test is exact, AUC handles ties, log loss and ECE match hand values."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/stats_e20.py"
spec = importlib.util.spec_from_file_location("stats_e20", SRC)
ST = importlib.util.module_from_spec(spec)
sys.modules["stats_e20"] = ST
spec.loader.exec_module(ST)


def test_group_bootstrap_keeps_groups_together():
    groups = np.repeat(np.arange(10), 3)
    idx = ST.group_bootstrap_indices(groups, np.random.default_rng(0))
    assert idx.size == 30
    counts = np.bincount(groups[idx], minlength=10)
    assert all(c % 3 == 0 for c in counts)


def test_paired_difference_interval_and_p():
    rng = np.random.default_rng(1)
    n = 200
    groups = np.repeat(np.arange(100), 2)
    a = rng.binomial(8, 0.1, n) / 8
    b = np.clip(a + rng.binomial(8, 0.05, n) / 8, 0, 1)  # b is higher by ~0.05
    r = ST.paired_group_bootstrap(lambda i: float(np.mean(b[i] - a[i])), groups, draws=2000, seed=3)
    assert r["lo"] > 0 and r["p_two_sided"] <= 0.001 and 0.03 < r["point"] < 0.07
    null = ST.paired_group_bootstrap(lambda i: float(np.mean(a[i] - a[i])), groups, draws=200, seed=3)
    assert null["point"] == 0 and null["p_two_sided"] == 1.0


def test_sign_swap_exact():
    r = ST.sign_swap_test(np.array([1.0, 2.0]))
    assert r["p_two_sided"] == 0.5  # 2 of 4 sign patterns reach |mean| >= 1.5
    with pytest.raises(ValueError):
        ST.sign_swap_test(np.ones(13))


def test_auc_and_losses():
    assert ST.auc(np.array([0.9, 0.8, 0.2, 0.1]), np.array([1, 1, 0, 0])) == 1.0
    assert ST.auc(np.array([0.5, 0.5, 0.5, 0.5]), np.array([1, 1, 0, 0])) == 0.5
    assert abs(ST.auc(np.array([0.9, 0.3, 0.6, 0.1]), np.array([1, 1, 0, 0])) - 0.75) < 1e-12
    assert np.isnan(ST.auc(np.array([0.1, 0.2]), np.array([1, 1])))
    assert abs(ST.log_loss(np.array([0.5, 0.5]), np.array([1, 0])) - np.log(2)) < 1e-12
    assert abs(ST.ece(np.array([0.9, 0.9, 0.1, 0.1]), np.array([1, 1, 0, 0])) - 0.1) < 1e-12
    assert "p-val=" in ST.fmt({"point": 0.1, "lo": 0.0, "hi": 0.2, "p_two_sided": 0.05})
