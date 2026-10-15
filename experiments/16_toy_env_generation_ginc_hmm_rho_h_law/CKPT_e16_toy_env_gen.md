# CKPT e16: toy environment generation with the ρ–H law (GINC-style HMM tasks, CPU)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/CKPT_e16_toy_env_gen.md>

Created: 10-15-2026 00:20 PDT
Last updated: 10-15-2026 00:30 PDT

## State

- **Owner:** ultimate_brando9, nightly runs at 23:30 PDT on its own 4-CPU machine (no GPU, no SNAP); morning email to Brando after each night.
- **Branch / PR:** `ub9/e16-toy-env-generation`, never merged by the assistant.
- **Status:** night 1 done. Pipeline runs end to end; verdict NOT YET MEANINGFUL (forgetting regime: 0/288 runs improve the target; corr(log ρ, H) = 0.995).
- **Headline numbers (v2, n4, 51.2k tokens):** law regret 0.00 pts vs uniform random 12.63; best-fixed-env and highest-mixed-share baselines also 0.00; Eq. 7 RMSE 12.18 pts vs 12.82 for budget+scale only; rank accuracy 0.742.
- **Stuck / blocked:** nothing blocking. Background processes die when a shell call ends, so every stage runs in the foreground in chunks of 10 minutes or less.
- **Next step (night 2):** add `--kl 1.0` to `run_pilot.py`, generator-proposed mixture candidates, multi-token answers; then
  `python run_pilot.py --scale n4 --out results/pilot_v3 --stage pretrain --targets v2` and the RL chunks as in the README.
- **Brando to-do:** none. Optional: say if the toy should switch to the MDP family first.

## Log

- 10-15-2026 00:30 PDT: night 1 done. v1 (n4, held-out-concept targets) and v2 (4 scales × 12 envs × 2 seeds × 3 budgets, GINC-faithful target) ran; diag_lr and diag_kl ran; results.md written.
