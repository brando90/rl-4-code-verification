# Explicit-proof selection continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v9/CKPT_explicit.md

**TLDR:** Reconcile saved proof alternatives and questionable annotations without changing statements or starting training.

Created:10-19-2026 04:46PDT. Last updated:10-19-2026 05:09PDT.
## Goal
- Revisit12,823Workbook and500tiny tasks under the user's explicit-proof preference; Routine reviews use Terra; Sol is reserved for genuine ambiguity after the routing correction.
## What ran
- Completed 1,828 reviews (1,469 Sol/high; 359 Terra/medium), all original 69 through Sol; 39 changed-comment batches completed.
- Final assembly and protected screens completed; no new model training.
## Results
- 500 tiny files retained with prior accepted proof/32-case receipts; no qualifying saved explicit alternatives.
- 11,667 Workbook candidates retained, including 672 actual current kernel-verified proofs; 1,082 rejected and 74 unresolved excluded.
- Deduplicated verified training pool: 1,108 = 500 tiny + 608 Workbook; 64 duplicate statements removed, zero protected matches.
## Stuck / blocked
- Remaining 10,995 Workbook candidates require current proof checks before training admission; other audited source ingestion pending.
## Next steps
- Continue from the canonical checkout; preparation of other audited sources and current checks of unchecked Workbook candidates remain pending, with no new training launched.
- Exact runtime outputs: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v9/final/`; final summary and hashes in `results/finalization_summary.json`.
## Brando to-do
- None.
## Log
- 10-19-2026 04:46PDT -- Froze explicit-proof selection, scanned13,323tasks, prepared1,457Sol cases and launched first Sol/high worker.
- 10-19-2026 04:53PDT -- Completed39changed-comment batches,650Sol reviews and308kernel-verified decisions; broadened inventory preference while preserving native bounds, and armed the remote finalizing/recovery watch.
- 10-19-2026 05:09PDT -- Completed all 1,828 reviews and final assembly; routine queue rerouted to Terra, 1,108 verified distinct examples retained, exclusions explicit, 64 receipt admission labels reconciled without model/Lean calls.
- 10-19-2026 05:11 PDT -- Removed292completed remote worktrees after preserving/hash-checking unique artifacts; migrated and mechanically rechecked all500tiny comment records. No active training worktrees or source collections removed.
- 10-19-2026 05:12 PDT -- Published source/results in4d9bfac; mirrored37owned files byte-for-byte to canonical checkout. Remote292worker worktrees removed; local temporary checkout will be removed immediately after this final receipt is pushed. Canonical continuation: `/Users/lethan3/Documents/veribench-projects/rl-4-code-verification/`.
