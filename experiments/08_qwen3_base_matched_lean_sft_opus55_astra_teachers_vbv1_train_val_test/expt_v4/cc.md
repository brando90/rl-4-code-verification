# Sherlock training continuation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/cc.md>

**TLDR:** Complete the two frozen full-training runs in this version. Read CKPT_sherlock.md, PROTOCOL.md and results.md; adopt existing Slurm jobs rather than launching duplicates. Verify final checkpoint hashes and preserve every failed or missing run.

Keep the train-only corpus, model revision, two seeds and eight GPU-hour cap. Use the authenticated OnDemand shell for scheduler and artifact checks; no provider calls are needed. The test split stays unopened. Publish per-step tables, actual outcomes and persistent archive evidence, send the deduplicated completion notice, and stop the completion watch.

**TLDR-end:** Complete and report both declared Sherlock runs, including failure if either cannot finish.
