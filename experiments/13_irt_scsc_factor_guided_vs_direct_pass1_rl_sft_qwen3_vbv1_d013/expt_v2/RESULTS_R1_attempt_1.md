# R1 attempt 1: complete train-only measurement diagnostic

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_R1_attempt_1.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 passes R1 attempt 1: 400/400 train cells measured, 400/400 historical oracle value/status matches, no untyped inconsistency, and fixture coverage for every rejection cause above 1%.

Created: 10-13-2026 13:05 PDT
Status: **PASS**, development attempt 1 of at most 5 under A1.

## Selection and complete-path evidence

Seed 1302001 sampled cell identifiers only: **300 of 8,900 rejected train cells** and **100 of 4,036 measured train cells**, from the complete **12,936-cell train allowlist**. The selected 400 cells span **292 tasks / 254 task groups**. The rejected/accepted strata were deliberately sampled at different rates; this cohort is not an estimate of the full population's old measured share. No validation or test source was opened.

The unchanged version 1 `opaque_base_audit.reproduce` ran its full path (vacuity, parser-backed adapter, scorer and PartialCredit) on every selected cell. Phase-labelled exceptions and full subprocess streams were retained. Version 2 separately measured the same unchanged source using the independent historical oracle and the accepted attempt-2 elaborator. No early rejection path was removed from the version 1 comparison.

## Rejection cause table

The denominator is exactly **300 previously rejected train cells**, as PLAN §4 requires.

| Version 1 cause | Count / rejected cells | Share [Wilson 95% interval] | Authored coverage |
|---|---:|---|---|
| `identity_duplicate` | 1/300 | 0.33% [0.06, 1.86] | duplicate_obligation |
| `parser_parse_error` | 296/300 | 98.67% [96.62, 99.48] | truncated_syntax |
| `vacuity_unparseable_type` | 3/300 | 1.00% [0.34, 2.90] | unparseable_compiling, unparseable_noncompiling |

These are the requested descriptive binomial Wilson intervals; multiple cells can share a task, so the intervals do not account for within-task dependence. No hypothesis test was specified (p-val=n/a). The parse-error branch is the only branch **above** 1%; it is covered. The 1% vacuity branch and the duplicate-identity branch also have authored coverage.

## Acceptance and limits

- **Measured:** 400/400; no resource-limit or transient-infrastructure exclusion, no untyped missing cell.
- **Oracle equality:** 400/400 values **and statuses** matched their source-specific historical readbacks.
- **Consistency:** 400/400 `consistent`; no untyped discrepancy; no inequality was inferred from factor equality alone.
- **Fixture coverage:** all branches above 1% covered, with mappings fixed before execution.
- **Verification:** `E13_REQUIRE_LEAN_INTEGRATION=1 make test`: **286 passed, 23 skipped**, 185.82 seconds; includes three new train-isolation/admission tests and all seven required Lean integration cases.
- All 400 selected cells had one per-cell attempt in the persistent ledger; the development attempt did not resample or replace any cell.

This validates measurement on the sampled train cohort. It neither reproduces all 38,784 historical cells nor establishes predictive usefulness or reinforcement-learning efficacy. L1v2 must still bind the complete measurement and prediction setup before validation/test factors are computed.

## Measured memory and cost

Every complete cell sampled its worker/descendant resident memory every 0.1 second and retained child maximum resident memory. Across **400 cells**, the 99th-percentile peak was **6.452 GiB**, maximum **6.459 GiB**. The peak statistic conservatively combines tree-sum observations and the child maximum; shared pages may be counted more than once. Very short peaks between samples can be missed.

The first serial cell peaked at **6,924,185,600 bytes**. PLAN §7's formula admitted 48 workers, with a **64-GiB virtual-address limit per cell** and a verified systemd aggregate memory ceiling of **1,049,300,488,192 bytes**. Admission also checked the 25%-available floor and current headroom. No other owner's processes were killed.

Mean complete-cell wall time was **18.298 seconds**, summed across cells **7319.244 seconds** (includes both version 1 and version 2 paths; it is not elapsed batch wall time or processor time). Scaling that combined-path cost to 38,784 cells at 48 workers gives **4.11 hours**, or **5.13 hours with 25% reserve**. This is a conservative planning extrapolation, not a measured full-reproduction runtime; different source complexity and shared-node load can change it. Concurrency and aggregate headroom will be recalculated at launch.

## Artifacts and next step

[Procedure](R1_attempt_1/README.md), [selection lock](R1_attempt_1/selection_lock.json), [execution lock](R1_attempt_1/execution_lock.json), [memory admission](R1_attempt_1/memory_admission.json), [machine-readable result and evidence digests](R1_attempt_1/result.json). Full private cell evidence: `/lfs/skampere1/0/brando9/rl4cv_e13v2/R1_attempt_1`. The full result-stream digest is `c0011f2d09c9717f738276b5cdcc6d5e4a40c6bc0ca3e6edbdd5401bc35eb82a`.

Next: implement and validate the prespecified prediction configuration, freeze L1v2 with the complete manifests/folds and carried F0v2/F1v2 forecasts, then execute R2 with its test subset isolated in an opaque process. A1's development retry permission ends at L1v2.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2's train-only diagnostic passed 400/400; historical reproduction remains unexecuted and awaits L1v2.
**Snapshot:** R1_attempt_1 PASS; 400/400 measured and oracle-equal; 296/300 parse-error rejections; zero untyped inconsistencies; R2 0/38,784.
