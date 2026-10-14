# Experiment 15 protocol: 2PL IRT rung-to-rung forecast of per-task success and mixed-group share (Qwen3 Base SFT ladder, VeriBench V1 validation split)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/PROTOCOL.md>

**TLDR:** This protocol fixes the data, rungs, item response theory (IRT) models, baselines, statistics and decision rules for Q2 of the VeriBench IRT idea page: can a two-parameter logistic (2PL) fit on the earlier supervised fine-tuning (SFT) rungs forecast the next rung's per-task success probability and expected mixed-group share better than carrying the last rung forward and than a scalar scaling curve? Zero model calls; validation split only. Changes after the lock go to `results.md` → Deviations, never here.

**Status:** LOCKED, revision 1 (10-14-2026, by the commit that adds this folder). The forecast `expt_v1/forecasts/e15_forecast.json` is frozen by `rl4cv.forecast.freeze_forecast` in the next commit, before any real-data fit or statistic. No quality-assurance review was requested for this round (Rule 57: the worker decided every open choice and labels each as agent-suggested).

## What was seen before the lock

- Experiment 08's README (status lines: version 1 complete with PARTIAL selection; "8B step 658 and 14B step 334 are unmatched diagnostics; neither 1.7B nor 4B passes a rung", the rung gate being a validation mixed-group share ≥ 0.05), its `ladder_manifest.json`, `ladder_manifest_base14b.json` and `sft_schedule.json` (rung token counts), the file listing of `results/ladder/`, the header and first two rows of three per-task files (`sft_8B_f0p5`, `base_8B_e05`, `base14b`; two aerospace tasks each), and the header and first four rows of experiment 05's 896-task 1.7B file (four aerospace tasks, all zero).
- Experiment 05's published summary (Qwen3 Base gives essentially zero RL signal at 1.7B/4B/8B) and the idea page's Q2 row.
- A preview of `base_qwen3_e05_on_d013_splits.json` printed its 1.7B *test*-split aggregate (all zero). It is Base-model data under experiment 05's locked protocol, not a trained-policy outcome; it is disclosed here and not used.
- **No per-rung aggregate, per-task matrix, IRT fit or forecast statistic** on the real validation files was computed or read; `validation_ladder.json`, experiment 08's `results.md` tables and every `*test*` outcome file were not opened.
- Synthetic data only for the code: `analyze_e15.py --synthetic` (2PL-generated stand-in with the real shapes) and `tests/test_e15_irt.py`.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Every input file (29 files: validation and test id lists, two ladder manifests, the SFT schedule, 24 validation per-task files) | `expt_v1/input_pins_e15.json`, SHA-256 `d082db74761c87ecbf0bad64b0a48ec91b45e4defe84087edc2ec7d645182dbf`; the analyzer refuses any file whose hash differs |
| Task set | experiment 08's `task_ids_sha256` = `666d6d6b31cb3f736d8ca0eee625ff5ad5ea31efa7e0ce3a10c350091848c84d` (135 validation tasks); the analyzer asserts 135 tasks per file, all in `vbv1_validation_task_ids.txt`, none in `vbv1_test_task_ids.txt` |
| Rung tokens | `sft_schedule.json`: 720,775 / 1,442,549 / 2,884,708 / 4,318,781 / 5,752,936 cumulative assistant loss tokens at steps 82 / 164 / 334 / 497 / 658; identical for all sizes (matched recipe) |
| Code | `expt_v1/irt_e15.py`, `expt_v1/analyze_e15.py`, `tests/test_e15_irt.py` at the lock commit |
| Environment | Python 3 with numpy 2.2.6 and scipy 1.16.3 on Brando's Mac; host and versions are recorded in `analysis_e15.json` |

## Population and denominators

- **Tasks:** the 135 validation-split tasks of decision D-013, sorted by task id. The train split is not used (the idea page allows it only as a labelled secondary; none is run here). The test split (222 tasks) is never read: experiment 08's `*test*` files are not inputs, and the loader raises on any test id.
- **Sizes:** Qwen3 Base 1.7B, 4B, 8B, 14B (exact revisions in experiment 08's `sft_schedule.json`).
- **Rungs per size (index: fraction of the SFT budget, tokens):** 0: Base, 0 tokens; 1: 12.5%, 720,775; 2: 25%, 1,442,549; 3: 50%, 2,884,708; 4: 75%, 4,318,781; 5: 100%, 5,752,936. The Base 1.7B/4B/8B rungs are experiment 05's receipts restricted to the validation split by experiment 08 (same sampler: G = 8, T = 0.6, 12,288-token cap, thinking template, seed 91). The Base 14B rung is experiment 08's own generation under the same sampler; the 14B size therefore has a rung 0 even though experiment 05 never ran 14B, and this provenance difference is stated beside every 14B number.
- **Attempts:** `samples_known` per task (declared 8; the loader records the realized count and treats a task with 0 known samples as missing, excluded from that rung's means and listed).
- **Outcomes:** primary `k_kernel_binary` (fully kernel-verified files among the attempts, VeriBench's strict verifier, never loosened); secondary graded outcome `round(mean_proof_fraction × samples_known)` treated as a count of the same attempts (a quasi-binomial partial-credit model; chosen over Beta-IRT because the fractions have point masses at 0 and 1).

## Models (frozen)

- **Covariate.** Primary form `log1p_ratio`: x = log(1 + tokens / 720,775), so Base is at 0 and the rungs are at log 2, log 3, log 5, log 7, log 9 (0.693, 1.099, 1.609, 1.946, 2.197). The declared offset is one 12.5%-rung of tokens: it keeps the Base rung in the trend without the infinite leverage of log(1 + tokens) (which would put Base 13 units below the first rung). Sensitivity form `log_tokens`: x = log(tokens); the Base rung stays in the item-parameter fit but not in the ability trend, so the first forecast rung is 50%.
- **IRT.** logit P(success on task j at size-rung i) = a_j θ_i + d_j (2PL; difficulty b_j = −d_j / a_j). 1PL sensitivity: one common slope. Item parameters are pooled across sizes and rungs (one difficulty and one discrimination per task), because a task's Lean difficulty is a property of the task and pooling is what lets earlier rungs and other sizes inform the item curves; abilities are one per size-rung. The eight attempts are conditionally independent given θ (binomial likelihood k of n); dependence between attempts of one task is covered by the task bootstrap, not the likelihood.
- **Fitting.** Marginal maximum a posteriori on experiment 14's grid (1,201 nodes on [−12, 12], standard-normal population weights; check grid 4,801 nodes on [−18, 18]) with experiment 14's priors (log a ~ N(0, 1), d ~ N(0, 5²)); L-BFGS-B, maxiter 20,000. A fit is accepted only if the objective and parameters are finite and the largest absolute gradient is ≤ 1e-4 on both grids. Abilities are expected a posteriori (EAP) means under the fitted parameters.
- **Rolling origin.** For each target rung index r ∈ {2, 3, 4, 5} (primary form; {3, 4, 5} for `log_tokens`), the item parameters are fitted on every available size-rung with index < r (all sizes at once), each size's EAP abilities on its rungs < r are regressed on x by ordinary least squares and extrapolated to x_r (with one usable rung the ability is carried forward and the slope recorded as none), and the forecast is p̂_j = σ(a_j θ̃ + d_j). The final rung (index 5, fitted on indices 0–4) is the primary target.
- **B1, last rung carried forward:** p̂_j = k_j / n_j at the size's last observed rung below r.
- **B2, scalar scaling curve:** for each size, logit of the pooled success rate (Σk + 0.5) / (Σn + 1) at each rung below r is regressed on x (same functional form as the IRT trend) and extrapolated to x_r; p̂_j is the same value for every task.

## Targets and errors

For each (outcome, form, target rung, size) and each arm, over the valid tasks:

- **Per-task p:** MAE = mean_j |p̂_j − k_j / n_j|; Brier = mean_j (p̂_j² − 2 p̂_j k_j / n_j + k_j / n_j), the exact mean over the n_j attempts of (p̂_j − y)².
- **Mixed-group share:** expected = mean_j (1 − p̂_j⁸ − (1 − p̂_j)⁸) with G = 8, against the realized share of tasks with 0 < k_j < n_j; the signed error is reported.
- **Pooled success rate:** mean_j p̂_j against mean_j k_j / n_j (signed).
- **Degenerate rung:** a size-rung with zero successes over all attempts. Degenerate rungs stay in the fitting data (they say the ability is low) and are listed; degenerate *target* rungs make the mixed-share target 0 and count toward the INCONCLUSIVE rule below.

## Statistics

- **Primary comparison.** For each eligible size, per-task differences |e_B| − |e_IRT| at the final rung (positive means IRT closer), averaged over tasks and then over sizes. Uncertainty: a paired task bootstrap with 10,000 draws (seed 20261014; tasks are the resampling unit; one index draw per replicate shared by all sizes so the pairing across sizes is kept), 95% percentile interval. Reported as x [lo, hi] p-val=n/a (the decision is interval-based; no p-value is computed).
- **Secondary.** The same intervals (2,000 draws) at every target rung for MAE and Brier, 2PL and 1PL, against each baseline; per-size intervals; the mixed-share and pooled-rate errors per rung; the `log_tokens` form; the proof-fraction outcome.
- **Monotonicity over training.** Per size, the number of rung-to-rung decreases of the pooled success rate and of the realized mixed share (the idea page asks for it because small IRT-selected sets can raise variance).
- **Seed variance.** Unavailable: experiment 08 trained one run per size and sampled each rung once (seed 91). Stated, not estimated.
- **Scope.** Intervals resample tasks with the fitted item parameters and trends held fixed; they are conditional on these four sizes, this schedule and this sampler, and are not intervals for a refitted procedure or for other models.

## Decision rules (frozen)

| ID | Rule | Threshold source |
|---|---|---|
| Eligibility | A size is eligible if it has ≥ 3 rungs and its final rung is non-degenerate | Agent-suggested (this protocol) |
| INCONCLUSIVE | Fewer than 2 eligible sizes, or more than 10% of the eligible sizes' target rungs (rolling origin, primary form and outcome) are degenerate | Master dispatch of 10-14-2026 (agent-suggested), made precise here: the share is taken over target rungs of eligible sizes, because Base rungs are expected to be degenerate and are fitting data, not targets |
| SUCCESS | At the final rung, the 2PL MAE difference against B1 **and** against B2 are both > 0 with 95% paired task-bootstrap intervals excluding 0 | Idea page Q2 row ("lower than both baselines"), interval rule agent-suggested |
| NO ADVANTAGE | Not INCONCLUSIVE and either comparison fails | Idea page Q2 row |
| Validity | If any fit used by the primary comparison fails its gates, the verdict is INCONCLUSIVE and the failure is reported | Agent-suggested |

A forecast that fails is reported exactly like one that holds. The primary is one comparison (two baselines joined by "and"); the secondary analyses carry no verdict.

## What the result means for Brando's questions

- **SUCCESS:** the ladder's next rung can be forecast from the previous ones; the next step is to use the fitted model to pick the SFT stopping point (the first rung whose forecast mixed share reaches 0.05) and the RL prompt pool (tasks forecast nearest p = 0.5) in a prospective, frozen forecast on a new ladder.
- **NO ADVANTAGE:** the measured ladder stays the tool; IRT's value for onset is not shown on this data.
- **INCONCLUSIVE:** the ladder is too degenerate (too many rungs with zero successes) to test forecasting; that itself says the 1.7B/4B deficits are not a matter of forecasting but of signal.

## Compute

- CPU only, zero model calls, no Valkyrie, no GPU. About 2 × 2 × 7 fits of ≤ 20 persons × 135 items plus the bootstraps: seconds to a few minutes on Brando's Mac (10 cores). If it exceeded 15 minutes it would move to `skampere1` under `/lfs/skampere1/0/brando9/rl4cv_e15/`; the synthetic run took 16 s, so it stays on the Mac.
- Command: `python experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/expt_v1/analyze_e15.py` (default 10,000 draws). The analyzer refuses to run on real data unless `rl4cv.forecast.verify_forecast` passes on the frozen forecast.

## Not in this protocol

- No model calls, no training, no change to experiments 05, 08, 13 or 14.
- No test-split or train-split outcomes.
- No multidimensional IRT, no Beta-IRT, no refit inside the bootstrap.
- No SFT-stopping or prompt-pool choice is acted on; the protocol only states how a SUCCESS would be used.
