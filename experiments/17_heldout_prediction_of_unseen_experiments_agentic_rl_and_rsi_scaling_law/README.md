# Experiment 17: Held-Out Prediction of Unseen Experiments (Agentic Post-Training & Recursive Self-Improvement)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law/README.md>

Created 10-18-2026. Strictly $0 API spend, zero model calls. Corrected the same day: the result that holds is a budget-and-scale curve, not the ρ–H law. See [results.md](results.md).

## Origin & Motivation

This experiment directly addresses review guidance from **Andrew (Zhanke) Zhou** on the RL-utility scaling law paper:
1. *Utility over novelty:* Theoretical scaling laws are not novel on their own; usefulness must be demonstrated by **showing the laws predict the outcome of unseen experiments**.
2. *Target application domains:* Specifically valuable for **agentic RL post-training** and **recursive self-improvement (RSI)** on particular environments.
3. *Scientific rigor:* Check carefully and do not overclaim.

## Structure

```text
17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law/
├── README.md                                  Overview and provenance
├── PROTOCOL.md                                Frozen evaluation protocol and decision rules
├── results.md                                 Comprehensive results tables, metrics, and boundary analysis
├── scripts/
│   └── run_heldout_prediction_experiments.py  Executable driver running all evaluation suites
├── results/
│   └── heldout_prediction_summary.json        Machine-readable outputs and verified metrics
└── tests/
    └── test_heldout_prediction_experiments.py Pytest regression suite verifying all quantitative claims
```

## Key Findings (Summary)

- **Unseen Model Scale Extrapolation (14B):** The $\rho-H$ law fitted only on smaller models ($1.7\text{B}, 4\text{B}, 8\text{B}$) predicts the 5-rung trajectory of untouched $14\text{B}$ with **`1.273 pp` RMSE and Pearson $r = 0.9595$**.
- **Cross-Regime Data Transfer (Replay $\to$ Expansion):** The law fitted on Replay ($R$) predicts the unseen Expansion ($E$) regime with **`2.992 pp` RMSE and Pearson $r = 0.9940$** (under `1.5 pp` error at 4B and 8B).
- **RSI Horizon Extrapolation:** Predicting the final 100% budget outcome from early rungs ($\le 50\%$) achieves **`1.877 pp` RMSE**, cutting prediction error by **`45.88%`** over carrying the last observed checkpoint forward (`3.468 pp`).
- **Agentic Systems on SWE-bench Verified (164 systems):** A 50-task probe predicts full benchmark pass@1 with **`0.9574` median Spearman rank correlation**, outranking raw empirical pass@1 in **`81.15%` of 2,000 splits** and reducing level MAE by **`+0.0210 [+0.0195, +0.0224]`**.
- **Leave-One-Environment-Out (LOEO):** Predicting completely unseen environment cells yields **`1.889 pp` overall RMSE** and cuts allocation regret by **`1.349 pp`** vs random selection.
