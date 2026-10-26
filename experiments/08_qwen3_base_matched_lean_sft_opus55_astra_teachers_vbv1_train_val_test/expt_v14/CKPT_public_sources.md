# Public-source validation checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/CKPT_public_sources.md

**TLDR:** Complete: 688/729 candidates passed formal checks; all 688 were assessed for admission, yielding 678 ready exercises (209 Mathlib, 469 DeepSeek). Final artifact is `admission_v2/training.jsonl`, bound by the stable `latest_admission.json` pointer. No model calls or training were launched here.

## Completed jobs

- Host: `eth127@skampere1.stanford.edu`.
- tmux: `rl4cv-public-source-verify-v14`.
- Watcher PID: 2117408; driver PID: 2117441. Read heartbeat/process identity before acting on these historical PIDs.
- Batch: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/bulk_validation/`.
- Eight single-threaded compiler slots, 60 seconds per compiler operation, no model calls or GPU use.
- `progress.json`, `row_results.csv` and per-case `checks/<id>/result.json` update remotely. CSV always includes all 729 declared rows, including pending cells.
- `completion.json` records full batch completion; `watch_completion.json` independently records successful driver exit or failure. An interrupted driver can be resumed once; deterministic gate failures stop.

The above PIDs and session describe the completed formal batch, not active workers. Final bulk result: 729/729 accounted, 688 formal passes, 39 syntax failures, one missing identifier and one other formal-check failure. The subsequent ordinary admission session `rl4cv-public-source-admit-v14` also completed with exit code 0; no restart is needed.

## Resume work

Do not restart either completed session. Run `python3 expt_v14/sync_bulk.py` and `python3 expt_v14/sync_admission.py` from the parent experiment directory to collect compact receipts. No extra Lean checks are necessary for rows already covered by validated source- and compiled-artifact-bound receipts.

The admission pass completed the declared comments/sketch, frozen FILE/Qwen token, 764-reference overlap and global deduplication gates against all 10,940 frozen current version 12 rows. It admitted 678 rows and recorded all ten exclusions. Formal exercises are not a claim of English-to-formal semantic alignment. The current version 12 dataset remains frozen; a future adaptation must merge the supplement into a new frozen dataset/run declaration.

Stable pointer: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/latest_admission.json`, `state=READY`, `version=admission_v2`. Exact training SHA256: `b7cdd07367612a5c2a95b6595fcc0606a6e4d4a970ded9125d575b53ae5f4f1a`. Version 1 is preserved, with `superseded.json`; never select it for a new regime. Version 2 corrects four `let` comment headers, and its 678 rows contain 308,320 assistant loss tokens. The annotated source is bound to verified original code by exact comment-only roundtrips, not a false claim of recompilation.

## Recorded preflight correction

The initial positive proof passed Lean/kernel inspection but its driver tried to open the Lean module identifier `_stdin` as an artifact path. No cohort cell was compiled in that failed preflight. The driver now verifies `evidence_dir/original.olean`. The original freeze/control/compiler artifacts and death receipt remain under `public_gap_sources_v14/preflight_failures/compiled_module_identifier_path/`. The corrected 729-source freeze and all three controls passed.

## Parent handoff

All V14 source/documents and compact receipts are ready for the parent coordinator to stage, commit and publish. This worker did not change the parent experiment index, stage files, commit, push, modify another version, launch a model, or change training. Public-source candidates and their pinned source artifact are on SNAP and do not require a live Mac to read.
