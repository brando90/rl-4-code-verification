# Experiment 19 protocol: interpretable IRT for SCSC factors, explain/predict and guide strict pass@1 (zero model calls)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/PROTOCOL.md>

**Status:** LOCKED, revision 2, 10-20-2026 16:51 PDT, before any real-data fit. Revision 2's gold-target forecast `expt_v1/forecasts/e19_forecast_gold_target.json` was frozen at 16:50 PDT (SHA-256 64a8ffc949d57567c1f69b4ac5b54c64c2ea25ca7ef7aab3c122b2f3ebd3e3d6). Deterministic checks gate it: `make test`, finite-difference gradients and synthetic recovery. Later changes are numbered amendments made before the data they affect.

**Amendment 01** (after the run started at 23:52:11Z and before any output was read): two primary endpoints (G1 and E1-strict IRT-beats-baselines; all else secondary), G1 reporting with its interval and the 135-task scope, corrected FSC point masses (59.5% / 2.5% on the primary panel), the committed compile-record check, and a token-cap sensitivity. See [AMENDMENT_01_10-20-2026.md](AMENDMENT_01_10-20-2026.md); it takes precedence where it differs.

**Revision history:**

- **Revision 1** was locked at 16:30 PDT (unpublished local commit cefd590a) under the provisional number 18, with frozen forecast `expt_v1/forecasts/e18_forecast.json` (SHA-256 ab3e31b275404be077d77597f9e004c6219da0d2fd3f517351a587945047a13c). Its run started on SNAP at 16:39 PDT and was stopped minutes later by its owner, before it wrote any output (its log holds only the two start lines). The reason was the renumbering below.
- **Revision 2** made two changes before any real-data output existed:
  - Renumbered 18 → 19, because branch `ub9/e18a-reasoning-gym-env-scoring` claimed experiment 18 before this folder was published.
  - Added a third downstream target, VeriBench experiment 111's strict gold-check pass@1 (sections 3 and 4). This follows the general coordinator's 10-20-2026 handoff: name "harsh SCSC" and "strict pass@1 on hidden gold tests (+PBTs)" as the downstream targets, and keep rl4cv 13's kernel strict reward distinct. The reference-consistency rows were re-extracted with their `typechecks` and `statable` columns, which the gold target needs.
- **What did not change:** revision 1's frozen forecast stays byte-identical. Its internal label reads 18. A second forecast, covering the gold target only, is frozen at revision 2 (`expt_v1/forecasts/e19_forecast_gold_target.json`).

**TLDR:** Two questions, zero paid calls, CPU only. (1) Explain and predict: on the 11 unsealed VeriBench V1 systems, do item response theory (IRT) models of the SCSC factors and task content predict held-out (validation-split) strict and harsh success better than simple baselines and the plain smooth score? (2) Guide: before any reinforcement learning (RL), can an IRT forecast pick the train prompts on which experiment 13's start policy gives mixed strict groups — the precondition for an IRT-selected prompt pool to raise strict pass@1 — measured against experiment 13's own frozen gate (AUC ≥ 0.70)? An IRT-weighted partial reward cannot be tested with existing data (section 6).

Terms used throughout:

- **SCSC** (smooth conjunctive score for code verification) = (IC_tests · IC_proofs · FSC)^(1/3). IC_tests: the Lean file typechecks and states at least one `example`. IC_proofs: the fraction of stated theorems the kernel accepts. FSC (formal specification coverage): the validated judge's coverage rating in [0, 1].
- **Strict success** = 1[IC_tests = 1 and IC_proofs = 1], the panel's analogue of rl4cv's official strict scorer (`kernel_binary`, experiment 13's strict reward). **Harsh success** = strict success and FSC = 1 (VeriBench experiments 111 and 119's harsh SCSC). **Gold-check pass@1** = the agent's own code passes every grounded gold unit test and no gold property is refuted (VeriBench experiment 111's preferred metric, tests + PBTs variant; section 3).
- **IRT:** P(system i succeeds on task j) = σ(a_j·θ_i + d_j), with ability θ_i, discrimination a_j and intercept d_j (a 2PL model); difficulty is −d_j/a_j.
- **Mixed group:** a group of G = 8 samples on one prompt with both strict successes and failures; only mixed groups give a group-relative policy optimization (GRPO) update any gradient. **AUC:** area under the ROC curve.

## 1. Questions and the decisions they inform

Source: the general coordinator's 10-20-2026 assignment, relaying Brando ("I really want the IRT and SCSC stuff to be running to see if they lead to downstream performance") and Azalia Mirhoseini's suggestion that the decomposed metric should guide improvement of the downstream harsh metric, not just correlate with it. VeriBench idea page: `experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md` (Q3 is folded in here as E3).

| ID | Question | Decision it informs |
|---|---|---|
| E1 | Do IRT models of the factors predict a held-out system's validation-split strict, harsh and gold-check outcomes better than its own train rate, a non-IRT additive model and the plain smooth score? | Whether IRT-based factor models are worth using as forecasting tools for VeriBench systems |
| E2 | Which interpretable task features explain item difficulty, and do they predict the difficulty of unseen tasks? | Whether task content can screen tasks or RL prompts before any rollout |
| E3 | Are strict success and FSC one latent skill or two? | Whether the factors carry information the scalar loses (idea page Q3) |
| G1 | Does an IRT forecast, using only other systems' outcomes and task content, identify the prompts on which experiment 13's start policy gives mixed strict groups? | Whether to send experiment 13's owner a frozen proposal for an IRT-selected prompt arm |
| G2 | Would an IRT-weighted partial reward raise strict pass@1? | Not testable with existing data (section 6) |
| G3 | Frozen per-prompt forecasts for experiment 13 v4's group-size batch (V4-G0) and an IRT prompt arm | Prospective check, scored when experiment 13 publishes those counts |

## 2. Data, splits and what was seen before this lock

All inputs are committed in this repository; their SHA-256 values are pinned in `expt_v1/input_pins_e19.json` at lock, and a mismatch stops the run.

- **Panel (E1–E3, G1 predictors):** the 11 systems of experiment 12's committed join (`experiments/12_…/expt_v1/results/input_manifest.json`) of VeriBench experiments 102 (Claude Code, Codex, Leanstral and the paper baseline) and 103 (seven single-call models). FSC is the validated H2 judge. Experiment 12 bound its sources by hash; those hashes equal VeriBench `origin/main` (07c4b48) for both files.
  - A cell enters the IRT fits only with source status `measured`. `zero_without_call` (428 baseline train/validation cells, 1 Codex) is treated as **missing**, following the VeriBench idea page ("the baseline's … empty outputs are missing, not zeros"); a sensitivity run counts them as failures (G1 only). `incomplete`, `unmeasured_infra` and `model_error` cells have no factors and are missing.
  - IC_proofs for the experiment 102 systems is VeriBench's source-scanned count, not the kernel-axiom rescore; this is inherited from experiment 12 and recorded as a limitation.
- **Reference consistency (gold-check target and E3b):** VeriBench experiment 111's per-cell rows for the same 11 systems (`typechecks`, `statable`, gold unit tests, PBTs and obligations), copied by `expt_v1/extract_rc_e19.py` from VeriBench commit 07c4b48 with source hashes (`results/inputs/rc_rows_panel_trainval_provenance.json`). Experiment 103 rows carry a `typechecks` column. Experiment 102 (TMLR) rows exist exactly for files that typecheck: on open train and validation tasks, a row is present for 1,861 of 1,861 measured cells that experiment 12 records as compiling and absent for 342 of 342 that do not. The baseline's 420 open `zero_without_call` cells are empty outputs, which typecheck trivially and have rows. The 27 rating-set tasks are withheld at the source; 18 of them fall in train or validation.
- **Start policy (G1 target):** experiment 13's start policy `sft_4B_f1p0` (Qwen3-4B, 658 SFT steps) on the 135 validation tasks, 8 samples each, from experiment 08 v1 (`ladder/sft_4B_f1p0_validation_per_task.csv`). Its sampler (temperature 0.6, top-k 20, top-p 0.95, 12,288 new tokens) is exactly experiment 13 v4's rollout sampler.
- **Start-policy ability calibration:** experiment 13 v2's A6 train diagnostic (`expt_v2/phase1/A6_S2_result.json`): 48 strict successes of 496 measured responses on 64 seeded train tasks (16 missing; full-denominator bounds [0.09375, 0.125]). Only this aggregate is used; A6 task identities stay closed, as experiment 13's owner left them.
- **Task features (E2, G1):** `expt_v1/results/task_features_e19.csv`, computed by `features_e19.py` from each task's Python source and gold Lean reference at the pinned VeriBench commit (c11b99b, `external/deps.lock.json`), hash-checked against the D-013 split manifest.
- **Splits (D-013):** train 539 tasks (400 groups), validation 135 (100 groups). **The test split (222 tasks) is never touched:** test rows are dropped on read by every loader, no test-task feature is computed or committed, and no test file is opened. VeriBench experiments 107 and 109 are excluded entirely: their per-item rows (and, before 11-06-2026, their aggregates in committed files) are sealed for everyone.
- **Already seen before this lock** (disclosed, none of it a predictor–outcome association): the start policy's marginal distribution of validation successes (102 tasks at 0/8, 32 mixed, 1 at 8/8; 100/1,080 successes) and the A6 counts above; experiment 12's published per-system factor means over 896 tasks; the panel's marginal FSC value counts, IC_tests/IC_proofs agreement counts and source-status counts; synthetic-data runs of this pipeline; and, at revision 2, the gold-check target's marginal cell accounting over all 11 systems on train and validation tasks (2,150 pass, 15 fail a gold check, 3,384 do not typecheck, 421 solver returned nothing, 1,444 missing: 443 lost generations, 172 withheld, 817 not statable, 12 with no grounded check), computed to verify the construction (0 cells with IC_tests = 1 lack a typecheck row).

## 3. Definitions

- **Gold-check pass@1 per cell** (VeriBench 111, `results/scsc_vs_rc_preferred_metric/README.md`, tests + PBTs variant): 1 when every grounded gold unit test passes on the agent's own code and no gold property is refuted by Plausible; 0 when the file does not typecheck or the solver returned nothing (`zero_without_call`, counted 0 here as VeriBench 111 does); missing for lost generation cells, withheld rating-set tasks, code that typechecks but is not statable, and statable cells with no grounded test and no testable property. Missing cells are never 0.
- **Responses:** strict, harsh and gold-check are binary. FSC enters the graded model as five ordered categories: 0 | (0, 0.5] | (0.5, 0.8] | (0.8, 1) | 1. Per-file smooth SCSC = (IC_tests·IC_proofs·FSC)^(1/3) (diagnostic only, as VeriBench defines it).
- **Why a graded response model (GRM), not Beta-IRT:** in this panel 56% of measured FSC values are exactly 1 and 8% exactly 0. A Beta density has no mass at either end, so partial credit enters through ordered categories instead, as experiment 14 decided for the same reason.
- **Task features** (counts as log1p, all z-scored with train-split moments): Python implementation statements, functions, loops, branches, float use, string use, asserts in `check`; gold-reference theorems, examples, non-comment lines; and six family-group indicators (humaneval, easy, realcode, cs, industry-real, industry-synthetic; security is the reference level).
- **Models** (all marginal maximum a posteriori on fixed ability grids, abilities N(0, 1)):
  - *2PL (random intercepts):* binary strict (or harsh) responses on one skill; log slopes N(0, s_a²); intercepts d_j = w0 + e_j with e_j ~ N(0, σ_e²) and w0 ~ N(0, 2²). With only 10–11 systems per item, experiment 14/15's weak priors (log slopes N(0, 1), intercepts N(0, 5²)) give overconfident predictions on items every system passes or fails. On synthetic 2PL data, they lost to the non-IRT additive baseline by 0.06 in held-out log loss. They are kept only as a G1 sensitivity.
  - *Explanatory 2PL:* the same with d_j = x_j·w + e_j, w ~ N(0, 2²), x_j = (1, task features).
  - *R0, regularization:* (s_a, σ_e) ∈ {0.25, 0.5, 1} × {0.5, 1, 2, 4} is chosen separately for the random-intercept and explanatory 2PL. The criterion is the mean held-out log loss of train-split strict cells under grouped 5-fold cell-level cross-validation, with folds by a hash of (system, D-013 group). Ties go to the larger σ_e, then the larger s_a. Only train cells enter R0. The random-intercept choice is used for E1, E3 and the G1 primary forecast; the explanatory choice for E2 and the G1 feature variants.
  - *Two-skill model (M3):* strict loads on skill s (2PL), FSC categories on skill f (GRM), with (s, f) bivariate normal, correlation ρ = tanh(r), r ~ N(0, 1). Strict intercepts are N(μ_d, σ_e²) and first FSC thresholds N(μ_g, σ_e²), with μ_d, μ_g ~ N(0, 2²). Slopes are log-normal with SD s_a; log threshold gaps are N(0, 2²); (s_a, σ_e) are R0's random-intercept choice. *Tied model (M3t):* the same with s = f.
  - *Unseen items* (no responses from any system) use the empirical-Bayes item curve: P(success | θ) averaged over the training items' fitted slopes and intercept residuals, centred at x·w (explanatory) or w0 (random intercept).

## 4. Analyses and pre-registered decision rules

Uncertainty, unless stated otherwise: 10,000 bootstrap draws over **validation task groups** (D-013 group id, so near-duplicate and safe/vulnerable pairs move together), seed 20261020, with the fitted models held fixed. These intervals cover task sampling of the validation split, not system sampling or fit uncertainty. p-values are two-sided percentile-bootstrap tests of a zero difference, 2·min(P(Δ* ≤ 0), P(Δ* ≥ 0)), floored at 1/10,000. "CI above 0" means the 95% interval's lower end is above zero. Thresholds other than G1's are agent-suggested.

### E1. Held-out prediction for a held-out system (leave one system out)

For each of the 11 systems: item parameters are fitted on the other 10 systems over all train and validation tasks; the held-out system is observed on its **train** tasks only; its measured validation cells are predicted.

- **Methods:** M0 its own train rate ((successes + 0.5)/(n + 1)); M1 a non-IRT additive model, logit p = logit(M0) + logit(other systems' rate on the task) − logit(other systems' overall rate); M2 the random-intercept 2PL; M3 the two-skill model; M3t the tied model. For harsh, M2 is a 2PL on harsh responses and M3 gives P(strict and FSC category 1) from the joint posterior.
- **Metric:** mean per-cell log loss (and Brier score) over all held-out validation cells, pooled across systems.
- **Gold-check target:** M0, M1 and M2 (a random-intercept 2PL on gold-check responses), with each method using the gold target's own missingness; the two-skill model does not define it.
- **Rules (each target separately):** "IRT adds held-out information" iff both M1 − M2 and M0 − M2 have CI above 0. For strict and harsh, "the FSC skill adds information" iff M2 − M3 has CI above 0.
- **E1c, system level, the plain smooth score as a held-out pass@1 predictor:** each system's validation strict, harsh and gold-check rate is forecast from its train data by: its own train rate; a leave-one-system-out linear calibration of the train rate; the same calibration of its train mean smooth SCSC; the raw train mean smooth SCSC; and the IRT forecasts (mean of M2 cell predictions, and of M3 for strict and harsh). The smooth score is always the per-file SCSC over the system's measured panel cells. Reported: mean absolute error (MAE), mean bias (forecast − observed) with both means, and Pearson, Spearman and Kendall correlations across the 11 systems. **Rule:** from the bootstrap of MAE(rate calibrated) − MAE(smooth calibrated): "smooth better" if CI above 0, "smooth worse" if CI below 0, else "no detectable difference". With 11 systems this is low-powered and is labeled so.

### E2. Which task features explain difficulty

- **E2a:** R0's grid scores for both models are reported in full (section 3).
- **E2b (descriptive):** the explanatory 2PL on all 11 systems' train-task responses (strict; harsh and gold-check secondary). Each coefficient is in logit-intercept units per standard deviation of the feature (positive = easier), with a 95% interval from 500 refits on train-group bootstrap resamples (seeded), and the share of intercept variance the features explain.
- **E2c rule:** validation tasks are treated as unseen (no system's responses on them are used). Abilities come from train responses. Validation items are predicted from features (explanatory fit) or from the random-intercept population (no features), both fitted on train items. "Content features predict the difficulty of unseen tasks" iff (no-features − features) mean validation log loss has CI above 0.

### E3. One skill or two

- **E3a rule:** from the E1 folds, the mean per-cell held-out log predictive density of validation strict and FSC-category responses under M3 versus M3t. "Strict success and FSC are distinct skills" iff M3 − M3t has CI above 0. Also reported: ρ̂ for each fold (11 values, median and range).
- **E3b (descriptive):** across train and validation items, Pearson, Spearman and Kendall correlations between fitted 2PL intercepts for strict, for FSC = 1 and for RC_fspecs = 1 (the gold reference's obligations all proved; items with at least 3 measured RC cells), with 1,000-draw item-group bootstrap intervals.

### G1. Can an IRT forecast pick the prompts that give the start policy learning signal?

- **Forecast:** a random-intercept 2PL fitted on all 11 panel systems' strict responses over train and validation tasks. The start policy's ability θ0 is the value at which the mean predicted strict rate over the 539 train tasks equals the A6 rate 48/496. For each validation task, p̂ = σ(a·θ0 + d) and the forecast mixed-group probability is q̂ = 1 − p̂⁸ − (1 − p̂)⁸. No start-policy outcome enters the forecast.
- **Outcome:** the start policy's observed group of 8 on each validation task is mixed (1 ≤ k ≤ 7).
- **Primary statistic:** AUC(q̂, mixed) over the 135 validation tasks, with its 95% interval and a one-sided percentile-bootstrap p-value against 0.70 (the share of draws ≤ 0.70).
- **Comparators** (same AUC): the panel's strict rate per task; the panel's mean smooth SCSC per task (the smooth score as a prompt selector); an explanatory 2PL (features prior); features only (validation tasks unseen). Paired differences against the primary, with intervals and p-values.
- **Also reported:** the mixed share among the top quarter of tasks (34 of 135) by each score, against the uniform share; the expected mixed share under experiment 13's original arm-C prompt sequence (50% uniform + 50% proportional to item information a²·p̂·(1 − p̂)); expected mixed groups per 256-rollout update at G = 8; calibration (mean predicted against observed rate; binomial log loss against a constant A6-rate forecast; correlations of p̂ with k/8); the AUC of p̂ for "at least one success"; sensitivities with θ0 set at the A6 full-denominator bounds, with `zero_without_call` cells counted as failures, and with experiment 14/15's weak priors.
- **Rule** (threshold source: experiment 13 `PROTOCOL.md` section 4, gate F2, "AUC ≥ .70 for predicting mixed strict groups from 1 − p⁸ − (1 − p)⁸"):
  - **PASS, IRT-SPECIFIC:** AUC ≥ 0.70, and the AUC differences against both the panel strict rate and the panel mean smooth score have CI above 0.
  - **PASS, NOT IRT-SPECIFIC:** AUC ≥ 0.70 without that.
  - **FAIL FOR IRT, HEURISTIC PASSES:** AUC < 0.70 while a heuristic reaches 0.70.
  - **FAIL:** none reaches 0.70.
- **What each verdict triggers:** a PASS sends experiment 13's owner a frozen proposal for an added prompt-selection arm (strict reward, prompts drawn by the winning rule, frozen item parameters), with the G3 forecast. It never edits experiment 13's frozen v4 protocol. If the pass is not IRT-specific, the proposal uses the simpler heuristic and says IRT added nothing measurable. A FAIL is reported as a negative result, and no arm is proposed.

## 5. Numerical gates

- Every primary fit must reach a maximum absolute gradient ≤ 1e-4 on its fitting grid and on a wider check grid. One-skill grids are experiment 14's: 1,201 nodes on [−12, 12], checked on 4,801 nodes on [−18, 18]. The two-skill product grid is 401 nodes per axis on [−9, 9], checked on 1,201 per axis on [−12, 12]. If a two-skill fit fails its check, it is refitted once on 801 nodes per axis. A fit that still fails is reported as failed, and its comparisons are marked unavailable; they are never replaced by another model.
- Finite-difference gradient tests and synthetic-recovery tests run in `make test` before lock.

## 6. G2: an IRT-weighted partial reward cannot be tested with existing data

Experiment 13's original arm C weighted the partial-credit components (declarations, implementation/examples, proved fraction) by item information. Testing whether such a reward points toward strict success needs per-sample components *and* strict variation for one policy at the v4 sampler on tasks with open identities. No such data exist:

- For this start policy, every compiling A6 response was a strict success (48 compiling, 48 strict). Partial credit therefore varies only inside failed files.
- The A6 per-sample receipts keep task identities closed by the owner's choice.
- Experiment 13 v2's anchors and the v3 pilot sample at temperature 1, with essentially no strict successes.
- Experiment 08's validation cells record IC factors but not the declaration-level components.

**Cheapest test (not run here):** re-score experiment 08's stored `sft_4B_f1p0` validation outputs (1,080 Lean files on SNAP) with experiment 13's declaration probe. This is CPU-only and costs $0. Then test whether the component-weighted partial reward ranks a task's samples, or the tasks, in the direction of strict success.

## 7. G3: prospective forecasts for experiment 13 v4

After G1 runs, and before any v4 generation exists (v4 starts only after v3-A7's pilot ends), this lane freezes with `rl4cv.forecast.freeze_forecast`:

- the G1 primary model's p̂ and q̂ for G = 8 and G = 16 on all 539 train tasks;
- the implied mean mixed-group probability over the 32 V4-G0 tasks (NumPy `default_rng(1304001)` over the sorted train ids);
- a probability that an added IRT-selected prompt arm would beat arm A on validation strict mean at matched tokens.

Scoring, when experiment 13 publishes per-task G0 counts: Spearman correlation between q̂ and the unbiased per-task mixed probability, and AUC of q̂ for tasks with 1 to 31 successes out of 32.

## 8. Execution and outputs

- **Cost:** zero model calls, zero GPUs, $0. Development and tests run on the Mac with synthetic data. The locked real-data run executes once on SNAP `skampere1` (CPU), in tmux session `cc-rl4cv-e19-irt-run`, from a checkout at the lock commit; it refuses to start if HEAD differs from the lock commit.
- **Outputs:** `expt_v1/results/analysis_e19.json` (every statistic), plus the per-task G1 table (validation tasks only), the E1 per-system tables, the E2 coefficient table and `results_tables_e19.md`. All are committed; nothing here is sealed or private.
- **Reporting:** `results.md` (live), with Hard Rule 11 statistics. A failed rule is reported exactly like a passed one.

## 9. What this experiment does not claim

- It makes no RL claim: G1 tests the precondition for prompt-pool guidance (identifying learning-signal prompts), not that a selected pool raises strict pass@1. That needs experiment 13's arm and is forecast in G3.
- It makes no claim about frontier 2026 agents (experiments 107/109 are sealed), the test split or VeriBench V2/V3.
- With 11 systems, system-level results (E1c, ρ̂) are descriptive.
