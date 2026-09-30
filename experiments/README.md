# Experiments index

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/README.md>

**TLDR:** There are five designed experiments. Experiment 01 (small open models on VeriBench) is ready to run once decision D-101 is made; the others wait on the gates before them ([PLAN §6](../docs/PLAN.md#6-experiments-and-gates)).

| # | Experiment | State (09-30-2026) | Next action |
|---|---|---|---|
| 01 | [Small open-weight Qwen models on VeriBench V1, single call, with signal probe](01_small_open_models_veribench_v1_single_call_baseline/README.md) | Designed; protocol locked; code and agent prompt ready | D-101 (self-hosted inference), then run `expt_v1/cc.md` |
| 02 | [Lean environment pools, warm start, ρ–H probes](02_lean_environment_pools_warm_start_rho_h_probes/README.md) | Designed; agent prompt ready | Wait for gate G1; D-103, D-104, D-105 |
| 03 | [Lean 2×2 prospective scale replication (the crux)](03_lean_2x2_prospective_scale_replication/README.md) | Designed; agent prompt ready | Wait for gate G2; D-103 |
| 04 | [Reward-channel generalization: kernel versus judge-gated FSC](04_reward_channel_generalization_kernel_vs_fsc/README.md) | Designed | After 02; D-102 |
| 05 | [Cross-family composition and alignment](05_cross_family_composition_alignment/README.md) | Designed | After 03 and 04 |
