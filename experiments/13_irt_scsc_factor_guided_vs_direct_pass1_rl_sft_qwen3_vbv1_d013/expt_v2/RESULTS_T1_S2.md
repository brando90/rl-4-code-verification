# Experiment 13 v2-S2 T1 probability admission: PASS

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_T1_S2.md>

**TLDR:** T1 is final **PASS** on its fixed train probe, complete attempt 2. Continue to T2, then T3 and T4; no learning pilot is admitted yet.

The [LP freeze](phase2/LP_A6_S2_FREEZE.md) was published at `970d274` before any T1 device claim. The unchanged S2 generator and the prospectively frozen training configuration produced the [saved final result](phase2/T1_A6_S2_result.json). Attempt 1 remains INCOMPLETE-INFRA under A4, with its generated outputs excluded. The tested Ray socket-path repair and successor locks preceded this complete attempt. No admission statistic was recomputed for publication.

| Criterion | Measured value | Frozen threshold |
|---|---:|---:|
| Unsupported tokens | 0/44844 | 0 |
| Median absolute token log-probability error | 3.2748153898864985e-05 | ≤0.01 |
| 99th-percentile absolute error | 0.017602388858795164 | ≤0.10 |
| Importance truncation at ratio 2 | 0/44844 = 0.0 | ≤0.01 |

All 8/8 declared train responses were accounted. There are 28164 excluded prompt tokens, 44844 included output tokens, 5 terminal tokens in the assistant mask and 3 cap-limited responses. Quantiles use the frozen linear interpolation. These are fixed technical-probe criteria from PROTOCOL section 6, not population efficacy estimates; confidence intervals and p-values are not applicable (`p-val=n/a`).

The [anonymous token table](phase2/T1_A6_S2_tokens.csv) preserves every generator/trainer probability used by the saved result without task identities, task text or token identities. The last column indicates a registered terminal token. Missing/nonfinite probabilities, if any, are retained rather than dropped from the declared token count.

[Resource and cleanup receipts](phase2/T1_A6_S2_resources.json) account for 6 released device leases and 0.355751673 cumulative device-hours against the unchanged 2.0-hour T1 cap. This complete attempt used 0.186873268 hours against its 1.5-hour cap. Non-probe engine health preceded admission, numeric device mapping was used, and every stage released its lease after verified cleanup. No optimizer update occurred in T1. The overall technical allocation remains 23.75 device-hours, with gate caps still binding.

Continue to T2, then T3 and T4; no learning pilot is admitted yet. Historical G1 remains INCONCLUSIVE; C is disabled; H2/F2 remain UNAVAILABLE; independent batch 2 remains skipped. Any eventual comparison is scoped to A6's zero-strict-signal rollout regime.

Attempt-1 evidence and its zero-statistic infrastructure classification remain in [the published failure receipt](phase2/T1_A6_attempt1_result.json) and [repair record](phase2/T1_A4_REPAIR.md).

Publication verification: the required Lean integration suite passed **1,124 tests, 3 skipped, zero failures in 529.99 seconds**, direct exit 0 ([receipt](phase2/T1_A4_attempt2_publication_test.json)). Only saved numerical evidence and prose changed after this test; the gate statistic was not recomputed.
