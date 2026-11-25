# Experiment 02C — reward-channel generalization: kernel reward versus judge-gated FSC reward

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge/README.md>

**Part of:** [experiment 02](../README.md) (ρ–H-guided Lean environment design), phase C, the reward for the third metric (FSC); numbered experiment 04 before D-007

**TLDR:** On the same prompts and scales, this compares RL with a kernel-only reward against rewards that include compile-gated FSC. It tests whether ρ and H, measured before RL under each reward, predict which reward most improves VeriBench SCSC and FSC. That answers Azalea's question of whether VeriBench's metrics guide reward design, and whether the law survives LLM-judged rewards.

## Flagged: README/code mismatch on the judge gate (10-09-2026, unresolved)

The method section below says "the judge runs asynchronously, only on responses with `IC_tests · IC_proofs > 0`" — both mechanical factors positive. But `src/rl4cv/rewards.py`'s `fsc_compiled`/`needs_judge` (this phase's own named channel) gates on `ic_tests == 1.0 and vacuous_theorems == 0` only; it does not require `IC_proofs > 0` (that stricter gate is actually `scsc`'s, not `fsc_compiled`'s). This phase has no `PROTOCOL.md` yet and is still "TODO, after experiment 02A," so no locked protocol settles which gate is intended. Whoever locks this phase's protocol should pick one side and update the other before any training run reads `needs_judge`. See `notes/veribench_crosscheck_10-09-2026.md` for the full comparison.

## Goal, hypothesis and decision criterion

- **Motivation.** FSC is where frontier headroom remains ([FACTS §2](../../../docs/FACTS_veribench_baselines.md#2-frontier-systems-two-factors-are-nearly-saturated-fsc-carries-the-remaining-signal)). But a judged reward is noisier and more exploitable than the kernel.
- **Hypothesis (L4).** Per-channel ρ and H rank the channels' held-out SCSC gains with accuracy within 10 points of the kernel channel's own ranking. Compile-gated FSC rewards raise VeriBench FSC more than kernel-only rewards, without lowering IC_proofs.
- **Decision.**
  - If L4 holds, judge-gated environments can be selected before RL, which is the key step for non-verifiable domains (Nolera, and the Certification Judge thesis topic).
  - If it fails, report which part of the measurement breaks: judge noise in ρ, or concentration in H.

## Flag for the owner (10-09-2026, unresolved — pick a side only once this phase's own protocol settles it)

This README's "Method" step 3 (below) says the judge runs only when **both** mechanical factors are positive (`IC_tests · IC_proofs > 0`). That is actually the gate for the separate `scsc` channel. The `fsc_compiled` channel this phase is named for has a different, already-coded gate in `src/rl4cv/rewards.py`'s `needs_judge` (lines ~86-96): it fires whenever `ic_tests == 1.0 and vacuous_theorems == 0`, regardless of `ic_proofs`. No PROTOCOL.md exists yet for phase C (only phase A and phase B have one; this phase's status is still "designed"/TODO), so nothing locks which gate `fsc_compiled` should actually use — @lethan3, please settle this when phase C's protocol is written, and update whichever side (README prose or `needs_judge`) is wrong. Full crosscheck: [`../../../notes/veribench_crosscheck_10-09-2026.md`](../../../notes/veribench_crosscheck_10-09-2026.md) in this rl4cv worktree branch.

## Method

1. **Setup.** Take one family and one cell design from experiment 02A at 1.7B and 4B, with the same prompts for every channel.
2. **Channels:** `kernel_binary`, `proof_fraction`, `fsc_compiled` and `scsc` (definitions in `src/rl4cv/rewards.py`).
   - Measure ρ and H under each channel on the same Stage D probe responses. Only the reward changes; the responses are identical.
3. **Training.** Train 2 seeds per channel per scale with experiment 02B's contract.
   - The judge runs asynchronously, only on responses with IC_tests · IC_proofs > 0 (`rl4cv.rewards.needs_judge`).
   - Judge controls follow experiment 103: oracle ≥ 4, blank = 0, shuffled ≤ 1, vacuous ≤ 1.
4. **Reward-hacking audits at every checkpoint:**
   - share of compiling files with vacuous theorems;
   - the gap between FSC on compiling and non-compiling files;
   - a 30-item human spot check at step 128.
5. **Outcomes.**
   - VeriBench V1 SCSC, IC_tests, IC_proofs and FSC (full at step 128), plus within-source panel pass@1.
   - Fit Eq. 7 per channel and pooled, and compare the rankings.

## Dependencies

- Experiment 02A, and experiment 02B's contract.
- Decision D-102, the judge route and payer. Cost is judged responses × about $0.40; early training judges few responses because few compile.

## Status

| Step | Status |
|---|---|
| Design | Done (09-30-2026) |
| Everything else | TODO, after experiment 02A |
