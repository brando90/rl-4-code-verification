# Matched replay versus cached data expansion

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/README.md>

**TLDR:** Prepare the next supervised fine-tuning comparison using existing teacher outputs: replay the original corpus versus expand it, with matched additional loss tokens at four Qwen3 Base sizes. The failure taxonomy of the step-658 validation outputs, the shared corpus admission (2,585 of 2,587 candidates) and a draft protocol are complete; the protocol is not locked and no version-3 model run has launched.

**Status:** PREPARED, NOT LOCKED — taxonomy and corpus admission done 10-14-2026 (zero model calls); [PROTOCOL.md](PROTOCOL.md) is a draft to lock before training.
**Owners:** Lethan (`@lethan3`), 1.7B/8B and the MBPP part of the lock review; Rakshit (`@rakshit-kaushik`), 4B/14B and the cached-response part. B denotes billion model parameters; MBPP means Mostly Basic Python Problems.

## Question and decision

Does additional exposure to the original training set suffice for a reliable reinforcement-learning warm start, or does an expanded corpus help at the same loss-token budget? The agreed design is in the [10-13-2026 meeting plan](../../meetings/oct_13_2026/PLAN.md). A target Smooth Conjunctive Score for Code verification (SCSC) of 0.25 is a separate performance milestone from binary success probability and mixed-success learning signal.

The comparison continues the four step-658 checkpoints under two conditions, original-data replay (R) and original plus admitted expansion (E), each for 5,752,936 additional loss tokens with validation at half and full budget. The draft [PROTOCOL.md](PROTOCOL.md) fixes corpus contents, order, learning-rate reset, optimizer state, token accounting, validation manifests, the frozen gates and the meeting's decision rule; lock it before any training.

## What is done (all zero model calls)

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

**[p 9/10] Lock and run the two-condition continuation** (owners): fill the two `[decide at lock]` confirmations in PROTOCOL.md, precompute both conditions' step schedules, freeze the 16-system validation manifest and the forecast, run the disposable dry run on the E data path, then train 1.7B/8B (Lethan) and 4B/14B (Rakshit) on skampere1 under the existing lease discipline. Compute estimate: about 2.2 / 3.6 / 4.1 / 3.8 wall-clock hours for both conditions at 1.7B / 4B / 8B / 14B from version-1 throughput.

**[p 7/10] SCSC milestone** needs the Vals-funded judge route, which has returned HTTP 403 since 10-13-2026; until then only kernel-scored validation is available. Preserve version-2 evidence and its recovery contract.
