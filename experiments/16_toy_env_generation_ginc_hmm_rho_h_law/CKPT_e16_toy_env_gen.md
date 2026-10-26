# CKPT e16: toy environment generation with the ρ–H law (GINC-style HMM tasks, CPU)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/CKPT_e16_toy_env_gen.md>

Created: 10-15-2026 00:20 PDT
Last updated: 10-20-2026 17:45 PDT

## State

- **Owner:** ultimate_brando9, nightly runs at 23:30 PDT on its own 4-CPU machine (no GPU, no SNAP); morning email to Brando after each night.
- **Branch / PR:** `ub9/e16-toy-env-generation`, never merged by the assistant.
- **Status:** Night 4 done (`expt_v4`, GINC tiny transformers, alpha target-alignment term): **POSITIVE by the frozen rule** (law+alpha regret below random with non-overlapping intervals), but law+alpha is not better than the plain law and the best-on-n3 baseline is best. Earlier: Night 3 (`expt_v3` known MDP) NO ADVANTAGE; Night 2 (`expt_v2`) TIE WITH BASELINES.
- **Headline numbers (expt_v4, n4, mean over 3 budgets, 3 seeds, 2,000 bootstrap draws with refits):** law+alpha 1.08 pts [0.55, 1.82], law 0.93 [0.44, 1.73], alpha alone 0.65 [0.36, 1.16], best fixed on n3 0.12 [0.00, 1.49], uniform random 2.22 [2.03, 2.63]; law+alpha minus law [−0.23, +0.51]. Spearman with observed final n4 utility: alpha 0.63, law forecast −0.10, law+alpha forecast 0.45. RL strength S2 (lr 3e-4, KL 0.1) chosen by the pilot (F 171 vs Night 2's 4.6); forgetting regime, 17 of 144 n4 cells positive. Night 3: law 10.78 vs random 4.42.
- **Stuck / blocked:** nothing. Long stages run as resumable chunks (background shells stop at a time limit).
- **Next step:** pre-register a test of the cheap rules that won (alpha alone and best-on-a-smaller-scale) against the law on a positive-transfer regime or the real Reasoning Gym candidates, if Brando wants it; not filed.
- **Brando to-do:** none. Optional: say whether to move alpha / small-scale pilots to real environments.

## Log

- 10-20-2026 17:45 PDT: night 4 done (AT-564). Protocol + code frozen at 04da045 before RL; pilot chose S2; n4 forecast frozen and pushed at 661a84d before any n4 cell; 192 trajectories; POSITIVE by the frozen rule with the caveats above; results.md updated.

- 10-16-2026 23:55 PDT: night 3 done. Protocol addendum + mdp_v2 code frozen at 483c006 before RL; 18 (scale, repeat) jobs ran; NO ADVANTAGE with bootstrap intervals; toy part complete, no night 4 filed; results.md updated.

- 10-15-2026 23:45 PDT: night 2 done. GINC night 2 found already run by Codex on skampere1 (commits 29c6bad..121e86d), not repeated. Coded and ran the known-MDP sanity family (expt_v3, protocol frozen at 899ddc1 before RL): CHOICE ONLY; results.md updated.

- 10-15-2026 00:30 PDT: night 1 done. v1 (n4, held-out-concept targets) and v2 (4 scales × 12 envs × 2 seeds × 3 budgets, GINC-faithful target) ran; diag_lr and diag_kl ran; results.md written.
