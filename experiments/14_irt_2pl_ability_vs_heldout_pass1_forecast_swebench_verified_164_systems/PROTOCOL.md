# Experiment 14 protocol: IRT ability versus pass@1 on half A as forecasts of held-out pass@1 (SWE-bench Verified, 164 systems × 424 tasks)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/PROTOCOL.md>

**TLDR:** This protocol fixes the data, splits, item response theory (IRT) models, arms, statistics and decision rules for Q1 of the VeriBench IRT idea page. The question: does IRT ability estimated from the n_A tasks of half A forecast each system's pass@1 on the held-out half B better than its pass@1 on half A does, in rank and in level? It uses experiment 07's matrix and experiment 07's exact H2 splits, with zero model calls. Changes after the lock go to `results.md` → Deviations, never here.

**Status:** LOCKED, revision 2 (10-12-2026 21:54 PDT). Forecast `expt_v1/forecasts/e14_forecast.json`, SHA-256 `33de7cd2…6890`, frozen by `rl4cv.forecast.freeze_forecast` before any real-data IRT fit or Q1 statistic. This revision follows the single light quality-assurance (QA) review: Codex GPT-6 Astra (effort ultra) reviewed revision 1 at `1dad751` and returned `VERDICT: FAIL` with 2 critical, 4 major and 1 minor finding, all fixed here and in the code with regression tests and no re-review ([`reviews/`](reviews/)). The lock is the commit that adds the forecast.

## Question and origin

- **Q1** of [`experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance`](https://github.com/brando90/veribench/blob/main/experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md) in the VeriBench repository (Brando's request of 10-09-2026; his instruction at 16:45 PDT that day was to plan it, have Codex GPT-6 Astra (ultra) do one light QA round, and run it to completion).
- The idea page planned Q1 as an arm of experiment 10. [`10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs`](../10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/PROTOCOL.md) locked (revision 3, 10-09-2026 16:43 PDT) without it, so Q1 has its own folder here.
- **Why it matters.** [`07_scs4c_vs_pass1_swebench_across_models`](../07_scs4c_vs_pass1_swebench_across_models/results.md) found that its smooth score SCS4C-T on 50 tasks ranks systems by held-out pass@1 slightly *worse* than pass@1 on the same 50 tasks: median Δ −0.012, with Δ > 0 in 92 of 2,000 splits. IRT is the standard way to weight items. If IRT also adds nothing, it should not be promoted for evaluation or reinforcement-learning (RL) prompt selection on this kind of data.
- **The ceiling, stated up front.** When every system answers the same tasks, Rasch ability is a monotone function of the count solved, so Rasch ranks systems exactly as pass@1 on half A does. IRT can change the *ranking* only through discrimination weights (2PL) or partial credit (the graded model). It can change the *level* forecast by correcting for how hard half A happened to be, which needs item parameters for half B from other systems.

## What was seen before the lock

- Experiment 07's published results (`results.md`, `analysis_e07.json`, including all H2 values and the one-system-per-base-model list) and its code.
- Field names and counts of the per-cell file: 91,000 rows. In the 164 × 424 cohort, 69,536 cells are all measured: 68,608 test reports and 928 "no patch or patch not applied".
- **Synthetic data only** for the new code: a 2PL-generated stand-in with the real shapes (`analyze_e14.py --synthetic`; 40-split runs and one full-size dry run on `skampere1`). It exposed the fold artifact described under Arms, which changed the rank-arm design before the lock.
- **The light QA review of revision 1** ([`reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md`](reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md)). The reviewer used synthetic and constructed data only. The fixes are listed in [`reviews/light_qa_resolution_10-12-2026.md`](reviews/light_qa_resolution_10-12-2026.md).
- **One check on the real data:** experiment 07's own `held_out_prediction`, run on the replayed random stream, reproduces 07's published H2 block exactly, and our replayed permutations reproduce its medians and positive counts. This recomputes 07's published statistics (SCS4C-T versus pass@1 on half A) and nothing else. Result and time are recorded in `results.md`.
- No IRT fit, forecast or Q1 statistic was computed on the real matrix. The real-data run of experiment 10 was not read.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Per-cell factors | `experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz`, SHA-256 `f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d` (same pin as experiment 10) |
| Cohort order, published H2, sensitivity list | `experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/analysis_e07.json`, SHA-256 `16d551328ab9aedaad399f50fd4d59cf12759e0b377c8040d063dd5ef2c5b3f5` |
| Code | `expt_v1/analyze_e14.py`, `expt_v1/irt_e14.py` and `tests/test_e14_irt.py` at the lock commit; experiment 07's `analyze_e07.py` for the reproduction check |
| Environment | Python with numpy 2.2.6 and scipy ≥ 1.16; versions, host and thread settings are recorded in `analysis_e14.json` |

## Population and denominators

- **Cohort:** experiment 07's 164 included systems × 424 common-cohort tasks, 69,536 cells, every one measured and used. The declared upstream denominator is 182 systems × 500 tasks; 18 systems and 76 tasks fell outside 07's analysis cohort by 07's frozen inclusion rule. Every estimate here is conditional on the 164 × 424 cohort and is not extrapolated beyond it.
- **Order:** systems sorted by submission name, as 07 ordered them; tasks in 07's `common_cohort_ids` order. Both orders matter for the split replay.
- **Responses:** `resolved` (binary). The graded category is 2 if resolved, 1 if unresolved with 07's per-cell score > 0 (partial credit from the per-test FAIL_TO_PASS and PASS_TO_PASS fractions), and 0 otherwise. 07's single inconsistent cell (`20250516_cortexa_o3` on `matplotlib__matplotlib-20826`) is used as recorded; `resolved` decides its category.

## Splits

- **Exactly experiment 07's H2 splits.** Seed `20261007`. The generator is first advanced exactly as 07's H1 and H1b bootstraps advanced it: twice, 2,000 task resamples `integers(0, 424, 424)` followed by 2,000 system resamples `integers(0, 164, 164)`. It then draws 2,000 permutations of the 424 tasks for each n_A ∈ {25, 50, 100, 250}, in that order. Half A is the first n_A tasks; half B is the remaining 424 − n_A. "Half" is 07's name for the two parts; they are equal only by name.
- **Primary size:** n_A = 50 (07's primary). Other sizes are descriptive.
- **Stop rule:** 07's own `held_out_prediction`, run on the replayed generator, must equal 07's published H2 block field for field. Our replayed permutations must reproduce 07's published median Δ and positive-split count at every size.

## Models (frozen)

- **Ability grid (base):** 1,201 equally spaced nodes on [−12, 12], with standard-normal population weights. Fitting and scoring share it.
- **Check grid:** 4,801 nodes on [−18, 18], four times finer and 1.5 times wider. It is used only for the numerical gates below. (Revision 1's 401 nodes on [−6, 6] could truncate the posterior of a system far outside the reference panel; QA finding 1.)
- **1PL (Rasch with one common slope):** logit P(resolved) = aθ + d_j.
- **2PL:** logit P(resolved) = a_j θ + d_j.
- **Graded response model, three ordered categories (GRM3):** P(c ≥ 1) = σ(a_j θ + d_j) and P(c = 2) = σ(a_j θ + d2_j), with d2_j = d_j − exp(γ_j) so the thresholds stay ordered. P(resolved) = P(c = 2).
- **Priors (maximum a posteriori):** log a ~ N(0, 1), d ~ N(0, 5²), γ ~ N(0, 2²). Slopes are positive.
- **Fitting:** marginal maximum a posteriori. Each system's ability is integrated over the grid, and the analytic gradient follows Fisher's identity. The optimizer is scipy's L-BFGS-B (maxiter 20,000).
- **A fit is accepted only if all of these hold:**
  - the objective and parameters are finite;
  - the largest absolute gradient of the per-system objective is ≤ 1e-4 on the base grid;
  - the same bound holds when the fitted parameters are evaluated on the check grid.

  A non-finite value never passes (QA finding 2).
- **Numerical gates on scoring:**
  - every scored posterior keeps at most 1e-8 of its mass on the two end nodes of the base grid;
  - rescoring on the check grid changes forecasts, EAP abilities and posterior standard deviations by at most 1e-6.

  For within-half fits both gates are checked for every fit. For the K-fold models the endpoint gate is checked for every scored posterior, and the rescoring gate on the first 20 splits at n_A = 50 for every fold model.
- **Scoring:** each system's posterior over the grid gives the expected a posteriori (EAP) ability θ̂ and the posterior standard deviation. The held-out forecast is the posterior predictive mean of P(resolved), averaged over the half-B tasks. Binary models score through the sufficient statistic Σ_j a_j x_j (the count times the common slope for 1PL), so equal statistics give bitwise-equal posteriors.
- **Why not Beta-IRT.** The per-test fractions have point masses at exactly 0 and 1 (resolved means both fractions are 1). A Beta likelihood cannot represent these without inflation components. The ordinal graded model uses partial credit without that problem, at the cost of using only "any partial credit", not its size.
- **Why no multidimensional arm.** With n_A = 25–50 binary responses, a two-dimensional ability is weakly identified. It would add a fifth model family to a question already answered by the 2PL-versus-pass@1 contrast. It is left for a follow-up if Q1 continues.

## Arms

| Arm | Information it uses | Role |
|---|---|---|
| `pass1_A` | The system's resolved rate on half A | Baseline (experiment 07's) |
| `rasch_common_check` | 1PL posterior predictive with one item-parameter set (fold 0's) for every system | Check: rank Δ must be exactly 0 in every split. Its level is not reported (fold 0's parameters saw most systems' data) |
| `2pl_within_A` | 2PL refitted for each split on the half-A responses of all 164 systems; rank predictor = EAP θ̂ | **Primary rank arm**: the same information as 07's H2 arms, with no half-B data at all |
| `grm3_within_A` | The same, with graded categories (resolved plus partial credit) | Key secondary rank arm |
| `2pl` | Item parameters from the systems outside the target's fold (all 424 tasks of those systems); the target's θ posterior from its half-A responses; forecast = posterior predictive pass@1 on half B | **Primary level arm**; its rank is secondary |
| `1pl`, `grm3` | As `2pl` | Secondary |
| `mean_equating` | pass@1 on A plus (mean pass@1 on B − mean pass@1 on A) over the reference systems | Control: a difficulty shift without IRT |
| `linear_regression` | Ordinary least squares of pass@1 on B on pass@1 on A over the reference systems, applied to the target | Control: shift plus shrinkage without IRT |

- **System K-fold:** 10 balanced folds from a permutation seeded `[20261012, 1, fold_seed]`; fold seed 0 is primary. A target system's data never enter the item parameters used to forecast it.
- **Why the rank arms are refitted within half A.** On the synthetic stand-in at n_A = 50, the arms that are monotone in pass@1 on A *within* each fold (1PL, mean equating, regression) still showed rank Δ about −0.002 (0–1 of 40 splits positive). Fold-specific parameters break ties and reorder near-ties across folds, an artifact the size of the effect under test. A fit on half A of all systems uses no half-B data, so nothing leaks, and it is one parameter set, so there is no fold artifact. Level forecasts need half-B item parameters, which only other systems can supply, so they stay K-fold.

## Statistics

- **Rank.** For every split, Δ = Spearman(arm, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B). Spearman is Pearson on average ranks (`rl4cv.scs4c.spearman`), and forecasts are rounded to 12 decimals before ranking. A split whose forecast has any non-finite value, or whose within-half fit failed a gate, is undefined for that arm. It is never computed on a subset of systems.
  - **Per-size summary:** median Δ, 5th–95th percentile, mean, splits with Δ > 0 out of 2,000 (an undefined split counts as not positive, as in 07), exact-zero splits, and both median Spearman values.
  - **At n_A = 50:** a system-cluster bootstrap with 2,000 draws. Each draw resamples the 164 systems and re-ranks all 2,000 splits. It gives 95% percentile intervals for the median Δ and the share, with bootstrap p-values (twice the smaller tail share; nulls: median Δ = 0 and share = 0.60). Medians over splits of Pearson, Spearman and Kendall τ-b are also reported.
- **Level.** The error is e = forecast − pass@1 on B for every system and split.
  - **Reported per arm:** mean absolute error (MAE), root-mean-square error, and mean bias (forecast minus held-out, so positive means the forecast runs high), with both means.
  - **Comparison with pass@1 on A:** take each system's split-averaged absolute error. The difference is the mean over systems of MAE_i(pass@1 on A) − MAE_i(arm), so positive means the arm is closer.
  - **Uncertainty for the difference:** a 95% interval and a p-value from the same 2,000-draw system bootstrap. The null is a zero mean difference; p is twice the smaller tail count, +1 corrected.
  - **Diagnostic:** a paired sign-flip permutation test (10,000 flips) is reported beside it and labelled as what it tests: per-system differences symmetric about 0, a stronger null than a zero mean (QA finding 4). It never decides a rule.
  - Also reported: systems closer, and splits with lower MAE.
- **Scope of the uncertainty** (also printed beside the results; QA finding 6):
  - Intervals resample whole systems with the fitted item parameters, fold assignments, control fits and task splits held fixed.
  - They are conditional on the 164 × 424 cohort. They are not intervals for a refitted procedure, unseen tasks or new model families.
  - Split percentiles describe the split distribution and are not population intervals.

## Decision rules (frozen)

| ID | Rule | Threshold source |
|---|---|---|
| P1 (rank) | `2pl_within_A` at n_A = 50: median Δ > 0 **and** share(Δ > 0) ≥ 0.60 over 2,000 splits | Experiment 07's frozen H2 rule (agent-suggested by Claude, 10-07-2026), reused unchanged |
| P2 (level) | K-fold `2pl` at n_A = 50: MAE difference versus pass@1 on A > 0 with its 95% system-bootstrap interval excluding 0 | VeriBench idea page Q1 row (agent-suggested by session 323c2b90, 10-09-2026) |
| Q1 | **CONTINUE** if P1 or P2 holds; **NO ADVANTAGE** if neither holds | Idea page Q1 row |
| P1 validity | A within-half fit that fails any gate leaves its split undefined. P1 is **inconclusive** if more than 1% of the 2,000 within-half 2PL fits at n_A = 50 fail, or if the decision changes when every failed split is set to its worst (Δ = −∞) and its best (Δ = +∞) case (QA finding 2) | Agent-suggested (this protocol) |
| P2 validity | P2 is **inconclusive** if any of the 10 primary K-fold 2PL fits fails a gate, any K-fold 2PL posterior at n_A = 50 exceeds the endpoint-mass bound, or check-grid rescoring exceeds its tolerance | Agent-suggested (this protocol) |
| Q1 (combined) | **CONTINUE** if a valid P1 or a valid P2 holds; **NO ADVANTAGE** if both are valid and both fail; **INCONCLUSIVE** otherwise | Idea page Q1 row, with the validity rules above |
| Interpretation | A P2 win counts as item-level IRT information only if the K-fold `2pl` also beats `linear_regression` on level, with an interval excluding 0. Otherwise it is credited to using the reference panel (difficulty shift and shrinkage). The result states this attribution beside the verdict (QA finding 6) | Agent-suggested (this protocol) |

The two primary rules are joined by "or", as the idea page defined Q1. That multiplicity is disclosed, not corrected. A forecast that fails is reported exactly like one that holds.

## Secondary analyses (prespecified; no verdict unless stated)

- **S1:** every arm at every n_A, rank and level (level only for arms on the pass@1 scale).
- **S2 (key secondary):** the graded model. Its rank arm is `grm3_within_A` and its level arm is `grm3`, judged by the same two rules. Does partial credit, weighted by IRT, help where 07's unweighted partial credit hurt?
- **S3:** each K-fold IRT arm against `mean_equating` and `linear_regression` on level, at n_A = 50.
- **S4: promotion gates at n_A = 50.** The population is all ordered pairs (incumbent I, candidate C) of distinct systems.
  - Gates:
    - G0 (scalar; AlphaHebe semantics): pass@1_A(C) > pass@1_A(I).
    - G1: the paired z = Δpass@1_A / SE exceeds 1. SE is the standard deviation (ddof 1) of the per-task differences, divided by √n_A.
    - G2 (the IRT gate from the idea page): (θ̂_C − θ̂_I) / √(sd_C² + sd_I²) > 1, using the within-half 2PL EAP abilities and posterior standard deviations.
    - Degenerate pairs (QA finding 3): a zero standard error gives z = +∞ for a positive gain, −∞ for a negative gain and 0 for identical responses. ±∞ are valid z values.
    - Matched counts: G1m takes the top N2 pairs by the paired z, where N2 is G2's count in that split (ties broken by pair index). G2m takes the top N1 by the IRT z. The matched counts are asserted in every split. If any split cannot be matched, the matched comparison is reported as unavailable. A rate with zero promotions is undefined, never 0.
  - Outcomes: a promotion is harmful when pass@1_B(C) < pass@1_B(I) and correct when it is greater.
  - Reported: promotions per split, and harmful- and correct-promotion rates pooled over splits. The matched differences HPR(G1m) − HPR(G2) and HPR(G1) − HPR(G2m) (positive means the IRT gate is safer) come with a 2,000-draw system-cluster bootstrap (conditional on each split's selections) and its p-value.
- **S5: stability.**
  - Each arm's per-system standard deviation of forecast and error across the 2,000 halves A, averaged over systems, with the ratio to pass@1 on A and a system-bootstrap interval.
  - The K-fold 2PL comparison repeated with fold seeds 1–4.
  - Pairwise agreement of item parameters across the 10 fold fits.
  - Convergence counts of the within-half fits at every size.
  - Each SWE-bench submission is a single run, so run-to-run (seed) variance of the systems is unavailable. The variance caution of Madaan et al. (2024) is addressed here through split-to-split and fold-seed stability.
- **S6: sensitivity, one system per base model.** Experiment 07's 73 systems, with the rank arm `2pl_within_A` refitted on those 73 and the level arm K-fold within the 73 (fold stream 6). n_A = 50.
- **S7: held-out cell Brier score at n_A = 50 (descriptive).** The K-fold 2PL cell predictions on half B, against a system-only predictor (pass@1 on A for every cell) and an item-only predictor (the reference systems' pass rate on each task).

## Validity checks and stop rules

1. Both input hashes match their pins.
2. The cohort reproduces 164 × 424 = 69,536 measured cells with exactly one inconsistent cell.
3. The split replay reproduces experiment 07's H2 exactly (see Splits).
4. The Rasch common-parameter check gives Δ = 0 in every split at every size. Otherwise STOP immediately (code defect), with no further analysis. The STOP writes a failure receipt with no verdict and no verdict-dependent outcomes, marks every frozen forecast outcome unavailable and exits non-zero (QA finding 5).
5. Fit convergence and the numerical gates, as in the models section and decision rules.
6. `rl4cv.forecast.verify_forecast` passes on the frozen forecast before any computation. The analyzer refuses to run otherwise.

## Compute

- **Resources:** CPU only. Zero model calls, no Valkyrie and no GPU.
- **Where it runs:** host `skampere1`, tmux session `ccv-rl4cv14-irt-q1-run`, from a `/lfs` checkout at the lock commit.
- **Command:** `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python analyze_e14.py --workers 64`. Results do not depend on the worker count.
- **Size:** about 16,000 within-half fits and 80 K-fold fits on the 1,201-node grid. The estimate is 1–2 hours with 32–64 processes.

## Not in this protocol

- No model calls.
- No change to experiments 07, 10 or 13.
- No task-sampling bootstrap with refits.
- No multidimensional IRT.
- No sealed VeriBench values (FSC for set B, set N or experiment 109) are read or needed.
