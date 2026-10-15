# Experiment 13 v2 amendment A6: zero strict signal under the frozen rollout sampler (batch 2, a pipeline diagnostic, and T5)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md>

**TLDR:** Under the frozen Phase 2 rollout sampler, the starting policy produces no compiling Lean file ([RESULTS_ANCHORS_S2.md](RESULTS_ANCHORS_S2.md), [RESULTS_CALIBRATION_S2.md](RESULTS_CALIBRATION_S2.md)). The sampler is temperature 1, top-p 1, top-k off, at most 8,192 new tokens, in float16.

| Anchor panel | Strict successes / measured | Q1 (well-formed output) |
|---|---:|---:|
| Base | 0/4,311 | 9.6% |
| 50% SFT | 0/4,303 | 7.6% |
| 100% SFT (the Phase 2 start) | 0/4,302 | 12.9% |

Whole-file compilation among the well-formed outputs (Q2) is 0/1,294 across all three panels. The historical evaluation sampler gave nonzero full-schedule strict success on validation (G0's data). It is temperature 0.6, top-p 0.95, top-k 20, at most 12,288 tokens (experiment 08's ladder; `phase2/evaluation_contract.py`).

Under the frozen plan:

- **Batch 2 measures nothing.** H2's predictor is unavailable, and arm C is already disabled.
- **T5 would test sparsity, not the pipeline.** Arm A's strict reward is all zeros, so T5's requirement that A learn would test reward sparsity, not pipeline feasibility. It would stop Phase 2 before the B − A and placebo contrasts.

A6 makes three changes, all before any Phase 2 learning update, validation outcome or test outcome:

1. Batch 2 is skipped.
2. A train-only pipeline diagnostic runs first.
3. T5 is applied to the arm that receives a nonzero reward, B.

**Status:** ADOPTED 10-15-2026 07:19 PDT by the version 2 master (Claude Code `claude-opus-5-5`, session "Oct 9: IRT for eval metric decomposition"), as coordinator.

**Disclosure:** A6 was written after observing the train anchor panels and the failed calibration. It was written before any Phase 2 learning, any T5 data and any new validation or test data.

## Why

- **T5's intent and how it was written.** T5 (PROTOCOL § 6) is "a technical feasibility selection ... not evidence for H3". Its intent is that the learning pipeline can raise a reward the policy actually receives. It was written as "A's train strict moving average increases", which assumes A's reward has signal.
- **What the anchors show.** At the start policy, A's reward has essentially none: 0 of 4,302 measured responses succeed. GRPO assigns all-zero groups zero advantage, so A's policy barely moves, whatever the pipeline's validity.
- **What the comparison means here.** A and B use the same sampler, trainer and token budget; only the reward differs. In this regime the B − A contrast asks the experiment's motivating question: does a factored partial-credit reward improve strict pass@1 where direct optimization of the downstream metric has no signal? B − P asks whether B's content matters beyond reward density.

## Rules

1. **No batch 2.** Independent batch 2 is not generated.
   - H2 and F2 (0.75, recorded prospectively) are reported UNAVAILABLE: the fixed conditional strict forecast is null (RESULTS_CALIBRATION_S2), so H2 cannot be evaluated on any batch.
   - This saves about 10 device-hours.
   - G1 still runs on the historical ladder, as planned. Arm C stays disabled.
2. **Pipeline diagnostic, before LP.** It rules out a generation defect, as opposed to the sampler effect.
   - **Run:** once, train-only, on 64 seeded train tasks × 8 samples from `sft_4B_f1p0`, using the frozen S2 runtime (float16, prompts, template and scorer unchanged) with the historical evaluation sampler.
   - **Reference:** before running, the owner publishes the historical full-schedule validation per-sample compile rate and strict rate from the experiment 08 ladder, and the diagnostic's frozen task-ID hash.
   - **Verdict:** the pipeline is sound if the diagnostic's strict successes are above 0 **and** its compile rate is at least one tenth of the historical compile rate.
   - **If unsound:** stop before LP and diagnose. A defect fix would invalidate the S2 anchors and needs its own amendment.
   - **Scope:** this diagnostic is not a hypothesis gate, and its outputs never enter any statistic of the comparison.
3. **T5 on arm B.**
   - The rule: B's own train-reward moving average must rise by at least 0.02 (two percentage points on B's 0–1 scale) from updates 1–10 to 21–30.
   - If it doesn't, extend B once to 60 updates, comparing 1–10 with 51–60. If it still doesn't, stop Phase 2 and publish.
   - A's strict learning curve, and its count of nonzero-gradient updates, are reported descriptively for every A seed. P is not gated.
   - A and P still run their pilots, and A's pilot lengths still set the token budget T at L2.
4. **Unchanged:**
   - the frozen rollout sampler, the S2 numerics, arms A, B and P (C disabled), seeds and pilot horizons;
   - the token-budget rule;
   - LP and T1–T4, and the train mutation and coverage audits with their stop rule;
   - the hosted coverage judge, the evaluation sampler and validation selection;
   - the single test evaluation, the primary contrast B − A, the placebo contrasts and the guards.
5. **Scope of claims.** Results hold for the regime the frozen rollout sampler produces, where strict reward has essentially no gradient at the start. They make no claim about regimes where A has signal, for example lower-temperature rollouts; a later version could test that prospectively.

G0 PASS, the S2 admission, the failed C calibration, the frozen placebo distribution and every other frozen artifact are unchanged.

## Clarification, 10-15-2026 08:15 PDT (master): infrastructure attempts of the diagnostic

**What "once-only" means.** In rule 2, "once-only" forbids rerunning the diagnostic after it has measured anything. [A4](AMENDMENT_A4_technical_gate_infrastructure_attempts_10-14-2026.md) applies to this diagnostic as it does to the other technical gates.

**What a rerun requires.** An attempt that ends on a reproducible infrastructure defect before generating any diagnostic response may be rerun once that defect is fixed. Attempt 1 ended this way at about 08:00 PDT. Its lease held 0.0038 device-hours and it failed on "frozen weights absent" with a `pytorch_model.bin` checkpoint, before generating anything. The rerun needs:

- a fix that changes no scientific setting;
- a regression test, a preflight check and a successor lock, all pushed first;
- at most 3 attempts in total, every attempt published;
- the frozen 2.0 device-hour allocation, used cumulatively.

**What stays final.** An attempt that generates and scores the cohort is final, whether the pipeline is SOUND or UNSOUND.
