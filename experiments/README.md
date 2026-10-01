# Experiments index

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/README.md>

**TLDR:** Three experiments follow Brando's two goals ([D-007](../docs/DECISIONS.md), 09-30-2026). Experiment 01 is the shared baseline and is running on SNAP. Experiment 02 is Varun's question: use the pre-RL ρ–H equation to design Lean environments and rewards that raise VeriBench's three metrics, in phases 02A–02D. Experiment 03 is Allen's coverage question: can RL move Lean prompts the starting policy never solves? The cross-family mixtures study is a deferred [idea](ideas/README.md). Brando (09-30-2026) wants the experiments run on SNAP, with Emily (@emxia18) running them: begin with [`scripts/cc_prompt_run_experiment_on_snap.md`](../scripts/cc_prompt_run_experiment_on_snap.md), which inventories the GPUs, picks a B200/H200/H100 host and launches an experiment's `cc.md`. Gates are in [PLAN §6](../docs/PLAN.md#6-experiments-and-gates).

| # | Experiment | Goal | State (09-30-2026) | Next action |
|---|---|---|---|---|
| 01 | [Small open-weight Qwen models on VeriBench V1, single call, with G=8 signal probe](01_small_open_models_veribench_v1_single_call_baseline/README.md) | Shared baseline for both goals | **Done (10-01-2026 09:08)** on `skampere1`; full declared set generated, scored and FSC-judged; Gate G1 **PASS** | Rename the folder to `01_small_qwen_vbv1_single_call_baseline_g8_signal_probe` (not yet done — deliberate follow-up, touches every cross-reference); then begin phase 02A |
| 02 | [ρ–H-guided Lean environment design, evaluated on VeriBench V1's three metrics](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/README.md) | Varun's question | Designed | Phase 02A after gate G1 |
| 02A | [Lean environment pools, warm start, ρ–H probes](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/README.md) | Build the Lean environments; measure ρ and H | Designed; agent prompt ready | Wait for gate G1; D-103, D-104, D-105 |
| 02B | [Prospective 2×2 forecast check (the crux)](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/README.md) | Does the frozen equation predict Lean RL gains? | Designed; agent prompt ready | Wait for gate G2; D-103 |
| 02C | [Reward channel for FSC: kernel versus judge](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge/README.md) | Reward for the third metric (FSC) | Designed | After 02A; D-102 decided |
| 02D | [Train the forecast-selected recipe, report VeriBench V1](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_d_train_forecast_selected_env_report_vbv1/README.md) | The application | Stub | After 02B and 02C |
| 03 | [RL on never-solved Lean prompts: binary versus dense reward](03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/README.md) | Allen's coverage question (open-weight models on SNAP) | Designed; agent prompt ready; PROTOCOL after 02A | After gate G2; needs the feedback reward channel in `rl4cv.rewards`; D-103 (≈ 90 B200 GPU-h) |
| idea | [Cross-family composition and alignment](ideas/cross_family_env_mixtures_alignment/README.md) | Extension | Deferred, not run | Revisit after 02B |

Background for 03: [notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md](../notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md).

## Old → new numbering (09-30-2026, D-007)

Commits, issue comments, earlier decision entries and experiment 01's own files written before this change use the old numbers.

| Old | New | Folder now |
|---|---|---|
| 02 Lean environment pools, warm start, ρ–H probes | 02A | `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes` |
| 03 Lean 2×2 prospective scale replication | 02B | `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check` |
| 04 Reward-channel generalization | 02C | `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge` |
| 06 Solve VeriBench (had no folder) | 02D | `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_d_train_forecast_selected_env_report_vbv1` |
| 05 Cross-family composition and alignment | idea | `ideas/cross_family_env_mixtures_alignment` |
| 07 Coverage gating | 03 | `03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1` |
