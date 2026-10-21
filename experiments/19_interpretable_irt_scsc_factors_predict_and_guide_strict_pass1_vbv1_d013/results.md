# Experiment 19 results: interpretable IRT for SCSC factors, explain/predict and guide strict pass@1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/results.md>

Experiment 19 (rl4cv, zero model calls, 11 unsealed VeriBench V1 systems, D-013 validation split): an IRT forecast picks the prompts where experiment 13's start policy gives mixed strict groups (AUC 0.862 [0.792, 0.925], above 13's 0.70 gate), but not better than the plain panel pass rate. IRT factor models add nothing over a simple additive model for held-out strict pass@1. The smooth score forecasts held-out harsh and gold-check pass@1 worse than the raw rates do.

**Status:** DONE 10-21-2026. The single locked run (lock 30db1fc3, Amendment 01 at 19ba81ff) ran on skampere1 from 23:52:11Z to 01:50:56Z (7,124 s, exit 0, $0). One numerical gate failed (the untied two-skill model, M3, in 8 of 11 folds), so its comparisons are unavailable. Result tables: [expt_v1/results/results_tables_e19.md](expt_v1/results/results_tables_e19.md); raw output: `expt_v1/results/analysis_e19.json`.

**Last updated:** 10-21-2026

| Phase | State |
|---|---|
| Protocol lock (revision 2), pins, two frozen forecasts | DONE 10-20-2026 |
| Amendment 01 (light QA: primary endpoints, G1 scope, corrections, cap sensitivity) | DONE, before any output was read |
| Locked run (R0, E1, E2, E3, G1) | DONE; M3 gate failed in 8/11 folds, every other fit converged |
| Token-cap sensitivity (Amendment 01) | DONE |
| G3 frozen forecasts for experiment 13 v4 | DONE (frozen 01:58:55Z, before any v4 generation) |

## Primary endpoints (Amendment 01)

| Endpoint | Rule | Measured | Verdict |
|---|---|---|---|
| **P1, G1:** does an IRT forecast find the prompts where experiment 13's start policy gives mixed strict groups? | AUC ≥ 0.70 (experiment 13 PROTOCOL.md §4, gate F2) | AUC 0.862 [0.792, 0.925], 0/10,000 bootstrap draws ≤ 0.70 (one-sided percentile-bootstrap p-val < 0.0001). A point-estimate gate on n = 135 validation tasks: 32 mixed, 103 not mixed, 100 bootstrap groups. F2 was written for 539 train tasks. | **PASS, NOT IRT-SPECIFIC** |
| **P2, E1-strict:** does IRT add held-out information about strict success? | M1 − M2 and M0 − M2 log-loss differences both have 95% intervals above 0 | M1 − M2 = +0.0015 [−0.0059, +0.0086] p-val=0.69. M0 − M2 = +0.0386 [+0.0166, +0.0616] p-val=0.0002. 1,308 validation cells, 609 positives. | **FALSE**: IRT beats the system's own rate but not the non-IRT additive model |

Intervals here and below are percentile bootstraps over validation task groups: 10,000 draws, seed 20261020, fitted models held fixed. They do not cover system sampling or fit uncertainty. p-values test a zero difference, two-sided (2·min share of draws on each side), unless stated otherwise.

## G1 in detail: choosing RL prompts for experiment 13 (validation, start policy `sft_4B_f1p0`, v4 sampler)

| Forecast (no start-policy outcome used) | AUC for a mixed group of 8 [95% CI] | Mixed share in the top quarter (34 of 135) [95% CI] |
|---|---|---|
| Random-intercept 2PL, primary | 0.862 [0.792, 0.925] | 0.706 [0.433, 0.853] |
| Panel strict pass rate (heuristic) | 0.852 [0.781, 0.916] | 0.647 [0.424, 0.794] |
| Panel mean smooth SCSC (heuristic) | 0.857 [0.785, 0.922] | 0.676 [0.441, 0.824] |
| Explanatory 2PL (panel + task features) | 0.883 [0.818, 0.939] | 0.706 [0.438, 0.875] |
| Task features only (validation tasks unseen) | **0.954 [0.909, 0.987]** | 0.794 [0.531, 0.919] |
| Uniform pool | 0.5 | 0.237 |

- **Not IRT-specific.** IRT minus the panel strict rate: +0.011 [−0.004, +0.027] p-val=0.15. IRT minus the panel smooth score: +0.006 [−0.014, +0.025] p-val=0.58.
- **Task content predicts better than other systems' outcomes (secondary, exploratory).** The features-only model beats the primary 2PL by 0.092 [0.023, 0.164] p-val=0.011. The explanatory 2PL also beats the primary, by 0.021 [0.008, 0.037] p-val=0.001. Features-only versus explanatory was not a pre-registered contrast. One plausible reason, not tested here: the single-call systems' failures are often Lean well-formedness problems that this SFT policy does not share.
- **A selected pool triples learning signal per update.** Top-quarter mixed share 0.706 against 0.237 uniform: +0.469 [0.266, 0.562] p-val=0.0001. At G = 8 that is 22.6 against 7.6 mixed groups per 256-rollout update. Experiment 13's original arm-C prompt sequence (50% uniform + 50% item information) gives 0.312: +0.074 [0.050, 0.097] p-val=0.0001.
- **Ranking is good, level is not.** Mean predicted mixed probability is 0.482 against 0.237 observed. Predicted per-task success rates spread less (SD 0.107) than observed k/8 (SD 0.204): the policy is more all-or-nothing than the model. Mean predicted strict rate is 0.111 against 0.093 observed (bias +0.018). Binomial log loss is 0.234, against 0.309 for a constant A6-rate forecast.
- **Sensitivities (secondary).** The primary AUC stays at 0.862 or 0.863 with θ0 set at the A6 full-denominator bounds, at 0.846 with `zero_without_call` counted as failures, and at 0.820 with experiment 14/15's weak priors.
- **Token-cap sensitivity (Amendment 01).** Dropping the 13 tasks with ≥ 4 of 8 samples at the 12,288-token cap (all 13 had zero successes) leaves 122 tasks (32 mixed, 90 not, 88 groups). There the primary AUC is 0.845 [0.768, 0.915], with 5/10,000 draws ≤ 0.70. The heuristics score 0.831 and 0.839, and IRT minus the panel strict rate is +0.014 [−0.003, +0.031] p-val=0.10. Same pattern.

**What this means for experiment 13.** Prompt selection by any of these forecasts would roughly triple the gradient-carrying groups per update, which is the precondition for a pool to raise strict pass@1. Under the pre-registered rule, the proposal to 13's owner uses the simpler panel-pass-rate heuristic, not IRT. The features-only forecast is the best predictor here but exploratory. G3 tests all three forecasts prospectively on 13's own V4-G0 train batch.

## Explain and predict across systems (E1–E3; secondary except P2)

**Held-out cells (leave one system out; mean log loss over validation cells):**

| Target (cells, positives) | M0 own rate | M1 additive (non-IRT) | M2 random-intercept 2PL | M1 − M2 [95% CI] p-val |
|---|---|---|---|---|
| Strict (1,308; 609) | 0.4136 | 0.3765 | 0.3750 | +0.0015 [−0.0059, +0.0086] p-val=0.69 |
| Harsh SCSC (1,308; 456) | 0.4057 | 0.3504 | 0.3484 | +0.0020 [−0.0090, +0.0128] p-val=0.70 |
| Gold-check pass@1, tests+PBTs (1,226; 469) | 0.4328 | 0.3704 | 0.3839 | −0.0135 [−0.0209, −0.0057] p-val=0.0014 |

Item difficulty from other systems matters (M0 − M1 is +0.037 to +0.063, every interval above 0). The IRT structure adds nothing beyond a simple additive model, and for gold-check pass@1 it is slightly worse. The FSC-skill comparisons (M3) are unavailable. As a descriptive note only (not a pre-registered contrast): the tied one-skill model, which forces FSC onto the strict skill and passed its gates, predicts strict cells much worse than M2 (0.532 against 0.375).

**System level (E1c, n = 11 systems; validation pass rate forecast from train data):**

| Target | MAE, own train rate calibrated | MAE, smooth SCSC calibrated | Rate minus smooth [95% CI] p-val | Verdict |
|---|---|---|---|---|
| Strict | 0.030 | 0.033 | −0.004 [−0.010, +0.011] p-val=0.67 | no detectable difference |
| Harsh SCSC | 0.027 | 0.180 | −0.154 [−0.164, −0.127] p-val=0.0001 | smooth worse |
| Gold-check | 0.034 | 0.102 | −0.068 [−0.087, −0.046] p-val=0.0001 | smooth worse |

- **Biases.** Mean bias (forecast − observed) of the calibrated forecasts is within ±0.01 for every target.
- **Raw smooth score.** It sits +0.120 above the observed harsh rate (means 0.443 vs 0.323) and +0.034 above gold-check (0.443 vs 0.409).
- **Rank correlations.** For strict, every forecast correlates about 0.99 with the observed rates (Pearson / Spearman / Kendall 0.993 / 0.982 / 0.927 for smooth). For harsh, the smooth score drops to 0.628 / 0.606 / 0.561. The worst offenders are the paper baseline and Leanstral: harsh 0.000 on validation, yet calibrated smooth forecasts of 0.598 and 0.340.
- **IRT vs plain rate.** The IRT forecast (M2) matches the calibrated rate at the system level: MAE difference +0.0005 [−0.0057, +0.0131] for strict.

**Task features (E2).** Content features predict the difficulty of unseen tasks for every target. Without features minus with features, in validation log loss: strict +0.067 [+0.047, +0.087], harsh +0.076 [+0.047, +0.104], gold-check +0.067 [+0.040, +0.095]; p-val=0.0001 for all three. The strict coefficients below are logit intercept per SD (negative = harder), with 500-refit train-group bootstrap intervals; all 500 refits converged for each target.

- **Harder:** longer Python implementations (−0.72 [−1.11, −0.36]), longer gold references (−0.34 [−0.62, −0.10]), string handling (−0.13 [−0.26, −0.01]), and IndustrySet relative to the security set (real −0.99 [−1.44, −0.59], synthetic −0.96 [−1.40, −0.58]).
- **Unexpectedly hard:** the easy set (−1.33 [−2.06, −0.69]).
- **Not credibly different from zero:** gold theorem count (−0.08 [−0.28, +0.15]).
- **Inflated statistic:** the "share of intercept variance explained" (0.985–0.995) is inflated by R0's strong shrinkage (residual SD 0.5) and should not be quoted as a fit statistic.

**One skill or two (E3).** The pre-registered held-out test (E3a) is unavailable because of the M3 gate failure. Descriptively, across the 674 items, how hard a task is for strict success and how hard it is for FSC = 1 correlate at Spearman 0.568 [0.516, 0.619] (Pearson 0.541, Kendall 0.398). Strict and gold obligations proved (RC_fspecs = 1) correlate at only 0.269 [0.147, 0.379] (428 items with ≥ 3 RC cells). FSC = 1 and RC_fspecs = 1 correlate at 0.247 [0.155, 0.334]. The intervals come from 1,000 item-group bootstraps.

## G2 and G3

- **G2 (IRT-weighted partial reward):** not testable with existing data, as the protocol recorded. The cheapest test is a CPU re-score of experiment 08's stored `sft_4B_f1p0` validation files with experiment 13's declaration probe.
- **G3:** frozen at 2026-10-21T01:58:55Z (`expt_v1/forecasts/e19_g3_forecast_v4_g0.json`, sha256 abb0cb31…, ledger time authoritative; the judgement's "made_at" text says 19:05 PDT and is 6 minutes off). That was after experiment 13's 18:55 PDT master checkpoint, which reported v4 as CPU code only.
  - It holds per-task strict probabilities and mixed-group probabilities (G = 8 and 16) for all 539 train tasks from three forecasts: the primary 2PL, the panel strict rate, and features only.
  - The raw model-implied mean mixed probability over V4-G0's 32 tasks is 0.42. The judgement corrects for the validation over-prediction and forecasts the observed value at 0.20 [0.10, 0.32]. It puts P(G0 selects G = 16) = 0.30 and P(an added top-quarter prompt arm beats arm A on validation strict mean at matched tokens) = 0.60.
  - Scoring follows when 13 publishes per-task G0 counts.

## Frozen forecasts of this lane's own outcomes, scored

| Forecast | Numeric inside 80% interval | Events, mean Brier | Not scored (M3 gate) |
|---|---|---|---|
| `e18_forecast.json` (revision 1, 16:30 PDT) | 2/7 | 0.075 on 8 | 2 numeric, 3 events |
| `e19_forecast_gold_target.json` (16:50 PDT) | 1/3 | 0.215 on 4 | none |

My priors badly underestimated G1. The primary AUC was forecast 0.72 [0.62, 0.81] and came in at 0.862; features only was forecast 0.65 [0.55, 0.75] and came in at 0.954. I also did not expect the smooth score to be worse for gold-check pass@1 (P = 0.20, Brier 0.64).

**Hash convention:** each `.sha256` sidecar is the SHA-256 of the canonical JSON text without its trailing newline (`rl4cv.forecast`). Verify with `rl4cv.forecast.verify_forecast`. A plain `sha256sum -c` fails because the files end with a newline.

Both hashes for each frozen file, so either check works. Each file was committed once and never modified:

| File | Recorded (canonical text, no final newline) | Plain sha256 of the file bytes |
|---|---|---|
| `e18_forecast.json` | ab3e31b275404be077d77597f9e004c6219da0d2fd3f517351a587945047a13c | cf9bed2aaea2d1c27394be8eebb9af8375db7ba14a88860f12bf194bf70312ee |
| `e19_forecast_gold_target.json` | 64a8ffc949d57567c1f69b4ac5b54c64c2ea25ca7ef7aab3c122b2f3ebd3e3d6 | 2b4fd33b515d6b0d81302cc64374f03e1ffaa89e9469bcce0e87611f24ff5940 |
| `e19_g3_forecast_v4_g0.json` | abb0cb3115b86fd3107a565fdfacd53343f285b7d27b34fd30d4dcb682436286 | f5ef9be081218170e0f5cc038b7a42a3a89bf811619291017f5a5066f33142f8 |

One-line check of the recorded hash: `python3 -c "import hashlib,sys; b=open(sys.argv[1],'rb').read(); print(hashlib.sha256(b.rstrip(b'\n')).hexdigest())" <file>`.

## Limitations

- **Small panel.** Only 11 systems, and system-level statistics have n = 11. VeriBench 107/109's 2026 frontier systems stay sealed until 11-06-2026.
- **Regularization at the grid edge.** R0 chose the edge of its grid: slope SD 0.25 for both models, and residual SD 0.5 for the explanatory model. Shrinkage stronger than the grid allows might have been preferred.
- **Two-skill integration.** The untied two-skill model's product grid was too coarse even at 801 nodes per axis for 8 of 11 folds.
- **Inherited measurement choices.** IC_proofs for the four experiment 102 systems is VeriBench's source-scanned count. The gold-check target is reconstructed from committed VeriBench 111 rows using its documented rules; experiment 111's per-cell file is private, so it is not cross-checked against it.
- **G1's population.** G1 measures validation tasks, which have no SFT exposure. Experiment 13 trains on train tasks, which do; G3 checks that transfer.
- **What G1 shows.** G1 shows prompt selection raises the gradient-carrying share. It does not show that strict pass@1 rises.
- **Process.** The repository suite has 61 failures on macOS (process and tmux tests) but only 3 on Linux (skampere1: 1,357 passed). Those 3 also fail at origin/main 57482ca2 without this experiment (receipt: `expt_v1/results/receipts/pytest_origin_main_57482ca2_three_preexisting_failures.txt`).

## Chronology and reproducibility

- 10-20-2026 16:30 PDT: revision 1 locked as a provisional experiment 18. Its run was stopped at start with no output.
- 16:50–16:51 PDT: revision 2 (renumbered 19, gold-check target added); lock 30db1fc3; gold forecast frozen.
- 23:52:11Z: locked run started.
- 00:20:27Z: Amendment 01 committed (19ba81ff, then pushed). At 00:22Z `analysis_e19.json` was still absent, so it did not exist at commit time.
- 01:50:56Z: run ended, `RUN_EXIT=0`. 01:58:55Z: G3 frozen.
- Inputs: `expt_v1/input_pins_e19.json`. Run log: `expt_v1/results/receipts/run_e19_log_skampere1.txt`, a byte-identical copy of the gitignored `run_e19.log` (sha256 574a8615…). Environment: Python 3.12.14, NumPy 2.2.6, SciPy 1.16.3 on skampere1.
- `analysis_e19.json` sha256: 8edbb91d5b57259381cdcaa60013f44382c37b284ff51121b5d3b5b132ef604d.

**Copy-ready message:** "Quick IRT update: an IRT model fit on other systems does find the prompts where our 4B SFT policy gets mixed (learnable) GRPO groups (AUC 0.86 on 135 validation tasks, about 3x the mixed groups per update), but a plain pass-rate ranking does just as well and task-content features alone do better (0.95). Across 11 VeriBench systems the IRT factor models add nothing over a simple additive baseline for held-out strict pass@1, and the smooth SCSC is a worse forecaster of held-out harsh and gold-test pass@1 than the raw rates, so for guiding RL toward the harsh metric the useful signal is prompt selection, not the factor decomposition."

**TLDR-end:** [rl4cv: expt19 interpretable IRT for SCSC factors, explain/predict + guide strict pass@1] Experiment 19's IRT forecast picks experiment 13's learnable prompts (AUC 0.862, above the 0.70 gate) but no better than the panel pass rate, and task features alone do best (0.954). IRT factor models add nothing over a simple baseline for held-out strict pass@1 (+0.0015 [−0.0059, +0.0086]), and the smooth score forecasts held-out harsh and gold-check pass@1 worse than the raw rates.
