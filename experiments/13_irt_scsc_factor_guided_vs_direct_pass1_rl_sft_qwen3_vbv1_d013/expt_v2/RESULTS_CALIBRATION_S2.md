# Experiment 13 v2-S2 train calibration result

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_CALIBRATION_S2.md>

**TLDR:** The one calibration run completed, but arm C is not admitted. All partial fits, failures, item artifacts, the placebo distribution and F2 = 0.75 are frozen before independent batch 2. A/B/P continue under the published transition rules.

Updated: 10-15-2026 07:09 PDT. Experiment `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`: three frozen train policies, 539 tasks, eight responses per task; 12,916/12,936 observed and 20 missing. Missing cells remain unobserved. This is in-sample calibration, not held-out efficacy.

## Chronology and disposition

Method freeze `f8f16be` and [input freeze](locks/CALIBRATION_S2_INPUTS.json) at `cc0dc01a30069ce1542a070061db41184186e14d` precede the only run. [Final artifact lock](locks/CALIBRATION_S2.json) binds the raw result and 29 artifacts; [aggregate summary](phase1/calibration_S2_summary.json) exposes counts and diagnostics without task IDs. The process exited 0, with no retry. `FROZEN` describes immutable artifacts, not scientific admission.

The fixed conditional strict forecast is unavailable, so its batch-2 predictions remain null; no replacement is chosen. The forecast F2 (mixed-strict-group area under the receiver operating characteristic curve, AUC, prediction 0.75; admission threshold 0.70) remains recorded prospectively and will be reported unavailable if it cannot be evaluated. PLAN section 5 still orders independent batch 2 and final G1/H2. PROTOCOL section 4 explicitly freezes the empirical placebo distribution of B rewards even if C fails: 4,302/4,312 full1 outputs are measured, ten remain missing. No uniform or substitute C weights are introduced.

## Marginal models and admission

The three components are d, the error-free command fraction; t, implementation and examples elaborate with at least one example; and p, proved-theorem fraction. Models retain the original counts, missingness and five fixed initializations.

| Component | Total denominator | Outputs with zero denominator / 12,936 | Empty items / 539 | Result |
|---|---:|---:|---:|---|
| d | 97,557 | 10,689 | 3 | Not admitted: empty/disconnected denominator pattern; all three prior fits rejected |
| p | 15,868 | 11,415 | 45 | Not admitted: empty/disconnected denominator pattern; all three prior fits rejected |
| t | 12,916 | 20 | 0 | Not admitted: 15/15 prior/start fits finite and converged; pooled calibration bias excludes zero |

The variance check is **INCONCLUSIVE** because marginal models are unavailable; it does not fabricate weights or a variance statistic. The fixed threshold is nonzero reward variance on at least 0.15 of eligible constant-strict train groups.

## Existing calibration estimates and uncertainty

Point estimates and 95% intervals below are copied from the single completed fit and its existing 10,000-draw, seed-1302031 bootstrap over 400 whole train task groups, paired across policies and responses. Intervals condition on fitted predictions; they do not include refitting or repeated-training uncertainty. Bias is predicted minus observed. All metrics are on the 0–1 scale; p-value is not applicable (descriptive calibration, no hypothesis test). Q1 is the first conditional hurdle: extraction plus example/theorem presence and syntactic non-vacuity.

| Model / policy | Measured outputs | Observed mean [95% interval] | Predicted mean [95% interval] | Bias [95% interval] | Absolute error [95% interval] |
|---|---:|---|---|---|---|
| t / base | 4,311 | 0.00417537 [0.00228938, 0.00633361] | 0.00175418 [0.00150781, 0.00203473] | -0.00242118 [-0.00431491, -0.00075066] | 0.00577396 [0.00372667, 0.00810207] |
| t / half | 4,303 | 0.00139438 [0.00045935, 0.00256294] | 0.03354024 [0.03220382, 0.03502593] | 0.03214587 [0.03085003, 0.03359527] | 0.03465553 [0.03280670, 0.03668787] |
| t / full1 | 4,302 | 0.00092980 [0.00022847, 0.00188947] | 0.03292794 [0.03159781, 0.03441081] | 0.03199814 [0.03065230, 0.03340103] | 0.03366374 [0.03201896, 0.03553099] |
| t / pooled | 12,916 | 0.00216785 [0.00134090, 0.00308839] | 0.02272700 [0.02175767, 0.02380140] | 0.02055915 [0.02038521, 0.02075259] | 0.02468533 [0.02297584, 0.02658454] |
| Q1 / base | 4,311 | 0.09580144 [0.08708620, 0.10484431] | 0.14621693 [0.13823527, 0.15420463] | 0.05041549 [0.04187145, 0.05893960] | 0.20465663 [0.19413138, 0.21541045] |
| Q1 / half | 4,303 | 0.07622589 [0.06802713, 0.08444683] | 0.02865198 [0.02614101, 0.03118696] | -0.04757391 [-0.05381674, -0.04139855] | 0.09574133 [0.08662661, 0.10498383] |
| Q1 / full1 | 4,302 | 0.12854486 [0.11531407, 0.14223470] | 0.19241666 [0.18296929, 0.20193396] | 0.06387179 [0.05562105, 0.07188828] | 0.24541785 [0.23258846, 0.25838610] |
| Q1 / pooled | 12,916 | 0.10018582 [0.09358705, 0.10686850] | 0.12243784 [0.11588293, 0.12898835] | 0.02225202 [0.02167563, 0.02282815] | 0.18194776 [0.17272415, 0.19117487] |

The frozen admission requires the pooled bias interval to contain zero. It does not for either fitted t or Q1. No tolerance was changed after observation.

## Numerical, recovery and conditional-model controls

Marginal finite-gradient checks pass: maximum absolute finite-difference discrepancy 1.1097721852593168e-08 versus 1e-05 tolerance. Probability invariance error is 2.220446049250313e-16 versus 1e-12; likelihood invariance error is 0 versus 1e-09. Conditional numerical controls also pass.

Synthetic recovery uses one fixed replicate on each real missingness/risk-set pattern, seed 1302041, requiring ability correlation at least 0.80 and probability mean absolute error at most 0.08, plus finite converged starts and prediction spread at most 0.02. These are fixed control point statistics, with no newly estimated interval or p-value; only three policy abilities enter each correlation.

| Pattern | Trials | Recovery correlation | Probability absolute error | Result |
|---|---:|---:|---:|---|
| t | 12,916 | 0.9999962118293151 | 0.07521484742985748 | PASS |
| M2 | 12,916 | 0.9999962118293151 | 0.07521484742985748 | PASS |
| Q1 | 12,916 | 0.9999962118293151 | 0.07521484742985748 | PASS |
| Q2 | 1,294 | 0.9973962137777642 | 0.15520523431814515 | FAIL |
| Q3 | 0 | unavailable | unavailable | FAIL |

Q2 is whole-file compilation conditional on Q1; Q3 is kernel honesty of all named theorems conditional on Q1 and Q2. Q2 recovery fails its absolute-error threshold; Q3 has no risk-set trials. The observed M2 strict outcome is constant zero on all 539 items. Q2 has 461 active items, all constant zero; Q3 has zero active items and all three policies empty. All three prior scales retain these identification failures. Q1 fits converge but fail calibration, so the conditional conjunction is unavailable. Declaration- and theorem-fraction recovery fail their empty-item condition. Exact starts, objective values, finite-gradient receipts, sensitivities and ten-bin calibration diagnostics remain bound in the artifact lock.

## Cost and next action

Processor usage was 0.0007972222222222223 hours (user 2.47 s + system 0.4 s), elapsed 2.9 s, zero device-hours and zero model calls. Retained calibration files: 32, 639121 logical bytes and 733184 allocated bytes.

Required publication suite: **1,010 passed, 3 skipped**, direct exit 0, 464.97 seconds. Five new authored coverage-publication checks and all 28 focused checks pass. No independent batch-2 outcome, held-out test measurement or experiment optimizer update has run. Freeze the independent routes after this publication, then use the existing leased device poller.
