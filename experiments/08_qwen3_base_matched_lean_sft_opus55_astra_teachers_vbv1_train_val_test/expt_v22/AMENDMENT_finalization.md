# expt_v22 — Sol review delta admission

## Cohort and separation

This finalizer admits a separate supplement from the user-authorized `gpt-6.1-sol` / high review of terminal experiment 21 tiny-proof failures. The review cohort may grow while experiment 21 is running. Finalization requires `lean_corpus_v22/cohort_closed.json` with state `CLOSED`, an exact manifest hash, and an exact final experiment 21 completion hash.

The final cohort contains every task whose immutable experiment 21 case status is `EXCLUDED_BOUNDED_REPAIR`, and no other tasks. Its size is the actual closed manifest length, denoted N; it is not assumed to be 500 or a preliminary observed failure count. Original source indices remain their sparse positions within the fixed 500-example curriculum. Each manifest entry must bind the original task ID, original index and exact first-pass failure-status hash. All N review cases must have terminal outcomes before publication.

Experiment 21 inputs, accepted data, failures, receipts and completion stay unchanged. The review records its own two language-model attempts and four new candidate hashes per case. This admission script launches no model call, Lean compilation or training job.

## Reused strict admission

`finalize_review.py` pins and reuses experiment 21's proof-scope, comment-only annotation, protected-reference and portable-receipt helpers. The adapted per-row admission body retains the exact original system/user and FILE envelope; immutable implementation, API, specifications and tests; source-bound frozen-kernel receipt and compiled-module hashes; honest named theorems with the original named-theorem set; strict 40-tactic policy with only the original unchanged anonymous `native_decide` test exception; a 2–10-line English sketch and meaningful inline proof comments; actual frozen FILE extraction and Qwen chat-template checks; fewer than 1,000 assistant loss tokens and at most 16,384 total tokens.

When a valid checked proof lacks inline comments, the existing authorized deterministic adapter inserts truthful descriptions of actual visible tactics. It preserves every checked-source byte through exact insertion replay, verifies balanced lexical contexts and identical non-comment tokens, and records separate checked and annotated source hashes. The raw receipt and raw checked source are retained. Annotated files are not claimed to have been recompiled, and the comments' mathematical semantics are not independently verified.

The 764 protected validation/test/fresh references are screened with the unchanged exact/near screen. Global normalized-source and user-prompt duplicates are removed against both the unchanged running experiment 20 cohort and the final accepted experiment 21 tiny pool, then within the review delta. The experiment 20 baseline SHA-256 is `0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7`; the experiment 21 accepted baseline is bound to its final completion's training hash. Review task IDs must be disjoint from first-pass accepted IDs.

Pinned reused sources:

- Experiment 21 `finalize_tiny.py`: SHA-256 `53b2260793a443c82e494672513c1ea57dd856335b0040ed976f7bb45bebc00e`.
- Experiment 21 `add_missing_inline.py`: SHA-256 `ad8bea2bd9e5d7c06294a4a297ead1b236bcef733fabce2de23961e6bef32253`.
- Frozen kernel inspector: SHA-256 `5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287`.

## Outputs

`lean_corpus_v22/final/` publishes atomically after all admission work completes. Existing final outputs are immutable; interrupted build directories are not training inputs.

- `repaired_tiny_training.jsonl`: accepted review rows only, retaining original task ID and original 0–499 source index, with review-specific provenance.
- `row_results.csv` and `excluded_rows.jsonl`: outcomes for all N declared review cases, including failed proofs and any later format, commentary, protection or dedup exclusions.
- `review_manifest.json`, `cohort_closed.json`, `v21_completion.json`, `freeze.json` and `completion.json`: exact cohort, baseline and output bindings with actual denominators.
- `proof_receipts_manifest.json`, the raw frozen inspector, reused helper snapshots and copied `proof_receipts/tiny_NNNN/` packages: exact raw checked and annotated sources, original source/messages, parsed proof boundaries, source/annotation bindings, raw checker receipts, compiled modules and inspector evidence. Each accepted package also retains its first-pass failure metadata and exact experiment 21 terminal status.

The final root completion appears after atomic publication. A later explicitly selected union may combine the first-pass accepted pool and this delta by original task ID/index; this script does not modify either training cohort or launch that union's training.

## Commands

```sh
python3 finalize_review.py --controls
CUDA_VISIBLE_DEVICES= /lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python -u finalize_review.py \
  --baseline /lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/data/training.jsonl
```
