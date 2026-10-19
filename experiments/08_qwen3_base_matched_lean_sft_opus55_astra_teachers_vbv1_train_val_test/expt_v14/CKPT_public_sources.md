# Public-source validation checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/CKPT_public_sources.md

**TLDR:** The independent CPU batch is running on all 729 frozen candidates. The first published progress receipt has 37 formal passes and zero failures; three positive/negative controls passed. All rows remain outside training.

## Running owner

- Host: `eth127@skampere1.stanford.edu`.
- tmux: `rl4cv-public-source-verify-v14`.
- Watcher PID: 2117408; driver PID: 2117441. Read heartbeat/process identity before acting on these historical PIDs.
- Batch: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/bulk_validation/`.
- Eight single-threaded compiler slots, 60 seconds per compiler operation, no model calls or GPU use.
- `progress.json`, `row_results.csv` and per-case `checks/<id>/result.json` update remotely. CSV always includes all 729 declared rows, including pending cells.
- `completion.json` records full batch completion; `watch_completion.json` independently records successful driver exit or failure. An interrupted driver can be resumed once; deterministic gate failures stop.

## Resume work

Do not restart the running session. Run `python3 expt_v14/sync_bulk.py` from the parent experiment directory to collect compact receipts. On completion, update the live results section with per-source formal-pass/failure counts and preserve failed cells. No extra Lean checks are necessary for rows already covered by validated source- and compiled-artifact-bound receipts.

Passing does not admit a row to training. Required remaining gates: semantic/context review as appropriate, comments and sketch policy, frozen FILE extraction/Qwen template/token checks, protected overlap screens, and global deduplication. The current version 12 dataset remains frozen. A future adaptation must create a new frozen dataset/run declaration.

## Recorded preflight correction

The initial positive proof passed Lean/kernel inspection but its driver tried to open the Lean module identifier `_stdin` as an artifact path. No cohort cell was compiled in that failed preflight. The driver now verifies `evidence_dir/original.olean`. The original freeze/control/compiler artifacts and death receipt remain under `public_gap_sources_v14/preflight_failures/compiled_module_identifier_path/`. The corrected 729-source freeze and all three controls passed.

## Parent handoff

All V14 source/documents and compact receipts are ready for the parent coordinator to stage, commit and publish. This worker did not change the parent experiment index, stage files, commit, push, modify another version, launch a model, or change training. Public-source candidates and their pinned source artifact are on SNAP and do not require a live Mac to read.
