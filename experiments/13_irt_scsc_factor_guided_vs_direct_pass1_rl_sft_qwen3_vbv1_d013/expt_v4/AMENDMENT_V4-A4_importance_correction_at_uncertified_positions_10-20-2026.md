# Experiment 13 v4 Amendment V4-A4: importance correction at uncertified positions

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/AMENDMENT_V4-A4_importance_correction_at_uncertified_positions_10-20-2026.md>

**Status:** adopted 10-20-2026 by the experiment 13 master, before any v4 generation or gate statistic. One Codex `gpt-6-astra` ultra consult graded it ADOPT WITH CHANGES (8/10), and all three of its must-fix items are incorporated below. It resolves the dispatch 2 [blocker](BLOCKER_V4_A1_importance_correction.md). [PROTOCOL.md](PROTOCOL.md), [V4-A1](AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md), [V4-A2](AMENDMENT_V4-A2_receipt_invariance_and_sampler_backend_10-20-2026.md) and [V4-A3](AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md) are otherwise unchanged.

**TLDR:** NeMo RL 0.4.0's loss multiplies each token by a truncated importance correction, exp(trainer old log π̃ − generator log π̃) capped at 2. That needs the generator's log π̃, which V4-A1 leaves unknown at uncertified positions. At those positions only, the correction is set to exactly 1. This **changes the actor-loss estimator**, and it is disclosed as an approximation. A guard stops training if more than 1% of tokens are uncertified, and the possible loss perturbation is reported every update.

## Rules

1. **Isolated, detached imputation.**
   - At uncertified positions the generator's log π̃ stays **unknown** in every receipt and statistic.
   - Only inside the actor-correction term is it replaced, by the detached trainer old log π̃ for that token, which makes the weight exactly 1.
   - The following are unchanged and verified so by tests on the installed loss: certified positions, the PPO ratio (both terms trainer-computed), clipping, advantages, token normalization, the cap of 2, and all support gates.
2. **Other consumers of the generator's log π̃.**
   - The recipe's KL coefficient is 0, so the loss's generation-dependent KL term is inactive. Admission verifies that it stays 0. If it were ever nonzero, launch would need a further amendment.
   - Every diagnostic that uses the generator's log π̃ (entropy and probability-error metrics) excludes uncertified positions and is labelled as covering certified positions only.
   - Imputed values never enter V4-T1 or any measured agreement.
3. **Guard.** Before each optimizer step, the uncertified fraction must be ≤ 1% on both of these measures:
   - generated positions;
   - valid actor-loss tokens, aggregated across all ranks and gradient-accumulation microbatches.

   A breach **stops that trajectory's training run** before the step, as a diagnosed stop under the existing single-attempt and A4 rules. Individual rollouts are never discarded and nothing is resampled. The rule applies to V4-T2, every pilot update, and every main-study update.
4. **Reported every update**, alongside V4-A1's certified fraction:
   - the uncertified fraction on both denominators;
   - at certified positions, the actor log-weight's 1st percentile, median and 99th percentile, plus the clamp rate;
   - the perturbation bound B = N⁻¹ Σ_{t∈U} |ℓ_t|, where N is the number of valid actor-loss tokens, U the uncertified tokens and ℓ_t a token's unweighted clipped loss.

   Because the true weight lies in [0, 2], B bounds the absolute change in the loss compared with the exact capped correction. **It does not bound the gradient change.** The empirical bias stays unmeasured and is disclosed as such.
5. **Fallback not adopted.** A v4-owned vLLM sampler hook would record the exact filtered sampled-token probability at every position. It is not adopted. If V4-T1 or the guard shows that more than 1% of tokens are uncertified, that hook becomes the prospective fix, as a new numbered amendment before any further data.

## What does not change

- The filtered-policy objective's support rule.
- The sampler and the receipts.
- Every gate threshold.
- The arms, the inference and the § 6 claims, plus one more disclosed limitation: a training-time approximation at no more than 1% of tokens.
