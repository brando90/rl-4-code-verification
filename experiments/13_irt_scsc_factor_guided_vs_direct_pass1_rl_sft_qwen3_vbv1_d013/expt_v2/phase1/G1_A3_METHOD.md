# Experiment 13 version 2: frozen G1 method under A3

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/G1_A3_METHOD.md>

**TLDR:** This freezes the executable historical G1 forecast and completion-bound method before any actual-data fit. It does not permit fitting until the method is published and Phase 1's prerequisites are met. G0 remains PASS; no G1 fit or statistic has run.

## Inputs and missingness

The source-bound loader verifies all inputs before parsing ordinary train/validation receipts. It preserves the complete 19-policy × 135-validation-task × 8-sample ladder grid, propagates each canonical excluded cell to every ladder alias, and leaves its outcomes and factors missing. Exactly the adopted 217-cell manifest is accepted. An unlisted missing cell, inequality, changed source or test row is an integrity error. Excluded measurement fields are never inspected by the loader.

Train/validation source features were prepared from 1,348 source files without opening test content. The historical forecast uses only the 135 validation feature records. Categories and standardization are learned within each training fold; held-out item residuals and target-policy ability are never fitted from target outcomes. Frozen source-family grouping, policy metadata, prior distributions and implementations are bound in `locks/G1_A3.json`.

## Fits and forecasts

Import the original frozen two-parameter logistic and conditional-hurdle implementations. Preserve all five initialization seeds, discrimination bounds, ability scale, priors, sensitivity fits and convergence criteria. Before interpreting each fold, synthetic recovery uses that fold's actual observed trial and conditional risk-count arrays, including zero cells, with the frozen seed and criteria. Finite gradients, location/scale likelihood invariance, chain consistency and at-most-0.02 five-start prediction disagreement remain required.

Earlier-rung baseline counts use measured successes and measured denominators. Reward predictors average observed earlier-rung factors; unavailable predictors remain unavailable. Missing inner targets are omitted from tuning with their counts reported. No held-out completion enters fitting or candidate selection. Failure of a required baseline or selected model disables arm C; available M2 diagnostics remain reported. Every inner and outer fit/control receipt and its observation counts is retained.

For both grouped-task and full-schedule-policy holdouts, select M3 versus M3e only within the frozen inner folds. Persist the complete same-cell predictions for that selection, M0, M1 and M2 before evaluating held-out completion bounds. No completion triggers a refit or reselection. The exclusive fit attempt record prevents rerunning a partial forecast.

## Bounds and G1 decision

Every excluded held-out strict label independently ranges over {0,1}. Linear-in-label means and paired group-bootstrap endpoints have exact extrema using the sign of each fixed coefficient. The bootstrap retains 10,000 draws, seed 1302031, the sorted frozen task groups and linear quantiles. These intervals condition on fixed forecasts; ranges over missing labels are not uncertainty intervals for missingness.

Enumerate policy-success totals for exact policy Pearson extrema up to 2^20 states, retaining every undefined constant-outcome completion. Above that limit, [-1,1] is an explicit outer bound that cannot certify PASS or FAIL by itself. Point area-under-curve and cell association bounds enumerate missing-positive totals with extremal fixed score/rank sums. Diagnostic bootstrap intervals use disclosed conservative outer ranges where exact joint completions cannot be certified; these do not substitute for exact admission statistics. Calibration bins preserve every declared cell.

PASS requires, for every completion and both holdout schemes: candidate-minus-M0 and candidate-minus-M1 log-loss upper 95% endpoints below zero; policy Pearson correlation at least 0.80 with no undefined completion; calibration-bias intervals containing zero; and all frozen implementation controls. A criterion failing for every completion establishes FAIL. Otherwise report INCONCLUSIVE. Both non-PASS outcomes disable arm C only, retaining the eligible A/B/P comparison under PLAN; G1 alone cannot enable C without H2 and the variance check.

## Execution chronology

The driver checks the published lock bytes, every implementation/input hash and the exact L1v2 numerical-library versions before reading measurements or fitting. Calibration code must call the same `verify_fit_lock` before its first actual fit and record the method-lock digest in its frozen result.

G1 execution additionally requires published LP-1 PASS with admission statistics computed, frozen calibration/items/F2 naming this method lock, and independently generated batch 2 with all 4,312 slots accounted and the calibration digest recorded. Missing H2 cells stay missing and can disable C; they do not suppress the independent historical G1 report. A prerequisite manifest supplies the published revision and digest of each receipt. Hash/chronology failures precede the fit ledger. Once a fit attempt starts, its forecasts, errors and result are retained; no scientific retry is admitted.

**TLDR-end:** [rl4cv: Experiment 13 v2] The final G1 method freezes fitting, missingness, fixed-forecast bounds and execution chronology before any actual fit.
**Snapshot:** Actual fits 0; historical grid 20,520 cells; original exclusions 217; initialization seeds 5; bootstrap draws 10,000; completion refits 0.
