# Matched replay versus cached data expansion

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/README.md>

**TLDR:** The locked supervised fine-tuning comparison continues the same starting weights with original-data replay or admitted expansion at matched loss-token budgets. Phase A is complete: four training runs, eight exports, 8,640 validation cells, four paired comparisons and eight namespace diagnostics. Phase B is running; the full 17,280-cell experiment remains incomplete. [Live results](results.md).

**Status:** RUNNING (10-16-2026). [PROTOCOL.md](PROTOCOL.md) was locked and published before training on 10-15-2026. Expansion 8B has resumed on four skampere3 devices after a retained zero-update infrastructure failure; 14B waits for its frozen eight-device layout.
**Execution owner:** recovery-02, the sole writer under Brando's continuation dispatch; [checkpoint and current identities](CKPT_e08_v3.md). The original Lethan/Rakshit assignments are historical. B denotes billion model parameters; MBPP means Mostly Basic Python Problems.

## Question and decision

Does additional exposure to the original training set suffice for a reliable reinforcement-learning warm start, or does an expanded corpus help at the same loss-token budget? The agreed design is in the [10-13-2026 meeting plan](../../meetings/oct_13_2026/PLAN.md). A target Smooth Conjunctive Score for Code verification (SCSC) of 0.25 is a separate performance milestone from binary success probability and mixed-success learning signal.

The comparison continues the four step-658 checkpoints under two conditions, original-data replay (R) and original plus admitted expansion (E), each targeting 5,752,936 additional loss tokens with validation at half and full budget. The locked [PROTOCOL.md](PROTOCOL.md) fixes corpus contents, order, learning-rate reset, optimizer state, token accounting, validation manifests, gates and the decision rule. Its crossing-step totals are 5,752,936 for replay and 5,757,776 for expansion.

## Completed preparation (zero new model calls)

- [RESULTS_failure_taxonomy.md](RESULTS_failure_taxonomy.md) and [results/failure_taxonomy.json](results/failure_taxonomy.json): every one of the 4 x 1,080 validation cells classified. Every capped cell is an unterminated file; compile errors are 78-81% of cells at all sizes; the frozen scorer leaves the "compiles but unproved" buckets empty; a 48-file `lake env lean` recheck gives the first-error kinds. Code: [failure_taxonomy.py](failure_taxonomy.py).
- [results/admitted_corpus_manifest.csv](results/admitted_corpus_manifest.csv) and [results/admitted_corpus_stats.json](results/admitted_corpus_stats.json): hash-verified, converted, jointly deduplicated, held-out-screened and tokenizer-checked candidate corpus (1,315 originals + 685 cached + 585 MBPP; 2 MBPP rows rejected for length; 0 duplicates; 0 held-out hits). Encoding: [mbpp_conversion_spec.md](mbpp_conversion_spec.md). Code: [admit_corpus_v3.py](admit_corpus_v3.py). Host corpus: `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/s_v3_candidates.jsonl`.
- [RESULTS_continuation_audit.md](RESULTS_continuation_audit.md), [results/continuation_audit.json](results/continuation_audit.json), [results/cached_train_candidates.csv](results/cached_train_candidates.csv) and [prepare_continuation.py](prepare_continuation.py): the 10-13 audit and candidate inventory.

From the repository root with the project Python environment:

```bash
python experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/prepare_continuation.py
python -m pytest -q tests/test_sft_continuation_audit.py
# on skampere1 (host data): source /lfs/skampere1/0/brando9/rl4cv_e08/env_e08.sh
#   /lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/.venv/bin/python /lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/scripts/failure_taxonomy.py
#   /lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/bin/python /lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/scripts/admit_corpus_v3.py
```

The admitted expansion adds 5,429,531 rendered loss tokens but zero new VeriBench source tasks (the 685 cached responses cover 360 already-covered train tasks) plus 453 MBPP tasks; these are inventories, not promised training gains.

## Next execution boundary

**[p 10/10] Complete Phase B:** preserve healthy jobs, finish both 8B/14B continuations and all remaining 8,640 validation cells, then check paired task bootstraps, namespace diagnostics and the immutable forecast. [Recovery and completion runbook](RUNBOOK_continuation_owner.md). Scientific caps and the original finite recovery deadline remain unchanged.

The SCSC milestone remains deferred under this dispatch's zero-paid-call budget. The test split remains unopened for version 3. Final success requires checked publication and actual completion notification.
