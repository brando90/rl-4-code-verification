# Experiment 13 v3 Protocol (Amendment A7): Factored-Reward Technical Gate & GRPO Learning Pilot

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/PROTOCOL.md>

**Status:** FROZEN 10-16-2026 (`expt_v3` / Amendment A7)

**TLDR:** `expt_v2` closed at `T2 attempt 3` ([RESULTS_T2_S2.md](../expt_v2/RESULTS_T2_S2.md)) because `rollout_groups.py` (`technical=True`) assembled the `T2` batch using Arm A's binary `strict` reward (`0/255` successes, `0/31` active GRPO groups, `grad_norm = 0.0`), even though [Amendment A6](../expt_v2/AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md) had already established that `strict` reward is identically zero at the starting policy under the frozen rollout sampler (`0/4,302` anchor cells) and switched `T5` in prose to Arm B's `factored_reward`. On the **exact same 255 measured `T2 attempt 3` rollouts**, Arm B's `factored_reward` is already positive on **`21/255` (`8.24%`)** responses across **`14/31` (`45.16%`)** complete 8-rollout groups (`112/248` nonzero-advantage slots; paired gain `+45.16 pp [+29.03 pp, +61.29 pp]`, two-sided exact McNemar `p-val = 0.000122`). `expt_v3` preserves all `expt_v2` artifacts untouched, aligns the `T2` and `T5` code paths with `AMENDMENT_A6` by using `factored_reward`, executes `T2_v3` $\to$ `T3_v3` $\to$ `T4_v3` $\to$ `T5_v3`, and runs the `Qwen3-4B` GRPO pilot (`Arm B` vs `Arm A` vs `Arm P`) at `$0` API spend.

---

## 1. Recorded Step-1 GRPO Signal-Density Finding (from Retained `T2 attempt 3` Cohort)

Without generating or scoring any new responses, the retained `T2 attempt 3` scoring receipt (`/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical/T2/attempt_3/score/cells/result.json`, SHA-256 `e9f4e62094e766663acd8e7f29b343e6742dcc41899cccc88a14cd08813dce45`) directly tests Step-1 GRPO gradient starvation on `32` train tasks $\times 8$ rollouts (`256` declared slots, `255` measured, `1` deterministic timeout, `31` complete 8-rollout groups = `248` usable slots) at the `Qwen3-4B` supervised fine-tuning warm start (`step_658`):

| Reward Condition on Retained `T2 attempt 3` Cohort (`255/256` measured) | Positive-Reward Slots (`/255`) | Active GRPO Groups with Within-Group Variance (`/31`) | Nonzero-Advantage Rollout Slots (`/248`) | Paired Active-Group Gain vs Arm A `[95% CI]` | Two-Sided Exact McNemar `p-val` | Measured 1-Step Optimizer Update Outcome |
|---|---:|---:|---:|---:|---:|---|
| **Arm A (`strict` binary `pass@1`)** | `0/255` (`0.00%`) | `0/31` (`0.00%`) | `0/248` (`0.00%`) | baseline | `n/a` | `grad_norm = 0.0`, `0/399` parameter tensors changed (**100% dead-step waste**) |
| **Arm B (`factored_reward` guarded SCSC)** | **`21/255` (`8.24%`)** | **`14/31` (`45.16%`)** | **`112/248` (`45.16%`)** | **`+45.16 pp [+29.03 pp, +61.29 pp]`** | **`0.000122`** (`14` vs `0` discordant groups) | Evaluated in `T2_v3` below |

---

## 2. Code Alignment with Amendment A6 (`expt_v3`)

In `expt_v2/AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md`:
1. Rule 3 moved `T5` from Arm A (`strict`) to Arm B (`factored_reward`), because testing pipeline feasibility on an all-zero binary reward tests reward sparsity rather than the training pipeline.
2. However, two code paths in `expt_v2/phase2/` were left hardcoded to `strict` / `Arm A`:
   - `rollout_groups.py` lines 66–72 (`if technical:`) assembled `T2` groups using `row['strict']` instead of `row['factored_reward']`.
   - `t5_driver.py` (lines 24, 38, 44–45) and `technical_measurements.py` (`t5`, lines 78–102) still required `row['arm'] == 'A'` and `row['strict_successes']`.

In `expt_v3`:
- **Immutability of `expt_v2`:** No file or receipt in `expt_v2/` or `/lfs/skampere1/0/brando9/rl4cv_e13v2/` is modified. `expt_v2`'s `STOPPED_AT_T2_FAIL` status under the `strict` technical reward path remains permanent.
- **`T2_v3` (Factored-Reward Technical Update & Refit Gate):**
  - Reuses the verified `256/256` generation receipts and `255/256` scorer receipts from `T2 attempt 3` (`e9f4e620...`), assembling `groups.json` with `row['factored_reward']` (`14/31` active groups, `112/248` nonzero-advantage slots).
  - Runs the 1-step `Qwen3-4B` optimizer update, checkpoint export, 8-response refit generation, and refit log-probability check in `/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/technical/T2/`.
  - Gate criterion (`PROTOCOL § 6 T2`): `grad_norm > 0`, `before_sha256 != after_sha256` (`parameter_change == True` across the `399` state tensors), `unsupported_tokens == 0`, and `median_absolute_logprob_error <= 0.01`.
- **`T3_v3` (Deterministic Replay Gate):**
  - Replays the exact saved `T2_v3` factored-reward batch from the verified pre-update state and requires `maximum_loss_difference <= 0.001`.
- **`T4_v3` (Evaluation Cost Probe Gate):**
  - Runs the 8-cell train-only evaluation cost probe and verifies projected compute fits within the Phase 2 device-hour budget at `$0` API spend.
- **`T5_v3` & Main `Qwen3-4B` GRPO Learning Comparison (`Arm B` vs `Arm A` vs `Arm P`):**
  - Evaluates `T5_v3` on Arm B's continuous `factored_reward` moving average (`+0.02` gain from updates `1–10` to `21–30`, with one permitted extension to `60` updates per `AMENDMENT_A6`).
  - Runs the paired `Qwen3-4B` GRPO trajectories for **Arm B (Guarded SCSC Factored Reward)**, **Arm A (Direct Binary `pass@1` Reward)**, and **Arm P (Placebo)** under matched seeds (`1301, 1302`), reporting active-group fraction (non-zero GRPO gradient steps), training reward curves, and held-out validation `pass@1` and `SCSC` at `$0` spend.
