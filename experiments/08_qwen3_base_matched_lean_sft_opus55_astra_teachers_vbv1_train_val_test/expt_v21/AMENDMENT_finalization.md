# expt_v21 — Accepted-only tiny repair admission

## Declared data and timing

This amendment describes admission of the fixed 500 tiny Python-to-Lean examples after their 25 Terra/high worker lanes finish. It does not change the running experiment 20 training cohort, start training, call a model, or compile Lean.

The source is `curriculum/training.jsonl`, SHA-256 `2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119`. The original system and user messages, FILE envelope, implementation, API, specification statements and tests stay exact. The annotated experiment 9 version is only an optional explanation seed. Each worker case has a source-bound cached parse and checker snapshots.

## Admission gates

`finalize_tiny.py` requires all 125 four-case batches to be terminal and accounts for all 500 unique source indices. Accepted case states alone are insufficient. For each proposed row it checks:

1. The original row and parsed input hashes agree with the frozen source and manifest.
2. The exact checked source matches an existing successful receipt from that case, the pinned inspector SHA-256 `5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287`, every named theorem is honest, the checked named-theorem set equals the original cached parser declarations, and the retained compiled module matches its receipt hash. If that source lacks inline explanation, the authorized comment-only adapter may produce a separate annotated training source as specified below.
3. Every original byte outside the targeted parsed proof terms is preserved, except the prescribed proof-sketch comment immediately after the imports. The 2–10-line sketch contains English explanation. At least one meaningful English inline comment appears inside the final training proof terms. This mechanical check does not establish that every English explanation is mathematically complete.
4. Every replaced proof is a `by` term without any of the frozen 40 excluded tactics or unproved/metaprogramming escapes. Replacement lexical contexts must be complete, and new declaration commands are rejected. Preserved proofs are also checked; only an unchanged original anonymous proof whose sole excluded tactic is `native_decide` receives the existing concrete-test exception. Named numerical test theorems receive no exception.
5. The frozen evaluator's actual FILE extractor recovers the exact source. The pinned Qwen3 tokenizer's chat template preserves the exact evaluation prompt and expected assistant loss span, with fewer than 1,000 assistant loss tokens and at most 16,384 total tokens.
6. The existing exact/near screen against 764 protected validation, test and fresh references passes. Global exact normalized source and user-prompt duplicates are excluded against the unchanged live experiment 20 cohort and earlier accepted tiny rows. The baseline is `corpus_training_v20/base/data/training.jsonl`, SHA-256 `0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7` (3,568 rows).

## Outputs and receipt portability

The finalizer writes into a new build directory and publishes `lean_corpus_v21/final/` atomically after all checks finish. An existing final directory is immutable. Failed build directories remain as evidence and are not training inputs.

- `tiny_training.jsonl`: accepted rows only, with original system/user messages and the repaired assistant FILE response.
- `row_results.csv` and `excluded_rows.jsonl`: every source outcome and the precise reason for any exclusion. Kernel acceptance and training admission are separate fields.
- `freeze.json`, `protected_screen.json` and `completion.json`: source, baseline, all case bindings, protection-screen and final-output hashes and exact denominators.
- `proof_receipts_manifest.json` and `proof_receipts/tiny_NNNN/`: `CheckedSolution.lean` is the exact kernel-checked source; `Solution.lean` is the training source. Each package also includes original source/messages, cached proof ranges, envelope, original verification receipt, raw new checker receipt, scope binding, explicit comment binding and copied compiler/inspector evidence. The files are regular copies with relative manifests; old absolute paths inside raw receipts are retained as historical provenance, with copied evidence beside them. `kernel_axioms.py`, `driver_snapshot.py` and `add_missing_inline.py` preserve the inspected checker and admission code.

The root `completion.json` is written only after atomic publication. A formal pass refers to the exact `CheckedSolution.lean` source checked by the unchanged inspector. Any annotated source is linked by the separate comment-only binding; it is not claimed to have been recompiled. English commentary semantics are not independently verified. All unsuccessful, oversized, unsupported, overlapping or duplicate examples remain excluded with their recorded reason.

## Authorized comment-only annotation

During the first actual admission preflight, some kernel-accepted sources had a proof sketch but no inline proof comment. The coordinator explicitly authorized deterministic truthful comments without another model call or redundant Lean compilation. This change applies to every otherwise-qualified row missing inline comments, rather than only the first nine detected cases.

After validating the raw checked source, `add_missing_inline.py` describes an actual visible first tactic, using fixed explanations such as rewriting with the displayed equalities or expanding the displayed definitions. It inserts only line comments and whitespace inside existing proof terms. An exact insertion replay preserves every raw checked-source byte; independent comment stripping must yield identical non-comment tokens, with strings retained, and both lexical contexts must be balanced. The annotated source then passes the original scope, tactic, header/comment, FILE, tokenizer, protection and dedup gates. Unsupported visible operations remain honestly excluded if no truthful supported comment can be inserted.

The raw receipt and raw checked-source hash stay unchanged. `comment_binding.json` records the checked and annotated source hashes, receipt hash, exact insertion positions/text, identical-token hash and operation labels. The training row and portable manifest identify both hashes and the evidence kind. Worker files and case acceptance receipts are never edited; the adapter runs only during admission and launches no compilation or model work.

## Commands

Run the inexpensive local deterministic controls first:

```sh
python3 finalize_tiny.py --controls
```

After all worker batches finish, use the existing CPU-only training interpreter:

```sh
CUDA_VISIBLE_DEVICES= /lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python -u finalize_tiny.py \
  --baseline /lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/data/training.jsonl
```

This produces a separate future supplement. It does not append to or restart the running experiment 20 training job.
