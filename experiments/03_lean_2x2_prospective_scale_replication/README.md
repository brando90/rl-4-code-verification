# Experiment 03 — Lean 2×2 prospective scale replication (the crux: does the ρ–H law generalize?)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/03_lean_2x2_prospective_scale_replication/README.md>

**TLDR:** This repeats the paper's controlled experiment in Lean 4: 4 cells × 2 seeds × 4 scales, with a fixed NeMo RL contract. It fits the Eq. 7 utility model at small scales and freezes hashed forecasts for 8B and then 14B before seeing their outcomes. That tests whether the law carries over to code verification (levels L1, L2, L3 and L5 in the plan).

## Goal, hypothesis and decision criterion

Hypotheses, following [PLAN §3](../../docs/PLAN.md#3-hypotheses-what-counts-as-the-law-generalizes):

- **L1:** environment choice changes held-out Lean utility at matched budget.
- **L2 (primary):** a Lean-refit ρ–H model, frozen, predicts the untouched 14B curves. Criteria: RMSE below the budget/scale-only baseline, rank accuracy ≥ 70%, regret ≤ the fixed-label rule.
- **L3 (exploratory):** the paper's math coefficients rank Lean cells above chance.
- **L5:** within-source cell effects correlate (> 0.5) with VeriBench effects.

**Decision.** These levels decide what the paper claims: cross-domain transfer of the form (L2), of the coefficients (L3), or neither. Every prospective test is reported, including failed ones, as in the paper's own 8B miss.

## Structure

```
03_lean_2x2_prospective_scale_replication/
├── README.md
├── PROTOCOL.md          ← locked before the first RL run
├── results.md
├── forecasts/           ← frozen forecasts, .sha256 sidecars, forecast_ledger.jsonl (append-only)
└── expt_v1/
    ├── cc.md
    └── results/
```

## Method

1. **Inputs.** Experiment 02's cells (4 × 256 per scale), warm starts, frozen panel, cap and reward channel (`kernel_binary` for the law test; the judge-gated channels belong to experiment 04).
2. **RL contract.** Identical to the paper's except for the verifier and any cap change locked in `PROTOCOL.md`:
   - NeMo RL v0.6.0 with unnormalized leave-one-out advantages, token-level loss, importance correction, symmetric clipping 0.2, no KL, dynamic sampling off and overlong filtering on;
   - temperature 0.6, top-p 0.95, top-k 20;
   - AdamW 2×10⁻⁶, 128 steps of 4 prompts × 8 responses, two passes over each cell;
   - checkpoints at 16, 32, 48, 64, 96 and 128;
   - no adaptive stopping, prompt redraw or seed replacement.
3. **Evaluation at every checkpoint:**
   - `kernel_binary` pass@1 on the 1,000-task within-source panel;
   - VeriBench V1 IC_tests and IC_proofs, and exact SCSC, calling the judge only where IC_tests · IC_proofs > 0.

   Full VeriBench FSC is judged at step 128. Utility is linearly interpolated against cumulative generated tokens and compared at 25%, 50%, 75% and 100% of the largest budget all four cells share at that scale.
4. **Chronology** (every forecast written with `rl4cv.forecast.freeze_forecast` before its outcomes are read):
   1. Run 1.7B and 4B (16 trajectories). Fit Eq. 7 with `rl4cv.utility_model.fit_utility_model`.
   2. Freeze the **8B forecast**. Also freeze the **L3 forecast**: the paper's `paper_frozen_14b_model()` coefficients with standardizers from the Lean training fold.
   3. Run 8B and score both forecasts.
   4. Refit on 1.7B–8B and freeze the **14B forecast**, with its curve-level envelope from LOSO residuals.
   5. Run 14B, score, then do the four-scale LOSO refit.
5. **Baselines, following DataDecide as the paper does:**
   - model forms: budget/scale-only, ρ-only, H-only;
   - decision rules: the fixed label chosen on the training fold, raw mixedness, starting success, the uniform portfolio.
6. **L5.** Correlate the step-128 cell effects on the within-source panel with the VeriBench SCSC and IC effects.

## Dependencies

- Experiment 02's gate G2.
- Decision D-103 (about 500–700 B200 GPU-hours) and D-105 (the paper's NeMo configs).

## Status

| Step | Status |
|---|---|
| Design | Done (09-30-2026) |
| PROTOCOL.md | TODO, after experiment 02 |
| 1.7B / 4B runs | TODO |
| Frozen 8B and L3 forecasts | TODO |
| 8B runs and scoring | TODO |
| Frozen 14B forecast | TODO |
| 14B runs, scoring, LOSO | TODO |
