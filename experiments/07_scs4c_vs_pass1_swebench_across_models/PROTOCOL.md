# Experiment 07 phase A protocol — SCS4C-T versus pass@1 across SWE-bench Verified submissions

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/PROTOCOL.md>

**TLDR:** Locked before cross-system analysis; pre-lock exposure is disclosed below. Phase A computes SCS4C-T = G · (T_fix · T_keep)^(1/2) from every public SWE-bench Verified submission's per-instance `report.json`, then tests whether it tracks pass@1 across systems (H1), whether partial credit on failed tasks tracks capability (H1b), and whether it predicts held-out pass@1 better than pass@1 does (H2). No model calls. Changes after the lock go to `results.md` → Deviations, never here.

Locked: 10-07-2026 by the experiment 07 master (Claude Code, Opus 5.5, for Brando). Frozen forecast: `expt_v1/forecasts/e07_phase_a_forecast.json` (SHA-256 sidecar and ledger beside it).

**Outcomes seen before the lock.** One cell, to check the file format: `20251127_openhands_claude-opus-4-5` on `astropy__astropy-13033` (patch applied, FAIL_TO_PASS 0/1, PASS_TO_PASS 20/20, unresolved). Plus public leaderboard pass@1 numbers, which are common knowledge. No factor statistic, correlation or split result had been computed on real data.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Submission list and metadata | `SWE-bench/experiments` commit `40f164d5b8f1d249bf95a6df8b74b577fd8e519d`, `evaluation/verified/*` (182 entries at the pin) |
| Per-instance reports | `s3://swe-bench-submissions/verified/<submission>/logs/<instance>/report.json` (unsigned access), or the submission's own repository named in `metadata.yaml` `assets.repo` |
| Task universe and gold lists | `princeton-nlp/SWE-bench_Verified`, split `test`, revision `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` (500 tasks) |
| Code | `src/rl4cv/scs4c.py`, `expt_v1/fetch_e07.py`, `expt_v1/analyze_e07.py` at the commit that adds this file |

## Cells and denominators

- **Unit.** A submission (one model with one agent scaffold) is a system; a cell is one system on one task. Declared denominator: 500 tasks per system.
- **Factors.** From the report: G = patch exists, is not None and applied. T_fix and T_keep = successes / (successes + failures) in the report's FAIL_TO_PASS and PASS_TO_PASS lists (the lists the official harness used for `resolved`); an empty list is vacuously 1.
- **Missing data.** No patch (absent or empty in `all_preds.jsonl`, or listed as no generation or empty patch in `results.json`) is a genuine 0. A patch with no report is **unmeasured**: listed, never counted as 0.
- **Inclusion.** A system enters the cross-system analysis if at least 95% (475) of its 500 cells are measured. Excluded systems are listed with counts.
- **Cohort.** Primary analyses use the common cohort: tasks measured for every included system. Its size is reported; each system's own-cohort scores are reported beside it.
- **pass@1.** The official `resolved` flag, on the same cohort. The leaderboard convention (known official resolved count divided by 500, otherwise unknown resolution counted unresolved only for this diagnostic) is reported as `pass1_declared`. A known resolution from `results.json` can contribute to that count even when per-test factors are unmeasured.

## Analyses (primary analyses in `analyze_e07.py`, seed 20261007)

| ID | Statistic | Uncertainty | Frozen prediction | Verdict rule |
|---|---|---|---|---|
| H1 | Pearson, Spearman, Kendall τ-b between system SCS4C-T and pass@1; mean bias and mean absolute error of SCS4C-T − pass@1 | 95% percentile bootstrap, 2,000 draws, resampling tasks; separately, resampling systems | Spearman ≥ 0.90 | Construct check only (partly true by construction) |
| H1b | The same three correlations between each system's mean per-cell SCS4C-T over its unresolved cohort cells (partial credit) and its pass@1 | Same two bootstraps | Spearman > 0 with the task-bootstrap interval excluding 0 | Positive / no evidence / negative as in the README |
| H2 | For 2,000 random task splits per size n_A ∈ {25, 50, 100, 250}: Δ = Spearman(SCS4C-T on A, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B), B = the other cohort tasks | Median, 5th–95th percentiles and share of Δ > 0 over splits (the split distribution, not a population interval) | At n_A = 50: median Δ > 0 and share ≥ 0.60 | Primary size n_A = 50; other sizes descriptive |
| H3 | Measured cells, unresolved cells, unresolved cells with SCS4C-T > 0 | Counts with denominators | Descriptive | — |

Thresholds are agent-suggested (Claude, 10-07-2026); Brando or Emily may revise them only before the run, by a new locked version. A forecast that fails is reported exactly like one that holds.

## Validity checks and stop rules

- **Consistency.** With report lists as denominators, `resolved` must equal (G = 1, T_fix = 1, T_keep = 1). If more than 0.5% of measured cells violate this, stop and diagnose the parser before reporting any hypothesis.
- **Gold-list agreement.** Count reports whose test sets differ from the pinned gold lists, per system (dataset-version drift); report, do not exclude.
- **Coverage.** If fewer than 20 systems pass inclusion, report phase A as underpowered rather than giving verdicts.
- **GitHub-hosted logs.** Submissions whose logs live in their own repository need an adapter. A worker may add one as a recorded deviation before the analysis runs; a submission whose logs lack per-test status is excluded with that reason.
- **Sensitivity (reported, not primary).** One system per base model (the latest submission), if metadata names the model. The worker implements this separately per `expt_v1/cc.md` § 3 before publication.

## Not in phase A

No model calls, no new patches, no D_gold factor, no judge, no docstring score. Phases B and C need their own locked protocols.
