# CKPT e16: toy environment generation with the ρ–H law (GINC-style HMM tasks, CPU)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/CKPT_e16_toy_env_gen.md>

Created: 10-15-2026 00:20 PDT
Last updated: 10-15-2026 23:45 PDT

## State

- **Owner:** ultimate_brando9, nightly runs at 23:30 PDT on its own 4-CPU machine (no GPU, no SNAP); morning email to Brando after each night.
- **Branch / PR:** `ub9/e16-toy-env-generation`, never merged by the assistant.
- **Status:** night 2 done. GINC night 2 (`expt_v2`) ran on skampere1 by Codex (see CKPT_e16_night2.md): 384/384 cells, TIE WITH BASELINES. Known-MDP sanity family (`expt_v3`) ran here: gate passes (20/22 positive at n4), corr(log ρ, H) = 0.820, verdict CHOICE ONLY.
- **Headline numbers (expt_v3, n4, 102.4k tokens):** law regret 0.98 pts vs uniform random 4.32, best fixed env from n1–n3 0.51, ρ-only 9.70; law pick b13 +6.76 pts vs observed best b08 +7.63; ρ inflates on noisy solved envs (b15 predicted +7.46, observed −2.73).
- **Stuck / blocked:** nothing. Background processes die when a shell call ends; every stage runs in the foreground (expt_v3 takes 4 minutes on 4 cores).
- **Next step (night 3, 10-16-2026 23:30):** in `expt_v3`, three start-policy repeats per scale and bootstrap intervals on regret, a wider scale grid (n2 and n3 are too close), and a diagnostic ρ from noise-free rewards to size the noise failure; then decide whether the toy is done.
- **Brando to-do:** none. Optional: say if Codex on SNAP takes night 3 instead, so the two don't duplicate.

## Log

- 10-15-2026 23:45 PDT: night 2 done. GINC night 2 found already run by Codex on skampere1 (commits 29c6bad..121e86d), not repeated. Coded and ran the known-MDP sanity family (expt_v3, protocol frozen at 899ddc1 before RL): CHOICE ONLY; results.md updated.

- 10-15-2026 00:30 PDT: night 1 done. v1 (n4, held-out-concept targets) and v2 (4 scales × 12 envs × 2 seeds × 3 budgets, GINC-faithful target) ran; diag_lr and diag_kl ran; results.md written.
