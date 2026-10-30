# Experiment 25 (checkpoint reuse for the rho-H law): outcome label, Oct 30 2026

**Label (toy evidence only): ADOPT for dense-checkpoint curves (R1) and prefix extrapolation (R2); the rolling rho/H form (R3) is NOT supported; WRONG DOMAIN cannot be decided yet because the real Lean pilot (Stage 2b) has not run.**

## Numbers (all committed; see results.md, expt_v6/results.md, stage2a/RESULTS_gate8.md)
- P1 holds (Night 6 toy, 492 runs): dense reuse is not worse than independent runs at equal compute. Curve RMSE 0.00283 vs 0.00482 (A-B CI [-0.0022, 0.00003]); n3 forecast RMSE 0.0530 vs 0.0536. Both forecasts are about 5 pp off in absolute terms.
- P2 holds, weakly: 50% prefix fit RMSE ratio 1.010 (CI [1.006, 1.016]); on Nights 4/5 ratio 0.975/0.970 but Eq. 7 has no skill at n4 (rank accuracy 0.42-0.48, chance 0.5). The per-cell saturating and sigmoid arms fail the 1.25 ratio (about 3.2 and 15).
- P3 fails: rolling rho/H LOEO MSE 1.352e-5 vs zero 1.391e-5, start-only 1.467e-5, previous 2.892e-5.
- P4 equivalent (1.7B SFT rungs vs fresh runs, pooled 50%+100%): dH +0.002 [-0.024, +0.027] within +-0.073; dlog rho +0.174 [-0.170, +0.480] only at the coarse margin +-0.49.
- P5 holds, negative sign: cosine minus constant -0.0053 (100 steps), -0.0091 (200 steps), so reuse needs a constant learning rate.
- Within-run variance is 2.3-3.0x the seed variance of fitted curves, which favours dense reuse.
- Public Marin Delphi / Snowball math checkpoints (R5, about 3 of 20 GPU-h): P6 not testable (2-3 of 8 environments measurable at 3.4B, 4 needed), P7 not supported (|Spearman| H 0.6 vs 0.8 bar; 25B extrapolation misses), P8 no form beats a flat baseline, Q4 and Q2(c) blocked by the laion license. These are method evidence only, never inputs to the label. R5 stopped under its own stop rule.
- Stage 2a (trainer wiring, Sherlock): dense checkpoints, per-step rollout logs, 1% log-prob gate passed (0.061%) over 8 updates; measured about 1720 s per update (999-3273), 13,752 GPU-s for 8 updates.

## What this means for 02B / future RL runs (no-regret, independent of Stage 2b)
Keep every checkpoint, log every rollout, use a constant learning rate, count trajectories (not checkpoints) as the sample size. Checkpoints do NOT replace separate runs per scale x environment x seed.

## Open: Stage 2b (real Lean pilot) is gated and not launched
- Blocked on 02A Stage D (warm-start and probe outputs): the two environments with most different rho cannot be named. Not on main as of Oct 30.
- Cost as the plan specified it (4 trajectories x 128 steps) at the measured 1720 s per update: about 245 GPU-h training alone, plus 38-77 GPU-h evaluation and about 180 CPU-h Lean scoring. The plan's own rule is to ask Brando above 160 GPU-h, so this needs his decision or a smaller pilot (for example 64 steps: about 122 GPU-h training) before launch.

Caveats: toy only (K=4 tokens, KL 0.1 saturates U, n4 is a forgetting regime); 3 seeds so intervals are coarse; SFT-rung evidence is 1.7B only; 7 pre-existing pytest failures in experiments 08/13 are untouched by this work.

Agent: cc opus 5.5 xhigh
