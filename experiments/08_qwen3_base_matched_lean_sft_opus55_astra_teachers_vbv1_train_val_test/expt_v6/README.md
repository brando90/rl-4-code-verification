# Qwen3 1.7B training with the 500-example concise Lean curriculum

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/README.md

**TLDR:** Compare the existing 1.7B checkpoint continued on existing data against the same checkpoint continued on existing data plus all 500 verified tiny examples. Also train 4B on augmented data, as requested. Three separate A100s run in parallel, with matched assistant-token targets and full validation. All three trainers are running; validation improvement is not yet measured. The [4B supervision amendment](AMENDMENT_4b_wallclock.md) reflects its measured offload runtime.

See the [protocol](PROTOCOL.md), [live results](results.md), [continuation checkpoint](CKPT_tiny_training.md) and [data-generation results](../expt_v5/results.md). This folder remains active while training or the warm-start decision depends on it. Training data and weights are copied and verified into `/lfs/skampere1/0/eth127/rl4cv_tiny_training`; the test split remains unopened.

The user-authorized [4B fused CPU optimizer amendment](AMENDMENT_4b_fused_optimizer.md) preserves the completed trajectory and full float32 optimizer state at a checkpoint before switching the update kernel. Its controller and validation continuation run in remote tmux `rl4cv-tiny-4b-fused`.
