# rl-4-code-verification — experiments index

TLDR: one folder per experiment, `NN_descriptive_setup/`, each with a `README.md` design doc (TLDR first), an executable `config.yaml`, `scripts/` runbooks that open with a TL;DR, committed `manifests/`, and Markdown `results/`; large artifacts live under `/lfs` on SNAP and are linked with hashes.

| Home | Status | One line |
|---|---|---|
| [01_predict_rl_env_utility_veribench_qwen35_snap](01_predict_rl_env_utility_veribench_qwen35_snap/README.md) | DESIGN DRAFT 09-30-2026 | Measure VeriBench task subsets as RL environments (`q_mixed`, `ρ`, `H`) under Qwen3.5-2B/4B/9B, train GRPO on a 2×2 of cells, test whether the frozen ρ–H utility model predicts untouched-9B held-out improvement, and test coverage gating (binary vs per-theorem credit vs compiler feedback) on the zero-signal bucket. Run locally: [scripts/cc_prompt_launch_phase0_on_snap.md](01_predict_rl_env_utility_veribench_qwen35_snap/scripts/cc_prompt_launch_phase0_on_snap.md) (inventory SNAP GPUs, pick B200/H200/H100, set up `/lfs`, launch); on the host: [scripts/cc_runbook_phase0_coverage_census.md](01_predict_rl_env_utility_veribench_qwen35_snap/scripts/cc_runbook_phase0_coverage_census.md). |

Background notes: [notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md](../notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md).
