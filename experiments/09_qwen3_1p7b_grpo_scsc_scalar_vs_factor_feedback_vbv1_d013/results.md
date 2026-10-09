# Live results: Qwen3 1.7B factored-score policy training

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/results.md>

**TLDR:** Authorized design and baseline audits are recorded; no new training or improvement is measured yet.

Status: AUTHORIZED — execution preflight pending.

- Declared comparisons: strict conjunction versus smooth geometric mean; scalar versus named-factor feedback at identical smooth reward.
- Six training trajectories planned; zero completed. Throughput-only horizon selection is specified before main training.
- Maximum evaluation declaration: 945 validation and 1,554 test cells; zero measured in this version.
- Existing audit: kernel-only factors did not differentiate the inspected 1.7B/4B 75% validation outputs. These prior outcomes motivate using full FSC, not relabeling the kernel proxy as smooth.
- Resource, judge-route, optimizer and two-turn integration controls remain prerequisites. No efficacy conclusion exists.
