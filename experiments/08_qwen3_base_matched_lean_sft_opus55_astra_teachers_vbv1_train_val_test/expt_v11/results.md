# Sol explicit-proof repair status

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v11/results.md

**TLDR:** RUNNING, 10-19-2026 05:43 PDT. Sol/high: 35/68 cases complete, 35 exact-source kernel-verified explicit repairs; 16 running and 17 pending.

Compiler admission uses the same pinned Lean4.22 and frozen kernel checker, plus the explicit-tactic policy. Every failed/missing case stays in the declared68-case accounting.

## Latest execution snapshot

RUNNING, 10-19-2026 05:43 PDT. Sol/high: 35/68 cases complete, 35 exact-source kernel-verified explicit repairs; 16 running and 17 pending.

[All68case rows](results/repair_rows.csv) · [Usage estimate](results/usage.json) · [Frozen dispatch](results/dispatch.json). Raw candidates, logs, final Lean files and training artifacts remain under `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v11/`.

## Verification evidence

The first actual repair passed pinned kernel checks; the separate format preflight passed the frozen FILE extractor, Qwen template/token checks, and all764protected-reference screens. [Format preflight](results/format_preflight.json). [Checker controls](results/checker_controls_completion.json) rejected an unfinished proof and `exact?` while accepting a real explicit proof. The underlying repository src/tests are unchanged from the recorded Linux gate (1,362passed,24skipped,6subtests), with new experiment scripts additionally parsed and exercised end to end. No new training has started.
