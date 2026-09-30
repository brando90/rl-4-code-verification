# Experiment 03 v1 — run the Lean 2×2 RL grid across four scales with frozen prospective forecasts

**TLDR:** You will:

- train 32 RL trajectories (4 cells × 2 seeds × Qwen3 1.7B, 4B, 8B, 14B Lean warm starts) under the paper's fixed NeMo RL contract, with VeriBench's kernel check as the verifier;
- evaluate every checkpoint on the frozen within-source panel and on VeriBench V1;
- freeze a hashed forecast before each larger scale is trained.

**Success:** every trajectory and checkpoint evaluation completes or is explicitly recorded as failed. The 8B, L3 and 14B forecasts are frozen before their outcomes and scored exactly as frozen. The L1, L2, L3 and L5 verdicts are published with their numbers.

**Deliverable:** a draft PR "Experiment 03: Lean 2×2 prospective scale replication — results" with `results.md`, the forecast ledger and the LOSO tables.

**Constraints:**

- Never open a scale's outcomes before its forecast is frozen with `rl4cv.forecast.freeze_forecast`.
- Never change the contract mid-grid.
- Never replace a failed seed by outcome.
- Launch GPU jobs only after Brando approves the estimate.

Read `~/agents-config/INDEX_RULES.md`, `CLAUDE.md`, `docs/PLAN.md`, experiment 02's `results.md` and cells, and this experiment's `PROTOCOL.md` (write and lock it first if it does not exist, following experiment 01's template).

---

## Contract (lock these values in `PROTOCOL.md`)

| Setting | Value |
|---|---|
| Framework and advantages | NeMo RL v0.6.0 (configs from the paper's archive, D-105); unnormalized leave-one-out advantages; token-level loss; importance correction; symmetric clip 0.2; no KL; dynamic sampling off; overlong filtering on |
| Decoding | temperature 0.6, top-p 0.95, top-k 20; response cap and total sequence limit from experiment 02 |
| Optimizer and schedule | AdamW 2×10⁻⁶, weight decay 0.01; 128 steps of 4 prompts × 8 responses; seeds 9001 and 9002 |
| Checkpoints | 16, 32, 48, 64, 96, 128 (weights only; a failed run restarts from the same warm start with the same seed) |
| Reward | `kernel_binary` from VeriBench's pinned kernel check, computed outside the rollout sandbox |
| Evaluation per checkpoint | within-source panel pass@1 at G = 1 with the same decoding and cap; VeriBench V1 with IC_tests, IC_proofs and exact SCSC (judge only where IC > 0, D-102) |
| Evaluation at step 128 | full FSC on VeriBench V1 |

## Steps

1. **Run 1.7B and 4B.**
   - Run the 16 trajectories and evaluate their checkpoints.
   - Build observations: the two-seed mean utility at 25%, 50%, 75% and 100% of the largest shared generated-token budget per scale, anchored at U(E, N, 0) = 0 but not fitted on the anchor.
   - Store them in `results/observations.jsonl`.
2. **Fit and freeze the 8B forecasts.**
   - Fit `fit_utility_model` on 1.7B and 4B using Stage D ρ and H.
   - Freeze `forecasts/fc_8b_rhoH` with the predicted curves, rankings and chosen cell per budget.
   - Also freeze `forecasts/fc_8b_L3`: `paper_frozen_14b_model()` coefficients with standardizers refit on the Lean 1.7B and 4B cells.
   - Record both hashes in `results.md` *before* launching 8B.
3. **Run and score 8B.** Run the 8B trajectories, then score both forecasts (RMSE, rank accuracy, regret, envelope coverage) against the baselines.
4. **Refit and freeze the 14B forecast.** Refit on 1.7B–8B and freeze `forecasts/fc_14b_rhoH` with its LOSO envelope. Record the hash, then run 14B and score.
5. **Four-scale LOSO.** Run `leave_one_scale_out` for ρ–H, ρ-only, H-only and budget/scale-only, and compute the decision-rule regrets.
6. **L5.** Correlate the step-128 within-source cell effects with the VeriBench effects.
7. **Report.**
   - `results.md` with every table and the L1, L2, L3 and L5 verdicts with numbers.
   - `results_summary_<timestamp>.md`.
   - Publish the draft PR named in the TLDR.
   - GPU cleanup.

TL;DR: This prompt trains the 32-trajectory Lean RL grid with NeMo RL and VeriBench's kernel verifier, freezes hashed Eq. 7 forecasts (via `rl4cv`) before each larger scale, scores them against simple baselines, and publishes whether the ρ–H law transfers to Lean.
