# Sherlock H100 two-seed Lean supervised fine-tuning

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/README.md>

**TLDR:** Both full Qwen3-1.7B-Base training replications completed, with all 1,316 updates and persistent exports verified in 2.12 GPU-hours. [Protocol](PROTOCOL.md), [completed results](results.md), and [checkpoint](CKPT_sherlock.md) distinguish prepared, queued, running and completed work.

The two data-order seeds use one 80 GB H100 at a time. This separately labelled Transformers implementation is not a result from the frozen NeMo conditions. The live dependency is Sherlock training capacity for the ongoing warm-start program; preserve this folder while that dependency remains.
