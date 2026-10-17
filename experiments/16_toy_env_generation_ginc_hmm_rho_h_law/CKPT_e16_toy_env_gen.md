# CKPT e16: toy environment generation with the ρ–H law (GINC-style HMM tasks, CPU)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/CKPT_e16_toy_env_gen.md>

Created: 10-15-2026 00:20 PDT
Last updated: 10-16-2026 23:55 PDT

## State

- **Owner:** ultimate_brando9, nightly runs at 23:30 PDT on its own 4-CPU machine (no GPU, no SNAP); morning email to Brando after each night.
- **Branch / PR:** `ub9/e16-toy-env-generation`, never merged by the assistant.
- **Status:** toy part complete (night 3). GINC night 2 (`expt_v2`, Codex on skampere1): TIE WITH BASELINES. Known MDP night 3 (`expt_v3`, mdp_v2: 6 scales, 3 start-policy repeats, 5,940 RL rows): gate passes (20/22 positive at s6), corr(log ρ, H) = 0.819, verdict NO ADVANTAGE. Night 2b's CHOICE ONLY (one start policy per scale) did not replicate.
- **Headline numbers (expt_v3 mdp_v2, s6, mean over 3 budgets):** law regret 10.78 pts [9.53, 12.28] vs uniform random 4.42 [4.21, 4.93], best fixed env from s1–s5 1.47 [0.18, 2.93]; law picks b15 (noisy, already solved) at every budget, observed −3.75 pts vs best b08 +8.20. Noise-free ρ moves b15's prediction only from +6.32 to +5.04; a law refit on noise-free features still has regret 4.77 (no better than random).
- **Stuck / blocked:** nothing. Background processes die when a shell call ends; every stage runs in the foreground (expt_v3 takes 4 minutes on 4 cores).
- **Next step:** none filed. A changed law (for example a target-relevance term next to ρ and H) would be a new experiment with its own protocol, if Brando wants it.
- **Brando to-do:** none. Optional: say whether to test a changed law in the toy, or move on.

## Log

- 10-16-2026 23:55 PDT: night 3 done. Protocol addendum + mdp_v2 code frozen at 483c006 before RL; 18 (scale, repeat) jobs ran; NO ADVANTAGE with bootstrap intervals; toy part complete, no night 4 filed; results.md updated.

- 10-15-2026 23:45 PDT: night 2 done. GINC night 2 found already run by Codex on skampere1 (commits 29c6bad..121e86d), not repeated. Coded and ran the known-MDP sanity family (expt_v3, protocol frozen at 899ddc1 before RL): CHOICE ONLY; results.md updated.

- 10-15-2026 00:30 PDT: night 1 done. v1 (n4, held-out-concept targets) and v2 (4 scales × 12 envs × 2 seeds × 3 budgets, GINC-faithful target) ran; diag_lr and diag_kl ran; results.md written.
