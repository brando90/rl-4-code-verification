# CPU concurrency amendment

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v7/AMENDMENT_parallel12.md

**TLDR:** Increase CPU checking to twelve workers following the user request, preserving completed results and every scientific setting.

On October 19, 2026, the user requested greater parallelism. Increase diagnostic
checking from two to twelve workers. The host has 128 logical CPUs, approximately
1.7 TiB available memory, and a load average of approximately 41. Existing
benchmark scoring and GPU training continue unchanged.

The transition preserves every completed result, archives incomplete checks, and
rechecks only interrupted infrastructure work from the identical saved responses.
There is no new generation, altered selection, changed scorer, changed test case,
or deadline extension. The checker source hash is verified against admission.
The original two-hour checking deadline remains in force. Runtime transition and
continuation receipts record preserved results and any interrupted task IDs.
