# Matched step-658 test results — 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/results.md>

**TLDR:** Qwen3 1.7B, 4B, 8B and 14B are compared after identical supervised fine-tuning (SFT): 1,315 examples, 658 updates and 5,752,936 loss tokens on VeriBench V1; execution status is **PARTIAL**.

**Last updated:** 10-13-2026 17:51 PDT

**Status:** PARTIAL — Vals managed AWS unavailable for BrandoMiranda-fellow; route controls unadmitted, generation stopped under the runbook partial rule

All scores are on a 0–1 scale. IC_tests is the kernel test factor; IC_proofs is the fraction of stated theorems proved with allowed axioms; fsc_compiled is compile-gated formal specification coverage from the validated judge. SCSC (smooth conjunctive score for code verification) is the geometric mean of these three factor means on one common known cohort. Kernel binary success additionally requires the unchanged strict proof and non-vacuity checks.

Every interval below uses 10,000 task-bootstrap resamples, seed 0, carrying all eight samples together; **p-val=n/a** (interval estimation only). These intervals cover this single training run, not training-seed variation. Incomplete summaries use their measured cohort, retain unknowns in declared counts, and provide full-manifest bounds in the evaluation JSON.

## Matched trained and Base systems

| Size / system | Scope | IC_tests [95%] | IC_proofs [95%] | fsc_compiled [95%] | SCSC [95%] | Kernel binary [95%] | Known factors / declared | Known kernel / declared |
|---|---|---|---|---|---|---|---|---|
| 1.7B `test_sft_1p7B_f1p0` | all | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 1776 | 0 / 1776 |
| 1.7B `test_sft_1p7B_f1p0` | core | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 1216 | 0 / 1216 |
| 1.7B `test_sft_1p7B_f1p0` | industryset | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 560 | 0 / 560 |
| 1.7B `base_1p7B_e05` | all | 0.0000 [0.0000, 0.0000] | 0.0001 [0.0000, 0.0002] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1776 / 1776 | 1776 / 1776 |
| 1.7B `base_1p7B_e05` | core | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1216 / 1216 | 1216 / 1216 |
| 1.7B `base_1p7B_e05` | industryset | 0.0000 [0.0000, 0.0000] | 0.0003 [0.0000, 0.0008] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 560 / 560 | 560 / 560 |
| 4B `test_sft_4B_f1p0` | all | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 1776 | 0 / 1776 |
| 4B `test_sft_4B_f1p0` | core | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 1216 | 0 / 1216 |
| 4B `test_sft_4B_f1p0` | industryset | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 560 | 0 / 560 |
| 4B `base_4B_e05` | all | 0.0011 [0.0000, 0.0028] | 0.0006 [0.0000, 0.0017] | 0.0006 [0.0000, 0.0016] | 0.0007 [0.0000, 0.0019] | 0.0006 [0.0000, 0.0017] | 1776 / 1776 | 1776 / 1776 |
| 4B `base_4B_e05` | core | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1216 / 1216 | 1216 / 1216 |
| 4B `base_4B_e05` | industryset | 0.0036 [0.0000, 0.0089] | 0.0018 [0.0000, 0.0054] | 0.0020 [0.0000, 0.0052] | 0.0023 [0.0000, 0.0061] | 0.0018 [0.0000, 0.0054] | 560 / 560 | 560 / 560 |
| 8B `test_sft_8B_f1p0` | all | 0.1120 [0.0828, 0.1441] | 0.1120 [0.0828, 0.1441] | 0.1106 [0.0815, 0.1422] | 0.1116 [0.0823, 0.1435] | 0.1120 [0.0828, 0.1441] | 1776 / 1776 | 1776 / 1776 |
| 8B `test_sft_8B_f1p0` | core | 0.1637 [0.1225, 0.2072] | 0.1637 [0.1225, 0.2072] | 0.1615 [0.1206, 0.2044] | 0.1629 [0.1219, 0.2062] | 0.1637 [0.1225, 0.2072] | 1216 / 1216 | 1216 / 1216 |
| 8B `test_sft_8B_f1p0` | industryset | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 560 / 560 | 560 / 560 |
| 8B `base_8B_e05` | all | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1776 / 1776 | 1776 / 1776 |
| 8B `base_8B_e05` | core | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1216 / 1216 | 1216 / 1216 |
| 8B `base_8B_e05` | industryset | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 560 / 560 | 560 / 560 |
| 14B `test_sft_14B_f1p0` | all | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 1776 | 0 / 1776 |
| 14B `test_sft_14B_f1p0` | core | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 1216 | 0 / 1216 |
| 14B `test_sft_14B_f1p0` | industryset | unavailable | unavailable | unavailable | unavailable | unavailable | 0 / 560 | 0 / 560 |
| 14B `base14b` | all | 0.0028 [0.0006, 0.0056] | 0.0028 [0.0006, 0.0056] | 0.0015 [0.0002, 0.0034] | 0.0023 [0.0004, 0.0045] | 0.0028 [0.0006, 0.0056] | 1776 / 1776 | 1776 / 1776 |
| 14B `base14b` | core | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1216 / 1216 | 1216 / 1216 |
| 14B `base14b` | industryset | 0.0089 [0.0018, 0.0179] | 0.0089 [0.0018, 0.0179] | 0.0048 [0.0005, 0.0107] | 0.0073 [0.0017, 0.0144] | 0.0089 [0.0018, 0.0179] | 560 / 560 | 560 / 560 |

Full-manifest bounds below are worst-case bounds over unknown factors, not confidence intervals.

| System | Scope | SCSC full-manifest bounds |
|---|---|---|
| `test_sft_1p7B_f1p0` | all | [0.0000, 1.0000] |
| `test_sft_1p7B_f1p0` | core | [0.0000, 1.0000] |
| `test_sft_1p7B_f1p0` | industryset | [0.0000, 1.0000] |
| `test_sft_4B_f1p0` | all | [0.0000, 1.0000] |
| `test_sft_4B_f1p0` | core | [0.0000, 1.0000] |
| `test_sft_4B_f1p0` | industryset | [0.0000, 1.0000] |
| `test_sft_14B_f1p0` | all | [0.0000, 1.0000] |
| `test_sft_14B_f1p0` | core | [0.0000, 1.0000] |
| `test_sft_14B_f1p0` | industryset | [0.0000, 1.0000] |

The 1.7B and 4B step-658 checkpoints failed version 1 validation format gates; their values are matched-budget diagnostics, not established reinforcement-learning warm starts.

## SFT minus Base paired differences

| Size | Scope | SCSC difference [95%] | Kernel binary difference [95%] | Missing factor pairs | Missing kernel pairs |
|---|---|---|---|---|---|
| 1.7B | all | unavailable | unavailable | 1776 | 1776 |
| 1.7B | core | unavailable | unavailable | 1216 | 1216 |
| 1.7B | industryset | unavailable | unavailable | 560 | 560 |
| 4B | all | unavailable | unavailable | 1776 | 1776 |
| 4B | core | unavailable | unavailable | 1216 | 1216 |
| 4B | industryset | unavailable | unavailable | 560 | 560 |
| 8B | all | 0.1116 [0.0823, 0.1435] | 0.1120 [0.0828, 0.1441] | 0 | 0 |
| 8B | core | 0.1629 [0.1219, 0.2062] | 0.1637 [0.1225, 0.2072] | 0 | 0 |
| 8B | industryset | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0 | 0 |
| 14B | all | unavailable | unavailable | 1776 | 1776 |
| 14B | core | unavailable | unavailable | 1216 | 1216 |
| 14B | industryset | unavailable | unavailable | 560 | 560 |

## Scaling at the matched token budget

| Adjacent sizes | Scope | SCSC difference [95%] | Kernel binary difference [95%] | Missing factor pairs |
|---|---|---|---|---|
| 14B-8B | all | unavailable | unavailable | 1776 |
| 14B-8B | core | unavailable | unavailable | 1216 |
| 14B-8B | industryset | unavailable | unavailable | 560 |
| 4B-1.7B | all | unavailable | unavailable | 1776 |
| 4B-1.7B | core | unavailable | unavailable | 1216 |
| 4B-1.7B | industryset | unavailable | unavailable | 560 |
| 8B-4B | all | unavailable | unavailable | 1776 |
| 8B-4B | core | unavailable | unavailable | 1216 |
| 8B-4B | industryset | unavailable | unavailable | 560 |

## Version 1 step-334 diagnostic

The 14B step-334 checkpoint used 2,884,708 loss tokens and is excluded from the matched table. Its original values and ratings are read unchanged.

| Scope | IC_tests [95%] | IC_proofs [95%] | fsc_compiled [95%] | Step-334 SCSC [95%] | Known / declared | Step-658 minus step-334 SCSC [95%] | Kernel binary difference [95%] |
|---|---|---|---|---|---|---|---|
| all | 0.0873 [0.0653, 0.1098] | 0.0873 [0.0653, 0.1098] | 0.0861 [0.0645, 0.1089] | 0.0869 [0.0651, 0.1095] | 1776 / 1776 | unavailable | unavailable |
| core | 0.1258 [0.0954, 0.1571] | 0.1258 [0.0954, 0.1571] | 0.1242 [0.0943, 0.1558] | 0.1253 [0.0952, 0.1568] | 1216 / 1216 | unavailable | unavailable |
| industryset | 0.0036 [0.0000, 0.0089] | 0.0036 [0.0000, 0.0089] | 0.0036 [0.0000, 0.0089] | 0.0036 [0.0000, 0.0089] | 560 / 560 | unavailable | unavailable |

## Frozen forecasts

The forecast hash was verified before scoring. PASS, FAIL and UNRESOLVED are reported equally; F1 tests validation-rate inclusion in the test interval, F2 tests whether each trained-minus-Base interval lower bound exceeds zero, and F3 tests strict size ordering of the trained score point estimates. These are the frozen forecast criteria, not additional hypothesis tests.

| Forecast | Verdict | Evidence |
|---|---|---|
| F1/test_sft_14B_f1p0 | **UNRESOLVED** | unavailable |
| F1/test_sft_1p7B_f1p0 | **UNRESOLVED** | unavailable |
| F1/test_sft_4B_f1p0 | **UNRESOLVED** | unavailable |
| F2/test_sft_14B_f1p0/SCSC | **UNRESOLVED** | unavailable |
| F2/test_sft_14B_f1p0/kernel_binary | **UNRESOLVED** | unavailable |
| F2/test_sft_1p7B_f1p0/SCSC | **UNRESOLVED** | unavailable |
| F2/test_sft_1p7B_f1p0/kernel_binary | **UNRESOLVED** | unavailable |
| F2/test_sft_4B_f1p0/SCSC | **UNRESOLVED** | unavailable |
| F2/test_sft_4B_f1p0/kernel_binary | **UNRESOLVED** | unavailable |
| F3 | **UNRESOLVED** | unavailable, unavailable, 0.1116, unavailable |

## Coverage, ratings and charges

| New system | Known factors / declared | Ratings measured / declared | Reported judge charge |
|---|---|---|---|
| `test_sft_1p7B_f1p0` | 0 / 1,776 | 0 / not frozen | not reported |
| `test_sft_4B_f1p0` | 0 / 1,776 | 0 / not frozen | not reported |
| `test_sft_14B_f1p0` | 0 / 1,776 | 0 / not frozen | not reported |

Route controls measured **0/50** ratings. The fixed audits require **1,080** test ratings over 180 files; all are missing because candidate files were unavailable. Additional compile-gated rating eligibility remains unknown for **5,328** cells. The test pack was not frozen or admitted. [Complete coverage inventory](results/terminal_coverage_v2.json) lists every missing generation, fixed-audit/control rating and unresolved eligibility identity. Both failed admissions were positively reconciled as unserved; no model request was admitted.

The current CLI authenticates to `BrandoMiranda-fellow`, but the server has no Daytona mapping and returns HTTP 403: managed AWS access is unavailable for this organization. [Blocker evidence](results/judge_route_blocker_v2.json) records the supported-client checks. Vals must restore this existing route before controls or test judging can resume. No substitute funding or model was used.

New test ratings measured: 0/not yet frozen. Reported test subtotal: not reported; route controls: not reported. Missing test charge receipts: 0; unknown charges are not asserted to be zero. Reused-system historical charges are not charged again. Host compute costs were not measured.

Every unknown factor cell is listed without truncation in [test_eval_v2.json](results/test_eval_v2.json); every matched and diagnostic cell is in [test_factor_cells_v2.csv](results/test_factor_cells_v2.csv). When built, the judge pack records omissions and fixed-audit membership in `results/judge/judge_pack_test.json`. Available admitted-rating receipts are retained in `results/judge/harvests/`; every missing or unadmitted test rating is separately enumerated in [unknown_judge_ratings_v2.json](results/unknown_judge_ratings_v2.json). No missing cell is treated as a measured zero.

The validated judge is GPT-6 Sol high plus Claude Opus 5.5 max, three ratings per member/file; the mean of member medians is divided by five. Audit coverage on noncompiling files remains diagnostic. Human agreement on these student outputs, training-seed variation, and independent repeatability of the final ensemble were not measured.

## Verification and provenance

Full `make test`: 338 passed, 4 skipped in 293.25 seconds (terminal run). `git diff --check` passes. All six reused systems reproduce every original scope field exactly, including means, bounds and intervals. The independent CSV summarizer checks every factor mean and SCSC across all nine systems and three scopes (108 checks); unknown-only cohorts are checked as unavailable. Version 1 files remain unchanged.

Scientific inputs: [protocol](PROTOCOL_v2.md), [input checks](results/inputs_check.json), [manifest](results/test_manifest_v2.json), [route identity](results/route_identity_v2.json), [forecast scores](results/forecast_evaluation_v2.json), [independent check](results/independent_factor_check_v2.json). Runtime state and failed attempts stay under `/lfs/skampere1/0/brando9/rl4cv_e08/v2/`. The [checkpoint log](CKPT_e08v2.md) retains launch, environment recovery and publication history.

Closeout: the partial report was published at `c7940fe` and its remote bytes verified. The required PARTIAL DONE email was sent once at 17:51:20 PDT with the specified team CCs ([receipt](results/done_email_receipt_v2.json)). All owned jobs/services, leases, port claims and cron entries are retired ([teardown](results/teardown_v2.json)); the resumable checkpoint remains.

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2 matched step-658 test] The matched-budget test evaluation is partial; measured and unknown cells, paired comparisons and every forecast are reported above.

**Snapshot:**

```text
Status: PARTIAL — Vals managed AWS route blocked
New measured cells: 0 / 5,328
Reused matched cells: 8,880 / 8,880
Control ratings: 0 / 50
Fixed-audit ratings: 0 / 1,080
New forecast verdicts: UNRESOLVED
```
