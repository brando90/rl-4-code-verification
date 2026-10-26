# Auxiliary Lean proof data and explanatory comments

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v8/README.md

**TLDR:** User-authorized preparation of public proof sources and commented copies of500existing training examples. This prepares data; it does not start training.

[Protocol](PROTOCOL.md) · [Results](results.md) · [Checkpoint](CKPT_corpus.md)

Runtime: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v8`. Local coordinator checkout is `/Users/lethan3/Documents/veribench-projects/.worktrees/rl4cv-lean-corpus-10-19-2026`. Current preparation feeds the active warm-start study, so this folder remains active.

## Artifacts and format

- `annotations/training.jsonl`:500commented tiny training examples, retaining the original system/user prompts and replacing only the assistant Lean file with its commented copy. All original code and proofs are preserved.
- `workbook_annotations/manifest.jsonl`:12,823public proof candidates, one supplied script (index0) per original statement, with source IDs, splits, original hashes and protected-screen status.
- `workbook_annotations/examples/<id>/`: commented `Solution.lean`, model-authored `comments.json`, mechanical `receipt.json`, and the final tokenizer/extractor `format_receipt.json`.
- `workbook_annotations/normalized_candidates.jsonl`: auxiliary theorem-to-complete-file conversations in the same system/user/assistant envelope, `FILE:` marker and Lean fence. These explicitly remain unadmitted until current-toolchain proof verification.
- `workbook_annotations/batches/`: fixed64-row input units, bounded CLI attempts and status/coverage receipts. Raw model logs are retained on the host and are never training targets.
- `workbook_annotations/progress.json`, `usage.json`, `completion.json`: live pool status, token-based cost estimate and final completion status. `row_results.csv` records every declared row, including missing/failed/flagged candidates.

The100worker sessions are named `codex-rl4cv-workbook-000` through `codex-rl4cv-workbook-099`. On skampere1, use `tmux attach -t codex-rl4cv-workbook-000` to inspect a worker, or `tmux attach -t rl4cv-workbook-comment-watch` for the progress/recovery watch. Completed worker sessions exit normally; completed artifacts remain on disk. This run performs comment insertion and normalization, without Lean recompilation or model training.
