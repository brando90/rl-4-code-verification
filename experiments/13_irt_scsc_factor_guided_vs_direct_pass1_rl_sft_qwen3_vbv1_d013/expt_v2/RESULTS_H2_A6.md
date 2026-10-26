# Experiment 13 v2-S2: H2 and F2 unavailable under A6

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_H2_A6.md>

**TLDR:** H2, the independent mixed-group prediction check, and forecast F2 are **UNAVAILABLE** because the frozen conditional strict predictor is null. Arm C remains disabled. Independent batch 2 is skipped under adopted [A6](AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md).

The prospective F2 value remains 0.75 in its original immutable artifact; no observed area under the curve exists, and no replacement predictor or fit is introduced. [Machine-readable status](phase1/H2_F2_A6_result.json) binds the published calibration and frozen predictions. No hypothesis test or uncertainty interval can be computed for an unavailable prediction.

The batch-2 plan, controller and generation directory were never created. No device lease is active. Its unpublished lock draft was retained privately as cancelled; no frozen artifact changed. Historical G1 still runs once using [the A6 execution lock](locks/G1_A6.json) and the unchanged G1 fitting body and historical ladder. The single calibration and every earlier gate remain final.
