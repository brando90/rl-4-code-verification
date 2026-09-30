# Experiments index

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/README.md>

**TLDR:** There are six designed experiments. Experiment 01 (small open models on VeriBench) is approved and ready (D-101 accepted 09-30-2026); the others wait on the gates before them ([PLAN §6](../docs/PLAN.md#6-experiments-and-gates)). Brando (09-30-2026) wants them started on SNAP, with Emily (@emxia18) running them: begin with [`scripts/cc_prompt_run_experiment_on_snap.md`](../scripts/cc_prompt_run_experiment_on_snap.md), which inventories the GPUs, picks a B200/H200/H100 host and launches an experiment's `cc.md`.

| # | Experiment | State (09-30-2026) | Next action |
|---|---|---|---|
| 01 | [Small open-weight Qwen models on VeriBench V1, single call, with signal probe](01_small_open_models_veribench_v1_single_call_baseline/README.md) | Designed; protocol locked; code and agent prompt ready; D-101 approved 09-30-2026 | Run `expt_v1/cc.md` on a GPU host via the SNAP prompt; CPU pilot in progress |
| 02 | [Lean environment pools, warm start, ρ–H probes](02_lean_environment_pools_warm_start_rho_h_probes/README.md) | Designed; agent prompt ready | Wait for gate G1; D-103, D-104, D-105 |
| 03 | [Lean 2×2 prospective scale replication (the crux)](03_lean_2x2_prospective_scale_replication/README.md) | Designed; agent prompt ready | Wait for gate G2; D-103 |
| 04 | [Reward-channel generalization: kernel versus judge-gated FSC](04_reward_channel_generalization_kernel_vs_fsc/README.md) | Designed | After 02; D-102 |
| 05 | [Cross-family composition and alignment](05_cross_family_composition_alignment/README.md) | Designed | After 03 and 04 |
| 07 | [Coverage gating: zero-signal bucket × reward density](07_coverage_gating_zero_signal_bucket_reward_density/README.md) | Designed (09-30-2026); agent prompt ready; PROTOCOL after 02 | After gate G2; needs the feedback reward channel in `rl4cv.rewards`; D-103 (≈ 90 B200 GPU-h) |

Experiment 06 (solve VeriBench, the application) has no folder yet; it follows 03–05 per the plan. Background for 07: [notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md](../notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md).
