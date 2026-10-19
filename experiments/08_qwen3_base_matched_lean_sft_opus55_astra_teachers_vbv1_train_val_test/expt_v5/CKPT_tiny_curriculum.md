# Elementary Python to Lean generation checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v5/CKPT_tiny_curriculum.md

**TLDR:** All 25 Terra/high CLI workers finished on skampere1 under the explicitly authorized lab OpenAI key. Four coordinator prototypes passed compilation, axiom checks, 32-case comparisons and exact 1.7B/8B tokenizer formatting. All 500 examples passed final admission and export-hash verification.

## Current state

- COMPLETE: 500/500 examples admitted; 25 topics x20; no outstanding generation, repair or admission work.
- Canonical local directory: `/Users/lethan3/Documents/veribench-projects/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v5`.
- Deliverables: `dataset/training.jsonl`, `tiny_curriculum_500.tar.gz`, `dataset/examples/`, and `results.md`.
- All 500 compiled under Lean 4.22.0, passed the axiom allowlist, 32 fixed Python comparison cases each, exact 1.7B/8B format identity, protected-reference screening and deduplication. All 4,950 exported file hashes verified; no symlinks.
- Complete assistant spans: min97, median137, mean137.5, max192, total68,750 Qwen tokens.
- Cluster root remains `/lfs/skampere1/0/eth127/rl4cv_tiny_curriculum`; final snapshot in `final/`. All 25 model workers finished. Worker artifacts stay at the original paths; their scratch git worktrees were retired after verified preservation.
- User authorized the lab OpenAI key after the Vals project key hit an enforced spend limit. Temporary remote credential copies were deleted after all workers and admission finished; original credentials remain untouched.
- API usage estimate: $13.82 at saved rates, not an invoice. See results/billing_estimate.json.
- Dataset checks PASS. Existing repository-wide macOS tests: 1271 passed, 58 failed, 57 skipped; Linux-only process assumptions and missing locked-dependency fixtures are recorded. No preexisting code was edited; no commit/push was performed.
- The detached source checkout was copied into the canonical folder with file-hash verification and removed. Do not relaunch completed workers or overwrite the final results with a stale progress mirror.
- Model training has not started. Any training experiment uses a separately specified protocol; the frozen older runs remain separate.

## Events

- 10-18-2026 PDT: froze the 500-task central manifest, verified four prototypes, switched from rejected Vals project key to explicitly authorized lab key, launched all 25 Terra/high workers, and verified exact 1.7B/8B tokenizer identity on the four prototypes.

## Completion

- 10-18-2026 23:17 PDT: 500/500 admitted; 0 protected overlaps; 0 duplicate Lean files; 4,950 exported files hash-verified; no symlinks.
- Canonical local deliverables: `/Users/lethan3/Documents/veribench-projects/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v5`.
- Training JSONL and archive are self-contained artifacts; Lean dependencies are pinned in the package. No training was launched.
- Source worktree is retired after verified copy into the canonical repository; do not relaunch finished workers.
