# QA numbers re-run: rl-4-code-verification @ a47acee (zero model calls)

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/docs/qa_11-26-2026/reports/QA_NUMBERS_opus55.md

**TLDR:** Six experiments (15, 07, 17, 16, 25 stage 0, 18c) reproduce from committed inputs, byte-identical or within floating-point noise; three (14, 10 v2, 19) reproduce in part because their full reruns need 3 to 63 CPU-hours; no headline number contradicts its results file. The test suite has 1,402 passed and no genuine failure: all five non-passes are sandbox limits.


Reviewer: Claude Opus 5.5, independent QA. Date: 11-26-2026. Host: 2-CPU container, Python 3.13, numpy 2.5.3, scipy 1.18.1, no torch.
Method: the pristine snapshot `/home/claude/qa_snapshot` (HEAD a47acee, `git status` clean before and after) was copied to `/home/claude/qa_work/numbers/snap` (analyses) and `/home/claude/qa_work/numbers/repo_copy` (tests). All outputs were written under `/home/claude/qa_work/numbers/out/`. No git network operations, no model calls and no downloads. No frozen forecast, PROTOCOL.md or results file in either checkout was written. Exp 16's `main()` also re-freezes a forecast, so it was not called; `score()` was called directly instead.

Legend: REPRODUCED = rerun from committed raw inputs matches; PARTIAL = only part could be rerun here; MISMATCH = rerun disagrees; NOT REPRODUCIBLE HERE = compute or inputs not available.

## Summary table (prose, one line each)

1. Exp 15 (IRT 2PL forecast of RL-signal onset): REPRODUCED.
2. Exp 14 (IRT 2PL vs held-out pass@1): PARTIAL. The 164 x 424 matrix is committed and verified; the full fit was not run because it needs about 50 CPU-hours.
3. Exp 10 v2 (promotion-gate replay): PARTIAL. The run was started and stopped because it needs about 3.4 CPU-hours. The committed JSON matches the tables and the QA 0.00345 claim holds at q = 0.50.
4. Exp 07 phase A and follow-ups 11-25-2026: REPRODUCED. There is one 6th-decimal difference in H2 at n_A = 50.
5. Exp 19: PARTIAL. All 9 input pins verify and the derived tables and cap sensitivity are byte-identical; the main run needs about 63 CPU-hours.
6. Exp 17: REPRODUCED. All 208 leaves match to within 1e-14.
7. Exp 16: REPRODUCED. The output is byte-identical.
8. Exp 25 (checkpoint reuse) stage 0: REPRODUCED. All 4 outputs match to within 2.4e-14 relative.
9. Exp 18c (`analyze18c.py` as frozen): REPRODUCED. JSON and Markdown are byte-identical.
10. Tests: 1,402 passed, 4 failed, 66 skipped, 1 collection error. All 5 non-passes are environmental; there are 0 genuine failures.

## 1. Experiment 15: REPRODUCED

- Command (in `snap/`): `python3 experiments/15_*/expt_v1/analyze_e15.py --out-dir /home/claude/qa_work/numbers/out/e15` (default 10,000 draws; the frozen forecast verified).
- Exit 0, 18.9 s wall (the committed run took 13.65 s).
- Verdict NO ADVANTAGE; primary B1 − IRT 2PL = −0.0066 [−0.0169, +0.0038]; B2 − IRT 2PL = +0.1151 [+0.0992, +0.1300]; 4/4 sizes eligible. These match exactly at the stated 4 dp (results.md:5, :14, :26; experiments/README.md:33).
- `results_tables_e15.md` is byte-identical. `analysis_e15.json`, `per_rung_e15.csv` and `per_task_forecasts_e15.csv.gz` differ only at the 1e-9 level (optimizer and BLAS floating noise; for example the primary point is −0.006648684331 committed vs −0.006648684334 rerun). A 1PL fit's iteration count changed from 42 to 40. No stated number moves.
- The rolling-origin table at results.md:37 ([−0.0169, +0.0039], [+0.0994, +0.1306]) comes from the 2,000-draw secondary block (`secondary/kernel_binary|log1p_ratio|1.0`) and matches. It is not a conflict with the 10,000-draw primary.
- The QA 11-25 corrections were checked against the rerun:
  - The 1.7B IRT expected mixed share at 25% is 0.0592 (≥ 0.05 gate) while the realized share is 0.0074 at 25% and 0.0815 at 50%, so "forecast onset 25%, observed 50%" is correct.
  - The realized/frozen-forecast mixed-share ratios at 100% are 0.1481/0.005 = 29.6, 0.2370/0.02 = 11.9, 0.2370/0.08 = 3.0 and 0.2889/0.15 = 1.9, matching "29.6, 11.9, 3.0, 1.9".

## 2. Experiment 14: PARTIAL (matrix committed; full fit not rerun)

- The 164 x 424 matrix is committed. It is derived from `experiments/07_*/expt_v1/results/per_cell_e07.jsonl.gz` (91,000 rows), and its SHA-256 `f064c395…3a4d` equals the pin in analyze_e14.py:37. `analysis_e07.json` also matches its pin (`16d55132…f5`).
- `load_real()` gives 164 systems x 424 tasks = 69,536 cells with 1 inconsistent cell, as expected (analyze_e14.py:43).
- `python3 analyze_e14.py --render-only --out-dir <copy>`: exit 0, 0.37 s. `results_tables_e14.md` is byte-identical to the committed file, so the tables are faithful to `analysis_e14.json`.
- Not rerun: the locked analysis (2,000 splits x 4 sizes x within-half 2PL/GRM refits plus fold fits) took 2,831 s on 64 processes (results.md, "Locked run"), about 50 CPU-hours. That is infeasible on 2 cores within the budget.
- Portability finding: exp 14's stop rule `reproduce_e07_h2` requires the exp 07 H2 replay to equal the published values exactly (`==`). On numpy 2.5.3 the n_A = 50 median comes out as −0.012140169 against the published −0.012138953 (see section 4). The locked exp 14 run would therefore likely STOP on this host. That is a numerical-environment sensitivity (the locked run used numpy 2.2.6 and scipy 1.16.3), not a data problem.

## 3. Experiment 10 v2: PARTIAL (rerun not completed; committed outputs checked)

- Command: `python3 experiments/10_*/expt_v2/analyze_e10_v2.py --workers 2 --out /home/claude/qa_work/numbers/out/e10/e10_v2_main_qa.json`. It was stopped after about 12 minutes without output. The committed run took 380.7 s on 32 workers (`e10_v2_main.json` `runtime_s`), about 3.4 CPU-hours, or roughly 2 hours here.
- The committed `e10_v2_main.json` and `e10_v2_matched_test_lists.json` record `per_cell` on skampere1 with SHA-256 `f064c395…`, the same committed matrix. The inputs are therefore available, and the rerun is only compute-limited.
- Table-to-JSON spot checks all match: R0 0.2581 [0.2365, 0.2867]; R_irt2pl 0.2046 [0.1848, 0.2297]; R_grm3 0.2000 [0.1815, 0.2251]; S0+ 0.1720 [0.1549, 0.1991]; S_grm3 0.1659 [0.1477, 0.1926]; R0 − R_irt2pl +0.0535 [+0.0322, +0.0722]. The same values are in expt_v2/results.md and experiments/README.md:28.
- The QA 11-25 claim "largest 424-vs-421 difference is 0.00345" (expt_v2/results.md:6) is correct for all q = 0.50 estimates: the maximum is S3.hpr, 0.22832 vs 0.22487, a difference of 0.003449.
  - Scope caveat: at q = 0.25 the `S0plus-R2.hpr_abs_reduction` estimate differs by 0.00371 (−0.09701 vs −0.09330).
  - The `hpr_rel_reduction` estimates at q = 0.25 differ by up to 0.030.
  - If "every primary finding" is meant to include q = 0.25/0.75 secondaries, "within 0.0035" is slightly too strong.
- Experiment-local tests `expt_v2/tests/test_e10_v2.py`: 2 passed.

## 4. Experiment 07: phase A claims and follow-ups 11-25-2026: REPRODUCED

### Phase A

`analyze_e07.py` needs the raw fetched SWE-bench report tree (`--data`, from fetch_e07.py), which is not committed. Instead, the QA script `/home/claude/qa_work/numbers/scripts/e07_phaseA_from_percell.py` rebuilt the factor matrices from the committed per-cell file (via exp 14's `load_real`). It then ran exp 07's own `system_scores`, `bootstrap_corr`, `partial_credit` and `held_out_prediction` with seed 20261007 in the original RNG order (H1, then H1b, then H2). Exit 0, 16 s.

- H1 Spearman 0.985208, task-bootstrap 95% CI [0.9788, 0.9867]. The claim "0.985 [0.979, 0.987]" matches.
- H1b Spearman 0.735557, task CI [0.5068, 0.8013]. The claim "0.736 [0.507, 0.801]" matches (experiments/README.md:5, :25).
- H2 at n_A = 50: median Δ −0.0121402, 92/2000 positive (share 0.046). The claim "median Δ −0.012", 92/2000, share 0.046, matches at the stated precision.
- The whole H1/H1b/H2 JSON equals the published blocks, except for 2 leaves:
  - task-bootstrap Pearson upper limit, 0.9768929198377676 vs …678 (1 ulp);
  - H2 n_A = 50 `delta_median`: rerun −0.012140169227 vs published −0.012138953191.
  - The second difference is visible at the 6-decimal level used in `followups_11-25-2026.md` (table row 1, "−0.012139") and exp 14 results.md ("−0.012139"); the rerun gives −0.012140. The split count (92) and the n_A = 25/100/250 blocks are identical.
  - Likely cause: a floating-point difference in Spearman ranks or the median between numpy versions. It is not a data difference.

### Follow-ups 11-25-2026

- Command (in `snap/`): `PYTHONPATH=src python3 experiments/07_*/followups_11-25-2026/analyze_followups.py --receipts <committed per_cell_e07.jsonl.gz> --original …/analysis_e07.json --systems …/per_system_e07.csv --out /home/claude/qa_work/numbers/out/e07/followup_repro.json`. Exit 0, 4.1 s.
- The doc points `--receipts` at a skampere1 path. The committed file has the identical SHA-256 recorded in `analysis_11-25-2026.json`, so the analysis is reproducible from the repo.
- 190 leaves compared, 6 differ:
  - 1 is the receipts path string;
  - 5 are last-ulp float differences (≤ 4e-16).
- Every prose number in followups_11-25-2026.md matches at the stated 6 dp: 0.767192, 0.573933, 0.639849, 0.193259 = 0.127343 + 0.065916 (0.065927 / −0.000010), 0.216083, 0.191983, 0.050870, −0.074970, −0.011737 (97/2000), −0.004944 (406), −0.005477 (344), 0.192465, 0.054341 and 0.049399.
- Experiment-local tests `followups_11-25-2026/test_followups.py`: 15 passed.
- Not rerun: `run_real_fncli_controls.py` (Phase B real control). It needs `raw_inputs/swebench_pro_verified.jsonl` and fetched OpenLibrary sources, which are not committed (the doc says the dataset was downloaded).

## 5. Experiment 19: PARTIAL

- All 9 input pins in `expt_v1/input_pins_e19.json` verify by SHA-256 (exp 13 A6 receipt, exp 12 manifest, rc_rows, the split manifest and the train/validation/test id lists, the start policy and task features).
- `render_tables_e19.py --out <copy>`: exit 0, 0.08 s, byte-identical to `results_tables_e19.md`.
- `sensitivity_cap_e19.py --out <copy>`: exit 0, 3.6 s, byte-identical to `sensitivity_cap_e19.json`.
- The prose claims match the committed tables:
  - AUC 0.862 [0.792, 0.925] (0.8624 [0.7920, 0.9248]);
  - M1 − M2 +0.0015 [−0.0059, +0.0086] p = 0.69;
  - M0 − M2 +0.0386 [+0.0166, +0.0616];
  - 1,308 cells and 609 positives;
  - panel strict rate 0.852 and features-only 0.954 (experiments/README.md:38);
  - smooth calibrated harsh MAE 0.180 vs rate-calibrated 0.027 (0.1804 vs 0.0266);
  - gold-check 0.102 vs 0.034.
- Not rerun: `analyze_e19.py`. The locked run took 7,124 s on 32 workers (results.md:7), about 63 CPU-hours.

## 6. Experiment 17: REPRODUCED

- Command: `python3 scripts/run_heldout_prediction_experiments.py` (it writes its summary into its own `results/`; this was done only in the scratch copy, after saving the committed file to `out/e17_committed_summary.json`). Exit 0, 0.9 s.
- 208 leaves were compared; 13 differ, all at or below 1.4e-14.
- Matches: corrected horizon test budget-and-scale RMSE 1.372 pp, copy-halfway 3.468 pp (3.4676), ρ–H 1.790 pp (1.7896), and an error reduction of 60.43%. The unseen 14B base-feature ρ–H RMSE is 1.194 vs budget 1.120. Withdrawn-label numbers: law 1.273 and MAE 1.201 (the QA note correctly fixes 1.199 to 1.201), transfer 2.992 / r 0.9940, and horizon law 1.877 / MAE 1.699.
- The summary JSON keeps the withdrawal machine-readable: `rho_H_beats_budget_scale_on_horizon: false` and `rho_H_beats_budget_scale_on_14b: false`.
- Observation (not a mismatch): in the corrected 14B block, ρ–H and budget-scale have an identical Pearson r (0.9563604155770374). This suggests the base-feature ρ–H prediction is an affine function of the budget-scale prediction, because the features are constant per scale. That fits the "ρ–H adds nothing" reading.
- Experiment-local tests: 4 passed.

## 7. Experiment 16 (14B math panel): REPRODUCED

- Command: `PYTHONPATH=src:. python3 -c "import score_heldout_14b as s; s.score()"`. Exit 0, 1.2 s. The output JSON is byte-identical (sorted keys) to `results/heldout_14b_scores.json`.
- Equation 7 and highest H choose HL at all three budgets, with regret 0.2867 pp (claim 0.287); rank accuracy 0.778 (14/18) vs 0.611; highest ρ and ρ x H choose HH with regret 4.423; uniform regret 2.717; RMSE 2.291; permutation null 520/13,824, p = 0.0376. All match results.md and experiments/README.md:35.
- Caveat: the inputs are hard-coded paper Table 4/5 values in the script (not raw logs), plus `paper_frozen_14b_model` in `src/rl4cv/utility_model.py`. This reproduction therefore verifies the arithmetic, not the paper's measurements.

## 8. Experiment 25 (checkpoint reuse) stage 0: REPRODUCED

- Command: `PYTHONPATH=src python3 experiments/25_checkpoint_reuse_for_rho_h_law/expt_v1/stage0.py all`, run in the scratch copy after saving the committed outputs. Exit 0, 11.1 s.
- Inputs: the exp 16 toy Night 4 and Night 5 cells (committed) and exp 08 ladder and fresh CSVs (committed).
- All 4 outputs (`0b_prefix_night4/5`, `0b_cross_start_night4_to_night5` and `0c_real_rho_h`) match, with a maximum relative difference of 2.3e-14.
- Matches: P2 RMSE ratio at n4 0.975 / 0.970; ratio at n3 0.984 / 0.990; rank gaps −0.017 / 0.000 and 0.000 / 0.025; P4 dH +0.0021 with half-width 0.026 against margin 0.073 (EQUIVALENT); dlogρ +0.174 [−0.170, +0.480] with half-width 0.325 against margin 0.49 (EQUIVALENT at the coarse margin only, with 9,997/10,000 valid draws, as stated at results.md:145).
- A harmless `divide by zero in log` warning at stage0.py:268 is the source of the 3 invalid draws.

## 9. Experiment 18c (`analyze18c.py` as frozen): REPRODUCED

- Command (in `expt_18c/`): `PYTHONPATH=<snap>/src python3 analyze18c.py --root results --out <out>/results_18c.json --md <out>/results_18c_table.md`. Exit 0, 41 s. The frozen forecast SHA verified.
- `results_18c.json` and `results_18c_table.md` are byte-identical to the committed files, which confirms the "reproduced byte for byte" claim at results_18c.md:22.

## 10. Repository tests (no torch)

- Setup: `src/ tests/ pyproject.toml experiments/ docs/ external/ scripts/ Makefile` were copied to `/home/claude/qa_work/numbers/repo_copy`.
- Command: `PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider --continue-on-collection-errors -rfEs`. Exit 1, 161 s. The log is at `/home/claude/qa_work/numbers/out/pytest_full.txt`.
- Result: 1,402 passed, 4 failed, 66 skipped, 1 error, 6 subtests passed.
- Environmental failures and errors (all 5 non-passes):
  1. ERROR collecting `tests/test_e20_loss.py`: missing `torch`.
  2. FAILED `test_e08_v3_native_continuation.py::test_locked_dependency_paths_exist`: the locked files under `external/veribench_scorer/scripts/scsc/` (run_real_eval.py, pbt_diagnostic.py, kernel_axioms.py, lean_public_context.py) and `../ultimate-utils/py_src/uutils/emailing.py` are absent. They are also absent in the pristine snapshot, because `make external` was not run and the sibling repo is not present.
  3. FAILED `test_e13_evaluation_contract.py::test_real_frozen_prompt_builder_keeps_thinking_template_and_hashes`: VeriBench checkout not found (VERIBENCH_ROOT / external).
  4. FAILED `test_e13_selected_publication.py::test_hosted_pack_uses_same_fixed_samples_and_never_needs_hidden_outcomes`: `ModuleNotFoundError: common`, imported from the unfetched VeriBench experiments 100/103.
  5. FAILED `test_e13_worker_shutdown.py::test_real_zombie_environment_error_then_census_clear`: the container kernel returns `ProcessLookupError` (ESRCH) for a zombie's `/proc/<pid>/environ` where the test expects `PermissionError`. This is a host-kernel behavior assumption, so the test is not portable.
- Genuine failures: 0.
- Skips (66): torch (11), pinned judge deps (7), external VeriBench experiments 100/103 (7), Lean routes and prerequisites (4 + 4 + 3), judge renderer (3), NeMo (3 + 1), reasoning_gym (3), Ray (1), and others.
- Experiment-local tests outside `testpaths` also pass: exp 10 v2 (2), exp 07 follow-ups (15) and exp 17 (4).

## Mismatches worth acting on

1. Exp 07 H2 at n_A = 50: the rerun gives median Δ −0.012140 vs the published −0.012139 (6th decimal; `analysis_e07.json` H2 "50" `delta_median`; cited at followups_11-25-2026.md table row 1 and exp 14 results.md phases table). The split count of 92/2000 is identical. Because exp 14's stop rule compares these values with exact `==`, the locked exp 14 run is not portable to numpy 2.5.x. Suggest documenting that the stop rule is environment-pinned (numpy 2.2.6), or comparing with a tolerance in any future version.
2. Exp 10 v2's "within 0.0035" (expt_v2/results.md:6) holds at q = 0.50. At q = 0.25 one absolute-reduction contrast differs by 0.0037 and relative reductions differ by up to 0.030; scope the sentence to q = 0.50 if that is what was meant.
3. No reproduced headline number contradicts its results file or experiments/README.md.

## Could not reproduce here, and why

- Exp 14 full fit: about 50 CPU-hours (64 processes x 2,831 s).
- Exp 19 main analysis: about 63 CPU-hours (32 workers x 7,124 s).
- Exp 10 v2 rerun: about 3.4 CPU-hours (32 workers x 381 s); it was started and stopped. Inputs are committed, so it is compute-only.
- Exp 07 `analyze_e07.py` from raw: it needs the fetched SWE-bench submissions tree (not committed). The H1/H1b/H2 recomputation from the committed per-cell matrix substitutes for it.
- Exp 07 Phase B real controls: they need downloaded SWE-Bench Pro Verified rows and OpenLibrary sources (not committed).
- Exp 16 and 17 rely on hard-coded paper or table inputs, so only the arithmetic was verified.

## Artifacts

- Scratch copies: `/home/claude/qa_work/numbers/snap`, `/home/claude/qa_work/numbers/repo_copy`
- QA script: `/home/claude/qa_work/numbers/scripts/e07_phaseA_from_percell.py`
- Outputs: `/home/claude/qa_work/numbers/out/` (e15/, e14/, e07/, e19/, e18c/, e16_scores_qa.json, e17_committed_summary.json, e25_committed/, pytest_full.txt)
