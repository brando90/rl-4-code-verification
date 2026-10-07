# Experiment 01 zero-score diagnostic — summaries (10-07-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/results/diagnostics_10-07-2026/README.md>

**TLDR:** These are per-model summaries from recompiling all 8,064 G = 1 files of experiment 01 with the frozen scorer. They also cover two comment-and-name-only edit variants and a proof → `sorry` ablation. All are diagnostics, never VeriBench scores. The write-up and tables are in [`results.md`](../../../results.md#zero-score-diagnostic-10-07-2026-are-the-zeros-real).

| File | Contents |
|---|---|
| `model_own_files/summary_<label>.json` | One per model, from the model's unchanged files, over all 896 cells: failure classes, error categories and regions, top first errors, the reasoning-block split, and the recompile-vs-recorded mismatch list (empty for every model). |
| `namespace_escaped/summary_<label>.json` | The same fields, over only the cells with a digit-leading `namespace`, after escaping that name with `«»`. |
| `comment_syntax_repaired/summary_<label>.json` | The same fields, over only the cells the comment repairs edit (plus the namespace escape). |
| `combined_<label>__0.json` | Frozen-scorer IC_tests / IC_proofs over all 896 cells: the model's own files. |
| `combined_<label>__1.json` | The same, with namespace-escaped rows replacing the cells that variant edits. |
| `combined_<label>__2.json` | The same, also with comment-repaired rows. |

- **Scoring of each file.** `as_written` scores each file as is; `failing_proofs_sorried` first replaces the proofs that hold an error with `by sorry`.
- **Intervals.** 95% Wilson intervals over tasks.
- **Regenerating the tables.** `python diagnose_zero_scores.py --work-dir full --render --labels …` and `--combine full_nsfix full_surface`, run in `/lfs/skampere1/0/brando9/rl4cv_e01_diag_10-07-2026/`. The per-cell `rows_<label>.jsonl` files and edited Lean files stay on that host, because they contain model output on VeriBench tasks.
- **`recompile_vs_scored_mismatches` in the variant summaries.** There it lists the edited files that now compile where the recorded original did not. That is expected, not a scorer disagreement. In `model_own_files/` it is empty for every model.
- **Known gap.** `files_with_lean3_markers` came from a loose regex that also matched valid Lean 4 `cases … with`; it is not reported.
