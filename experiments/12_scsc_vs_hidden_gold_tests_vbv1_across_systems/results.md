# Experiment 12 results — hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/results.md>

Experiment `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` compared saved code from 11 primary systems using hidden gold-reference tests with zero experiment model calls: **all three frozen predictions hold for the implemented adapter; mapping limitations qualify correctness claims**.

**Status:** DONE (version 1). **Version 2 (10-15-2026):** all four controls passed and the full primary evaluation is running on skampere1; see [live version-2 results](expt_v2/results.md) (frozen hashes verified, full suite 1,191 passed / 18 skipped, 77 targeted checks pass; self-tests 591/591, renamed recovery 48/50, mutant detection 44/50, wrong-task rejection 49/50; all 4,626 eligible groups admitted with 9,856-cell accounting); the version-1 results below are unchanged.
**Last updated:** 10-10-2026 05:19 PDT (version-1 results); status line 10-15-2026

SCSC means smooth conjunctive score for code verification. It combines internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). A2 changes only mechanical symbol mapping; P1–P3 thresholds remain frozen.

## Frozen predictions

| Prediction | Estimate | 95% task-cluster bootstrap | Threshold and verdict |
|---|---:|---|---|
| P1 system Spearman | 0.891 | [0.782, 0.900] (10000/10000 defined) | ≥0.80: HOLDS |
| P2 area under the receiver operating characteristic curve | 0.640 | [0.583, 0.696] (10000/10000 defined) | ≥0.60 and interval excludes 0.50: HOLDS |
| P3 pooled within-system Spearman | 0.151 | [0.074, 0.225] (10000/10000 defined) | >0 and interval excludes 0: HOLDS |
| G-A applicability | 0.690 (3224/4674) | Deterministic census | ≥0.50: PASS |

P1 contains 11 systems and resamples 896 tasks. P2/P3 contain 3199 compiling, applicable, score-measured cells (2999 passing / 200 failing), on 752 observed tasks. Intervals use 10,000 paired task-cluster draws, seed 20261009; systems are retained together within each sampled task. Undefined draws are reported, not replaced. Thresholds are master-suggested and frozen in the original forecast; p-val=n/a. Single saved run per cell; repeated scoring variability is unavailable.

P2 pools within-system normalized score midranks before computing the binary-outcome area. P3 correlates pooled within-system normalized score and graded-outcome midranks. Ranks are recomputed in every bootstrap draw. An applicable cell needs only one evaluable test, whereas all-tests-pass requires every extracted test to be evaluable and true. Therefore an all-tests-pass failure can reflect partial adapter applicability as well as a false test; the inspected cases distinguish these.

## System-level agreement and absolute differences

| Statistic | Estimate | 95% task bootstrap | 95% system bootstrap sensitivity |
|---|---:|---|---|
| pearson | 0.865 | [0.843, 0.885] (10000/10000 defined) | [0.487, 0.993] (10000/10000 defined) |
| spearman | 0.891 | [0.782, 0.900] (10000/10000 defined) | [0.493, 1.000] (10000/10000 defined) |
| kendall_tau_b | 0.782 | [0.673, 0.818] (10000/10000 defined) | [0.378, 1.000] (10000/10000 defined) |
| mean_score | 0.482 | [0.471, 0.492] (10000/10000 defined) | [0.308, 0.666] (10000/10000 defined) |
| mean_hidden | 0.421 | [0.408, 0.433] (10000/10000 defined) | [0.234, 0.615] (10000/10000 defined) |
| bias_score_minus_hidden | 0.061 | [0.052, 0.070] (10000/10000 defined) | [-0.046, 0.138] (10000/10000 defined) |
| mean_absolute_difference | 0.136 | [0.129, 0.144] (10000/10000 defined) | [0.080, 0.207] (10000/10000 defined) |

Descriptive system correlations (no additional verdicts):

| Pair | Pearson | Spearman | Kendall τ-b |
|---|---:|---:|---:|
| SCSC versus graded hidden rate | 0.864 | 0.891 | 0.782 |
| IC_tests versus hidden all-pass | 0.911 | 0.900 | 0.818 |
| IC_proofs versus hidden all-pass | 0.912 | 0.909 | 0.855 |
| FSC versus hidden all-pass | -0.210 | 0.009 | -0.055 |

Positive bias means SCSC exceeds the hidden all-tests-pass rate. A1 computes the geometric mean of factor means over each system’s common measured factor cohort; hidden means use that cohort minus unavailable hidden outcomes and no-test tasks. These denominators are reported separately.

## Primary systems

| System | Factors measured / declared | IC_tests | IC_proofs | FSC | SCSC | Compile | Applicable / compiling | P1 hidden mean (n) | Full hidden bounds (observed / missing / no tests) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 896/896 | 0.287 | 0.289 | 0.294 | 0.290 | 823/896 | 217/823 | 0.703 (290) | [0.231, 0.902] (290/592/14) |
| claude-opus-5-max | 681/896 | 0.608 | 0.607 | 0.737 | 0.648 | 428/896 | 356/428 | 0.529 (609) | [0.379, 0.460] (810/72/14) |
| claude_code | 896/896 | 0.978 | 0.977 | 0.964 | 0.973 | 876/896 | 623/876 | 0.927 (640) | [0.672, 0.947] (640/242/14) |
| codex | 896/896 | 0.999 | 0.999 | 0.918 | 0.971 | 895/896 | 705/895 | 0.929 (705) | [0.743, 0.943] (705/177/14) |
| gemini-3.1-pro-high | 889/896 | 0.057 | 0.054 | 0.866 | 0.139 | 52/896 | 28/52 | 0.032 (856) | [0.031, 0.056] (860/22/14) |
| gpt-5.6-luna-high | 890/896 | 0.163 | 0.163 | 0.856 | 0.283 | 145/896 | 113/145 | 0.127 (844) | [0.121, 0.158] (850/32/14) |
| gpt-5.6-sol-high | 889/896 | 0.388 | 0.388 | 0.921 | 0.518 | 347/896 | 289/347 | 0.333 (819) | [0.312, 0.375] (826/56/14) |
| gpt-6-astra-high | 855/896 | 0.524 | 0.524 | 0.966 | 0.642 | 462/896 | 342/462 | 0.418 (729) | [0.355, 0.488] (765/117/14) |
| gpt-6-luna-high | 888/896 | 0.143 | 0.140 | 0.882 | 0.260 | 127/896 | 107/127 | 0.122 (855) | [0.118, 0.139] (863/19/14) |
| leanstral | 896/896 | 0.509 | 0.534 | 0.653 | 0.562 | 518/896 | 443/518 | 0.507 (807) | [0.464, 0.549] (807/75/14) |
| qwen3.6-27b-thinking | 604/896 | 0.002 | 0.002 | 0.899 | 0.014 | 1/896 | 1/1 | 0.000 (599) | [0.000, 0.000] (882/0/14) |

Bounds count every unavailable hidden outcome as failing versus passing over all declared cells with extracted tests. Noncompiling code is a hidden failure; compiling but unevaluable code stays missing. Detailed no-test, unmeasured and applicable counts are in [analysis_e12.json](expt_v1/results/analysis_e12.json).

## Amendment sensitivities and subsets

| Analysis | Spearman or area | 95% task-cluster interval |
|---|---:|---|
| A1 P1: model_error/incomplete set to zero; infrastructure missing excluded | 0.873 | [0.782, 0.900] (10000/10000 defined) |
| A2 P2: mapping steps 1–2 only (1518 cells) | 0.791 | [0.712, 0.858] (10000/10000 defined) |
| A2 P3: mapping steps 1–2 only | 0.146 | [0.045, 0.226] (10000/10000 defined) |
| Core614 P1 (descriptive) | 0.791 | [0.764, 0.800] (10000/10000 defined) |
| Core614 P2 (descriptive) | 0.632 | [0.568, 0.697] (10000/10000 defined) |
| Core614 P3 (descriptive) | 0.176 | [0.062, 0.274] (10000/10000 defined) |
| IndustrySet282 P1 (descriptive) | 0.936 | [0.891, 0.945] (10000/10000 defined) |
| IndustrySet282 P2 (descriptive) | 0.614 | [0.518, 0.722] (10000/10000 defined) |
| IndustrySet282 P3 (descriptive) | 0.090 | [0.017, 0.162] (10000/10000 defined) |

Core614: P1 uses 11 systems / 614 tasks; P2/P3 use 2159 cells (1998 passing / 161 failing) on 474 observed tasks.


IndustrySet282: P1 uses 11 systems / 282 tasks; P2/P3 use 1040 cells (1001 passing / 39 failing) on 278 observed tasks.


A2 restricted cohort: 1518 cells (1480 passing / 38 failing), 674 observed tasks.


Mapping steps: 1 normalized name; 2 unique compatible type; 3 candidate definitions agree on hidden argument tuples; 4 candidate example/theorem reference counts resolve disagreement or undecidability. Hidden expected values never decide a mapping.

Primary-panel mappings:

| Mapping step | Symbols | Share of mapped symbols |
|---|---:|---:|
| 1 | 5075 | 0.660 |
| 2 | 693 | 0.090 |
| 3 | 1532 | 0.199 |
| 4 | 387 | 0.050 |

All-panel mapping counts (cell-symbol mappings, including mappings in otherwise unevaluable cells):

| Panel | Step 1 | Step 2 | Step 3 | Step 4 | Total |
|---|---:|---:|---:|---:|---:|
| primary | 5075 (0.660) | 693 (0.090) | 1532 (0.199) | 387 (0.050) | 7687 |
| experiment01 | 17 (0.500) | 11 (0.324) | 4 (0.118) | 2 (0.059) | 34 |
| experiment08_validation | 874 (0.644) | 3 (0.002) | 442 (0.326) | 38 (0.028) | 1357 |
| all | 5966 (0.657) | 707 (0.078) | 1978 (0.218) | 427 (0.047) | 9078 |

Per-system discrimination (area reported only when both classes have at least 10 cells):

| System | Pass / fail cells | Area |
|---|---:|---:|
| baseline | 204/13 | 0.666 |
| claude-opus-5-max | 322/20 | 0.576 |
| claude_code | 593/30 | 0.701 |
| codex | 655/50 | 0.687 |
| gemini-3.1-pro-high | 27/1 | unavailable |
| gpt-5.6-luna-high | 107/6 | unavailable |
| gpt-5.6-sol-high | 273/14 | 0.602 |
| gpt-6-astra-high | 305/28 | 0.634 |
| gpt-6-luna-high | 104/3 | unavailable |
| leanstral | 409/34 | 0.534 |
| qwen3.6-27b-thinking | 0/1 | unavailable |

Factor discrimination, descriptive:

| Factor | Cells | Area on within-system ranks | Within-system Spearman with graded rate |
|---|---:|---:|---:|
| IC_proofs | 3199 | 0.542 | 0.064 |
| FSC | 3199 | 0.635 | 0.160 |

## Secondary panels

These are descriptive saved-output panels. Experiment 08 uses validation only; its test split and sealed experiments 107/109 were not accessed.

| Panel / system | Declared | IC_tests | IC_proofs | Kernel rate (n) | Hidden all-pass (observed n) | Missing / no tests | Full hidden bounds | Hidden among kernel-verified (observed n / verified) | Kernel-conditioned bounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| experiment01 / qwen3-1.7b_g1 | 896 | 0.000 | 0.000 | 0.000 (896) | 0.000 (882) | 0/14 | [0.000, 0.000] | unavailable (0/0) | unavailable |
| experiment01 / qwen3-14b_g1 | 896 | 0.006 | 0.001 | 0.001 (896) | 0.006 (882) | 0/14 | [0.006, 0.006] | 1.000 (1/1) | [1.000, 1.000] |
| experiment01 / qwen3-4b_g1 | 896 | 0.000 | 0.000 | 0.000 (896) | 0.000 (882) | 0/14 | [0.000, 0.000] | unavailable (0/0) | unavailable |
| experiment01 / qwen3-8b_g1 | 896 | 0.002 | 0.000 | 0.000 (896) | 0.002 (882) | 0/14 | [0.002, 0.002] | unavailable (0/0) | unavailable |
| experiment01 / qwen3.5-0.8b_g1 | 896 | 0.000 | 0.000 | 0.000 (896) | 0.000 (878) | 4/14 | [0.000, 0.005] | unavailable (0/0) | unavailable |
| experiment01 / qwen3.5-2b_g1 | 896 | 0.000 | 0.000 | 0.000 (896) | 0.000 (879) | 3/14 | [0.000, 0.003] | unavailable (0/0) | unavailable |
| experiment01 / qwen3.5-4b_g1 | 896 | 0.001 | 0.000 | 0.000 (896) | 0.003 (881) | 1/14 | [0.003, 0.005] | unavailable (0/0) | unavailable |
| experiment01 / qwen3.5-9b_g1 | 896 | 0.000 | 0.000 | 0.000 (896) | 0.003 (881) | 1/14 | [0.003, 0.005] | unavailable (0/0) | unavailable |
| experiment01 / qwen3.6-27b-local_g1 | 896 | 0.001 | 0.000 | 0.000 (896) | 0.001 (882) | 0/14 | [0.001, 0.001] | unavailable (0/0) | unavailable |
| experiment08_validation / base14b | 1080 | 0.008 | 0.008 | 0.008 (1080) | 0.008 (1072) | 0/8 | [0.008, 0.008] | 1.000 (9/9) | [1.000, 1.000] |
| experiment08_validation / base_1p7B_e05 | 1080 | 0.001 | 0.001 | 0.000 (1080) | 0.002 (1067) | 5/8 | [0.002, 0.007] | unavailable (0/0) | unavailable |
| experiment08_validation / base_4B_e05 | 1080 | 0.005 | 0.003 | 0.003 (1080) | 0.004 (1071) | 1/8 | [0.004, 0.005] | 1.000 (3/3) | [1.000, 1.000] |
| experiment08_validation / base_8B_e05 | 1080 | 0.000 | 0.000 | 0.000 (1080) | 0.000 (1072) | 0/8 | [0.000, 0.000] | unavailable (0/0) | unavailable |
| experiment08_validation / sft_14B_f0p125 | 1080 | unavailable | unavailable | unavailable (0) | unavailable (0) | 1072/8 | [0.000, 1.000] | unavailable (0/0) | unavailable |
| experiment08_validation / sft_14B_f0p25 | 1080 | unavailable | unavailable | unavailable (0) | unavailable (0) | 1072/8 | [0.000, 1.000] | unavailable (0/0) | unavailable |
| experiment08_validation / sft_14B_f0p5 | 1080 | unavailable | unavailable | unavailable (0) | unavailable (0) | 1072/8 | [0.000, 1.000] | unavailable (0/0) | unavailable |
| experiment08_validation / sft_14B_f0p75 | 1080 | unavailable | unavailable | unavailable (0) | unavailable (0) | 1072/8 | [0.000, 1.000] | unavailable (0/0) | unavailable |
| experiment08_validation / sft_14B_f1p0 | 1080 | unavailable | unavailable | unavailable (0) | unavailable (0) | 1072/8 | [0.000, 1.000] | unavailable (0/0) | unavailable |
| experiment08_validation / sft_1p7B_f0p125 | 1080 | 0.004 | 0.004 | 0.004 (1080) | 0.004 (1072) | 0/8 | [0.004, 0.004] | 1.000 (4/4) | [1.000, 1.000] |
| experiment08_validation / sft_1p7B_f0p25 | 1080 | 0.001 | 0.001 | 0.001 (1080) | 0.000 (1071) | 1/8 | [0.000, 0.001] | unavailable (0/1) | [0.000, 1.000] |
| experiment08_validation / sft_1p7B_f0p5 | 1080 | 0.018 | 0.018 | 0.018 (1080) | 0.015 (1070) | 2/8 | [0.015, 0.017] | 0.941 (17/19) | [0.842, 0.947] |
| experiment08_validation / sft_1p7B_f0p75 | 1080 | 0.041 | 0.041 | 0.041 (1080) | 0.036 (1071) | 1/8 | [0.036, 0.037] | 0.907 (43/44) | [0.886, 0.909] |
| experiment08_validation / sft_1p7B_f1p0 | 1080 | 0.049 | 0.049 | 0.049 (1080) | 0.045 (1071) | 1/8 | [0.045, 0.046] | 0.923 (52/53) | [0.906, 0.925] |
| experiment08_validation / sft_4B_f0p125 | 1080 | 0.006 | 0.006 | 0.006 (1080) | 0.006 (1072) | 0/8 | [0.006, 0.006] | 1.000 (6/6) | [1.000, 1.000] |
| experiment08_validation / sft_4B_f0p25 | 1080 | 0.042 | 0.042 | 0.042 (1080) | 0.037 (1072) | 0/8 | [0.037, 0.037] | 0.889 (45/45) | [0.889, 0.889] |
| experiment08_validation / sft_4B_f0p5 | 1080 | 0.039 | 0.039 | 0.039 (1080) | 0.030 (1071) | 1/8 | [0.030, 0.031] | 0.780 (41/42) | [0.762, 0.786] |
| experiment08_validation / sft_4B_f0p75 | 1080 | 0.037 | 0.037 | 0.037 (1080) | 0.028 (1065) | 7/8 | [0.028, 0.035] | 0.909 (33/40) | [0.750, 0.925] |
| experiment08_validation / sft_4B_f1p0 | 1080 | 0.093 | 0.093 | 0.093 (1080) | 0.069 (1065) | 7/8 | [0.069, 0.076] | 0.796 (93/100) | [0.740, 0.810] |
| experiment08_validation / sft_8B_f0p125 | 1080 | 0.014 | 0.014 | 0.013 (1080) | 0.011 (1072) | 0/8 | [0.011, 0.011] | 0.786 (14/14) | [0.786, 0.786] |
| experiment08_validation / sft_8B_f0p25 | 1080 | 0.069 | 0.069 | 0.069 (1080) | 0.062 (1072) | 0/8 | [0.062, 0.062] | 0.880 (75/75) | [0.880, 0.880] |
| experiment08_validation / sft_8B_f0p5 | 1080 | 0.071 | 0.071 | 0.071 (1080) | 0.059 (1067) | 5/8 | [0.059, 0.063] | 0.875 (72/77) | [0.818, 0.883] |
| experiment08_validation / sft_8B_f0p75 | 1080 | 0.082 | 0.082 | 0.082 (1080) | 0.063 (1062) | 10/8 | [0.062, 0.072] | 0.848 (79/89) | [0.753, 0.865] |
| experiment08_validation / sft_8B_f1p0 | 1080 | 0.096 | 0.096 | 0.096 (1080) | 0.073 (1065) | 7/8 | [0.073, 0.079] | 0.804 (97/104) | [0.750, 0.817] |

Full hidden bounds use declared cells minus no-test cells; kernel-conditioned bounds use all kernel-verified cells, retaining unavailable outcomes in the bounds. The 5,400 unavailable factor cells remain explicit in the frozen manifest.

## Inspected disagreements

The prescribed ranking selects 10 high-score failures (all Claude Opus 5) and 10 low-score successes (all Leanstral); these are selected extremes, not a random audit. Six high-score cases map to precondition/postcondition helpers and four have only partial type applicability. All ten low-score cases have IC_tests=0 and no self-test declarations despite passing the hidden suite. Detailed source, bridge and log hashes are in [disagreements_e12.json](expt_v1/results/disagreements_e12.json).

**Post-lock implementation limitation:** the frozen identifier lexer omits question-mark suffixes, merging legal Lean names such as a core and its optional-result wrapper. This can defeat direct-name matching and suppress reference counts, contributing to helper selection in the inspected cases. The adapter and outcomes remain frozen; this requires a corrected prospective version. The A2 steps 1–2 sensitivity still includes partial type-applicability failures. Consequently these results validate association with the implemented test pipeline, not an error-free measure of semantic correctness.

| Group | System / task | SCSC | Hidden result | Inspection |
|---|---|---:|---|---|
| high_score_failing | claude-opus-5-max / concurrent_set_synthetic__my_hazard_pointer_can_free | 1.000 | 0 | Step 4 chose preCondition (nonnegative protector count), not canFree (zero protectors); 2/8 tests pass. The source contains the intended core and an Option wrapper. The frozen lexer collapses the question-mark suffix, also suppressing core reference counts. This is a helper-mapping failure, not evidence that the intended implementation is wrong. |
| high_score_failing | claude-opus-5-max / concurrent_set_synthetic__my_lww_register_pick_left | 1.000 | 0 | Step 4 chose the nonnegative-timestamp preCondition instead of pickLeft, which compares timestamps; 5/8 tests pass. The source also has a question-mark-suffixed wrapper that the lexer merges with the core name. Failing tests exercise helper selection, not the intended core. |
| high_score_failing | claude-opus-5-max / easy_set__1_myadd | 1.000 | 0 | Same-name mapping reaches an Except-returning addition wrapper. Only the commutativity test is evaluable and passes (1/14); 13 tests cannot elaborate scalar expected values or nested calls at the wrapper type. No evaluated test is false. |
| high_score_failing | claude-opus-5-max / easy_set__33_myminimum | 1.000 | 0 | The named minimum returns Option Int, so seven scalar-result tests cannot elaborate. The imperative gold name maps by unique type to scalar minList, whose five tests pass (5/12 total). No evaluated test is false. |
| high_score_failing | claude-opus-5-max / humaneval_set__humaneval_22_filter_integers | 1.000 | 0 | The candidate filters a heterogeneous PyVal list, while the gold suite supplies integer lists. Twelve tests fail type elaboration; the empty-list inequality alone passes (1/13). No evaluated test is false. |
| high_score_failing | claude-opus-5-max / hypervisor_set_synthetic__my_interrupt_route | 1.000 | 0 | Steps 4/3 select postCheck, a conjunction of correctness checks, instead of myInterruptRoute; 5/8 tests pass. Core and imperative definitions have question-mark-suffixed wrappers that the frozen lexer merges with their unsuffixed names, defeating direct-name selection. False results concern the selected helper. |
| high_score_failing | claude-opus-5-max / memory_bugs_set_synthetic__my_bump_alloc_fits | 1.000 | 0 | Step 4 selects preCondition, which checks nonnegative inputs, instead of the capacity comparison; 4/7 tests pass. The intended core is present, but question-mark-suffixed wrappers collide in the frozen lexer and remove unique name/reference matches. This is a helper-mapping failure. |
| high_score_failing | claude-opus-5-max / os_embedded_set_synthetic__my_power_transition_ok | 1.000 | 0 | Step 4 selects preCondB (states are in range), not the allowed-transition predicate; 6/9 tests pass. The intended core is present; its question-mark-suffixed wrapper collides in the frozen lexer. Failures for disallowed transitions are helper-mapping failures. |
| high_score_failing | claude-opus-5-max / regulated_set_synthetic__my_dose_interval_ok | 1.000 | 0 | Step 4 selects PostB, which checks that the implementation obeys its specification, instead of gate (elapsed interval comparison); 4/8 tests pass. The intended gate and Option-returning implementation are present. The reference-count rule selects a correctness helper whose truth is not the requested decision. |
| high_score_failing | claude-opus-5-max / security_set__security_6858__safe__104_unsafehttpparse_safe | 1.000 | 0 | Nine of twelve tests pass. The three empty-list tests cannot infer the candidate polymorphic element type; the source compares list length to buffer size. No evaluated test is false. |
| low_score_passing | leanstral / aerospace_set_synthetic__my_arming_interlock | 0.000 | 1 | The mapped implementation computes three-input conjunction for arming; all 7/7 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.7. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / aerospace_set_synthetic__my_safing_vote | 0.000 | 1 | The mapped implementation computes three-input disjunction for safing; all 7/7 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.3. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / aerospace_set_synthetic__my_sensor_watchdog_fresh | 0.000 | 1 | The mapped implementation computes timestamp inclusion in the freshness interval; all 5/5 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.8. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / aerospace_set_synthetic__my_tmr_voter | 0.000 | 1 | The mapped implementation computes Boolean majority voting; all 7/7 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.7. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / compilers_set_real__my_cpython_dis_jump_target | 0.000 | 1 | The mapped implementation computes relative/absolute jump target arithmetic with an optional result; all 7/7 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.6. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / concurrent_set_real__my_cas_success | 0.000 | 1 | The mapped implementation computes equality for compare-and-swap success; all 8/8 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.8. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / concurrent_set_real__my_h2_flow_window_after_send | 0.000 | 1 | The mapped implementation computes natural-number window subtraction; all 8/8 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.2. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / concurrent_set_synthetic__my_lww_register_pick_left | 0.000 | 1 | The mapped implementation computes left timestamp greater than or equal to right; all 8/8 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.4. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / concurrent_set_synthetic__my_rcu_epoch_can_reclaim | 0.000 | 1 | The mapped implementation computes reader epoch strictly newer than retired epoch; all 8/8 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.8. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |
| low_score_passing | leanstral / concurrent_set_synthetic__my_vector_clock_merge_le_target | 0.000 | 1 | The mapped implementation computes four-way conjunction for componentwise vector-clock bounds; all 8/8 hidden tests pass. Recorded IC_tests=0 forces SCSC=0 despite IC_proofs=1 and FSC=0.1. Source inspection found no example declarations or evaluation commands; it contains proofs. The score penalizes missing self-tests, not failure on these hidden tests. |

## Validation, provenance and limitations

A1 reproduced all 11 published source aggregates under their own conventions and all 100 sampled compile statuses. Primary joins retain 9,678 hash-bound cells, 176 flagged unique paths, and two missing files. The extraction contains 10,534 tests on 882/896 gold tasks; 14 tasks have no extractable tests.

Final controls: C1 591/591 tests; C2 48/50 recovered tasks; C3 44/50 compiling mutants detected; C4 49/50 wrong-task pairs rejected. Thresholds remain 98%, 95%, 60% with at least 50 compiling mutants, and 95% respectively. These are deterministic checks on the fixed 50-task sample, p-val=n/a.

Evaluation completed all 43,840 declared cells (9,856 primary; 8,064 experiment 01; 25,920 experiment 08 validation), with 5,386 unique execution jobs, zero timeouts and zero infrastructure retries. Repository verification: 237 passed / 24 skipped; experiment-local checks: 32 passed. Outcome SHA-256: `e21a4a512784fff53a61af67cd609cc11548d70feb9b2ba6ca24904f627bdbb9`. See [completion verification](expt_v1/results/evaluation_verification.json) and [protocol lock](expt_v1/results/protocol_lock.json).

Historical failures and implementation corrections remain in [the checkpoint](expt_v1/CKPT_e12.md), with round-1 through round-5 receipts. A1 resolved aggregation conventions; A2 resolved identical-type alternatives before the protocol lock or any real-candidate hidden outcome. The extractor expands only closed literal aliases used exclusively as test inputs; all 10,534 tests and their expected values are retained. Candidate and gold source files and factors were never edited. All three forecasts remain frozen.

The outcome is finite-test success, not a proof of full program correctness or a human acceptance rating. Missing applicability is bounded rather than silently scored zero. Core and IndustrySet results, missing-factor sensitivity and unambiguous-mapping sensitivity are descriptive and do not replace the frozen verdicts. Next versions must repair and prospectively validate identifier parsing and entry-point selection, then cover hidden proofs and the agent-spec v8 panel.

**TLDR-end:** [rl4cv: 12_scsc_vs_hidden_gold_tests_vbv1_across_systems] Hidden gold-test agreement is fully measured under the frozen protocol and amendments; all three frozen predictions hold for the implemented adapter; mapping limitations qualify correctness claims.

**Snapshot:**
```text
P1 Spearman: 0.891
P2 area: 0.640
P3 within-system Spearman: 0.151
Applicable: 3224/4674
Evaluated cells: 43840/43840
```
