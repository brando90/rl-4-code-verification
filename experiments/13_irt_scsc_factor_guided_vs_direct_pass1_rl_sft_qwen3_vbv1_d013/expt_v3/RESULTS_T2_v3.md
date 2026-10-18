# Experiment 13 v3 T2: PASS on the retained factored-reward cohort

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/RESULTS_T2_v3.md>

**TLDR:** T2_v3 PASS: gradient norm 0.0936069563, parameter change True, and refit median absolute log-probability error 4.987977445e-05. The comparison uses the exact same 256 train rollouts and identical pre-update weights, optimizer and scheduler; only advantages differ in the saved loss-input tensors. The CPU random-state difference is disclosed below.

**Measured:** 10-16-2026 20:31 PDT. **Provider spend:** $0; local offline NeMo and vLLM only.

| Observation | Strict binary reward (immutable v2) | Factored reward (v3) |
|---|---:|---:|
| Declared / measured responses | 256 / 255 | 256 / 255 |
| Positive measured rewards | 0/255 | 21/255 |
| Complete groups / declared groups | 31/32 | 31/32 |
| Active complete groups | 0/31 | 14/31 |
| Nonzero-advantage slots | 0/248 | 112/248 |
| Optimizer calls | 1 | 1 |
| Gradient norm | 0 | 0.0936069563 |
| Parameter change | False; 0/399 tensors changed | True; full digest covers 399 tensors |
| Refit responses | 8 | 8 |
| Unsupported refit tokens | 0/44,844 | 0/42692 |
| Median absolute refit log-probability error | 0.000032748153898864985 | 4.98797744513e-05 |
| T2 verdict | FAIL | PASS |

The v3 criterion is the frozen protocol's positive gradient, changed full parameter hash, zero unsupported refit tokens and median absolute error ≤0.01. Refit p99 error (0.01772953987) and importance-truncated tokens (0/42692) are descriptive, not added admission thresholds. The missing deterministic scorer outcome remains missing; its full eight-response group is masked, with all generated tokens retained in resource accounting.

Before hash: `7fed40220b3d759cd49391bd311b15a5468137d3bf99dff425ac401c838c16ae`.
After hash: `d74212a60879cd4240a280255f3395aeb39ec412bd7941fa4fe07ce24080ac3b`.
The saved scoring receipt remains `e9f4e62094e766663acd8e7f29b343e6742dcc41899cccc88a14cd08813dce45`. [Group table and all original generation hashes](results/retained_cohort.json), [gate result](results/T2_v3.json), [update summary](results/T2_v3_update_summary.json), and [permanent strict result](../expt_v2/RESULTS_T2_S2.md) provide the reproducible comparison. Raw checkpoints and the exact replay batch stay at `/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/technical/T2/attempt_1`.

[Tensor identity](results/actual_batch_identity.json) verifies that every actual loss-input tensor except advantages is bitwise equal to the strict-run input, including recomputed trainer probabilities (maximum difference 0). [Pre-update state comparison](results/pre_update_state_identity.json) verifies identical parameter/optimizer digests and Python, NumPy and CUDA random states. Torch's CPU random state differs after the additional probability-recomputation pass; the comparison does not claim byte-identical CPU random state across the two reward conditions. T3 restores v3's own exact saved pre-update random state, as required for deterministic replay. The original state was restored before recomputation; no update is repeated to remove this disclosed difference.

These are fixed-cohort technical measurements, with no population efficacy claim or stochastic repeat estimate (p-val=n/a for numerical/hash gates). The active-group difference is the previously recorded 14/31 = 45.16 percentage points, with a group-bootstrap 95% interval [29.03, 61.29] percentage points and two-sided exact McNemar p=0.0001220703125 on 14 versus 0 discordant groups. That interval describes resampling these 31 train groups; it does not quantify seed-to-seed learning uncertainty.

This result does not establish improved validation pass@1 or official VeriBench SCSC. The guarded training reward and the official SCSC aggregate have different definitions; the latter includes validated formal-specification coverage. Downstream replay, cost and learning results are reported in [the live ledger](results.md).

Copy-ready collaborator message: “I compared strict and factored reward on the exact same retained rollout batch. The factored update has gradient norm 0.093607, parameter change True, and refit error 4.98798e-05; this is a technical pipeline result, not yet evidence of better held-out performance.”

**TLDR-end:** [rl-4-code-verification: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3] T2_v3 PASS; the strict v2 failure and every original artifact remain unchanged.
