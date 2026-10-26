# Explicit-proof curation completed with recorded exclusions

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v9/results.md

**TLDR:** Completed 10-19-2026: all 1,828 review cases and all 39 changed-comment batches finished. The final assembly contains 500 tiny examples and 11,667 Workbook candidates; 672 Workbook candidates have actual current kernel checks. After removing 64 duplicate statements, the verified training pool contains 500 tiny examples plus 608 Workbook proofs. No new training has started.

## Final accounting

| Source or phase | Declared | Final outcome |
|---|---:|---|
| Tiny Python-to-Lean | 500 | All 500 commented, formatted and admitted; unchanged code matches prior accepted compilation and 32-case differential receipts. |
| Workbook | 12,823 | 11,667 formatted candidates; 1,082 statement rejections and 74 unresolved cases excluded. |
| Questionable or preference-policy cases | 1,828 | 260 verified original keeps, 412 verified supplied replacements, 1,082 rejections, 74 unresolved. |
| Changed or missing annotations | 2,462 in 39 batches | All 39 batches completed. |
| Verified pool before deduplication | 1,172 | 500 tiny plus 672 Workbook; no exact or near protected-set matches. |
| Verified pool after deduplication | 1,108 | 500 tiny plus 608 Workbook; 64 duplicate Workbook statements removed. |

These are curation counts on selected cases, not model benchmark scores. The **10,995 other formatted Workbook candidates lack current compiler/kernel checks and are excluded from the verified training pool**. Full [row accounting](results/row_results.csv), [completion receipt](results/completion.json), [final summary and output hashes](results/finalization_summary.json), and [protected-screen summary](results/protected_screen_summary.json) are committed. All 13,323 declared tasks have a row; there are zero missing follow-ups or unexpected finalizer failures.

## Proof preference and annotations

Every Workbook statement's supplied proof alternatives were scanned (223,156 scripts total). Initial selection changed 2,661 Workbook scripts; the later expanded automation inventory and targeted review can override those initial choices. Existing proof scripts were selected, never generated anew, and mathematical statements were preserved. Plain `exact`, `apply`, `rw`, `rfl`, structural steps, and explicit `linear_combination` remain eligible. Search and broad automation are disfavored when a qualifying supplied proof exists; valid fallbacks remain labeled when it does not. This is a documented inventory, not a claim to enumerate arbitrary custom Lean tactics. No `linsolve` occurs in this collection.

All 500 tiny examples were also compared with matching saved versions, requiring identical implementations and theorem/test statements outside proof bodies. No qualifying saved alternative was found. Their original verified proofs and existing explanatory sketches/comments are retained. Comments are checked mechanically against exact original source bytes; unchanged tiny files were not recompiled. All tiny assistant answers remain under 1,000 tokens.

The first Workbook annotation pass preserved its failed batch statuses and recovered 12,822 usable per-row outputs; version 9 supplied the missing annotation and reconciled subsequent flags. Each retained file passes comment integrity, exact frozen FILE extraction, and the pinned Qwen conversation-template/token checks. Workbook tasks retain their genuine mathematical prompts; no Python inputs were invented. Brief proof sketches and inline explanations are training text; private agent traces and intermediate model work are excluded.

## Routing correction

The user initially requested Sol for 69 questionable cases. The coordinator broadened that queue to later annotation and policy flags. After the user questioned that expansion, unstarted routine cases were routed to Terra/medium, while completed and in-flight Sol work was retained. Final decisions: **1,469 Sol/high and 359 Terra/medium**. All original 69 were reviewed by Sol. No Terra case requested further Sol escalation. See the [routing amendment](results/routing_amendment.json).

The models were `gpt-6.1-sol` and `gpt-5.6-terra`, through Codex CLI 0.114.0 on skampere1 using the previously authorized lab credential. The completed version-9 configured-rate estimates are $63.02 Sol review, $17.58 Terra review and $6.37 changed-script annotation. These are estimates, not provider invoices; unknown cache-write surcharges and version-8 work are excluded. See [token receipts](results/usage.json).

## Verification and limitations

A positive review decision required an actual pinned frozen Lean/kernel PASS for the selected source hash, with only the permitted kernel axioms. Checks were bounded to four distinct supplied candidates per case, 15 seconds per compiler operation and 24 global compiler slots. A timeout remains unresolved rather than proving invalidity. Rejecting a mismatched or vacuous statement does not authorize editing that statement. Raw decisions, alternatives and compiler receipts remain beside the cluster artifacts.

Repository verification: **1,362 tests passed, 24 skipped, 6 subtests passed** on Linux; skips retain the recorded unavailable foreign fixtures. Nineteen focused comment-integrity, proof-preference and routing controls passed without model calls or Lean compilation. The full repository gate preceded the final experiment-helper routing changes; focused controls and the completed end-to-end assembly cover those changes. See [test receipt](results/test_gate.json).

Final artifacts reside at `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v9/final/`:

- `tiny_training.jsonl`: 500 annotated tiny examples.
- `workbook_candidates.jsonl`: 11,667 annotated candidates with explicit verification/admission flags.
- `workbook_verified_reviewed.jsonl`: 672 checked Workbook proofs, including 64 labeled duplicates.
- `combined_verified_training.jsonl`: 1,108 deduplicated verified examples, in the warm-start conversation/file format.
- `examples/<task_id>/Solution.lean` and `receipt.json`: retained final files and final admission decisions.

The protected screen used 764 validation/test/diagnostic references, exact normalized text and word five-gram Jaccard threshold 0.7; zero exact and zero near matches. This text screen does not establish semantic independence. The tokenizer revision is pinned in the summary. Sixty-four per-example admission receipts were reconciled after deduplication; proof bytes, compiler results and JSONL hashes did not change.

Mathlib and DeepSeek source audits are complete but ingestion is pending. DeepSeek provisional preparation is authorized while license confirmation remains pending. MiniF2F/ProofNet validation sources lack supplied proof targets and are not positive training labels. This completed phase does not mean every audited source has been ingested.

All 292 completed cluster worker worktrees were removed after preserving and hash-checking their unique artifacts under each phase’s `worker_records/`. The 500 tiny annotation records were copied byte-for-byte to canonical example folders, checked against the assembled files, and finalizers now read those records. Live training workers and older source collections were preserved. [Cleanup receipt](results/cleanup_summary.json).
