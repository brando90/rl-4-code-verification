# Verify retained Workbook proof candidates on the current toolchain

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v10/README.md

**TLDR:** Complete current Lean/kernel checks for all 10,995 retained Workbook candidates that lack them. Earlier annotations, source statements and curation decisions remain intact.

[Protocol](PROTOCOL.md) · [Results](results.md) · [Checkpoint](CKPT_verification.md)

`bulk_verify.py prepare` freezes source hashes and the full cohort under `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v10/`. `run --workers 48` checks the whole queue with the pinned frozen inspector, writes compiler receipts and periodically updates progress and a row table. It supports bounded restarts through immutable per-cell receipts and an exclusive coordinator lock.

This phase establishes formal proof validity only. Earlier rejected statement/intent mismatches require semantic review; a compiler PASS does not reverse them. The 74 unresolved cases remain excluded pending cause-specific recovery.

Native GX10 acceleration is installed and active:16slots on a frozen1,600-source subset, alongside48cluster slots. `gx10_worker.py` verifies the native environment before the same frozen inspector runs. `relay_gx10.py` validates and relays successful exact-source receipts to unstarted cluster cells, retaining raw evidence by host. `sync_progress.py --watch --publish` publishes milestone snapshots and stops after both jobs finish. These two laptop processes perform orchestration only; all Lean compilation remains on the remote machines.
