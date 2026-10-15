# Experiment 13 v2-S2: prospective selected-test independent coverage analysis

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/COVERAGE_ANALYSIS_S2_METHOD.md>

**TLDR:** The independent-coverage analysis uses the already specified sample index 0 on all 222 test tasks and every eligible arm/seed. It joins saved hidden-test and validated formal-specification coverage to the exact selected-checkpoint scoring evidence, preserves missing observations and reports descriptive differences with uncertainty. This is prospective implementation preparation: no actual test input or outcome has been opened.

The primary strict analysis and its frozen implementation remain unchanged. This separate secondary analysis implements PROTOCOL section 7 and the sample choice already published in [EVALUATION_S2_METHOD.md](EVALUATION_S2_METHOD.md). It does not admit a test execution, change a sampler, select another sample or establish noninferiority.

## Population and evidence

- All 222 test tasks remain declared: 152 core and 70 IndustrySet, with paired seeds 13011, 13012 and 13013. The eligible arm set comes from L2; under A6 it is A, B and P.
- Each run uses its one validation-selected checkpoint and the same sample index 0 for the independent metrics. Main failures and unavailable selections retain all their missing samples with the published reason.
- [selected_coverage_join.py](selected_coverage_join.py) first applies the unchanged strict evidence join. Independent execution locks must bind the same L2, selected checkpoint and strict score; every physical input hash and every cell identity must match. Hidden-test summaries must match their retained measurement receipts and verified cleanup.
- Formal-specification coverage retains the frozen compilation gate and the validated ensemble's three repeats for each of two members. Known compile failure scores zero; unknown compilation or incomplete ratings remain unavailable. A missing whole route requires a published same-checkpoint reason. It never substitutes another judge.
- The theorem-count diagnostic uses the original score's stated-theorem denominator. It is not a count of proved theorems or a substitute for either independent coverage measure.

## Statistics and limitations

[selected_coverage_analysis.py](selected_coverage_analysis.py) reports each metric separately for the pooled population, core and IndustrySet. It retains observed/declared counts, per-seed means for complete populations, paired effects B−A, B−P and P−A, and the additional C contrasts only when C is eligible.

For complete observations, 95% intervals use the existing primary analysis's paired seed/task-group bootstrap: 10,000 draws, seed 1302301, conditional on the selected checkpoints. These are descriptive three-seed intervals, not evidence of a confirmed improvement. No hypothesis test or p-value is introduced.

Missing coverage values in [0,1] produce full-manifest bounds; no full-population point estimate or inferential interval is fabricated. The observed common-cohort effect is separately labeled. Missing theorem counts retain a nonnegative lower bound and an unbounded upper side, as appropriate; no maximum theorem count is invented. Noninferiority remains **not established**, since no justified margin or precision requirement was registered. This directly retains PROTOCOL's H5 limitation.

## Publication and one analysis

Before main, publish a `SELECTED_TEST_COVERAGE_ANALYSIS` method lock binding the task/group/domain metadata, eligible arms, seeds, fixed sample, bootstrap seed and implementation dependencies. L2 must bind that exact method and those sources.

After the relevant selected-test results are published, a separate `SELECTED_TEST_COVERAGE_ANALYSIS_INPUTS` lock binds every run and raw receipt. [selected_coverage_analysis_driver.py](selected_coverage_analysis_driver.py) verifies both locks and all evidence before exclusively creating its output directory. It saves the complete joined rows and one result; it cannot overwrite or silently repeat an existing analysis.

The added code is independent of the live technical-gate lock. Validation uses authored populations and receipts, including full missing runs, unequal independent effects, compile-gated ratings, changed checkpoint/input rejection, actual paired bootstrap behavior and one-analysis finality. No model call, device claim, fit or real test measurement is part of this preparation.

Validation on 10-15-2026: 39 focused checks passed in 21.80 seconds; required Lean integration passed 1,157 tests with 3 skipped, zero failures, direct exit 0 in 512.90 seconds ([receipt](selected_coverage_analysis_publication_test.json)).
