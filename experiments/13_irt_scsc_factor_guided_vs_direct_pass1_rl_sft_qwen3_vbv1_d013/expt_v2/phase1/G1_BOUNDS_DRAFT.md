# Experiment 13 version 2 G1 completion bounds: prospective implementation draft

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/G1_BOUNDS_DRAFT.md>

**TLDR:** For `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`, Amendment A3 requires missing historical cells to stay missing in fitting and bounds on held-out outcomes with forecasts fixed. This is a draft, not an admission lock. No Phase 1 fit has run. Publish the completed implementation, tests and hash lock before any fit.

## Fitting and chronology

Import the frozen two-parameter logistic and conditional-hurdle item response theory implementations from `prediction/`. Preserve their five initialization seeds, gradients, priors, discrimination bounds, ability scale, prior-sensitivity fits and train-only feature standardization. Do not modify those frozen files.

The complete-case requirement in frozen `nested_forecast_v2.py` cannot implement A3 directly. A separate wrapper must construct the same declared policy/task/sample grid, mark exactly the 217 listed cells missing before reading their measurements, and pass `observed=False` into the frozen fitting functions. An unlisted missing cell remains an integrity/completeness failure. No test row is permitted. Do not substitute zero labels for missing observations.

Earlier-rung baseline counts use measured successes and measured denominators. Earlier-rung reward averages and calibration transitions use available measured observations; a transition missing its entire earlier predictor or later target is unavailable. No target completion may enter this calculation or inner selection. If a required predictor or calibration cannot be constructed, record the unsupported forecast and disable arm C rather than impute from held-out outcomes. The wrapper must document these counts per fold.

Synthetic recovery uses the actual admitted earlier-rung risk-count and missingness arrays, with the frozen seed and criteria. It is not evidence about later outcomes. Retain all identification failures, prior-sensitive estimates, likelihood-invariance and finite-gradient checks. Five-start disagreement must remain at most 0.02 on the frozen diagnostic grid; recovery criteria stay those in L1v2. These controls precede interpretation of fitted forecasts.

For each required outer scheme, freeze each cell's predictions from the training-selected candidate, M0, M1 and M2 before completing held-out labels. Never select between M3 and M3e on a completion, and never refit for a completion. Keep all declared held-out cells and policy/task groups. Each excluded held-out strict outcome ranges independently over {0,1}. This is fixed-forecast uncertainty; fitting uncertainty is not resampled.

## Gate statistics

`g1_bounds.py` currently implements the following components with exhaustive synthetic comparisons:

1. **Linear-in-label metrics.** Log loss, candidate-minus-baseline log-loss contrasts, mean bias, absolute error, Brier score and observed/predicted means are means of `a_i*y_i+b_i`, with coefficients fixed by predictions. An excluded label minimizing its contribution is 0 for nonnegative `a_i` and 1 otherwise; maximizing reverses that choice. Both are feasible completions.
2. **Paired group bootstrap.** Use the frozen evaluator's sorted groups, seed 1302031, 10,000 draws and linear quantiles. Every draw is a nonnegative weighted mean. Therefore the same two completions minimize/maximize every draw, and also each percentile endpoint. This supplies exact ranges for the upper 95% confidence-interval endpoint of both log-loss contrasts and both endpoints of the calibration-bias interval. Confidence intervals condition on fixed forecasts; the ranges across completions are not confidence intervals for missingness.
3. **Policy Pearson correlation.** Fixed predicted policy means and each policy's known successes reduce the search to integer totals of successful excluded outcomes per policy. Enumerate their Cartesian product when at most 2^20 states. Record undefined constant-outcome completions. If the search exceeds that limit, the valid outer range [-1,1] cannot certify the correlation gate; mark the result INCONCLUSIVE unless another criterion already establishes FAIL.

PASS requires every completion to satisfy both paired log-loss upper endpoints <0, policy Pearson correlation ≥0.80 with no undefined completion, and calibration-bias intervals containing zero, for both required outer schemes, plus all frozen implementation controls. A criterion failing for every completion establishes FAIL; otherwise the result is INCONCLUSIVE. Either non-PASS disables only arm C under the admission record. Never classify a mixed-completion outcome as a scientific failure of every completion.

## Remaining implementation before locking

The source-bound loader now propagates canonical exclusions to every ladder alias before inspecting measurements, rejects unlisted missingness/inequality and sealed rows, and retains the complete declared grid. Train/validation local features have been prepared from 1,348 hash-verified source files (539/135 tasks), with zero test sources opened and zero fits. Source-family categories are one-hot encoded only within the training fold.

The forecast wrapper now records every inner and outer fit receipt and observation count, and exposes a durable forecast sink before evaluating completion bounds. A separate A3 wrapper imports frozen model fitting routines while allowing an unavailable M1 reward predictor to remain missing without suppressing M2. The bounds evaluator reports available M2 diagnostics even when the selected candidate is unavailable.

Before actual fitting, finish the execution driver with publication/prerequisite checks and exclusive fit attempts, freeze final input/configuration/implementation hashes in `locks/G1_A3.json`, run the required integration suite, and publish. The current draft remains non-executable; no actual-data recovery or model fit is authorized by it.

## Implementation progress, 10-14-2026

`nested_a3.py` preserves the frozen nested holdouts and model implementations, masks every listed excluded outcome/factor, uses observed earlier-rung counts and rewards, omits missing inner targets, and never fits a full-schedule target. `fit_controls.py` sends the actual observed strict and three conditional risk-count matrices to the frozen synthetic recovery implementation before admitting each fold. Five initializations, finite gradients, location/scale invariance and chain consistency remain required. Actual data have not been fitted.

`g1_bounds.py` now provides exact point bounds for binary-label area under the curve and cell Pearson/Spearman/Kendall associations by enumerating missing-positive totals and extremal ordered score sums. Bootstrap endpoint bounds relax repeated copies only outward; when completion changes the defined-draw set, the full metric range is reported. Policy correlations use exact integer-count enumeration up to the existing 2^20 limit; their bootstrap endpoints conservatively use [-1,1]. Calibration-bin observed means receive full-denominator bounds. These outer intervals are disclosed and cannot replace the exact gate statistics.

Before execution, the final lock must bind these files, the exclusion manifest, frozen prediction dependencies, input manifests, tests and configuration. This document is still a draft and does not authorize an actual fit.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] The draft gives exact fixed-forecast bounds for linear metrics, paired bootstrap endpoints and finite policy-correlation searches; the missing-data wrapper and diagnostic bounds are implemented, while the final input-bound lock remains before actual fitting.
**Snapshot:** actual Phase 1 fits 0; target-completion refits forbidden; paired draws 10,000; policy-correlation search cap 2^20; G1 draft lock prepared; actual fitting remains unattempted.
