# Fresh-base 1.7B training finished; validation generation is resuming

**Doc link:** [protocol](PROTOCOL.md)

**Status:** Training COMPLETE. Validation generation is RUNNING on physical GPU 5. **Last updated:** 10-19-2026 1:23 PDT.

The fresh Qwen3-1.7B-Base run in `expt_v20` finished its one declared training pass. It did not reuse a previous fine-tune or optimizer. The test split stayed sealed. Validation scores are not available yet.

| Measurement | Result |
|---|---:|
| Planned / completed optimizer updates | 1,784/1,784 |
| Admitted rows | 3,568/3,568 |
| Assistant loss tokens | 2,948,296 |
| Final logged training loss | 0.476 |
| Peak allocated GPU memory | 43.79 GiB |
| Training time | 1,973 seconds |
| Device | one A100-80GB, physical GPU 0 on skampere1 |
| Validation cells scored | 0/1,080 |

The final logged loss is the last training step, not a mean over the run. Admitted rows are 678 public proofs, 684 Python-to-Lean examples, 61 repairs and 2,145 workbook examples. Seed 20261019. Checkpoint: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/run/hf`.

Generation exited before writing any answers. The first failure was system SciPy against NumPy 2.3.5; SciPy 1.16.3 is installed in the generation environment. A second attempt on GPU 1 then failed because system PyOpenSSL did not match the environment’s cryptography. PyOpenSSL 26.4.0 now loads from that environment. The saved training weights were left in place. The waiter found physical GPU 5 empty and started generation at 1:22 PDT, process 3047869. The model loaded, 3.21 GiB of weights, and graph compilation was underway with 0 of 1,080 answers written.

The canonical run directory is owned by `eth127` and is not writable from `brando9`. Recovery writes the 1,080 validation answers under `/lfs/skampere1/0/brando9/rl4cv_v20_validation_recovery` and waits for an empty A100 among physical GPUs 1, 0 and 5. Sampling stays at the frozen settings: 8 answers, seed 91, temperature 0.6, top-p 0.95, top-k 20, 12,288 new tokens, thinking on, `<|im_end|>` stop. One GPU, about 68 GB at 0.85 memory utilization, 8-hour bound.

**TLDR-end:** [rl4cv: fresh-base checkpoint] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v20` finished 1,784/1,784 supervised updates. Validation generation is running on GPU 5, with 0/1,080 answers written at launch.
