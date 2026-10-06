# Live results for the diagnostic intervention study

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/results.md>

**TLDR:** All 24 authored checker controls passed, but external applicability is 0/24 against the 20/24 gate; no repair or training benefit has been measured.

**Status:** BOUNDED ENGINEERING STUDIES COMPLETE — external endpoint applicability failed; repair and training remain NOT ADMITTED.

**Last updated:** 10-06-2026.

The authored checker controls are complete: 24/24 measured cells match their frozen expectations. The external applicability study found 0/24 tasks supported by the required generic Lean adapter, below the predeclared 20/24 engineering gate. These results support checker engineering and an applicability limitation; they do not measure a causal repair benefit.

| Phase | State | Evidence |
|---|---|---|
| Interpretation and detailed plan | DONE | [README](README.md), [PLAN](PLAN.md), [METRICS](METRICS.md), [sources](sources/context.md) |
| Frozen input inventory | DONE | Four inputs, 6,556,256 bytes; all hashes match their recorded committed VeriBench sources |
| Remote deterministic audit | DONE | [Readable report](expt_v1/results/RESULTS_existing_artifacts.md), [data](expt_v1/results/audit.json), [receipt](expt_v1/results/execution_receipt.json) |
| Authored endpoint checker controls | DONE | [Immutable-row reconciliation](expt_v2/endpoint_validation/results_2026-10-06T0734Z_reconciliation.json): 24/24 measured and matching; original 20 rows preserved, four missing cells completed |
| External endpoint applicability | DONE, FAILED GATE | [Version-3 findings](expt_v3/results.md): 0/24 supported adapters versus 20/24 required; missing support is not evidence that tasks are unsolvable |
| Matched-cost repair comparison | NOT ADMITTED | 0/192 repair cells and 0/1,296 judge-member calls; no independent repair outcomes |
| Environment/reward training | NOT ADMITTED | Candidate-only partitions 141/24/24; experiment02 readiness is NOT_ADMITTED, forecast NOT_FROZEN, trajectories 0/4 |

The [version-3 report](expt_v3/results.md) records the solved-reference alternative and its limitations: original external source bytes compiled for 22/24 tasks, but only 6/24 original reference theorems passed strict kernel trust, 16/24 used forbidden `sorryAx`, and 2/24 were unknown after compilation failure. No reference was edited or silently promoted to accepted status. These are fixed engineering panels; uncertainty intervals and hypothesis tests are not applicable.

## Historical existing-artifact audit

The zero-model-call audit below completed on `skampere1.stanford.edu` with exit code 0 on 10-05-2026. Its original inventory, checks and cost scope remain unchanged.

## Measured inventory and decision

- **5,420 saved rows**, **4,444 with all three factors present**. These are finite-file counts, not sampled population estimates; confidence intervals and p-val=n/a.
- Original VeriBench version-1 snapshot: **5,376 / 6,272 declared cells**, with **896 absent** (the `claude-opus-5-max` configuration in this saved snapshot). This does not establish the status of live or later jobs. Core 614 and IndustrySet 282 panels are accounted for separately per model in the report.
- Other saved conditions: **35 original version-2 rows**, **2 separate recovery rows**, and **7 multifile rows**. The audit does not reconstruct their full task manifests or combine these conditions.
- Historical diagnostic inputs: **3,112 adapter rows** and **3,112 replay-pair rows**. Adapter labels are found 1,061; name_only 776; type_mismatch 677; failed 598. These labels do not certify semantic adapters or strict kernel trust. Replay labels are retained only as historical observations.
- **Independent-outcome correlation: NOT IDENTIFIABLE from selected inputs.** No accepted independently measured reference-test/reference-obligation success endpoint is available. A correlation with SCSC's own factors would not answer the question.

SCSC means Smooth Conjunctive Score for Code verification. Old replay contains a documented transitive-axiom trust caveat; this run does not rerun or accept those proofs. The current paper and this repository also differ in dataset aggregation order. Both limitations are explicit dependencies before new scored causal comparisons.

## Execution and verification

- Dedicated remote artifact directory: `/lfs/skampere1/0/brando9/rl4cv_azalia_audit/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/`.
- Named session: `rl4cv-azalia-artifact-audit`; deterministic Python only, bounded by a 300-second timeout. Its recorded start and finish are within the same second; no model worker or graphics processor allocation was launched.
- **0 new model calls, 0 graphics processor hours, $0 incremental provider charges.** This describes the audit, not the prior studies' costs or the conversation's subscription usage.
- Input, script, protocol and output hashes verified locally against the remote receipt. All four inputs also match bytes at the recorded upstream Git revision. Frozen protocol remains unchanged after measurement.
- Experiment safeguard tests: **5 passed**. Repository checks with `VERIBENCH_ROOT=/Users/brandomiranda/veribench make test`: **34 passed, 0 skipped**. The first default-path test invocation had 32 passed and 2 skipped because its external checkout discovery did not include the Mac path; setting the documented environment variable resolved both skips.
- Standard host health preflight: local scratch and Python passed; shared distributed storage free-percent gate failed. The bounded audit writes only to its dedicated local scratch directory and does not require shared storage writes or model clients. No cleanup of shared files was attempted.

## Next dependency

**[p 9/10] Develop a generic Lean endpoint adapter and accepted external-reference route** using the [version-4 draft](expt_v4/README.md). It specifies declaration/type mapping, namespace and dependency isolation, strict proof trust and non-vacuity checks before external validation. Its new model-call budget is zero and it is not an execution admission. Preserve the failed 0/24 version-3 result. The [experiment02 readiness receipt](../02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/results/training_readiness_manifest_2026-10-06.json) separately blocks training and numeric forecasts.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] Factor-feedback engineering completed 24/24 authored controls, but external applicability failed at 0/24 against the 20/24 gate. Repair and training remain unadmitted.
**Snapshot:**
```text
authored_controls_measured=24/24; matching=24/24
external_endpoint_applicable=0/24; required=20/24
candidate_partitions=train141/validation24/test24
repair_cells_measured=0/192; judge_member_calls=0/1296
training=NOT_ADMITTED; forecast=NOT_FROZEN
next_adapter_version=DRAFT; new_model_call_budget=0
```
