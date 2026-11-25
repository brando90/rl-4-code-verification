# 12_scsc_vs_hidden_gold_tests_vbv1_across_systems — version-2 completed analysis

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/RESULTS_analysis_v2.md>

**Updated:** 10-16-2026 00:53 PDT

All 4,626 eligible groups and all 9,856 declared cells are accounted for. P1 HOLDS: system Spearman 0.8909 [0.7818, 0.9000]; P2 HOLDS: area under the receiver operating characteristic curve (AUC) 0.7448 [0.5768, 0.8659]; P3 HOLDS: within-system Spearman 0.1445 [0.0497, 0.2290]. Fully applicable coverage is 3235/4626 = 0.6993: PASS.

Smooth conjunctive score for code verification (SCSC) combines internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). These results measure agreement with hidden computational gold-reference tests on saved VeriBench V1 (VBV1) candidates; they do not establish human acceptance or complete semantic correctness. Zero new model calls, zero judge calls, zero graphics processing units, and $0 Vals spend.

## Scope, denominators and missing outcomes

The fixed panel has 11 systems × 896 tasks = 9,856 cells, including 154 cells on 14 tasks without extracted tests. Exactly 4,626 compiling, joined, test-bearing cells were evaluated. There are 8309 observed binary outcomes (3199 passing) and 1393 missing test-bearing outcomes. No-test cells are excluded consistently from protocol statistics. The additional all-declared bounds below retain them as unknown, preserving the literal 9,856-cell denominator.

| Status | Cells |
| --- | --- |
| evaluated | 3394 |
| file_missing | 2 |
| no_tests | 154 |
| noncompiling | 5074 |
| not_applicable | 1232 |

| Accounting | Passes / observed | Missing | All missing fail / all missing pass |
| --- | --- | --- | --- |
| Protocol: tasks with tests | 3199/8309 | 1393 | 0.3297 / 0.4733 |
| All declared cells | 3199/8309 | 1547 | 0.3246 / 0.4815 |

A non-compiling test-bearing candidate is a failure. A compiling candidate with any unevaluable test has a missing binary all-pass outcome, even when every evaluable test passes. The graded rate uses evaluable tests only. Missing outcomes are never silently converted to successes.

## Dynamic controls

| Control | Count | Rate | Frozen gate | Verdict |
| --- | --- | --- | --- | --- |
| C1 gold self-tests | 591/591 | 1.0000 | ≥0.9800 | PASS |
| C2 renamed gold recovery | 48/50 | 0.9600 | ≥0.9500 | PASS |
| C3 compiling mutant detection | 44/50 | 0.8800 | ≥0.6000 and ≥50 mutants | PASS |
| C4 wrong-task rejection or failure | 49/50 | 0.9800 | ≥0.9500 | PASS |

All 50 prescribed tasks completed before primary evaluation. [Per-task controls](results/controls_v2.json). The frozen adapter, forecasts, references and version-1 files remain unchanged.

## Frozen hypotheses and coverage gate

| Hypothesis | Estimate [95% task-cluster interval] | Denominator | Frozen threshold | Verdict |
| --- | --- | --- | --- | --- |
| P1: system ranking | 0.8909 [0.7818, 0.9000] | 11 systems; 896 task clusters | Spearman ≥0.80 | HOLDS |
| P2: discriminate passing candidates | 0.7448 [0.5768, 0.8659] | 3210 cells; 3174 pass / 36 fail; 735 observed tasks | AUC ≥0.60 and lower 95% bound >0.50 | HOLDS |
| P3: within-system graded ranking | 0.1445 [0.0497, 0.2290] | same 3210 cells | Spearman >0 and lower 95% bound >0 | HOLDS |
| G-A: fully applicable coverage | 0.6993 [0.6759, 0.7216] | 3235/4626 | ≥0.50 | PASS |
| At least one evaluable test | 0.7337 [0.7116, 0.7554] | 3394/4626 | Descriptive | No gate |

Thresholds come from the original frozen experiment forecast, carried into [version-2 protocol §5](PROTOCOL.md). They were agent-suggested before evaluation. Version 2 applies the unchanged coverage threshold to the stricter fully applicable cohort. All intervals use 10,000 paired task-cluster bootstrap draws, seed 20261009, retaining all systems in each sampled task. The P2/P3 resampling frame is all 896 tasks; within-system normalized midranks are recomputed in every draw. p-val=n/a: no p-value gate was specified.

## System-level agreement and calibration

P1 uses the common three-factor score cohort within each system, with the hidden mean over its non-missing test-bearing subset. This preserves the version-1 definition; it is not an identical cell denominator for score and hidden outcome. The per-system factor and hidden denominators are shown below. Positive bias means SCSC is higher than hidden all-pass rate.

| Statistic | Estimate [95% task interval] | 95% system-bootstrap sensitivity |
| --- | --- | --- |
| Spearman ρ | 0.8909 [0.7818, 0.9000] | [0.4930, 1.0000] |
| Pearson r | 0.8668 [0.8467, 0.8853] | [0.4922, 0.9927] |
| Kendall τ-b | 0.7818 [0.6727, 0.8182] | [0.3777, 1.0000] |
| Mean SCSC | 0.4818 [0.4714, 0.4917] | [0.3082, 0.6657] |
| Mean hidden outcome | 0.4419 [0.4296, 0.4541] | [0.2466, 0.6466] |
| Bias: SCSC − hidden | 0.0399 [0.0323, 0.0471] | [-0.0713, 0.1203] |
| Mean absolute difference | 0.1242 [0.1173, 0.1308] | [0.0626, 0.2024] |

| Descriptive score/outcome | Systems | Spearman | Pearson | Kendall | Mean score | Mean hidden | Bias | Mean absolute difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCSC / graded hidden | 11 | 0.8909 | 0.8683 | 0.7818 | 0.4818 | 0.4450 | 0.0369 | 0.1228 |
| IC_tests | 11 | 0.9000 | 0.9137 | 0.8182 | 0.4234 | 0.4419 | -0.0185 | 0.0659 |
| IC_proofs | 11 | 0.9091 | 0.9146 | 0.8545 | 0.4252 | 0.4419 | -0.0167 | 0.0644 |
| FSC | 11 | 0.0091 | -0.2068 | -0.0545 | 0.8141 | 0.4419 | 0.3722 | 0.4654 |

The graded and individual-factor rows are descriptive point estimates; their intervals were not specified. A single saved scoring run exists per cell. Raw-repeat standard deviation and aggregate test–retest variability are unavailable; task resampling measures task-sample uncertainty, not generation, scorer-repeat, reference or adapter uncertainty.

## Per-system factors and outcomes

| System | Declared | Factor cohort | IC_tests | IC_proofs | FSC | System SCSC | Compiles | Compile rate | P1 hidden n | P1 hidden mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 896 | 896 | 0.2868 | 0.2891 | 0.2936 | 0.2898 | 823 | 0.9185 | 279 | 0.7348 |
| claude-opus-5-max | 896 | 681 | 0.6079 | 0.6074 | 0.7366 | 0.6479 | 428 | 0.4777 | 623 | 0.5650 |
| claude_code | 896 | 896 | 0.9777 | 0.9774 | 0.9642 | 0.9731 | 876 | 0.9777 | 712 | 0.9607 |
| codex | 896 | 896 | 0.9989 | 0.9987 | 0.9182 | 0.9712 | 895 | 0.9989 | 679 | 0.9897 |
| gemini-3.1-pro-high | 896 | 889 | 0.0574 | 0.0544 | 0.8661 | 0.1393 | 52 | 0.0580 | 864 | 0.0417 |
| gpt-5.6-luna-high | 896 | 890 | 0.1629 | 0.1629 | 0.8555 | 0.2832 | 145 | 0.1618 | 843 | 0.1329 |
| gpt-5.6-sol-high | 896 | 889 | 0.3881 | 0.3881 | 0.9209 | 0.5176 | 347 | 0.3873 | 810 | 0.3370 |
| gpt-6-astra-high | 896 | 855 | 0.5240 | 0.5237 | 0.9664 | 0.6425 | 462 | 0.5156 | 722 | 0.4501 |
| gpt-6-luna-high | 896 | 888 | 0.1430 | 0.1398 | 0.8819 | 0.2603 | 127 | 0.1417 | 855 | 0.1240 |
| leanstral | 896 | 896 | 0.5089 | 0.5342 | 0.6527 | 0.5619 | 518 | 0.5781 | 779 | 0.5250 |
| qwen3.6-27b-thinking | 896 | 604 | 0.0017 | 0.0017 | 0.8994 | 0.0135 | 1 | 0.0011 | 598 | 0.0000 |

| System | Compiling with tests | Fully applicable | Any evaluable | Observed hidden | Pass / observed | Graded mean | Protocol bounds | All-declared bounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 809 | 206 (0.2546) | 217 (0.2682) | 279 | 205/279 (0.7348) | 0.7366 | 0.2324 / 0.9161 | 0.2288 / 0.9174 |
| claude-opus-5-max | 428 | 370 (0.8645) | 380 (0.8879) | 824 | 366/824 (0.4442) | 0.4471 | 0.4150 / 0.4807 | 0.4085 / 0.4888 |
| claude_code | 865 | 695 (0.8035) | 722 (0.8347) | 712 | 684/712 (0.9607) | 0.9715 | 0.7755 / 0.9683 | 0.7634 / 0.9688 |
| codex | 881 | 679 (0.7707) | 723 (0.8207) | 679 | 672/679 (0.9897) | 0.9971 | 0.7619 / 0.9921 | 0.7500 / 0.9922 |
| gemini-3.1-pro-high | 50 | 37 (0.7400) | 39 (0.7800) | 869 | 37/869 (0.0426) | 0.0426 | 0.0420 / 0.0567 | 0.0413 / 0.0714 |
| gpt-5.6-luna-high | 145 | 112 (0.7724) | 118 (0.8138) | 849 | 112/849 (0.1319) | 0.1319 | 0.1270 / 0.1644 | 0.1250 / 0.1775 |
| gpt-5.6-sol-high | 345 | 280 (0.8116) | 289 (0.8377) | 817 | 275/817 (0.3366) | 0.3407 | 0.3118 / 0.3855 | 0.3069 / 0.3951 |
| gpt-6-astra-high | 459 | 334 (0.7277) | 362 (0.7887) | 757 | 333/757 (0.4399) | 0.4409 | 0.3776 / 0.5193 | 0.3717 / 0.5268 |
| gpt-6-luna-high | 126 | 107 (0.8492) | 110 (0.8730) | 863 | 106/863 (0.1228) | 0.1232 | 0.1202 / 0.1417 | 0.1183 / 0.1551 |
| leanstral | 517 | 415 (0.8027) | 433 (0.8375) | 779 | 409/779 (0.5250) | 0.5295 | 0.4637 / 0.5805 | 0.4565 / 0.5871 |
| qwen3.6-27b-thinking | 1 | 0 (0.0000) | 1 (1.0000) | 881 | 0/881 (0.0000) | 0.0000 | 0.0000 / 0.0011 | 0.0000 / 0.0167 |

Each system has 896 declared cells and 14 no-test cells. Protocol bounds use 882 tasks; all-declared bounds use 896. The graded mean in this table is over binary-observed rows, preserving the version-1 table definition. [Machine-readable system table](results/systems_v2.json) also retains available-factor means and kernel-verification descriptives.

## Prespecified sensitivities

| Cohort | Cells | Pass / fail | P2 AUC [95% interval] | P3 Spearman [95% interval] |
| --- | --- | --- | --- | --- |
| Primary fully applicable | 3210 | 3174 / 36 | 0.7448 [0.5768, 0.8659] | 0.1445 [0.0497, 0.2290] |
| S-V2a: at least one evaluable | 3368 | 3318 / 50 | 0.7496 [0.6252, 0.8493] | 0.1610 [0.0773, 0.2395] |
| S-V2b: fully applicable, static steps 1–2b | 2964 | 2941 / 23 | 0.8278 [0.6406, 0.9320] | 0.1598 [0.0533, 0.2438] |
| S-V2d: common fully applicable, v1 | 3038 | 2999 / 39 | 0.7330 [0.5952, 0.8482] | 0.1315 [0.0471, 0.2118] |
| S-V2d: common fully applicable, v2 | 3038 | 3011 / 27 | 0.7422 [0.5367, 0.8974] | 0.1284 [0.0311, 0.2161] |

| P1 sensitivity | Systems | Spearman [95% interval] | Pearson | Kendall | Bias | Mean absolute difference |
| --- | --- | --- | --- | --- | --- | --- |
| S-V2c: model_error/incomplete as failure | 11 | 0.8727 [0.7727, 0.8909] | 0.8653 | 0.7455 | 0.0381 | 0.1224 |
| S-V2d common cohort, v1 | 10 | -0.2393 [-0.5706, 0.1438] | 0.0683 | -0.1840 | -0.0250 | 0.0337 |
| S-V2d common cohort, v2 | 10 | 0.0061 [-0.4502, 0.3502] | 0.3597 | 0.0460 | -0.0283 | 0.0314 |

S-V2d contains 3062 cells fully applicable in both versions. The same task resampling seed is used for the two versions. These are sensitivity estimates, never replacements for the primary verdicts.

## Core and industry subsets

| Subset | Declared tasks | P1 Spearman [95% interval] | Fully applicable score cells | Pass / fail | P2 AUC [95% interval] | P3 Spearman [95% interval] |
| --- | --- | --- | --- | --- | --- | --- |
| Core614 | 614 | 0.7909 [0.7727, 0.8000] | 2193 | 2159 / 34 | 0.7632 [0.6014, 0.8835] | 0.1917 [0.0762, 0.2933] |
| IndustrySet282 | 282 | 0.9455 [0.9000, 0.9455] | 1017 | 1015 / 2 | 0.1855 [0.0417, 0.5729] | -0.0363 [-0.0711, -0.0074] |

Per-system tables for each subset, individual-factor P2/P3 descriptives and every interval’s defined-draw count are retained in [the complete analysis receipt](results/analysis_e12_v2.json). Optional secondary panels were not evaluated in this primary-only dispatch.

## Every frozen forecast

| Forecast | Point forecast | Plausible range | Measured | Inside range? | Directional prediction |
| --- | --- | --- | --- | --- | --- |
| P1 | 0.8900 | 0.8000–0.9500 | 0.8909 | HOLDS | about unchanged (v1 0.891) |
| P2 | 0.6800 | 0.6200–0.7400 | 0.7448 | DOES NOT HOLD | HOLDS |
| P3 | 0.2000 | 0.1200–0.3000 | 0.1445 | HOLDS | DOES NOT HOLD |
| G-A | 0.6200 | 0.5500–0.7000 | 0.6993 | HOLDS | No separate directional rule |
| applicability_any_evaluable | 0.7200 | 0.6600–0.7800 | 0.7337 | HOLDS | HOLDS |
| failing_share | unavailable | 0.0200–0.0600 | 0.0112 | DOES NOT HOLD | HOLDS |

Failing share: 36/3210 = 0.0112 [0.0057, 0.0181]; version-1 comparator 200/3,199. A forecast plausible range is a frozen prediction range, not a confidence interval. P1 “about unchanged” has no separate numerical tolerance; its point, range and frozen ≥0.80 hypothesis are reported without inventing another gate.

Amended static-census consistency: HOLDS; observed {'n_cells': 4626, 'fully_mapped': 3121, 'probe': 263, 'none': 927}, expected {'n_cells': 4626, 'fully_mapped': 3121, 'probe': 263, 'none': 927}. The V2-A1 amendment supersedes the original forecast’s pre-amendment mapping counts. Both frozen forecast files and hashes are preserved.

## Mapping and paired version comparison

| Mapping step | Mapped symbols | Share of mapped symbols |
| --- | --- | --- |
| 1 | 4823 | 0.6507 |
| 2a | 882 | 0.1190 |
| 2b | 1365 | 0.1842 |
| 3 | 294 | 0.0397 |
| 4 | 48 | 0.0065 |

Mapping counts describe symbols, so multiple symbols can belong to one cell. Static coverage is a mapping property; fully applicable coverage additionally requires every test to elaborate and yield a Boolean outcome.

| v1 all-pass | v2 all-pass | Changed-entry-point cells |
| --- | --- | --- |
| 0 | False | 1 |
| 0 | None | 3 |
| 0 | True | 13 |
| 1 | True | 174 |
| None | False | 7 |
| None | None | 28 |
| None | True | 153 |

All 379 post-amendment changed-entry-point rows are retained in [the paired table](results/paired_changed_entry_points_v2.json). None means missing. Version 1’s binary field treated partial applicability differently, so an outcome transition alone is not proof of a semantic correction.

| System | Originally inspected task | v1 category | v1 all-pass | v2 all-pass | v2 tests pass/evaluable | v2 fully applicable |
| --- | --- | --- | --- | --- | --- | --- |
| claude-opus-5-max | concurrent_set_synthetic__my_hazard_pointer_can_free | helper_mapping | 0 | True | 8/8 | True |
| claude-opus-5-max | concurrent_set_synthetic__my_lww_register_pick_left | helper_mapping | 0 | True | 8/8 | True |
| claude-opus-5-max | easy_set__1_myadd | partial_applicability | 0 | None | 1/1 | False |
| claude-opus-5-max | easy_set__33_myminimum | partial_applicability | 0 | None | 5/5 | False |
| claude-opus-5-max | humaneval_set__humaneval_22_filter_integers | partial_applicability | 0 | None | 1/1 | False |
| claude-opus-5-max | hypervisor_set_synthetic__my_interrupt_route | helper_mapping | 0 | True | 8/8 | True |
| claude-opus-5-max | memory_bugs_set_synthetic__my_bump_alloc_fits | helper_mapping | 0 | True | 7/7 | True |
| claude-opus-5-max | os_embedded_set_synthetic__my_power_transition_ok | helper_mapping | 0 | True | 9/9 | True |
| claude-opus-5-max | regulated_set_synthetic__my_dose_interval_ok | helper_mapping | 0 | None | 0/0 | False |
| claude-opus-5-max | security_set__security_6858__safe__104_unsafehttpparse_safe | partial_applicability | 0 | None | 9/9 | False |
| leanstral | aerospace_set_synthetic__my_arming_interlock | zero_self_test_factor | 1 | True | 7/7 | True |
| leanstral | aerospace_set_synthetic__my_safing_vote | zero_self_test_factor | 1 | True | 7/7 | True |
| leanstral | aerospace_set_synthetic__my_sensor_watchdog_fresh | zero_self_test_factor | 1 | True | 5/5 | True |
| leanstral | aerospace_set_synthetic__my_tmr_voter | zero_self_test_factor | 1 | True | 7/7 | True |
| leanstral | compilers_set_real__my_cpython_dis_jump_target | zero_self_test_factor | 1 | True | 7/7 | True |
| leanstral | concurrent_set_real__my_cas_success | zero_self_test_factor | 1 | True | 8/8 | True |
| leanstral | concurrent_set_real__my_h2_flow_window_after_send | zero_self_test_factor | 1 | True | 8/8 | True |
| leanstral | concurrent_set_synthetic__my_lww_register_pick_left | zero_self_test_factor | 1 | True | 8/8 | True |
| leanstral | concurrent_set_synthetic__my_rcu_epoch_can_reclaim | zero_self_test_factor | 1 | True | 8/8 | True |
| leanstral | concurrent_set_synthetic__my_vector_clock_merge_le_target | zero_self_test_factor | 1 | True | 8/8 | True |

Frozen original-20-row prediction: HOLDS. Details: `{"helper_resolved_or_missing": 6, "holds": true, "low_still_passing": 10, "n_helper_rows": 6, "n_low_rows": 10, "n_partial_rows": 4, "partial_missing_and_evaluable_pass": 4, "remaining_helper_failures": 0}`. [Original 20 rows and mappings](results/paired_inspected_v1_rows_v2.json).

## Twenty newly selected disagreements

Selection is the frozen version-1 rule applied to version 2’s fully applicable, compiling, score-measured cohort: 10 highest-SCSC failures and 10 lowest-SCSC successes, with system/task tie breakers. The selected rows and per-test evidence are inspected in [the disagreement report](DISAGREEMENTS_v2.md) (file not committed; QA 11-25-2026).

| Group | System | Task | SCSC | Tests pass / total | Mapping steps |
| --- | --- | --- | --- | --- | --- |
| high_score_failing | claude_code | humaneval_set__humaneval_38_encode_cyclic | 1.0000 | 12/14 | 4, 4, 4 |
| high_score_failing | claude_code | security_set__security_6858__safe__69_unsafednsspoofing_safe | 1.0000 | 13/15 | 1, 1, 1, 1, 4, 1 |
| high_score_failing | claude_code | security_set__security_6858__vulnerabilities__130_unsafebitlockerbios | 1.0000 | 9/14 | 2a, 2a |
| high_score_failing | claude_code | security_set__security_6858__vulnerabilities__148_unsafeformatstringleak | 1.0000 | 6/14 | 2a, 2a |
| high_score_failing | codex | security_set__security_6858__safe__69_unsafednsspoofing_safe | 1.0000 | 13/15 | 1, 1, 1, 1, 4, 2b |
| high_score_failing | gpt-5.6-sol-high | regulated_set_synthetic__my_watchdog_safe_required | 1.0000 | 6/8 | 1, 2a |
| high_score_failing | gpt-5.6-sol-high | security_set__security_6858__safe__60_unsafebroadcasteavesdrop_safe | 1.0000 | 7/14 | 2a, 2a |
| high_score_failing | gpt-5.6-sol-high | security_set__security_6858__safe__69_unsafednsspoofing_safe | 1.0000 | 11/15 | 1, 1, 1, 4, 4, 2b |
| high_score_failing | gpt-6-astra-high | security_set__security_6858__safe__69_unsafednsspoofing_safe | 1.0000 | 11/15 | 1, 1, 1, 4, 4, 2b |
| high_score_failing | gpt-6-luna-high | security_set__security_6858__safe__117_unsafexfijump_safe | 1.0000 | 5/14 | 3, 3 |
| low_score_passing | leanstral | aerospace_set_synthetic__my_arming_interlock | 0.0000 | 7/7 | 1, 2a |
| low_score_passing | leanstral | aerospace_set_synthetic__my_safing_vote | 0.0000 | 7/7 | 1, 2a |
| low_score_passing | leanstral | aerospace_set_synthetic__my_sensor_watchdog_fresh | 0.0000 | 5/5 | 1, 2a |
| low_score_passing | leanstral | aerospace_set_synthetic__my_tmr_voter | 0.0000 | 7/7 | 1, 2a |
| low_score_passing | leanstral | compilers_set_real__my_cpython_dis_jump_target | 0.0000 | 7/7 | 1, 2a |
| low_score_passing | leanstral | concurrent_set_real__my_cas_success | 0.0000 | 8/8 | 2a, 2a |
| low_score_passing | leanstral | concurrent_set_real__my_h2_flow_window_after_send | 0.0000 | 8/8 | 1, 2a |
| low_score_passing | leanstral | concurrent_set_synthetic__my_lww_register_pick_left | 0.0000 | 8/8 | 1, 2a |
| low_score_passing | leanstral | concurrent_set_synthetic__my_rcu_epoch_can_reclaim | 0.0000 | 8/8 | 1, 2a |
| low_score_passing | leanstral | concurrent_set_synthetic__my_vector_clock_merge_le_target | 0.0000 | 8/8 | 1, 2a |

## Reproducibility and limitations

Outcome ledger SHA-256: `5ecab23e05ce1cd87262aadc016b598e044c332f21efb88ca2bdb1b28c66c438`. [All 9,856 per-cell records](results/cells_v2.jsonl) (file not committed; QA 11-25-2026); [analysis JSON](results/analysis_e12_v2.json); [completion receipt](results/evaluation_complete_v2.json); [frozen runtime manifest](results/evaluation_launch_v2.json); [preflight](results/preflight_v2.json).

The run used Lean v4.22.0 with pinned Mathlib on skampere1, two low-priority CPU workers, the inherited 600-second Lean timeout, and at most one identical infrastructure retry per group. The complete receipt audit records module reuse and retries. No adapter tuning, candidate modification, gold-reference modification, new model scoring, or outcome-based sample selection occurred.

Task-bootstrap intervals reflect resampling the existing 896 task clusters for one saved run. The system-bootstrap sensitivity has only 11 systems. Missing adapter coverage can select an easier measured cohort; full-denominator bounds and the prespecified sensitivities expose, but do not eliminate, that limitation. Passing finite computational tests does not prove the full intended specification. No human labels or repeated model runs were collected.
