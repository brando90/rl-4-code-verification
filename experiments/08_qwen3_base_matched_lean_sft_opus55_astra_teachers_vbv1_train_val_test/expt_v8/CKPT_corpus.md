# Corpus preparation continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v8/CKPT_corpus.md

**TLDR:** Prepare public auxiliary proof data and training-only explanations using Terra/high.

Created: 10-19-2026 04:23 PDT. Last updated: 10-19-2026 05:09 PDT.

## Goal
- Normalize eligible public proof sources and annotate500existing tiny examples.
## What ran
- Finished25Terra/high tiny-comment workers and100Terra/medium Workbook workers on skampere1.
- Full Linux repository gate:1362passed,24skipped,6subtests passed. User requested Sol reconciliation/new proof preference in version9.
## Results
- Tiny:500/500commented, code/template/token checks pass; prior accepted compilation/32-case receipts reused, no recompilation.
- Workbook:12,822/12,823normalized candidates,1,457heuristic flags;1missing assembly assigned to version9.
## Stuck / blocked
- DeepSeek license confirmation pending (user authorizes provisional preparation); MiniF2F/ProofNet ports lack proof targets.
- Workbook proof correctness/current-toolchain compatibility pending; annotation is not a validity certificate.
## Next steps
- Continue `../expt_v9/CKPT_explicit.md` and remote `lean_corpus_v9/live_progress.json`.
- Publish owned source/results and mirror canonical checkout after final checks.
## Brando to-do
- None.

## Log
- 10-19-2026 04:23 PDT -- Froze preparation protocol; corrected comment density and prohibited validation-derived annotation material.
- 10-19-2026 04:37 PDT -- Completed500tiny annotations and final mechanical/template admission without recompilation; launched100cluster workers on12,823Workbook candidates with an ordinary-code recovery watch.
- 10-19-2026 04:53 PDT -- Finished Workbook native pass and normalized12,822rows; all failures retained, Sol/new proof-selection policy continues in version9.
- 10-19-2026 05:09 PDT -- Version9 completed preference reconciliation: 11,667 Workbook candidates, 672 checked proofs, and 1,108 deduplicated verified examples including all500tiny. Other audited source ingestion remains pending.
