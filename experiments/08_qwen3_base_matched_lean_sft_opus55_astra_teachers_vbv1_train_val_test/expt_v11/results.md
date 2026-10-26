# All 68 unresolved Workbook proofs repaired and verified

**Doc link:** [experiment home](README.md)

**TLDR:** Complete: all 68 unchanged target statements have explicit Sol/high repairs passing pinned Lean/kernel and warm-start-format checks. Seven exact duplicate statements leave 61 unique training examples. No validation/test-reference overlap was found.

**Last updated:** 10-19-2026 06:05 PDT.

| Check | Result |
|---|---:|
| Declared repair cases | 68 |
| Actual pinned Lean/kernel passes | 68 |
| FILE extraction and Qwen template/token passes | 68 |
| Unique training rows | 61 |
| Duplicate statements excluded from training | 7 |
| Protected references screened | 764 |
| Exact / near protected hits | 0 / 0 |

## Method and evidence

Sixteen `gpt-6.1-sol` high-reasoning Codex CLI workers ran on skampere1 with four compiler slots. Every original theorem name, statement and hypothesis is preserved; new proved helper lemmas and explicit replacement proofs were allowed. Final source contains no discouraged automation, sorry, admit, new axioms or native_decide. Each final exact source hash has a successful frozen kernel receipt with allowed axioms only.

The [per-case table](results/final_row_results.csv), [final summary](results/final_summary.json), [statement audit](results/statement_audit.json), [usage](results/usage.json) and [completion](results/completion.json) retain the measured evidence. All seven duplicate exclusions were also checked for statement identity after renaming the root theorem and collapsing whitespace. All 68 final proofs remain available.

Assistant answer lengths: minimum 212, median 389.5, maximum 1,464 tokens; 62/68 below 1,000. The frozen total-conversation cap is 16,384. Configured-rate cost estimate was approximately $7.05, not an invoice; cache-write surcharges are unknown.

## Artifact locations

Runtime root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v11/`. Exact final Lean files and receipts: `final/examples/<task_id>/`; training file: `final/repaired_training.jsonl`, SHA-256 `0119aeeecc699e8c5b80d7b29e8a195399a9db56ff3364bcfe41b3d9652edffb`. Raw CLI records and compiler snapshots remain on the execution host. Sixteen finished micro-worktrees were removed after preserving unique artifacts and verifying their hashes; [cleanup receipt](results/cleanup.json).

This is the completed 68-case repair batch. Broader corpus assembly and the newly authorized 1.7B training campaign are recorded separately in versions 12–14. No training was performed in this repair phase.
