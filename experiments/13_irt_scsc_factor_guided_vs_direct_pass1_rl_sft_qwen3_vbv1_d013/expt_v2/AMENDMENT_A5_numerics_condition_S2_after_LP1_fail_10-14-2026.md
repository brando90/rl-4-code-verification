# Experiment 13 v2 amendment A5: numerics-corrected condition S2 after the measured LP-1 failure

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A5_numerics_condition_S2_after_LP1_fail_10-14-2026.md>

**TLDR:** Under the original numerical stack S1, LP-1 failed one criterion on a measured attempt, and that FAIL is final ([RESULTS_LP1.md](RESULTS_LP1.md), `77558aa`). S1 is bfloat16 vLLM 0.10.0 generation with the bfloat16 NeMo RL 0.4.0 trainer.

| LP-1 criterion | Observed | Threshold | Result |
|---|---:|---:|---|
| 99th-percentile absolute log-probability error | 0.1248 | ≤ 0.10 | FAIL |
| Median absolute log-probability error | 0.0003 | ≤ 0.01 | PASS |
| Unsupported tokens | 0/40,035 | 0 | PASS |
| Tokens truncated at importance-ratio cap 2 | 0/40,035 | ≤ 1% | PASS |

A5 opens one separately versioned technical condition, S2. Only numerical execution changes, and it changes identically for the generator and the trainer:

1. The S2 setting is selected on a disjoint, train-only development probe by a rule declared before any measurement.
2. S2 is confirmed once on the original frozen LP-1 probe, with every threshold unchanged.
3. If no candidate qualifies, or the confirmation fails, version 2 stops at LP-1, and that stop is published.

**Status:** ADOPTED 10-14-2026 17:17 PDT by the version 2 master (Claude Code `claude-opus-5-5`, session "Oct 9: IRT for eval metric decomposition"), as coordinator.

**Disclosure:** A5 was written after LP-1's measured S1 failure. That failure stays final and is reported with every S2 result. No validation or test data is touched. G0 and every scientific gate are unchanged.

## Why

- **What LP-1 measures.** It is a technical admission. It asks whether the generator's and the trainer's token probabilities agree closely enough for the importance-corrected reinforcement-learning update to be valid. It does not test the hypothesis.
- **The cause is engineering.** bfloat16 differences between inference and training engines accumulate over long sequences, and here three of eight responses reached the 8,192-token cap. This is a known numerical problem with standard remedies: higher precision, or matched kernels.
- **The repair is a new condition, not a retry.** Fixing the stack to meet a fixed fidelity criterion is the repair the rules expect, as a separately versioned condition. Reusing the probe or loosening the threshold until something passes is not; A5 does neither.

## Rules

1. **Labels.** S1 is the configuration through LP-1 attempt 2. Its result is final and is reported in every summary. Everything run under S2 is labeled `v2-S2`.
2. **Candidates.**
   - Before any development measurement, the owner publishes at most 4 candidate settings in a frozen list, ordered by expected Phase 2 cost from cheapest to most expensive.
   - Each candidate changes only numerical execution settings, identically for vLLM generation and the NeMo RL trainer. Examples:
     - weight and activation dtype (`float16` or `float32`);
     - logit and log-softmax precision;
     - attention-backend or batching determinism settings.
   - Each candidate uses the installed package versions only.
   - Nothing else changes: not the sampler, token caps, data, seeds, thresholds, importance-ratio cap, policy weights (except a dtype cast) or the scorer.
3. **Development probe.**
   - Use a seeded draw of 8 train tasks, disjoint from the LP-1 probe's tasks, with the same policy, sampler and caps as LP-1.
   - Publish the task IDs' hash before any S2 measurement.
   - Measure each candidate once, in list order. A4 governs infrastructure failures.
4. **Selection.** S2 is the first candidate that clears every LP-1 criterion on the development probe with a 20% margin:
   - unsupported tokens 0;
   - median error ≤ 0.008;
   - 99th-percentile error ≤ 0.08;
   - truncation fraction ≤ 0.008.

   If no candidate qualifies, version 2 stops at LP-1.
5. **Confirmation.**
   - Freeze S2 in `locks/LP1_A5_S2.json`. It names the numerical change and binds every unchanged LP-1 scientific setting at its previous hash.
   - Run `E13_REQUIRE_LEAN_INTEGRATION=1 make test` and push.
   - Then run LP-1 **once** on the original frozen probe with the unchanged thresholds. The result is final, PASS or FAIL; A4 covers only infrastructure failures that occur before measurement.
   - If it fails, version 2 stops at LP-1. Version 2 gets no further stack condition.
6. **Downstream.** S2 applies to every later generation and training step: the anchors, batch 2, LP, T1–T4, the pilots, the main runs and the evaluation generation. T4 re-measures the cost under S2, and PROTOCOL § 6's cost re-estimate before the main runs uses those measurements.
7. **Device time.** All development and confirmation runs together are capped at 3.0 device-hours, with at most 0.5 per run. Only idle devices claimed through the experiment-13 lease registry may be used.

G0 PASS, the A3 exclusions, the frozen forecasts and every later gate threshold are unchanged.
