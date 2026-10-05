# Live results for the diagnostic intervention study

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/results.md>

**Status:** AUDIT COMPLETE — endpoint engineering, repair and training studies remain PLANNED. The canonical folder stays active because these phases and thesis inclusion depend on it.

**Last updated:** 10-05-2026 11:13 PDT.

The zero-model-call existing-artifact audit completed on `skampere1.stanford.edu` with exit code 0. It supports an availability finding, not a new correctness correlation or causal intervention claim.

| Phase | State | Evidence |
|---|---|---|
| Interpretation and detailed plan | DONE | [README](README.md), [PLAN](PLAN.md), [METRICS](METRICS.md), [sources](sources/context.md) |
| Frozen input inventory | DONE | Four inputs, 6,556,256 bytes; all hashes match their recorded committed VeriBench sources |
| Remote deterministic audit | DONE | [Readable report](expt_v1/results/RESULTS_existing_artifacts.md), [data](expt_v1/results/audit.json), [receipt](expt_v1/results/execution_receipt.json) |
| Fixed-reference endpoint validation | PENDING | Independent reference success is absent from selected modern factor records |
| Matched-cost repair comparison | PLANNED | No measured solver calls admitted; independent outcome and score-aggregation contract required |
| Environment/reward training | PLANNED | Reuse `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics` |

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

**[p 9/10] Validate the fixed-reference endpoint harness on screened external tasks**, then freeze the component-versus-scalar repair comparison, because the independent outcome needed to interpret an improvement is missing. Exact models, toolchains, judge settings, full manifests and cost ceilings belong in the next version before measured calls. No new training campaign has started.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] The detailed thesis experiment plan and first remote audit are complete. Trusted auxiliary outcome validation and causal repair/training comparisons remain unmeasured.
**Snapshot:**
```text
saved_rows=5420
complete_factor_rows=4444
v1_snapshot_cells=5376/6272
independent_reference_outcome=unavailable
new_model_calls=0
exit_code=0
```
