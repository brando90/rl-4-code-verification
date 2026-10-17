# Experiment 16 results: ρ–H law for picking RL environments on toy GINC-style HMM tasks

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/results.md>

Design: [README.md](README.md). Night 1 measurements are preserved below in `expt_v1/results/`; the Night 2 continuation uses `expt_v2/results/pilot_v3/`; the known-MDP runs use `expt_v3/results/mdp_v1/` (Night 2b) and `expt_v3/results/mdp_v2/` (Night 3).

## Night 3: known-MDP with start-policy repeats and six scales (`expt_v3`, mdp_v2) — NO ADVANTAGE; the toy part is complete

**Status:** run complete, 10-16-2026 23:36–23:49 PDT, ultimate_brando9's 4-CPU machine, $0. Protocol addendum and code frozen and pushed (483c006) before any RL row: [expt_v3/PROTOCOL.md](expt_v3/PROTOCOL.md) (Night 3 addendum), [run_mdp_v2.py](expt_v3/run_mdp_v2.py), [analyze_mdp_v2.py](expt_v3/analyze_mdp_v2.py). Full tables: [expt_v3/results/mdp_v2/analysis_mdp_v2.md](expt_v3/results/mdp_v2/analysis_mdp_v2.md).

**Takeaway.** With three start policies per scale and a clean scale axis, the ρ–H law picks the worst kind of environment every time: an already-solved region with noisy rewards (b15), because Eq. 7 always prefers the highest ρ and H and reward noise inflates ρ. Its allocation regret is 10.8 pts, worse than picking at random (4.4) and far worse than "the best environment on the small models" (1.5). Night 2b's CHOICE ONLY does not replicate. Removing the noise from ρ fixes that one pick but not the law: a law fit on noise-free ρ and H still does no better than random (4.8 vs 4.4). In this toy, ρ and H measure how learnable an environment is, not how much it helps the target.

Same chain, 22 candidates, 3 budgets (25.6k / 51.2k / 102.4k tokens), 5 seeds, GRPO, KL 1.0 and exact-gradient oracle as Night 2b. New: six scales s1–s6 (38 / 72 / 140 / 276 / 548 / 5,252 parameters; smaller models get fewer behavior-cloning steps), three start-policy repeats each, 15 runs per cell, 5,940 RL rows. The law is fit on s1–s5 and read at s6.

| check (PROTOCOL.md) | result |
|---|---|
| Start target value rises with scale (mean of 3 repeats) | 0.181, 0.241, 0.305, 0.378, 0.436, 0.509 (n2/n3 tie fixed) |
| Gate: ≥3 candidates positive at s6, 102.4k tokens | **pass: 20 of 22** (378 of 396 cells positive; mean candidate +3.68 pts) |
| Separation: \|corr(log ρ, H)\| < 0.85 | pass, barely: 0.819 over 396 probes (0.800 with noise-free probes) |
| T1: Eq. 7 beats budget+scale only at s6 | formally: RMSE 3.26 vs 3.59 pts, rank accuracy 0.515 vs 0.500 |
| T2: law regret below random and every baseline | **fails: worse than random** |

| choice rule at s6 (mean over 3 budgets) | regret (pts) | 95% interval | law minus rule, 95% interval |
|---|---|---|---|
| ρ–H law (picks b15_r3_sl6_sg0.5 at every budget) | 10.78 | [9.53, 12.28] | – |
| ρ only (same pick) | 10.78 | [9.53, 12.28] | [+0.00, +0.00] |
| highest start success (same pick) | 10.78 | [9.02, 12.28] | [+0.00, +1.58] |
| H only | 4.77 | [3.84, 6.21] | [+3.57, +8.39] |
| uniform random | 4.42 | [4.21, 4.93] | [+4.96, +7.78] |
| highest mixed-group share | 4.20 | [3.98, 4.67] | [+5.20, +7.93] |
| exact-gradient oracle's ranking | 3.37 | [3.00, 3.98] | [+5.86, +8.70] |
| best fixed from s1–s5 (b12_r3_sl0_sg0.0) | **1.47** | [0.18, 2.93] | [+8.68, +9.92] |

Intervals: 2,000 bootstrap resamples of start-policy repeats (per scale) and seeds (per repeat), law and best-fixed label refit each time. The law has higher regret than every other rule in 100% of resamples. Bootstrap intervals on a max-minus-pick quantity lean high (resampling adds noise to the max), so the best-fixed interval sits partly above its point value.

At s6, 102.4k tokens: the law's pick b15 gains −3.75 pts (repeat means −1.28 / −4.04 / −5.92); the observed best is b08_r2_sl0_sg0.0 at +8.20 (SD over 15 runs 1.19); law predictions span only +4.5 to +6.3 pts while observed gains span −3.75 to +8.20. Spearman at s6: law vs observed −0.02, law vs oracle 0.19, observed vs oracle 0.66.

**Noise diagnostic (law unchanged).** b15's ρ is 106,797 with noisy rewards and 4,374 on the same rollouts without noise (24×). Plugging the noise-free ρ into the same fitted law lowers b15's prediction from +6.32 to +5.04 pts against an observed −3.75, so the noise accounts for about 1.3 of the 10.1-pt miss. Over the 11 noisy candidates, the mean absolute prediction error goes from 2.71 to 2.50 pts. A law refit on noise-free ρ and H (diagnostic only) picks b06_r1_sl6_sg0.0 with regret 4.77 pts, still no better than random.

### What the numbers say

1. **The failure is robust.** Each start-policy repeat analyzed alone gives the same pick (b15) and law regret of 9.6, 11.1 and 12.3 pts, against 0.1, 2.1 and 3.3 for the best fixed environment. The law also picks b15 in-sample at every training scale, where b15's gain falls from +1.2 (s1) to −0.9 pts (s5).
2. **Why.** Eq. 7's environment term rises with both log ρ and H (fitted b_ρ = +0.012, b_H = +0.006, no interaction with scale or budget), so it ranks environments the same way at every scale and budget. Nothing in ρ or H says whether training on a region transfers to the target, which is what separates b08/b12 (hard regions, good transfer) from b14/b15 (a region the policy has already solved).
3. **Night 2b's CHOICE ONLY was luck of one start policy per scale.** With repeats and a clean scale axis the same family gives NO ADVANTAGE: the law's regret interval [9.53, 12.28] is nowhere near Night 2b's 0.98 (a different top scale, so not the same cell, but the same family and law).
4. **Is the toy part complete? Yes.** Both toy families now give a clear answer with $0 compute: GINC (Night 2) ties the baselines; the known MDP (Night 3) loses to random, with intervals. The law as written doesn't pick training environments for a new target in these toys. Testing a changed law (for example, a target-relevance term next to ρ and H) would be a new experiment with its own protocol; it is not filed as Night 4.

**TLDR:** with 3 start policies per scale, 6 scales and bootstrap intervals, the ρ–H law loses to random in the known MDP (regret 10.8 vs 4.4 pts) because it always picks the noisy, already-solved environment; noise-free ρ doesn't rescue it (4.8). Toy part complete.

## Night 2: 16_toy_env_generation_ginc_hmm_rho_h_law — TIE WITH BASELINES

**Status:** EXPERIMENT COMPLETE. **Last updated:** 10-15-2026 20:42 PDT.

All **384/384 budget cells** completed (128 training trajectories, two seeds, three correlated budget observations per trajectory). **224/384 (58.33% [56.51, 60.16], p-val=n/a)** have strictly positive observed joint target utility; **79/128** final-budget trajectories are positive. This exceeds the user-chosen 30% prevalence threshold, but counts positive point estimates, not individually significant gains.

**Verdict: TIE WITH BASELINES**, the prospective protocol’s operational label for positive point utility without demonstrated advantage; this is not a statistical equivalence claim. The law selects base environment **e08**, gaining **+0.0375 [−0.3500, +0.4500] percentage points, p-val=0.500**. The interval includes zero, so **MEANINGFUL POSITIVE TRANSFER is not established**.

[Full outcome tables](expt_v2/results/pilot_v3/RESULTS_night2.md) · [Probe statistics](expt_v2/results/pilot_v3/RESULTS_probes.md) · [Prospective protocol and clarifications](expt_v2/PROTOCOL.md) · [Checkpoint](CKPT_e16_night2.md).

### Largest-scale choice at 51,200 generated tokens

Primary metric: change in joint four-token oracle-match accuracy over the same 4,000 held-out target prompts. Units are percentage points.

| Rule | Choice | Target utility [95% interval] | p-val | Allocation regret |
|---|---|---:|---:|---:|
| rho-H | e08 | +0.0375 [-0.3500, +0.4500] | 0.500 | 0.3000 |
| uniform-random | uniform over 16 | +0.0555 [-0.1875, +0.3064] | 0.250 | 0.2820 |
| best-fixed-n3 | e09 | +0.1375 [-0.3750, +0.6250] | 0.500 | 0.2000 |
| highest-pass-variance | e01 | +0.3375 [-0.0750, +0.7500] | 0.250 | 0.0000 |
| highest-mixed-share | m00 | +0.0125 [-0.3253, +0.3750] | 0.500 | 0.3250 |
| rho-only | e04 | +0.1625 [-0.2000, +0.5125] | 0.250 | 0.1750 |
| H-only | e09 | +0.1375 [-0.3750, +0.6250] | 0.500 | 0.2000 |

Intervals: 2,000 bootstrap draws resampling the paired target prompts and two training-seed indices, conditional on the fixed starting checkpoints and frozen choices. One-sided exact paired seed sign-flip tests use the null of zero utility or zero advantage; two seeds permit no p-value below 0.25. The prevalence interval resamples seed clusters separately within each fixed scale, preserving all environments/budgets; it does not include target-prompt or pretraining uncertainty. Allocation regrets are descriptive point estimates against the observed best candidate. The selected e08 final-budget seed utilities are -0.0750 and +0.1500 percentage points (two-seed sample standard deviation 0.1591 points); one pretrained checkpoint per scale gives no pretraining-repeat estimate.

At n4, Equation 7 has root mean squared prediction error **0.3513 [0.2747, 0.4276] percentage points, p-val=n/a**, versus **0.3191 [0.2471, 0.3896]** for budget-and-scale only; pairwise rank accuracy is **0.4722**, versus **0.5000**. Error intervals resample candidate environments with all budgets together and hold the fit fixed; mixtures share components, so these are descriptive intervals, not independent environment-family replication. The law’s mean prediction minus mean observed utility is **+0.3058 percentage points** (predicted mean +0.3446, observed mean +0.0388; 48 n4 environment/budget two-seed means).

### Coverage versus conditional entropy

| Coordinate | Pooled correlation across 64 cells [95% probe bootstrap] | n4 correlation across 16 candidates |
|---|---:|---:|
| Original law: effective coverage H | 0.6731 [0.5826, 0.7244] p-val=n/a | 0.8408 [0.7348, 0.8909] p-val=n/a |
| Four-token conditional entropy | -0.7925 [-0.8148, -0.7601] p-val=n/a | -0.9091 [-0.9267, -0.8780] p-val=n/a |

The original-law coverage gate passes the user-chosen absolute-correlation threshold 0.85, pooled and at every scale (n4 point estimate 0.8408). The n4 interval crosses 0.85, so the point-estimate pass is not proof of population decorrelation. Literal conditional entropy remains strongly correlated at n2–n4; **the every-scale entropy interpretation of the dispatch is not satisfied**. Night 1’s cited 0.995 statistic used coverage, not entropy. This distinction and the operative pooled-coverage gate were documented before reinforcement learning. Probe intervals resample 512 prompt groups within each fixed environment, paired across scales (2,000 draws); entropy uses eight sampled continuations per prompt with exact forward probabilities.

### Starting policies and execution

| Scale | Parameters | Pretraining steps | Joint target accuracy | Token target accuracy |
|---|---:|---:|---:|---:|
| n1 | 4,496 | 2,000 | 26.5500% | 42.6313% |
| n2 | 27,824 | 2,500 | 30.5500% | 46.2812% |
| n3 | 104,784 | 3,000 | 31.9000% | 47.8750% |
| n4 | 604,432 | 4,000 | 36.1250% | 51.2062% |

Starting accuracies describe the fixed 4,000-prompt cohort. All runs used central processing units (CPUs), nice 10, one PyTorch thread per training process and at most eight training processes; **$0 spend**, no hosted model calls. Four generated mixtures were included throughout. The law chose a base environment; the best observed mixture at the final n4 budget was m01 (+0.3125 percentage points, descriptive two-seed mean), which does not establish a generated-environment advantage.

Forecast chronology: `forecast_n4.json` was frozen at **10-15-2026 20:37:19 PDT**, before n4 training, with SHA-256 `e06e399faf0f10ae955eea5e115ef1f5ca2be6e8e76ca29f2134967c6977cf82`. All frozen hashes, 384 cell identities and utilities recomputed from per-prompt token hits passed verification. The corrected full repository suite passed **754 tests / 38 skipped**; focused tests passed **11/11**.

A metadata name collision initially stored environment diagnostics in the raw `env` field. The analysis recovers each label from its immutable filename, preserves raw bytes and numerical scores, and validates the scale/seed identity. A one-key serialization correction prevents the collision in later cells. Both fixes have timestamped frozen receipts; **zero training reruns**, with no changes to models, rewards, budgets or selection.

Per-cell scores, per-prompt hits, probe rewards, candidate definitions, frozen forecasts and statistics are committed under `expt_v2/results/pilot_v3/`. Ignored starting tensors stay in the user-designated execution checkout on skampere1 at the same relative path, with SHA-256 hashes in the metadata; they are reproducible from the committed code and seeds.

## Night 2b: known-MDP sanity family (`expt_v3`) — CHOICE ONLY, positive transfer established

**Status:** run complete, 10-15-2026 23:35–23:39 PDT, ultimate_brando9's 4-CPU machine, $0. Protocol frozen and committed (899ddc1) before any RL row: [expt_v3/PROTOCOL.md](expt_v3/PROTOCOL.md). Full tables: [expt_v3/results/mdp_v1/analysis_mdp.md](expt_v3/results/mdp_v1/analysis_mdp.md).

A 16-state chain MDP in 4 regions (each region has its own hidden action map), where the target value is exact (dynamic programming, no evaluation noise). Responses are episodes of variable length; episodes that hit the horizon are capped and not admitted, so ρ and H can separate. 22 candidates (16 single-region settings × slack × reward noise σ, plus 6 generator mixtures), 4 MLP scales (72 to 18,692 parameters), GRPO with KL 1.0 to the start policy, budgets 25.6k / 51.2k / 102.4k tokens, five seeds per cell. An exact-gradient oracle trains the same number of steps on the exact noise-free objective.

| check (PROTOCOL.md) | result |
|---|---|
| Gate: ≥3 candidates positive at n4, 102.4k tokens | **pass: 20 of 22** (236 of 255 cells positive overall; the mean candidate gains +3.45 pts) |
| Separation: \|corr(log ρ, H)\| < 0.85 | **pass, barely: 0.820** (by scale 0.80–0.84) |
| T1: Eq. 7 beats budget+scale only at n4 | passes only formally: RMSE 3.51 vs 3.54 pts, rank accuracy 0.645 vs 0.500 |
| T2: law regret below random and every baseline | beats random (0.98 vs 4.32 pts), **loses to best fixed candidate from n1–n3** (0.51) |

| choice rule at n4, 102.4k tokens | regret (pts) |
|---|---|
| ρ–H law (picks b13_r3_sl0_sg0.5, +6.76 pts, seed SD 1.02) | 0.98 |
| best fixed from n1–n3 (b12_r3_sl0_sg0.0) | 0.51 |
| highest mixed-group share | 4.16 |
| uniform random | 4.32 |
| exact-gradient oracle's ranking | 3.77 |
| H only | 4.92 |
| highest start success | 8.58 |
| ρ only | 9.70 |

Observed best: b08_r2_sl0_sg0.0, +7.63 pts (seed SD 1.52); the law's pick is within one seed SD of it.

### What the numbers say

1. **The RL setup now transfers.** Unlike Night 1 (0/288) and Night 2 (gains of tenths of a point), gains here are several points with seed SDs of 0.2–1.5 pts, so T1/T2 can be read. Verdict **CHOICE ONLY**: ρ and H together pick well (rank accuracy 0.645, regret 0.98 pts), much better than either alone (regret 9.70 and 4.92), but a skeptic's "best env from the small models" does as well or better.
2. **ρ counts reward noise as signal.** With σ = 0.5, an already-solved environment (b15, start success 0.99) has the largest ρ of all (110,943 vs 3,079 for the same env without noise) and the law predicts +7.46 pts; observed −2.73, the worst candidate. Across all candidates noise raises log ρ by +0.69 while observed utility is unchanged (+3.58 vs +3.33 pts). This is the law's largest miss and a concrete failure mode for verifiers with noisy or continuous rewards.
3. **The exact-gradient oracle is not the right "truth" for sampled RL.** It gains 5–7× more (it sees every state with no sampling noise) and favors starting far from the goal (oracle pick m03_r012_sl0, +49.9 pts exact vs +3.81 observed), where sampled episodes rarely succeed. Spearman(observed, oracle) = 0.54; the law tracks observed utility (0.38), not the oracle (0.01).
4. **Caveats.** One start policy per scale (no pretraining repeats), n2 and n3 start policies are close (target value 0.437 vs 0.444), and the observations are five-seed means without intervals on regret.

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

## Night 1 planned next steps (historical; Night 2 results above)

1. KL coefficient 1.0 in every run, and candidates that are *mixtures* of settings proposed by the generator (random subsets of the 9 settings, n, l ranges), so some candidates can actually raise the target. Gate: at least 3 of the candidates with positive n4 utility before reading T1/T2.
2. Separate ρ from H: multi-token answers (predict the next k symbols, reward = exact match or per-symbol partial credit) with a generation cap, so lengths and admission vary.
3. Deepen the scale axis: pretraining steps grow with model size so n4 is clearly stronger than n3.
4. Code and run the known-MDP sanity family.

**Historical Night 1 summary:** Night 1 ran the full toy pipeline on CPU with real numbers: the ρ–H law picked the least harmful environment (regret 0.00 vs 12.63 pts for random), but so did trivial baselines, every RL run lowered the target (0/288 positive), and log ρ and H were 0.995 correlated. Verdict NOT YET MEANINGFUL; night 2 adds a KL penalty, mixture candidates and multi-token answers.

**Snapshot:**
```
diag_kl (v2 target, 200 steps, lr 5e-4)
n3 e10  kl=0.0  env 0.725->0.833  target 0.502->0.477
n3 e10  kl=1.0  env 0.725->0.818  target 0.502->0.501
n2 e04  kl=0.0  env 0.291->0.857  target 0.483->0.239
n2 e04  kl=1.0  env 0.291->0.529  target 0.483->0.467
```

**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Night 2 (GINC, Codex on skampere1) completed all 384 cells at $0 with a tie against baselines (law pick +0.0375 pp, interval includes zero). The known-MDP sanity family (expt_v3, same night, 4-CPU machine) finally gives clear positive transfer (20 of 22 candidates, mean +3.45 pts) and separates ρ from H (corr 0.82): the ρ–H law beats random (regret 0.98 vs 4.32 pts) but not the best fixed environment from small models (0.51), verdict CHOICE ONLY, and ρ mistakes reward noise on solved prompts for signal.

**Snapshot:**
```text
GINC night 2 (expt_v2): 384/384 cells, n4 law pick e08 +0.0375 pp [-0.35,+0.45], TIE WITH BASELINES
known MDP (expt_v3):    gate 20/22 positive at n4, corr(log rho,H)=0.820
                        regret: law 0.98 | best-fixed-small 0.51 | random 4.32 | rho-only 9.70 pts
                        noisy solved env b15: rho 110,943, predicted +7.46, observed -2.73 pts
verdict (expt_v3): CHOICE ONLY
```
