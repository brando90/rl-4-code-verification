# Prefer explicit saved proofs and reconcile questionable candidates

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v9/README.md

**TLDR:** Apply the user's automation preference to every12,823Workbook statements and500tiny examples, and reconcile flagged Workbook cases against supplied alternatives with targeted checks. This changes selection and explanations, with targeted checks; it does not start training.

[Protocol](PROTOCOL.md) · [Results](results.md) · [Checkpoint](CKPT_explicit.md)

Runtime: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v9`. Version8originals are retained under the adjacent `lean_corpus_v8` directory. `selection.jsonl` contains every task's original/selected source hash, saved alternative index, remaining discouraged tactics, and review status. Public proof candidates are unadmitted until verified.

`annotations/` owns changed-script annotation batches, raw CLI outputs, sketches and mechanical preservation receipts. `review/cases/<id>/` owns the original flag, all supplied alternatives, bounded checker receipts, selected/commented proof and decision. The original mathematical statement is never edited; a mismatched/vacuous statement stays excluded. Raw logs and alternatives remain on the cluster, with compact row tables and source code inGit.

Selection examines500tiny files against matching saved versions, requiring the implementation and every theorem/test statement outside proof bodies to match. No qualifying saved replacement was found, so these remain their original verified proofs, with automation retained and explicitly recorded. The user requested a preference when an alternative exists, not generation of new proofs for the500.

Completed curation: 1,828 reviews, 500 tiny files and 11,667 Workbook candidates. Only the 672 currently checked Workbook proofs enter the verified pool; after 64 duplicate removals it contains 1,108 examples including all 500 tiny examples. Final routing was 1,469 Sol/high and 359 Terra/medium decisions. [Final accounting](results.md).
