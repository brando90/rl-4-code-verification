# Prospective amendment: admit verified public proof exercises

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/AMENDMENT_training_admission.md

**TLDR:** Assess every one of the 688 formal passes for actual training admission. Add deterministic comments describing visible proof operations without altering any original source byte; require existing kernel/artifact evidence, exact source/context preservation, frozen FILE/Qwen checks, protected screens and deduplication against the frozen version 12 training pool.

## Declared cohort and purpose

The independent bulk pass completed all 729 candidates: 217/217 Mathlib and 471/512 DeepSeek files passed current Lean/kernel checks. This admission cohort is exactly those 688 formal passes; all 41 failures remain excluded. The full candidate and source manifests are unchanged. The objective is auxiliary explicit Lean proof syntax and lemma-application training, without inventing Python translations or claiming English-to-formal semantic fidelity for sources without an English statement. Current version 12 datasets/runs stay frozen; a later regime must explicitly merge any admitted output.

## Comment policy

Use no paid model calls in this admission pass. A deterministic rule may explain only a visible formal operation: introducing quantified variables, applying a named lemma, rewriting with displayed equalities, building constructor fields, taking cases/induction, or using an explicit proof term. The top proof sketch lists operations actually found in the file, in source order. Inline comments appear before recognized proof steps, usually spaced by at least three original lines. They do not guess why a mathematical inequality is true or invent an informal mathematical problem. Retain all original comments, imports, definitions, hypotheses, statements and proof tokens. Unsupported files can be excluded with a recorded reason rather than receiving fabricated explanations.

Use the existing safe lexical comment insertion helper and its exact original-byte roundtrip. Independently compare comment-stripped original and annotated source. Bind the inserted-comment list, original source hash, annotated hash and original source/kernel/compiled-artifact receipt. This reuses proof evidence for unchanged code; it does not claim the annotated bytes themselves were recompiled. Exclude source-position metaprogramming contexts from this reuse. A potential untyped fractional-exponent risk flag remains quarantined pending review.

## Gates and frozen inputs

1. Freeze the exact 688-row admission manifest, original candidate hashes, completed bulk manifest/controls, source revisions, driver hash, original proof receipt hashes and the version 12 current-training hash before admission.
2. Validate the unchanged kernel inspector and each successful receipt, original source hash, compiled `original.olean` hash, all honest named theorems and original context check.
3. Preserve both original input messages and their exact source-prefix context. Only the assistant file changes through inserted comments. Use the actual frozen FILE extractor, Qwen tokenizer/chat template and 16,384 total-token cap.
4. Run the repo's exact and word-five-gram screens on full prompt/answer text and standalone formal statements against all 764 protected references (714 VeriBench V1 validation/test Python and Lean references plus 50 fresh diagnostic Python references).
5. Deduplicate normalized original Lean, input prompt and canonical explicit statement against every row in the frozen version 12 current pool and earlier admitted rows. Statement-only exclusion is conservative lexical redundancy, not a claim that differently scoped Mathlib contexts are semantically identical.
6. Record every declared row, admissions and exclusions; never conceal a failure or claim all 688 were admitted if gates exclude some. Retain DeepSeek's `license_unresolved_user_authorized` status.

## Output and persistence

Run the ordinary CPU finalizer in named tmux session `rl4cv-public-source-admit-v14`, with a recorded exit/completion receipt. Outputs: `training.jsonl`, `row_results.csv`, comment/source-binding receipts, screens, hashes, token counts and summary. No provider credentials or protected task contents are supplied to a model; no model is invoked. This pass neither starts training nor edits another experiment version.

The initial `admission_v1/` pass admitted 678 rows. A deterministic post-admission annotation audit found four direct `let` proof terms whose header described a named term instead of local bindings; the original code and artifacts are preserved. Before a new training merge, version `admission_v2/` corrects only that comment rule and assigns a descriptive exclusion to five frozen-FILE extraction byte mismatches. It repeats the identical 688-source admission cohort, all evidence, format and overlap gates; no proof changes, compilation or model calls are introduced. The current final training artifact is `public_gap_sources_v14/admission_v2/training.jsonl`.
