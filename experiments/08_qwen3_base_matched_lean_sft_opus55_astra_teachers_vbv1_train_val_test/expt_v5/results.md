# Elementary Python to Lean curriculum generation results

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v5/results.md

**Status:** COMPLETE. **Last updated:** 10-18-2026 23:17 PDT.

Generated **500 examples across 25 topics, 20 per topic**, using gpt-5.6-terra at high reasoning through 25 parallel cluster tmux workers and one bounded continuation for an exact duplicate. The explicitly authorized lab OpenAI key funded successful calls.

| Check | Result |
|---|---|
| Lean 4.22.0 compilation and kernel axiom allowlist | 500/500 PASS |
| Fixed Python/Lean differential comparisons | 16,000/16,000 cases PASS |
| Pinned 1.7B tokenizer, file extractor and assistant loss span | 500/500 PASS; token IDs match pinned 8B tokenizer |
| Protected validation/test references | 714 references; zero exact/near overlap tasks |
| Exact Lean duplicates after repair | 0 |
| Source/evaluated file and assistant extracted-file byte identity | 500/500 PASS |
| Export hashes | 4,950 files verified; zero symlinks |

## Size and coverage

Assistant tokens: min 97, median 137, mean 137.5, max 192, total 68,750. Every complete assistant training span is below 1000 tokens, including the file envelope, empty thinking block and end-of-message terminator.

There are 486 distinct normalized Python-plus-input-domain families; some examples intentionally revisit an operation with different proof properties. Four coordinator-authored style prototypes remain outside the 500-example target. One duplicate counting example received an additional informative count-at-most-length theorem and was reverified.

| Tactic | Examples containing it |
|---|---:|
| simp | 322 |
| rfl | 128 |
| norm_num | 100 |
| ring | 30 |
| exact | 27 |
| cases | 26 |
| by_cases | 12 |
| omega | 9 |
| rw | 3 |
| simpa | 3 |
| rcases | 2 |
| induction | 1 |

Tactic counts overlap. Counts describe this fixed artifact set; p-val=n/a. No training performance improvement is claimed.

## Deliverables

- [Training JSONL](dataset/training.jsonl)
- [Archive containing all Lean/Python sources, intent, fixed tests, evaluated Lean files and receipts](tiny_curriculum_500.tar.gz)
- [Dataset format](dataset/README.md)
- [Summary](results/summary.json), [format verification](dataset/format_1p7_verification.json), [contamination screen](dataset/contamination.json), [export verification](results/export_verification.json)

CLI usage gives an estimated $13.82 at the saved configured rates; this is not a provider invoice. See results/billing_estimate.json. The initial Vals key request was rejected at its project spend limit before completing model output; the user then explicitly authorized the lab key. No account spending limits were changed.

## Verification environment

The dataset checks above ran on cluster CPUs with the pinned Lean/Mathlib environment. The existing repository-wide suite on macOS returned 1271 passed, 58 failed and 57 skipped; existing failures include Linux /proc/pidfd assumptions and missing locked-dependency fixtures. No preexisting source files were changed. The package was later committed (it is tracked in main; QA 11-25-2026 stale-text fix).

**TLDR-end:** [rl4cv: elementary Python to Lean curriculum] All 500 requested examples passed compilation, proof-axiom, Python comparison, formatting and global admission checks; the complete package is ready.
