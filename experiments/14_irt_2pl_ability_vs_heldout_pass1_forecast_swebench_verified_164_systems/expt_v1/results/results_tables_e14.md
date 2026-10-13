# Experiment 14 result tables (rendered from `analysis_e14.json`)

Status: **PRIMARY ANALYSES COMPUTED**. Q1 verdict: **CONTINUE: 2PL forecasts held-out pass@1 better than pass@1 on half A (rank and level rule holds); the level gain also exceeds the non-IRT linear-regression forecast from the same reference systems**.

Level-win attribution (frozen interpretation rule): the K-fold 2PL level gain **exceeds** the non-IRT linear-regression forecast from the same reference systems, so it reflects item-level IRT information.

Intervals resample whole systems (164, or 73 in the sensitivity analysis) with the fitted item parameters, fold assignments, control fits and task splits held fixed; they are not intervals for a refitted procedure, unseen tasks or new model families. Split percentiles describe the 2,000 random halves and are not population intervals.

## Validity

| Check | Value |
|---|---|
| systems | 164 |
| tasks | 424 |
| cells | 69536 |
| inconsistent_cells | 1 |
| cells_by_graded_category | {"0": 23952, "1": 5675, "2": 39909} |
| per_cell_sha256 | f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d |
| analysis_e07_sha256 | 16d551328ab9aedaad399f50fd4d59cf12759e0b377c8040d063dd5ef2c5b3f5 |
| forecast_sha256 | 33de7cd2268f60ed4d4d828d6eec7f5c5b79a9ce457cc8da881f5d54dc706890 |
| e07_h2_reproduction | {"e07_code_on_replayed_stream_equals_published_h2": true, "replayed_permutations_reproduce_published_medians_and_counts": true, "replayed": {"25": {"delta_median": -0.009360066473104778, "positive_splits": 391}, "50": {"delta_median": -0.012138953190928725, "positive_splits": 92}, "100": {"delta_median": -0.012941050463773973, "positive_splits": 7}, "250": {"delta_median": -0.012669847666142708, "positive_splits": 0}}} |
| all_primary_fits_converged | true |

## Primary (2PL versus pass@1 on half A, n_A = 50, 2000 splits, 164 systems)

Rank arm `2pl_within_A` (2PL refitted on half A of every system, no half-B data); level arm `2pl` (2PL item parameters from the other folds' systems, all tasks).

- Rank rule (median Δ > 0 and share(Δ > 0) ≥ 0.60 over 2,000 splits at n_A = 50 (experiment 07's frozen H2 rule)): **holds** (failed within-half fits: 0; decision with failed splits at worst/best: [True, True]). Median Δ +0.0040 [+0.0016, +0.0066] p-val=0.0010 (system-cluster bootstrap); split 5th–95th [-0.0030, +0.0166]; Δ > 0 in 1623/2000 splits = 0.811 [0.600, 0.839] p-val=0.0520 (bootstrap, null share 0.60); median Spearman 0.9574 versus 0.9532 for pass@1 on A.
- Level rule (mean per-system absolute error lower than pass@1 on A, 95% system-bootstrap interval of the difference excluding 0): **holds** (numerical gates valid: True). Mean absolute error 0.0554 (pass@1 on A) versus 0.0344 (2PL); difference +0.0210 [+0.0195, +0.0224] p-val=0.0010 (system-cluster percentile bootstrap over systems (2000 draws) for the CI and the p-value (null: zero mean difference; p = twice the smaller tail count, +1 corrected); sign-flip diagnostic (10000 flips) assumes per-system differences symmetric about 0); 2PL closer for 159/164 systems and lower in 1972/2000 splits.
- Mean bias (forecast minus held-out pass@1): pass@1 on A +0.0001, 2PL -0.0007; mean forecast 0.5732 versus mean held-out pass@1 0.5739.

Key secondary (graded response model on resolved plus partial credit): rank rule **holds** (median Δ +0.0051 [+0.0020, +0.0080], share 0.838); level rule **holds** (difference +0.0218 [+0.0205, +0.0231] p-val=0.0010).

Numerical gates (tolerances: gradient 1e-4 on both grids, endpoint mass 1e-8, rescoring change 1e-6):

| n_A | Fits | Status | Max check-grid gradient | Max endpoint mass | Max rescoring change |
|---:|---|---|---:|---:|---:|
| 25 | within-half 2pl | 0/2000 failed | 0.0000002 | 5.9e-30 | 6.0e-14 |
| 25 | within-half grm3 | 0/2000 failed | 0.0000005 | 1.2e-29 | 4.2e-14 |
| 25 | K-fold 1pl | 0 endpoint violations | — | 4.4e-30 | — |
| 25 | K-fold 2pl | 0 endpoint violations | — | 4.2e-28 | — |
| 25 | K-fold grm3 | 0 endpoint violations | — | 6.3e-28 | — |
| 50 | within-half 2pl | 0/2000 failed | 0.0000003 | 2.7e-29 | 1.4e-13 |
| 50 | within-half grm3 | 0/2000 failed | 0.0000007 | 2.8e-28 | 7.9e-14 |
| 50 | K-fold 1pl | 0 endpoint violations | — | 2.4e-29 | — |
| 50 | K-fold 2pl | 0 endpoint violations | — | 9.8e-27 | — |
| 50 | K-fold grm3 | 0 endpoint violations | — | 3.8e-27 | — |
| 100 | within-half 2pl | 0/2000 failed | 0.0000005 | 1.3e-33 | 3.1e-13 |
| 100 | within-half grm3 | 0/2000 failed | 0.0000011 | 9.1e-36 | 1.9e-13 |
| 100 | K-fold 1pl | 0 endpoint violations | — | 2.4e-35 | — |
| 100 | K-fold 2pl | 0 endpoint violations | — | 1.4e-31 | — |
| 100 | K-fold grm3 | 0 endpoint violations | — | 5.0e-34 | — |
| 250 | within-half 2pl | 0/2000 failed | 0.0000010 | 1.3e-61 | 1.1e-12 |
| 250 | within-half grm3 | 0/2000 failed | 0.0000018 | 1.0e-77 | 5.5e-13 |
| 250 | K-fold 1pl | 0 endpoint violations | — | 2.1e-107 | — |
| 250 | K-fold 2pl | 0 endpoint violations | — | 6.8e-63 | — |
| 250 | K-fold grm3 | 0 endpoint violations | — | 1.2e-79 | — |
| 50 | K-fold 1pl rescoring (20 splits) | ok=True | — | — | 1.0e-13 |
| 50 | K-fold 2pl rescoring (20 splits) | ok=True | — | — | 9.4e-14 |
| 50 | K-fold grm3 rescoring (20 splits) | ok=True | — | — | 7.7e-14 |

## Rank: Δ = Spearman(arm forecast, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B)

| n_A | Arm | Median Δ | 5th–95th | Splits Δ > 0 | Share | Exact-zero splits | Median Spearman (arm) | Median Spearman (pass@1 on A) |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 25 | rasch_common_check | +0.0000 | [+0.0000, +0.0000] | 0/2000 | 0.000 | 2000 | 0.9202 | 0.9202 |
| 25 | 2pl_within_A | +0.0071 | [-0.0046, +0.0346] | 1649/2000 | 0.825 | 0 | 0.9284 | 0.9202 |
| 25 | grm3_within_A | +0.0102 | [-0.0030, +0.0403] | 1773/2000 | 0.886 | 0 | 0.9317 | 0.9202 |
| 25 | 1pl | -0.0094 | [-0.0171, -0.0050] | 0/2000 | 0.000 | 0 | 0.9105 | 0.9202 |
| 25 | 2pl | +0.0064 | [-0.0050, +0.0355] | 1584/2000 | 0.792 | 0 | 0.9282 | 0.9202 |
| 25 | grm3 | +0.0097 | [-0.0038, +0.0415] | 1745/2000 | 0.873 | 0 | 0.9315 | 0.9202 |
| 25 | mean_equating | -0.0084 | [-0.0163, -0.0038] | 1/2000 | 0.001 | 0 | 0.9118 | 0.9202 |
| 25 | linear_regression | -0.0100 | [-0.0178, -0.0053] | 0/2000 | 0.000 | 0 | 0.9101 | 0.9202 |
| 50 | rasch_common_check | +0.0000 | [+0.0000, +0.0000] | 0/2000 | 0.000 | 2000 | 0.9532 | 0.9532 |
| 50 | 2pl_within_A | +0.0040 | [-0.0030, +0.0166] | 1623/2000 | 0.811 | 0 | 0.9574 | 0.9532 |
| 50 | grm3_within_A | +0.0051 | [-0.0027, +0.0184] | 1676/2000 | 0.838 | 0 | 0.9584 | 0.9532 |
| 50 | 1pl | -0.0036 | [-0.0060, -0.0018] | 1/2000 | 0.001 | 0 | 0.9494 | 0.9532 |
| 50 | 2pl | +0.0036 | [-0.0032, +0.0171] | 1587/2000 | 0.793 | 0 | 0.9571 | 0.9532 |
| 50 | grm3 | +0.0048 | [-0.0029, +0.0184] | 1641/2000 | 0.821 | 0 | 0.9581 | 0.9532 |
| 50 | mean_equating | -0.0032 | [-0.0056, -0.0013] | 3/2000 | 0.002 | 0 | 0.9499 | 0.9532 |
| 50 | linear_regression | -0.0039 | [-0.0064, -0.0020] | 0/2000 | 0.000 | 0 | 0.9492 | 0.9532 |
| 100 | rasch_common_check | +0.0000 | [+0.0000, +0.0000] | 0/2000 | 0.000 | 2000 | 0.9708 | 0.9708 |
| 100 | 2pl_within_A | +0.0012 | [-0.0032, +0.0078] | 1304/2000 | 0.652 | 0 | 0.9720 | 0.9708 |
| 100 | grm3_within_A | +0.0009 | [-0.0040, +0.0080] | 1240/2000 | 0.620 | 0 | 0.9720 | 0.9708 |
| 100 | 1pl | -0.0015 | [-0.0025, -0.0006] | 3/2000 | 0.002 | 0 | 0.9693 | 0.9708 |
| 100 | 2pl | +0.0009 | [-0.0034, +0.0076] | 1233/2000 | 0.617 | 0 | 0.9719 | 0.9708 |
| 100 | grm3 | +0.0006 | [-0.0040, +0.0075] | 1154/2000 | 0.577 | 0 | 0.9716 | 0.9708 |
| 100 | mean_equating | -0.0013 | [-0.0022, -0.0004] | 14/2000 | 0.007 | 0 | 0.9695 | 0.9708 |
| 100 | linear_regression | -0.0016 | [-0.0026, -0.0007] | 1/2000 | 0.001 | 0 | 0.9692 | 0.9708 |
| 250 | rasch_common_check | +0.0000 | [+0.0000, +0.0000] | 0/2000 | 0.000 | 2000 | 0.9772 | 0.9772 |
| 250 | 2pl_within_A | -0.0005 | [-0.0045, +0.0036] | 833/2000 | 0.416 | 0 | 0.9769 | 0.9772 |
| 250 | grm3_within_A | -0.0014 | [-0.0057, +0.0032] | 581/2000 | 0.290 | 0 | 0.9760 | 0.9772 |
| 250 | 1pl | -0.0005 | [-0.0010, -0.0001] | 30/2000 | 0.015 | 0 | 0.9767 | 0.9772 |
| 250 | 2pl | -0.0008 | [-0.0047, +0.0032] | 741/2000 | 0.370 | 0 | 0.9766 | 0.9772 |
| 250 | grm3 | -0.0016 | [-0.0058, +0.0028] | 483/2000 | 0.241 | 0 | 0.9757 | 0.9772 |
| 250 | mean_equating | -0.0004 | [-0.0009, -0.0000] | 78/2000 | 0.039 | 0 | 0.9768 | 0.9772 |
| 250 | linear_regression | -0.0006 | [-0.0011, -0.0002] | 22/2000 | 0.011 | 0 | 0.9767 | 0.9772 |

## Level: forecast of each system's pass@1 on half B

| n_A | Arm | MAE | RMSE | Mean bias | MAE(pass@1 on A) − MAE(arm) [95% CI] p-val | Systems closer | Splits lower |
|---:|---|---:|---:|---:|---|---:|---:|
| 25 | pass1_A | 0.0772 | 0.0923 | -0.0006 | — | — | — |
| 25 | 1pl | 0.0484 | 0.0609 | -0.0011 | +0.0288 [+0.0272, +0.0302] p-val=0.0010 | 160/164 | 1942/2000 |
| 25 | 2pl | 0.0459 | 0.0583 | -0.0015 | +0.0313 [+0.0288, +0.0335] p-val=0.0010 | 156/164 | 1985/2000 |
| 25 | grm3 | 0.0444 | 0.0560 | -0.0052 | +0.0328 [+0.0307, +0.0346] p-val=0.0010 | 160/164 | 1990/2000 |
| 25 | mean_equating | 0.0546 | 0.0683 | +0.0000 | +0.0226 [+0.0213, +0.0239] p-val=0.0010 | 158/164 | 1780/2000 |
| 25 | linear_regression | 0.0491 | 0.0617 | +0.0001 | +0.0281 [+0.0264, +0.0296] p-val=0.0010 | 158/164 | 1943/2000 |
| 50 | pass1_A | 0.0554 | 0.0664 | +0.0001 | — | — | — |
| 50 | 1pl | 0.0361 | 0.0456 | -0.0005 | +0.0193 [+0.0184, +0.0201] p-val=0.0010 | 162/164 | 1919/2000 |
| 50 | 2pl | 0.0344 | 0.0436 | -0.0007 | +0.0210 [+0.0195, +0.0224] p-val=0.0010 | 159/164 | 1972/2000 |
| 50 | grm3 | 0.0336 | 0.0425 | -0.0033 | +0.0218 [+0.0205, +0.0231] p-val=0.0010 | 159/164 | 1981/2000 |
| 50 | mean_equating | 0.0395 | 0.0496 | +0.0000 | +0.0159 [+0.0149, +0.0167] p-val=0.0010 | 159/164 | 1835/2000 |
| 50 | linear_regression | 0.0366 | 0.0461 | +0.0001 | +0.0188 [+0.0178, +0.0197] p-val=0.0010 | 159/164 | 1932/2000 |
| 100 | pass1_A | 0.0425 | 0.0510 | +0.0008 | — | — | — |
| 100 | 1pl | 0.0279 | 0.0351 | -0.0003 | +0.0147 [+0.0141, +0.0152] p-val=0.0010 | 164/164 | 1928/2000 |
| 100 | 2pl | 0.0271 | 0.0343 | -0.0003 | +0.0154 [+0.0144, +0.0164] p-val=0.0010 | 158/164 | 1936/2000 |
| 100 | grm3 | 0.0270 | 0.0342 | -0.0023 | +0.0155 [+0.0144, +0.0165] p-val=0.0010 | 156/164 | 1938/2000 |
| 100 | mean_equating | 0.0301 | 0.0378 | +0.0000 | +0.0124 [+0.0117, +0.0131] p-val=0.0010 | 159/164 | 1823/2000 |
| 100 | linear_regression | 0.0282 | 0.0355 | +0.0000 | +0.0143 [+0.0136, +0.0150] p-val=0.0010 | 160/164 | 1942/2000 |
| 250 | pass1_A | 0.0370 | 0.0443 | +0.0013 | — | — | — |
| 250 | 1pl | 0.0244 | 0.0308 | -0.0001 | +0.0126 [+0.0122, +0.0131] p-val=0.0010 | 164/164 | 1906/2000 |
| 250 | 2pl | 0.0245 | 0.0309 | -0.0001 | +0.0126 [+0.0117, +0.0134] p-val=0.0010 | 157/164 | 1868/2000 |
| 250 | grm3 | 0.0250 | 0.0317 | -0.0016 | +0.0120 [+0.0110, +0.0130] p-val=0.0010 | 156/164 | 1782/2000 |
| 250 | mean_equating | 0.0262 | 0.0328 | +0.0000 | +0.0108 [+0.0102, +0.0114] p-val=0.0010 | 159/164 | 1821/2000 |
| 250 | linear_regression | 0.0247 | 0.0311 | +0.0000 | +0.0123 [+0.0117, +0.0129] p-val=0.0010 | 161/164 | 1930/2000 |

## Correlations with pass@1 on B at n_A = 50 (medians over splits)

| Arm | Pearson | Spearman | Kendall τ-b |
|---|---:|---:|---:|
| pass1_A | 0.9638 | 0.9532 | 0.8306 |
| rasch_common_check | 0.9651 | 0.9532 | 0.8306 |
| 2pl_within_A | 0.9527 | 0.9574 | 0.8259 |
| grm3_within_A | 0.9546 | 0.9584 | 0.8282 |
| 1pl | 0.9644 | 0.9494 | 0.8109 |
| 2pl | 0.9670 | 0.9571 | 0.8251 |
| grm3 | 0.9689 | 0.9581 | 0.8273 |
| mean_equating | 0.9633 | 0.9499 | 0.8118 |
| linear_regression | 0.9627 | 0.9492 | 0.8105 |

## IRT versus reference-panel controls at n_A = 50 (positive = IRT closer to held-out pass@1)

| Control | IRT arm | MAE(control) − MAE(IRT) [95% CI] p-val | Systems where IRT closer |
|---|---|---|---:|
| mean_equating | 1pl | +0.0034 [+0.0033, +0.0035] p-val=0.0010 | 164/164 |
| mean_equating | 2pl | +0.0052 [+0.0043, +0.0059] p-val=0.0010 | 146/164 |
| mean_equating | grm3 | +0.0060 [+0.0051, +0.0068] p-val=0.0010 | 144/164 |
| linear_regression | 1pl | +0.0004 [+0.0003, +0.0007] p-val=0.0010 | 99/164 |
| linear_regression | 2pl | +0.0022 [+0.0015, +0.0028] p-val=0.0010 | 133/164 |
| linear_regression | grm3 | +0.0030 [+0.0023, +0.0037] p-val=0.0010 | 134/164 |

## Promotion gates at n_A = 50 (ordered pairs; harmful = candidate below incumbent on half B)

Base rate if every pair were promoted: 0.4974. Matched-count failures: 0. a zero standard error gives z = +inf, -inf or 0 by the sign of the gain.

| Gate | Promotions per split (mean) | 5th–95th | Harmful-promotion rate | Correct-promotion rate |
|---|---:|---|---:|---:|
| G0_scalar | 12867.4 | [12764, 12954] | 0.0763 | 0.9189 |
| G1_pass1_1se | 10577.8 | [10149, 10927] | 0.0291 | 0.9684 |
| G2_irt_1se | 10745.6 | [10384, 11041] | 0.0265 | 0.9711 |
| G1m_pass1_top_matched_to_G2 | 10745.6 | [10384, 11041] | 0.0314 | 0.9660 |
| G2m_irt_top_matched_to_G1 | 10577.8 | [10149, 10927] | 0.0241 | 0.9737 |

- matched_G1m-G2: harmful-rate difference (pass@1 gate minus IRT gate, positive = IRT safer) +0.0049 [+0.0031, +0.0070] p-val=0.0010 (system-cluster percentile bootstrap (2000 draws), conditional on each split's selections).

- matched_G1-G2m: harmful-rate difference (pass@1 gate minus IRT gate, positive = IRT safer) +0.0050 [+0.0032, +0.0073] p-val=0.0010 (system-cluster percentile bootstrap (2000 draws), conditional on each split's selections).

## Stability

Per-system standard deviation across the 2,000 halves A at n_A = 50 (lower = steadier estimator):

| Arm | Mean SD of forecast | Mean SD of error | Ratio to pass@1 on A [95% CI] |
|---|---:|---:|---|
| pass1_A | 0.0611 | 0.0693 | 1 (reference) |
| 1pl | 0.0387 | 0.0437 | 0.631 [0.620, 0.643] |
| 2pl | 0.0343 | 0.0386 | 0.558 [0.544, 0.571] |
| grm3 | 0.0327 | 0.0368 | 0.531 [0.519, 0.543] |
| mean_equating | 0.0440 | 0.0495 | 0.715 [0.701, 0.730] |
| linear_regression | 0.0395 | 0.0445 | 0.643 [0.630, 0.656] |

Fold-seed stability of the primary 2PL comparison (n_A = 50):

| Fold seed | K-fold 2PL median Δ | Share Δ > 0 | MAE difference [95% CI] | Fits converged |
|---:|---:|---:|---|---|
| 0 | +0.0036 | 0.793 | +0.0210 [+0.0195, +0.0224] | True |
| 1 | +0.0033 | 0.772 | +0.0210 [+0.0194, +0.0223] | True |
| 2 | +0.0034 | 0.774 | +0.0209 [+0.0193, +0.0223] | True |
| 3 | +0.0037 | 0.798 | +0.0209 [+0.0193, +0.0223] | True |
| 4 | +0.0035 | 0.770 | +0.0209 [+0.0194, +0.0223] | True |

Item-parameter agreement across the 10 fold fits (mean and minimum pairwise correlation):

| Model | Parameter | Pearson mean | Pearson min | Spearman mean | Spearman min |
|---|---|---:|---:|---:|---:|
| 1pl | location_b | 0.9984 | 0.9975 | 0.9987 | 0.9983 |
| 1pl | slope_a | common slope per fold: [1.611, 1.634, 1.657, 1.622, 1.614, 1.627, 1.587, 1.569, 1.630, 1.583] | | | |
| 2pl | location_b | 0.9926 | 0.9811 | 0.9978 | 0.9964 |
| 2pl | slope_a | 0.9652 | 0.9312 | 0.9710 | 0.9430 |
| grm3 | location_b | 0.9916 | 0.9805 | 0.9979 | 0.9965 |
| grm3 | slope_a | 0.9663 | 0.9278 | 0.9718 | 0.9418 |

## Sensitivity: one system per base model (73 systems, n_A = 50)

- 2PL (within half A) rank: median Δ +0.0016, Δ > 0 in 1238/2000 = 0.619.
- 2PL (K-fold) level: MAE 0.0550 (pass@1 on A) versus 0.0385; difference +0.0165 [+0.0137, +0.0191] p-val=0.0010; fits converged: True.

## Held-out cell Brier score at n_A = 50 (descriptive; lower is better)

| Predictor | Brier |
|---|---:|
| 2pl | 0.0967 |
| system_only_pass1_A | 0.2208 |
| item_only_reference_rate | 0.1394 |

## Frozen forecast versus outcome

| Prediction | Forecast | Outcome | Inside 80% interval |
|---|---|---|---|
| P1_rank_median_delta_2pl_within_A_n50 | 0.001 [-0.004, 0.005] | 0.004021867545595914 | True |
| P1_rank_share_delta_positive_n50 | 0.55 [0.25, 0.85] | 0.8115 | True |
| P1_rank_rule_holds | p=0.4 | True | event occurred |
| P2_mae_pass1_A_n50 | 0.05 [0.04, 0.062] | 0.05538670014347203 | True |
| P2_mae_2pl_kfold_n50 | 0.035 [0.025, 0.046] | 0.0343526874583386 | True |
| P2_mae_difference_n50 | 0.015 [0.005, 0.025] | 0.02103401268513339 | True |
| P2_level_rule_holds | p=0.85 | True | event occurred |
| Q1_continue | p=0.88 | True | event occurred |
| Q1_inconclusive | p=0.04 | False | event did not occur |
| level_win_beyond_reference_panel | p=0.45 | True | event occurred |
| S3_2pl_minus_linear_regression_mae_n50 | 0.001 [-0.002, 0.004] | 0.002203537221351755 | True |
| S1_mae_mean_equating_n50 | 0.04 [0.03, 0.05] | 0.03953314887092249 | True |
| S1_kfold_2pl_rank_median_delta_n50 | -0.001 [-0.005, 0.003] | 0.0036213709433037256 | False |
| S2_grm3_within_A_rank_median_delta_n50 | -0.002 [-0.01, 0.004] | 0.005069289611437822 | False |
| S2_grm3_rank_rule_holds | p=0.25 | True | event occurred |
| S2_grm3_mae_difference_n50 | 0.013 [0.003, 0.023] | 0.021828875728225085 | True |
| S2_grm3_level_rule_holds | p=0.8 | True | event occurred |
| S4_G0_harmful_promotion_rate | 0.05 [0.03, 0.08] | 0.07628083799669172 | True |
| S4_matched_hpr_difference_pass1_minus_irt | 0.0 [-0.004, 0.004] | 0.004919998434713042 | False |
| S5_2pl_error_sd_ratio_to_pass1_A | 0.75 [0.6, 0.9] | 0.557518134150876 | False |
| S7_heldout_cell_brier_2pl | 0.12 [0.09, 0.15] | 0.09666728909059867 | True |

Timing (seconds): {"primary_fits": 118.5, "within_half_fits_n25": 168.0, "score_n25": 56.5, "within_half_fits_n50": 209.4, "score_n50": 97.3, "within_half_fits_n100": 407.7, "score_n100": 86.8, "within_half_fits_n250": 1092.5, "score_n250": 130.2, "kfold_rescore_check_n50": 4.8, "rank_bootstrap_n50": 187.3, "fold_seed_1": 43.6, "fold_seed_2": 43.3, "fold_seed_3": 43.8, "fold_seed_4": 44.4, "sensitivity": 95.4, "total": 2831.4}
