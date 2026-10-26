# Dispatch Prompt: Experiment 13 v3 — Factored-Reward Technical Gate & Qwen3-4B GRPO Pilot (`Arm B` vs `Arm A` vs `Arm P`)

**Target host:** `skampere1.stanford.edu` (use idle GPUs `0, 5, 7` via `CUDA_VISIBLE_DEVICES`; never disturb active `Expt 08 v3` processes on GPUs `1, 2, 3, 4, 6`).
**Budget:** Strictly **`$0` API spend** (`HF_HUB_OFFLINE=1`, local `vLLM` + `DTensorPolicyWorker` + Lean 4 verifier only).

## Instructions

1. Read `~/agents-config/INDEX_RULES.md`, `CLAUDE.md`, `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_T2_S2.md`, `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md`, and `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/PROTOCOL.md`.
2. **Preserve `expt_v2` immutability:** Do NOT modify any file in `expt_v2/` or `/lfs/skampere1/0/brando9/rl4cv_e13v2/`. Work in `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/` and `/lfs/skampere1/0/brando9/rl4cv_e13v3/`.
3. **Stage 1 (`T2_v3` Factored-Reward 1-Step Update & Refit Gate):**
   - Assemble the retained 256-rollout `T2 attempt 3` cohort (`/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical/T2/attempt_3/generate_update/output` and `/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical/T2/attempt_3/score/cells/result.json`) using `row['factored_reward']` (`14/31` active 8-rollout groups, `112/248` nonzero-advantage slots) into `/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/technical/T2/attempt_1/score/groups.json`.
   - Run the 1-step `Qwen3-4B` (`step_658`) optimizer update, checkpoint export, 8-response refit generation, and refit log-probability check on an idle `skampere1` GPU (`0`, `5`, or `7`).
   - Verify and publish `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/RESULTS_T2_v3.md` comparing `strict` (`grad_norm = 0.0`, `0/399` tensors changed) vs `factored_reward` (`grad_norm > 0`, `parameter_change == True`, `median_abs_logprob_error <= 0.01`) on the **exact same 256-rollout cohort**!
4. **Stage 2 (`T3_v3` Deterministic Replay & `T4_v3` Evaluation Cost Gate):**
   - Run `T3_v3` (exact saved batch replay from the pre-update state, verifying `maximum_loss_difference <= 0.001`) and `T4_v3` (8-cell train-only evaluation cost probe).
5. **Stage 3 (`T5_v3` & Paired `Qwen3-4B` GRPO Pilot — `Arm B` vs `Arm A` vs `Arm P`):**
   - Run the paired GRPO pilot updates (seeds `1301, 1302`) for **Arm B (`factored_reward`)**, **Arm A (`strict` binary reward)**, and **Arm P (`placebo`)** on idle `skampere1` GPUs (`0, 5, 7`), recording per-step active-group fraction, `grad_norm`, training reward trajectory, and held-out validation `pass@1` and `SCSC` at `$0` spend.
   - Publish `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/results.md`, run `pytest` on your new tests, and commit and push to `origin/main`.
