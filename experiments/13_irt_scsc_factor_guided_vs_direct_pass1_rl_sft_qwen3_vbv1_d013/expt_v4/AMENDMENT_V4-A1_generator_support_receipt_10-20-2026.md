# Experiment 13 v4 Amendment V4-A1: generator support receipt with a completeness certificate

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md>

**Status:** adopted 10-20-2026 by the experiment 13 master. No v4 generation, gate statistic or model output exists. This amends only the "Behaviour probabilities" bullet of [PROTOCOL.md](PROTOCOL.md) § 2.2 and the support criterion of V4-T1. The objective, sampler, thresholds and every other section are unchanged.

**TLDR:** A raw top-20 receipt cannot show which generator support was used when logits tie at the 20th place or at the top-p boundary. v4 therefore records the top 64 raw log-probabilities and certifies, position by position, whether the generator's support is fully determined. Every uncertified position counts against V4-T1's support-agreement allowance. This makes the gate harder to pass, never easier.

## Why

The implementation owner found this before any model execution ([checkpoint](CKPT_v4_implementation.md); reproducer in `tests/`). The pinned vLLM 0.10.0 sampler (`apply_top_k_top_p`) does three things that matter here:

- **Top-k ties:** it keeps every logit tied with the 20th largest, so the support can exceed 20 tokens. A top-20 receipt cannot reveal how many tokens are tied.
- **Top-p order:** it orders tokens with `torch.sort`, which is not stable, so within a tie group at the top-p boundary the tokens it keeps are unspecified.
- **No post-filter output:** its `processed_logprobs` mode is computed before temperature and filtering, so the engine exposes no post-filter probabilities.

The frozen bullet required the receipt to determine support "exactly", and otherwise declared V4-T1 unimplementable. Exactness is impossible from engine outputs at these positions. It is also unnecessary for the objective, because both ratio terms are trainer-computed (§ 2.2). The generator-side receipt serves only the agreement checks.

## Amended rules

1. **Receipt.** The generator runs with `max_logprobs = 64` and requests the top 64 raw log-probabilities, plus the sampled token's raw log-probability, at every generated position. This setting changes only what is recorded, not sampling. V4-T1 verifies it by comparing generations with and without the receipt.
2. **Top-k certificate.** Write v_r for the r-th largest raw log-probability. The top-k set is complete when v_64 < v_20 strictly. In that case every token tied with v_20 is in the receipt, and the top-k set is all receipt tokens with value ≥ v_20.
3. **Top-p reconstruction.** Over a certified top-k set, the generator's nucleus follows the installed order. Take the softmax of the values divided by 0.6, accumulate from the smallest value up, and drop tokens whose cumulative mass is ≤ 0.05, keeping the largest token.
   - **Uncertified boundary:** the nucleus is uncertified if the boundary falls inside a group of tokens with equal value, or if the cumulative mass at the boundary is within 1e-5 of 0.05 (a float32 reconstruction margin).
   - **Behaviour probability:** the generator's log π̃ for the sampled token follows from a certified nucleus.
4. **Certified positions.** A position is certified when both its top-k set and its nucleus are certified.
5. **V4-T1 support criterion (replaces "identical generator and trainer supports at ≥ 99% of sampled positions").** Positions that are certified and have identical generator and trainer supports must be at least 99% of sampled positions. Uncertified positions count as disagreements.
   - The log π̃ error quantiles use certified positions only, and the uncertified count is reported with them.
   - With fewer than 99% of positions certified, the gate fails.
6. **Trainer-side tie rule.** The trainer's support keeps every token tied with its 20th largest logit, as the generator does. At the top-p boundary it keeps the whole tie group, a superset of any order the generator could have used. A sampled token is therefore never excluded from the trainer's support by tie order alone. The "zero sampled tokens outside the trainer's support" criteria in V4-T1 and V4-T2 are unchanged.
7. **Storage.** The top-64 receipts are kept in full for the V4-T1 probe, the V4-G0 batch and the V4-T2 refit. During pilot and main updates, the tested reconstruction code reduces each position at generation time to:
   - the sampled token and its raw log-probability;
   - the top-k and nucleus certificate flags;
   - the support size;
   - the generator's log π̃ for the sampled token, where certified.

   It then discards the full receipt. Each update reports its certified fraction.
8. **Engine limit.** If the pinned engine cannot return 64 log-probabilities at the v4 context length, V4-T1 still fails as unimplementable, as frozen, and v4 stops.

## What does not change

- The filtered-policy objective.
- The old-weight support used in both ratio terms.
- The sampler (temperature 0.6, top-k 20, top-p 0.95, 12,288 tokens).
- Every V4-T1 threshold except the support criterion above.
- Every other gate, the arms, inference and the claims in § 6.
