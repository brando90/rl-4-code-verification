# Experiment 12 version 2 protocol — corrected adapter, SCSC versus hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/PROTOCOL.md>

**TLDR:** This fixes the inputs, the adapter, its controls, the per-test cell outcomes, the analyses and the stop rules for the version-2 rerun. Version 1's protocol (`../PROTOCOL.md`, locked 10-10-2026 with amendments A1 and A2) stays in force wherever this document is silent. It is locked when committed, after the zero-call mapping census and before any version-2 hidden-test outcome exists; the matching forecast is frozen in `forecasts/e12_v2_forecast.json` in its own later commit. Any later change is a dated amendment section appended here, never an edit.

**Lock line:** `LOCKED 10-14-2026 by the commit that adds this file` — adapter `scripts/adapter_v2.py` SHA-256 `6e825e94fd6838e1bc7699daba13c45c7a4540573405e42b7ea516b8bc3d8a93`; census `results/mapping_census_v2.json` as committed with this file; hidden suite `../expt_v1/results/hidden_tests_manifest.json` SHA-256 `f23f995671c12cded73f11447abd585d5a62c5ebf7b3c56aa1a2bf4d719e5b17`; inputs `../expt_v1/results/input_manifest_A1.json` SHA-256 `20ae9005857f6cff5d18325e5aa128e11b1eda7cb6833dfecffc93a21af1c5a0`. No version-2 real-candidate hidden outcome exists at lock.

## 1. Inputs (pinned; read-only; unchanged from version 1 § 1 and A1)

- Gold references at the `veribench` pin `c11b99ba`; primary panel = the 9,856 cells of `input_manifest_A1.json` with their recorded factors, compile status, join status and file hashes; secondary panels = `secondary_manifest_A1.json` (optional descriptives in version 2).
- Hidden tests = the frozen version-1 extraction (10,534 tests, 882 tasks, 14 `no_tests` tasks). DESIGN.md § 5 records why the corrected lexer does not change it.
- Excluded: sealed data (experiments 107 and 109), VeriBench V2 and multifile rows, experiment 08's test split.

## 2. Adapter (replaces version 1 § 3 and A2.1)

The adapter is `scripts/adapter_v2.py` at the hash above: the lexer of DESIGN.md § 2, the entry-point priority order of DESIGN.md § 3 (step 1 same normalized name with equal explicit arity; step 2 signature-compatible set with helper exclusion; 2a unique; 2b name affinity; step 3 agreement probe; step 4 reference counts; else `not_applicable`), and the allowed transformations of version 1 § 3 (renaming, namespace qualification, literal re-elaboration; no coercions, no `Option`/`Except` unwrapping, no gold code in the bridge, no added hypotheses, no language model). Hidden expected values never decide a mapping.

## 3. Controls (must pass before evaluation; expectations unchanged)

Run C1–C4 of version 1 § 3 with `adapter_v2` on the same 50 prescribed tasks (`../expt_v1/results/control_selection.json`) with the same expectations: C1 ≥ 98% of tests applicable and passing; C2 ≥ 95% of tasks recovered with every re-pointed test passing; C3 ≥ 60% kill rate over ≥ 50 compiling mutants; C4 ≥ 95% rejected or failing. Record `results/controls_v2.json` with the adapter hash. A miss is fixed by an amendment appended here, dated, with a new forecast note; controls are then rerun in full; no expectation is ever weakened, and no real-candidate cell is evaluated before all four pass.

## 4. Cells and outcomes (replaces version 1 § 4's per-cell fields)

Per test: `unmapped`, `type_unknown`, `pass` or `fail`. Per cell: `n_tests`, `n_mapped`, `n_evaluable`, `n_pass`, `n_unmapped`, `n_type_unknown`, `applicable` (≥ 1 evaluable), `fully_applicable` (all evaluable), `hidden_all_pass` (all tests evaluable and true; `None` otherwise), `hidden_all_evaluable_pass`, `hidden_pass_rate` = `n_pass / n_evaluable`, the mapping steps, helper exclusions and type-compatibility flags, `n_examples` and `n_eval_commands` of the candidate. Rules: a non-compiling candidate is a hidden failure (`hidden_all_pass = 0`, rate 0); a compiling candidate that is not fully applicable is **missing** for `hidden_all_pass`, always listed and bounded (all missing fail / all missing pass); `no_tests` tasks are excluded for every system alike. SCSC per cell and system S̃ follow version 1 § 4 and A1.1.

## 5. Analyses (seed 20261009; task-cluster bootstrap, 10,000 draws; p-val=n/a unless stated)

- **P1** (11 systems): Spearman(system SCSC, system hidden all-pass rate over non-missing common measured cells), with Pearson, Kendall τ-b, means, bias and mean absolute difference; task bootstrap and system bootstrap sensitivity. Frozen threshold ρ ≥ 0.80. Also reported with the graded rate and with each factor mean.
- **P2** (primary cohort: compiling, **fully applicable**, score-measured primary cells): system-stratified area under the ROC curve of per-cell SCSC for `hidden_all_pass`, pooled by within-system ranks. Frozen threshold ≥ 0.60 with the 95% interval excluding 0.50.
- **P3** (same cohort): pooled within-system Spearman(per-cell SCSC, `hidden_pass_rate`). Frozen threshold > 0 with the interval excluding 0.
- **G-A:** fully applicable / compiling cells with tests, overall and per system. Frozen gate ≥ 0.50; below it the verdict is LIMITED COVERAGE and the analyses still run with bounds. (Version 1's gate used ≥ 1 evaluable test; version 2 applies the same number to the stricter cohort, decided before the run. The ≥ 1 evaluable share is reported beside it.)
- **Sensitivities (reported, never the verdict):** S-V2a P2/P3 on the ≥ 1 evaluable cohort with `hidden_all_evaluable_pass`; S-V2b P2/P3 on cells mapped at steps 1–2b only (no probe); S-V2c P1 under A1.3's model_error/incomplete-as-failure rule; S-V2d the version-1 comparison: the same P1/P2/P3 statistics restricted to the cells that were fully applicable in both versions, and a paired table of version-1 versus version-2 outcomes on the 394 changed-entry-point cells and the 20 inspected rows.
- **Descriptives:** per-system table with all factors, compile rate, both applicability shares, hidden rates and bounds; the mapping step shares; core 614 / IndustrySet 282 splits; secondary panels if evaluated; 20 inspected disagreements selected by the version-1 rule (10 high-SCSC failing, 10 low-SCSC passing).

## 6. Validity checks and stop rules

- Version 1 § 6 and A1.4 joins stand: every cell joins to one file or is `file_missing`/`join_ambiguous`; stop above 5%.
- Before evaluation: verify the version-1 forecasts, `e12_v2_forecast.json`, this file's adapter hash and the census hash; recompile 100 sampled candidates and reproduce the recorded `compiles` on ≥ 99%, or reuse version 1's `compile_reproduction_A1.json` when the candidate hashes are unchanged (they are the same files).
- Never edit a candidate file, gold file, recorded factor, frozen forecast or version-1 result. Never re-sample, drop or reorder cells by outcome. Infrastructure retries rerun the identical cell with a receipt.
- Zero model calls, zero judge calls, zero GPUs. Compiled version-1 modules (`evaluation_A2/modules/*.olean`, same file hashes) may be reused to skip recompilation; bridges and probes are rebuilt with `adapter_v2`.

## 7. Not in version 2

Hidden proofs (`reference_obligations_proved`), a fresh agent-spec v8 panel, human acceptance ratings, and any `Option`/`Except` unwrapping.

## 8. Amendment V2-A1 (10-14-2026, worker; after the lock, before any evaluation or control run)

The static renamed-gold control (`results/static_controls_v2.json`, first run) found 7/882 tasks where step 2b (name affinity) picked a same-typed definition that was not the renamed tested symbol: an inner piece (`absDiff` for `quadAbsDiffPlusThree`), a prefix (`escapeHtml` for `escapeHtmlImp`), a wrapper target (`median_low` for `benchmark_median_low`, `covariance` for `benchmark_covariance`) and the safe variant of a security pair (`safeAccessMemory` for `unsafeAccessMemory`, `safeFindLast` for `unsafeFindLast`). No hidden outcome was involved. The fix is to the adapter before any Lean control or evaluation; predictions and thresholds are unchanged; the forecast amendment `forecasts/e12_v2_forecast_amendment_A1.json` records the new hashes.

- **V2-A1.1 Name affinity** (step 2b) now requires the candidate basename, normalized, to be a **suffix of the gold basename at a word boundary** (preceded by `_`, a digit, or starting with an upper-case letter, or the whole name); the gold twin suffixes `Imp`, `_imp`, `Imperative`, `_imperative` are stripped before the test, so `canFree` is affine to both `MyHazardPointerCanFree` and `MyHazardPointerCanFreeImp`. Prefixes and inner pieces are never affine.
- **V2-A1.2 Reference veto.** A unique affine member decides statically only if no other member of the compatible set is referenced strictly more often by the candidate's own examples and theorems; otherwise the cell is deferred to the agreement probe (reason `affine_member_out_referenced`) with the full set.
- **V2-A1.3 Receipts.** Adapter `scripts/adapter_v2.py` SHA-256 `da6fbe366b26e8518894ba5dd0d236de9e3f258f53e30c5181be08ebcfc7f430` replaces the lock-line hash; the census and static controls were rerun with it (census 3,121 fully mapped / 315 partial / 263 probe / 927 none; static C1 882/882; static C2 0/882 wrong). Section 3's Lean controls still gate the evaluation with unchanged expectations.
