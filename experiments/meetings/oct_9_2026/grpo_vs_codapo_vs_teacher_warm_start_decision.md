# Why the Qwen models aren't learning yet, and what to change: GRPO vs CoDaPO vs more teacher SFT data (10-09-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_9_2026/grpo_vs_codapo_vs_teacher_warm_start_decision.md>

**TLDR:** Keep Group Relative Policy Optimization (GRPO) as the first baseline, for implementation continuity and experimental control. The binding problems are not the optimizer: the base models almost never succeed, so no reward signal appears, and the one GRPO run (experiment 09) stopped on a rollout/trainer probability mismatch before any update. Next: fix the implementation under a new, prespecified condition; run a conditional GRPO pilot on the 8B SFT export; add success-discovery methods (adaptive sampling for zero-success prompts, expert iteration with compiler-feedback repair); then compare CoDaPO as a controlled optimizer arm.

Brando's question to the VeriBench coordinator session, 10-09-2026, after Andrew Zhanke Zhou advised "just use grpo": the Qwen models struggle and the SFT ones aren't succeeding much. Should we switch the RL algorithm to CoDaPO (Confidence and Difficulty-adaptive Policy Optimization, Brando's co-authored ICML 2026 method), or go through frontier models for more SFT data until the warm start works? Who should do it?

**Review:** one light review by Codex `gpt-6-astra` at `ultra` effort returned FIXES NEEDED (0 critical, 5 major, 3 minor). Every fix is applied here. The numerical claims were checked against `origin/main` at `a7c2ea20`.

## Evidence

- **Base models give almost no signal.** Experiment `05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk` (G=8, VeriBench V1): `kernel_binary` mixed-task counts are 0/896, 5/896 and 0/896 for 1.7B, 4B and 8B. Wilson 95% intervals: 0.000 [0.000, 0.004], 0.006 [0.002, 0.013], 0.000 [0.000, 0.004].
- **The SFT warm start creates signal.** Experiment `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` trains on 1,315 kept files covering 476 of 539 train tasks.
  - Full-fraction validation mixed-task shares: 20/135 = 0.148 [0.098, 0.218] for 1.7B and 32/135 = 0.237 [0.173, 0.315] for both 4B and 8B.
  - The 8B SFT export passes the kernel-based point-estimate readiness gates (extraction 974/1,080, capped 106/1,080, mixed 32/135), as does Base14B.
  - RL efficacy and the full judge-dependent reward signal are unmeasured, and formal checkpoint selection is still blocked.
  - Scientific 14B training stands at 0 of 658 updates, awaiting an admitted, available device layout.
- **At the 75% SFT rung, the dense kernel reward adds nothing yet.** For 1.7B and 4B, `kernel_binary` and `proof_fraction` disagree on 0 of 2,160 validation responses; formal specification coverage was not measured there. This is a statement about those rungs only.
- **The only GRPO run failed on implementation, not on learning.** Experiment `09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` (1.7B SFT initialization, NeMo RL 0.4.0):
  - 4 of 4,077 sampled actions fell outside the recomputed support;
  - 367 of 4,073 log-probability comparisons exceeded the 0.05 tolerance;
  - zero optimizer updates were made, and the experiment closed with a no-restart boundary.
- **CoDaPO** (arXiv 2606.07950; tmlr-group/CoDaPO `210c2051`) computes a weight of confidence × [1 − 4(d − 0.5)²] + 0.1, with d = 1 − group accuracy.
  - At d = 1 the weight is exactly 0.1, its minimum.
  - Its selector keeps weights at or above a percentile threshold, so all-fail prompts can be resampled when the threshold reaches the floor.
  - It runs on a separate verl stack, not NeMo RL 0.4.0.

## Reasoning

- **An already-sampled all-fail binary group gives zero reward-derived gradient under both GRPO and CoDaPO.** Every advantage is zero, and no weight changes that. CoDaPO's resampling can still discover successes later, as can any method that spends more samples on zero-success prompts. So the regime that blocks the base models calls for success discovery, not a reweighted optimizer.
- **The experiment 09 mismatch is specific to that implementation**, which recomputed truncated distributions. Changing advantage weights does not repair it. Truncated importance sampling (TIS), already in the pinned NeMo, is a candidate for finite probability errors. A looser tolerance cannot fix actions sampled outside the recomputed support.
- **Keep GRPO for implementation continuity and experimental control.** The ρ–H coordinates (`src/rl4cv/experience.py`) use unnormalized leave-one-out advantages per million generated tokens, a measurement definition that doesn't depend on the optimizer. Any CoDaPO-weighted coordinates or cross-optimizer forecast would be a new hypothesis.
- **"More frontier-model SFT data until it works" is too blunt.** On-policy verified successes (expert iteration) and concise, complete demonstrations target the observed failures better than more teachers.
  - Teacher augmentation can help both coverage (the 63 uncovered train tasks) and diversity on covered tasks.
  - Each added teacher is a new labelled condition.
  - Fable showed 870 of 970 output-cap errors in experiment 02A.
  - Whether outputs from an internal pre-release Vals model may be used as training data is **unverified**; ask Vals before relying on it.

## Recommendation (proposed priorities, not measured winners)

1. **[p 9/10] Diagnose probability and support under a new, prespecified implementation condition.**
   - Check weights sync, tokenization, precision, the actual behavior-policy probabilities and the sampling support (top-k/top-p truncation).
   - Validate any importance correction (TIS) and its clipping bias.
   - Run one real update, save and reload cycle.
   - Experiment 09's failed gate stays as recorded.
2. **[p 8/10] Conditional GRPO pilot on the 8B SFT export.**
   - First, measure training-only success and reward variation (full reward where the judge applies).
   - Freeze the endpoint and success criterion before training: strict pass rate on validation under the common one-turn, no-feedback harness.
3. **[p 7/10] Success discovery for zero-success prompts.** Use bounded larger groups or adaptive per-prompt sampling. With independent draws the mixed-group probability is 1 − pᴳ − (1 − p)ᴳ, and correlated samples reduce the gain. Report successes per generated token.
4. **[p 7/10] Rejection-sampling fine-tuning or expert iteration.** Generate on train tasks, verify with the kernel, and train on the successes. Compiler-feedback repair turns, already in the planned two-turn pilot, supply more successful trajectories.
5. **[p 6/10] Teacher-guided RL or an explicitly mixed supervised loss** if exploration stays inadequate. Teacher trajectories need an off-policy objective; don't treat them as student samples.
6. **[p 5/10] CoDaPO as a controlled optimizer comparison** once the implementation is valid. Positive GRPO learning is not a prerequisite. Port it, or implement a named adaptation in NeMo.
7. **[p 4/10] Targeted teacher augmentation**, for coverage and diversity, each as a labelled condition. Keep the VeriBench V1 test split and the private VBV2 set out.

## Who does it

Route through the existing rl4cv master (see `experiments/CKPT_MASTER_tmuxnone_cxd_01a11d6a.md`). It holds the experiment 08 and 09 state, device leases and continuation boundaries, and can reuse or dispatch one SNAP worker after checking current ownership; recorded state alone doesn't prove the master is live. Rakshit keeps ownership of the experiment 08 warm start (issue #7). The VeriBench rating-round session that wrote this memo does not run it.
