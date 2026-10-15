# Experiment 16 results: ρ–H law for picking RL environments on toy GINC-style HMM tasks

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/results.md>

Design: [README.md](README.md). All numbers below are real CPU runs from 10-14-2026 23:40 to 10-15-2026 00:12 PDT; raw rows are in `expt_v1/results/`.

## Night 1 (10-14/15-2026): verdict NOT YET MEANINGFUL (formally CHOICE ONLY)

The pipeline runs end to end (generator → start policies → ρ/H probes → GRPO → target utility → Eq. 7 fit → choice test). But no RL run improved the target, so the law could only rank how much each environment hurts.

### Start policies

| scale | params | pretrain loss (last 50 steps) | start greedy acc, v2 target (9 settings mixed, l=10) | start greedy acc, held-out concepts (S8, sh4, l=12) |
|---|---|---|---|---|
| n1 | 4,496 | 2.343 | 0.425 | 0.385 |
| n2 | 27,824 | 2.215 | 0.482 | 0.447 |
| n3 | 104,784 | 2.177 | 0.502 | 0.469 |
| n4 | 604,432 | 2.143 | 0.511 | 0.463 |

n4 is barely better than n3: 1,500 pretraining steps under-train the largest model, so the scale axis is shallow.

### v2 (primary target: pretraining concepts, all 9 settings mixed, prefix length 10)

Fit on n1–n3, predict n4 (144 observations = 4 scales × 12 envs × 3 budgets, two-seed means; mean |seed 0 − seed 1| gap 0.94 pts; SD of utility across envs at n4, largest budget, 14.0 pts):

| features | RMSE (pts) | rank acc | regret (pts) | LOSO RMSE | LOSO rank acc | LOSO regret |
|---|---|---|---|---|---|---|
| ρ–H (Eq. 7) | 12.18 | 0.742 | 0.00 | 10.03 | 0.663 | 0.04 |
| ρ only | 12.79 | 0.677 | 0.00 | 10.39 | 0.635 | 0.04 |
| H only | 12.75 | 0.662 | 0.00 | 10.36 | 0.633 | 0.04 |
| budget + scale only | 12.82 | 0.500 | 12.63 | 10.40 | 0.500 | 9.14 |

| choice rule at n4 | mean regret (pts) |
|---|---|
| ρ–H law | 0.00 |
| uniform random candidate | 12.63 |
| best fixed env from n1–n3 (e10) | 0.00 |
| highest starting success | 1.86 |
| highest mixed-group share | 0.00 |

- **T1 (scale transfer): fails in substance.** Rank accuracy 0.74 beats 0.50, but RMSE 12.2 pts is barely below the no-environment baseline's 12.8 pts against a 14 pt spread.
- **T2 (choice): beats random only.** The law picks e10_S4_sh4_n64_L24 (U = −3.80 pts, the least harmful env, also the oracle), but the best fixed env from the small scales and the highest mixed-group share pick the same env.
- Fitted ρ and H coefficients are large and opposite (b_ρ = −0.44, b_H = +0.46) because the two features are collinear here (below).

Per environment at n4, 51.2k generated tokens (observed vs law-predicted utility):

| env | observed U (pts) | predicted U (pts) | ρ | H | start success |
|---|---|---|---|---|---|
| e10_S4_sh4_n64_L24 | −3.80 | −11.03 | 376,186 | 0.800 | 0.471 |
| e02_S4_sh8_n64_L16 | −5.94 | −17.66 | 363,212 | 0.763 | 0.556 |
| e06_S8_sh8_n64_L24 | −6.07 | −13.88 | 355,190 | 0.766 | 0.457 |
| e03_S8_sh4_n64_L12 | −6.28 | −17.82 | 302,037 | 0.683 | 0.288 |
| e09_S12_sh2_n64_L24 | −6.48 | −19.11 | 218,052 | 0.537 | 0.156 |
| e07_S12_sh4_n64_L8 | −7.11 | −24.69 | 236,537 | 0.554 | 0.188 |
| e05_S8_sh2_n64_L4 | −9.57 | −17.88 | 184,780 | 0.469 | 0.120 |
| e08_S12_sh8_n2_L16 | −29.67 | −19.81 | 323,312 | 0.706 | 0.302 |
| e12_S12_sh4_n2_L4 | −33.07 | −19.85 | 215,541 | 0.530 | 0.160 |
| e11_S8_sh8_n2_L4 | −33.11 | −19.08 | 325,474 | 0.711 | 0.312 |
| e04_S8_sh4_n2_L12 | −35.65 | −21.41 | 266,253 | 0.616 | 0.202 |
| e01_S4_sh2_n2_L4 | −40.38 | −18.42 | 289,342 | 0.662 | 0.215 |

Full tables, including the held-out-concept secondary target and per-scale Spearman correlations: [expt_v1/results/pilot_v2/analysis_v2.md](expt_v1/results/pilot_v2/analysis_v2.md).

### What the numbers say

1. **Forgetting regime.** 0 of 288 (scale, env, seed, budget) runs have positive target utility. RL does work inside each environment (held-out in-env accuracy +15 to +21 pts on average per scale; e04 at n2 goes 0.30 → 0.87), but the in-env gain and the target utility correlate at −0.92: the more an environment moves the policy, the more it forgets the rest.
2. **Concept count dominates.** The five 2-concept environments average −27.1 pts on the target versus −4.2 pts for the 64-concept ones. RL on 2 concepts teaches memorized answers. ρ and H do not see this axis, which is why the law's largest misses are exactly these five rows.
3. **ρ and H are one feature here.** Across the 48 (scale, env) probes, corr(log ρ, H) = 0.995 and both correlate about 0.91 with starting success. With one-token answers and every response admitted, both measurements are functions of the per-prompt success distribution. The paper's two axes need variable-length responses or partial-credit rewards to separate.
4. **Reproducible.** v1's held-out-concept target and v2's secondary target are the same prompts; their n4 utilities match to the digit (e.g. e03 −3.35 pts in both runs).

### v1 (both targets built from never-seen concepts; n4 only)

Run first. Every candidate lowered both targets at n4 (target A −3.35 to −37.68 pts, target B −3.00 to −38.70 pts), so the smaller scales were not run for v1 and the primary target was switched to the GINC-faithful one (v2). n4 rows: `expt_v1/results/pilot_v1/n4_rl_*.jsonl`.

### Diagnostics

- **Learning rate** (`diag_lr.py`, [log](expt_v1/results/pilot_v1/diag_lr.log)): on the held-out-concept target, lower rates only trade in-env gain for less damage. n2, e03, 400 steps: lr 5e-4 in-env +4.0 pts, target −1.8; lr 1e-4 in-env +2.2, target −0.3; lr 3e-5 in-env +0.9, target +0.15 (within noise). The largest target gain in the whole diagnostic is +0.2 pts (n3, lr 3e-5).
- **KL to the start policy** (`diag_kl.py`, [log](expt_v1/results/pilot_v2/diag_kl.log)), v2 target, 200 steps: KL coefficient 1.0 stops most of the damage while keeping in-env gains (n3, e10: in-env 0.725 → 0.818, target 0.502 → 0.501; n2, e04 (2 concepts): target −1.5 pts instead of −24.4 pts). Still no positive transfer from any single-setting environment.

## Next (night 2, 10-15-2026 23:30)

1. KL coefficient 1.0 in every run, and candidates that are *mixtures* of settings proposed by the generator (random subsets of the 9 settings, n, l ranges), so some candidates can actually raise the target. Gate: at least 3 of the candidates with positive n4 utility before reading T1/T2.
2. Separate ρ from H: multi-token answers (predict the next k symbols, reward = exact match or per-symbol partial credit) with a generation cap, so lengths and admission vary.
3. Deepen the scale axis: pretraining steps grow with model size so n4 is clearly stronger than n3.
4. Code and run the known-MDP sanity family.

**TLDR-end:** [rl4cv: e16 toy env generation] Night 1 ran the full toy pipeline on CPU with real numbers: the ρ–H law picked the least harmful environment (regret 0.00 vs 12.63 pts for random), but so did trivial baselines, every RL run lowered the target (0/288 positive), and log ρ and H were 0.995 correlated. Verdict NOT YET MEANINGFUL; night 2 adds a KL penalty, mixture candidates and multi-token answers.

**Snapshot:**
```
diag_kl (v2 target, 200 steps, lr 5e-4)
n3 e10  kl=0.0  env 0.725->0.833  target 0.502->0.477
n3 e10  kl=1.0  env 0.725->0.818  target 0.502->0.501
n2 e04  kl=0.0  env 0.291->0.857  target 0.483->0.239
n2 e04  kl=1.0  env 0.291->0.529  target 0.483->0.467
```
