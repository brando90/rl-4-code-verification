# Sherlock live-training screenshot

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/results/sherlock_training.md>

**TLDR:** The original browser screenshot records an H100 allocation and actual optimizer steps, not a completed experiment.

Source: authenticated Sherlock OnDemand shell; captured 10-18-2026. Image: [sherlock_training.png](sherlock_training.png). Top summary: Qwen3-1.7B-Base on NVIDIA H100 80GB HBM3, job 48378536, host sh04-01n01.int, seed 20260830, 16/658 updates and 46.56 GiB peak. A later CSV tail in the same image shows updates 22, 23 and 24, reaching 48 examples and 197,859 loss tokens at 128.58 training seconds, with 47.85 GiB peak. Scheduler lists seed 1 job 48378539 and terminal collector 48378541 pending on dependencies. The [CSV sample](launch_step_sample.csv) contains five nonconsecutive observed rows; it is not the full trajectory. Test text remains unopened; no validation or test metric is shown.
