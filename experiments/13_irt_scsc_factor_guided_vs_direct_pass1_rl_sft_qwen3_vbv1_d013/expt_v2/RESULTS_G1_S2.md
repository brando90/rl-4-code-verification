# Experiment 13 v2-S2: historical G1 result under A6

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_G1_S2.md>

**TLDR:** **G1 INCONCLUSIVE; arm C remains disabled.** The single historical-ladder run completed normally under the A6 execution freeze at `7a447c8`. Both holdout schemes lack an admitted inner-selected candidate. No fit, forecast or gate is retried.

The original G1-A3 method, 27 implementation bindings, six input bindings, five fixed initializations, risk-set/missingness controls, sensitivity fits and completion bounds were unchanged. A6 removed only the independent-batch-2 prerequisite. The input grid has 20,520 validation cells across 19 policies and 135 tasks; 204 excluded alias cells remain missing. Each evaluation scheme predicts the same 3,240 full-schedule cells (three policies × 135 tasks × eight samples), retaining 58 excluded outcomes in the denominator.

Five grouped-task outer folds and the full-schedule-policy holdout all report `no admitted inner candidate`; the selected forecast is unavailable. Consequently the selected-versus-M0/M1 paired log-loss contrasts are unavailable, not zero, and cannot pass G1. This result independently disables C; the failed train calibration and unavailable H2 already do so. A/B/P remain eligible only after the separate A6 pipeline diagnostic and unchanged later gates.

M0 is the smoothed earlier-rung strict-rate baseline; M1 calibrates the earlier-rung factored reward; M2 is strict two-parameter logistic item response theory; M3 is conditional conjunctive item response theory; M3e adds the frozen task features. Unadmitted candidate outputs below are retained diagnostics, not substitutes for the missing selected forecast.

[Complete machine-readable result](phase1/G1_S2_result.json) retains every statistic and both bootstrap-endpoint ranges. [Control receipts](phase1/G1_S2_controls_summary.json) retain numerical checks, actual-pattern synthetic recovery, component starts and prior sensitivity. Each recovery uses one fixed synthetic replicate, not a population correlation estimate; no recovery confidence interval or hypothesis-test p-value is available.

The following point ranges bound all completions of missing binary labels. The interval column is the outer envelope of the 95% whole-task-group percentile-bootstrap endpoint ranges (100 groups, 10,000 paired draws, seed 1302031), with forecasts held fixed and no refits. Association endpoints use conservative repeated-cell relaxations; policy-correlation envelopes are the full [-1,1] range and are intentionally uninformative. Correlations across only three policies are descriptive and unstable. **p-val=n/a** throughout: prespecified admission comparisons and descriptive metrics, no hypothesis test. Mean bias is predicted minus observed; both means and absolute error are reported alongside association.

## full_schedule_policies

Verdict: **INCONCLUSIVE**; implementation admitted: False; missing required forecast: selected. Declared 3,240, excluded 58.

| Model | Statistic | Point completion range | 95% bootstrap outer envelope |
|---|---|---:|---:|
| M0 | log_loss | [0.22982665, 0.25945112] | [0.18380761, 0.30881572] |
| M0 | auc | [0.83154513, 0.87421144] | [0.77001178, 0.91994118] |
| M0 | pearson | [0.46894837, 0.53691298] | [0.39362144, 0.58803215] |
| M0 | spearman | [0.43255206, 0.50148519] | [0.32533015, 0.56754328] |
| M0 | kendall | [0.41141013, 0.47697401] | [0.31144208, 0.53972382] |
| M0 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M0 | predicted_mean | [0.14453361, 0.14453361] | [0.12858656, 0.16095219] |
| M0 | mean_bias | [0.047311385, 0.06521262] | [0.02623229, 0.083750026] |
| M0 | mean_absolute_error | [0.16923182, 0.18063957] | [0.1441628, 0.20681865] |
| M0 | brier | [0.058492436, 0.069900187] | [0.040299879, 0.08949037] |
| M0 | policy_pearson | [0.14367619, 0.81389522] | [-1, 1] |
| M0 | policy_spearman | [-0.5, 0.5] | [-1, 1] |
| M0 | policy_kendall | [-0.33333333, 0.33333333] | [-1, 1] |
| M1 | log_loss | [0.17250363, 0.22162224] | [0.11927254, 0.28118509] |
| M1 | auc | [0.86584454, 0.92890434] | [0.81008427, 0.95295641] |
| M1 | pearson | [0.48922554, 0.55261195] | [0.39757853, 0.60869212] |
| M1 | spearman | [0.36389921, 0.42396969] | [0.26910398, 0.47614677] |
| M1 | kendall | [0.31363893, 0.36541272] | [0.23317878, 0.40923456] |
| M1 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M1 | predicted_mean | [0.085912591, 0.085912591] | [0.063873934, 0.10882223] |
| M1 | mean_bias | [-0.011309631, 0.0065916032] | [-0.028350372, 0.021550209] |
| M1 | mean_absolute_error | [0.11472463, 0.12804039] | [0.082256612, 0.1618317] |
| M1 | brier | [0.052421118, 0.065736883] | [0.033508432, 0.086351315] |
| M1 | policy_pearson | [0.49430546, 0.96962322] | [-1, 1] |
| M1 | policy_spearman | [0.5, 1] | [-1, 1] |
| M1 | policy_kendall | [0.33333333, 1] | [-1, 1] |
| M2 | log_loss | [0.18049907, 0.2546631] | [0.11541395, 0.33072145] |
| M2 | auc | [0.87653692, 0.93609007] | [0.82264629, 0.95787248] |
| M2 | pearson | [0.4851176, 0.55095068] | [0.39373832, 0.61680694] |
| M2 | spearman | [0.37291005, 0.42269781] | [0.2736957, 0.48278905] |
| M2 | kendall | [0.30485545, 0.34555715] | [0.22413571, 0.39511439] |
| M2 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M2 | predicted_mean | [0.044380197, 0.044380197] | [0.029987837, 0.059526371] |
| M2 | mean_bias | [-0.052842025, -0.034940791] | [-0.075227687, -0.015122016] |
| M2 | mean_absolute_error | [0.087062014, 0.1029329] | [0.056988335, 0.13492975] |
| M2 | brier | [0.055002244, 0.070873132] | [0.03376228, 0.094091747] |
| M2 | policy_pearson | [0.57112484, 0.98781455] | [-1, 1] |
| M2 | policy_spearman | [0.5, 1] | [-1, 1] |
| M2 | policy_kendall | [0.33333333, 1] | [-1, 1] |
| M3 | log_loss | [0.16612981, 0.2388703] | [0.10696122, 0.30932944] |
| M3 | auc | [0.87311802, 0.9392498] | [0.81274691, 0.96053004] |
| M3 | pearson | [0.52600907, 0.59956961] | [0.42276871, 0.66736103] |
| M3 | spearman | [0.3701495, 0.42538455] | [0.26781797, 0.48613881] |
| M3 | kendall | [0.30259869, 0.34775356] | [0.21921287, 0.39795592] |
| M3 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M3 | predicted_mean | [0.049812192, 0.049812192] | [0.032796145, 0.067688301] |
| M3 | mean_bias | [-0.04741003, -0.029508796] | [-0.067807826, -0.011588221] |
| M3 | mean_absolute_error | [0.088468603, 0.10384778] | [0.057474851, 0.13658106] |
| M3 | brier | [0.051954202, 0.067333383] | [0.032104198, 0.088977042] |
| M3 | policy_pearson | [0.76272117, 0.99999998] | [-1, 1] |
| M3 | policy_spearman | [0.5, 1] | [-1, 1] |
| M3 | policy_kendall | [0.33333333, 1] | [-1, 1] |
| M3e | log_loss | [0.16214311, 0.24921221] | [0.10370899, 0.32288284] |
| M3e | auc | [0.88369382, 0.94436632] | [0.83228804, 0.96469588] |
| M3e | pearson | [0.52934126, 0.60249421] | [0.42766045, 0.66945749] |
| M3e | spearman | [0.38027013, 0.43046168] | [0.28323034, 0.48923216] |
| M3e | kendall | [0.31087235, 0.35190413] | [0.23186445, 0.40047981] |
| M3e | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M3e | predicted_mean | [0.049300488, 0.049300488] | [0.03164763, 0.06787037] |
| M3e | mean_bias | [-0.047921735, -0.0300205] | [-0.06767546, -0.012675015] |
| M3e | mean_absolute_error | [0.08714605, 0.10246539] | [0.055818997, 0.13545201] |
| M3e | brier | [0.051582232, 0.066901568] | [0.031874741, 0.088366237] |
| M3e | policy_pearson | [0.76978142, 1] | [-1, 1] |
| M3e | policy_spearman | [0.5, 1] | [-1, 1] |
| M3e | policy_kendall | [0.33333333, 1] | [-1, 1] |
| selected | all required statistics | UNAVAILABLE | UNAVAILABLE |

## grouped_tasks

Verdict: **INCONCLUSIVE**; implementation admitted: False; missing required forecast: selected. Declared 3,240, excluded 58.

| Model | Statistic | Point completion range | 95% bootstrap outer envelope |
|---|---|---:|---:|
| M0 | log_loss | [0.3157862, 0.38083473] | [0.19795963, 0.50712978] |
| M0 | auc | [0.31329771, 0.36071685] | [0.22008712, 0.47301693] |
| M0 | pearson | [-0.17351475, -0.1352729] | [-0.25135063, -0.031835606] |
| M0 | spearman | [-0.18772498, -0.14048905] | [-0.28308705, -0.025017866] |
| M0 | kendall | [-0.16850289, -0.12610368] | [-0.25486738, -0.022508986] |
| M0 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M0 | predicted_mean | [0.02735536, 0.02735536] | [0.026782693, 0.027953315] |
| M0 | mean_bias | [-0.069866862, -0.051965628] | [-0.10496574, -0.01928983] |
| M0 | mean_absolute_error | [0.1025713, 0.11954907] | [0.072015208, 0.15236382] |
| M0 | brier | [0.075973191, 0.092950962] | [0.045343507, 0.12600151] |
| M0 | policy_pearson | [undefined, undefined] | [-1, 1] |
| M0 | policy_spearman | [undefined, undefined] | [-1, 1] |
| M0 | policy_kendall | [undefined, undefined] | [-1, 1] |
| M1 | log_loss | [0.17344923, 0.22314501] | [0.1201489, 0.28274703] |
| M1 | auc | [0.8641719, 0.92914969] | [0.80520705, 0.95230773] |
| M1 | pearson | [0.48810073, 0.55295689] | [0.39435488, 0.60895641] |
| M1 | spearman | [0.35848449, 0.41967671] | [0.26131407, 0.47315094] |
| M1 | kendall | [0.29694735, 0.34763537] | [0.2173796, 0.39216864] |
| M1 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M1 | predicted_mean | [0.084901734, 0.084901734] | [0.06289979, 0.10775562] |
| M1 | mean_bias | [-0.012320488, 0.0055807465] | [-0.029097108, 0.020480781] |
| M1 | mean_absolute_error | [0.11423688, 0.12772141] | [0.081979287, 0.16138501] |
| M1 | brier | [0.052483604, 0.065968137] | [0.033533758, 0.086617402] |
| M1 | policy_pearson | [0.49868296, 0.97084442] | [-1, 1] |
| M1 | policy_spearman | [0.5, 1] | [-1, 1] |
| M1 | policy_kendall | [0.33333333, 1] | [-1, 1] |
| M2 | log_loss | [0.84299361, 0.8488587] | [0.82864109, 0.86207252] |
| M2 | auc | [0.53251146, 0.60037536] | [0.47491712, 0.64202697] |
| M2 | pearson | [0.039664221, 0.096155489] | [-0.006224795, 0.13438127] |
| M2 | spearman | [0.032286518, 0.098119115] | [-0.021820363, 0.14306622] |
| M2 | kendall | [0.027273452, 0.082884347] | [-0.01847104, 0.12081431] |
| M2 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M2 | predicted_mean | [0.58003552, 0.58003552] | [0.57973909, 0.58033774] |
| M2 | mean_bias | [0.4828133, 0.50071454] | [0.44800286, 0.53304861] |
| M2 | mean_absolute_error | [0.56190984, 0.56476699] | [0.55492862, 0.57120746] |
| M2 | brier | [0.32276622, 0.32562338] | [0.31576996, 0.33205815] |
| M2 | policy_pearson | [0.7273911, 0.99999972] | [-1, 1] |
| M2 | policy_spearman | [0.5, 1] | [-1, 1] |
| M2 | policy_kendall | [0.33333333, 1] | [-1, 1] |
| M3 | log_loss | [0.30836847, 0.33850025] | [0.25813336, 0.39292043] |
| M3 | auc | [0.51592712, 0.57597546] | [0.46156931, 0.61559104] |
| M3 | pearson | [0.034989968, 0.091644672] | [-0.0098024629, 0.13024123] |
| M3 | spearman | [0.015816922, 0.074267682] | [-0.033428519, 0.11599466] |
| M3 | kendall | [0.013361059, 0.06273628] | [-0.028239647, 0.098200912] |
| M3 | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M3 | predicted_mean | [0.16726746, 0.16726746] | [0.16638245, 0.16811797] |
| M3 | mean_bias | [0.070045235, 0.087946469] | [0.035211757, 0.12034063] |
| M3 | mean_absolute_error | [0.21823863, 0.23030295] | [0.19751792, 0.25270292] |
| M3 | brier | [0.081313627, 0.093377948] | [0.060632193, 0.11575894] |
| M3 | policy_pearson | [0.68305182, 0.99992542] | [-1, 1] |
| M3 | policy_spearman | [0.5, 1] | [-1, 1] |
| M3 | policy_kendall | [0.33333333, 1] | [-1, 1] |
| M3e | log_loss | [0.21710319, 0.2589634] | [0.16427908, 0.31315943] |
| M3e | auc | [0.83967035, 0.89964365] | [0.78469888, 0.93031105] |
| M3e | pearson | [0.37611022, 0.43292541] | [0.28190388, 0.49590995] |
| M3e | spearman | [0.33514454, 0.38877645] | [0.24214438, 0.44465475] |
| M3e | kendall | [0.27398199, 0.3178263] | [0.19822279, 0.36391176] |
| M3e | observed_mean | [0.079320988, 0.097222222] | [0.04703182, 0.13204225] |
| M3e | predicted_mean | [0.12522289, 0.12522289] | [0.10192911, 0.14704754] |
| M3e | mean_bias | [0.028000666, 0.045901901] | [0.0049736492, 0.068591938] |
| M3e | mean_absolute_error | [0.15876686, 0.17068267] | [0.1245259, 0.20390141] |
| M3e | brier | [0.062714909, 0.074630722] | [0.043518707, 0.094653437] |
| M3e | policy_pearson | [0.68566242, 0.99996274] | [-1, 1] |
| M3e | policy_spearman | [0.5, 1] | [-1, 1] |
| M3e | policy_kendall | [0.33333333, 1] | [-1, 1] |
| selected | all required statistics | UNAVAILABLE | UNAVAILABLE |

## Why selection was unavailable

Across the 24 outer/inner fitting scopes, numerical gradient/invariance controls pass, while Q3 (honesty conditional on compilation) synthetic recovery fails in all 24: 22 exceed the frozen probability-error limit and two have disconnected risk sets. The thresholds are mean absolute probability error ≤0.08 and ability correlation ≥0.80. The ranges below span fixed-pattern recovery controls; they are **not confidence intervals** or independent repeated experimental runs. Each recovery uses seed 1302041 and five fixed initializations.

| Recovery pattern | Pass / scopes | Reported fits / scopes | Ability-correlation range | Probability mean absolute error range |
|---|---:|---:|---:|---:|
| M2 | 24/24 | 24/24 | [0.99387375, 0.9988457] | [0.036894617, 0.045387871] |
| Q1 | 24/24 | 24/24 | [0.99387375, 0.9988457] | [0.036894617, 0.045387871] |
| Q2 | 24/24 | 24/24 | [0.9525393, 0.99772417] | [0.05028312, 0.072134451] |
| Q3 | 0/24 | 22/24 | [0.42493396, 0.94348698] | [0.11046611, 0.20763296] |

Q1 is well-formed output; Q2 is compilation conditional on well-formed output. No candidate was substituted after these controls failed. The original gate verdict is INCONCLUSIVE because the selected required forecast is unavailable.

## Execution and transition

Normal process exit 0; 940.84 user + 0.60 system seconds = 0.2615111111111111 processor-hours; elapsed 941.64 seconds, peak resident memory 257,480 KiB. Zero device-hours and zero model calls. Raw forecasts, fit receipts and timing remain privately hash-bound. A6 execution began only after the published prerequisite freeze.

G1 is final INCONCLUSIVE. H2 and F2 are UNAVAILABLE under A6. No independent batch 2 was generated. Phase 2 currently cannot start because the A6 diagnostic launcher failed before producing any response; see [the infrastructure report](RESULTS_A6_DIAGNOSTIC_S2.md).
