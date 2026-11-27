# Experiment 16 results: ρ–H law for picking RL environments on toy GINC-style HMM tasks

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/results.md>

Design: [README.md](README.md). Night 1 measurements are preserved below in `expt_v1/results/`; the Night 2 continuation uses `expt_v2/results/pilot_v3/`; the known-MDP runs use `expt_v3/results/mdp_v1/` (Night 2b) and `expt_v3/results/mdp_v2/` (Night 3); Night 4 uses `expt_v4/results/night4/`; Night 5 (replication) uses `expt_v5/results/night5/`.

## Night 5: Night 4 replicated on independent start checkpoints (`expt_v5`) — POSITIVE again; all three pre-registered predictions hold

**Status:** run complete, 10-26-2026 10:57–13:15 PDT, ultimate_brando9's 4-CPU machine (heavily shared, load ~12-17), CPU only, $0. Protocol, code and predictions frozen and pushed (16715b7) before any probe or RL; n1–n3 cells and the n4 forecast pushed (8b09301) before any n4 trajectory existed. [expt_v5/PROTOCOL.md](expt_v5/PROTOCOL.md), [night5.sh](expt_v5/night5.sh), full numbers in [expt_v5/results/night5/analysis.json](expt_v5/results/night5/analysis.json).

**Takeaway.** With freshly pretrained start checkpoints at all four scales (new init, new pretraining-document draw, new batch order; same concept bank, steps, environments, S2 strength, seeds, budgets and rules as Night 4), law+alpha's n4 regret is 0.96 pts [0.56, 1.73] vs uniform random 2.23 [2.08, 2.72], so the frozen rule again says POSITIVE (paired difference [−1.72, −0.84]). The Night 4 reading also replicates: the plain law is just as good (0.93 [0.53, 1.66]; law+alpha minus law [−0.24, +0.32]), and "best environment on n3" (m02) has the lowest point regret (0.14 [0.00, 1.45]); law+alpha minus best-fixed [−0.16, +1.52] does not separate. So the changed law beats random because it avoids the disastrous environments, not because it finds the best one.

| prediction (frozen before RL) | Night 4 | Night 5 | holds |
|---|---|---|---|
| P1 law+alpha interval below random's | 1.08 [0.55, 1.82] vs 2.22 [2.03, 2.63] | 0.96 [0.56, 1.73] vs 2.23 [2.08, 2.72] | yes |
| P2 law+alpha not better than law | diff [−0.23, +0.51] | diff [−0.24, +0.32] | yes |
| P3 best-on-n3 lowest point regret | 0.12 | 0.14 (m02 again) | yes |

| choice rule at n4 (mean over 3 budgets) | picks (12.8k, 25.6k, 51.2k) | regret (pts) | 95% interval |
|---|---|---|---|
| law+alpha | m03, e08, e08 | 0.96 | [0.56, 1.73] |
| ρ–H law (Eq. 7) | e08, e08, e08 | 0.93 | [0.53, 1.66] |
| alpha alone | m03, m03, m03 | 0.48 | [0.26, 1.04] |
| best fixed on n3 | m02, m02, m02 | 0.14 | [0.00, 1.45] |
| uniform random | all 16 | 2.23 | [2.08, 2.72] |

Other numbers: alpha ranks observed n4 utility at Spearman 0.72 (grad_cos 0.66, k-step NLL drop 0.65); the law's own predictions rank it at −0.21, law+alpha at 0.46 (Night 4: 0.63 / −0.10 / 0.45). alpha is nearly uncorrelated with log ρ (0.10) and H (0.01). Positive cells (of 144): n1 31, n2 30, n3 28, n4 12 (Night 4: 18, 46, 41, 17); mean final KL 0.12 / 0.19 / 0.22 / 0.27. At n4 only m01 and m02 gain at the largest budget (+0.27, +0.31 pts); e00 loses 11.3 pts. Denominators: 16 environments × 3 seeds × 3 budgets per scale, 4,000 target prompts, bootstrap 2,000 draws with every rule refit per draw.

**Read.** The Night 4 result does not depend on its single start checkpoint: it replicates under an independent draw of the start policy at every scale. What it shows is limited: n4 is a forgetting regime (132 of 144 cells not positive), so beating random means avoiding a few bad environments; all learned rules and the n3 baseline do that; none beats "best on n3". Remaining caveats: still one start checkpoint per scale per night (two independent checkpoints now agree), three RL seeds, a single toy family, and utility measured on the same target as the probes.

**Deviations (disclosed).** Python environment: venv `mrmr` (numpy 1.26.4, torch 2.14.1 CPU; versions in `n*_meta.json`), not Night 4's. `expt_v2/run.py` and `policy.py` gained an `E16_PRETRAIN_SEED` / `gen_seed` hook whose default reproduces Night 2/4 exactly. RL strength reused from Night 4's frozen receipt (no new pilot). No cell was rerun or dropped.

## Night 4: target-alignment term alpha added to the ρ–H law, GINC tiny transformers (`expt_v4`) — POSITIVE by the frozen rule, but alpha adds nothing over the law and the small-model baseline is best

**Status:** run complete, 10-20-2026 12:40–17:29 PDT, ultimate_brando9's 4-CPU machine, CPU only, $0. Protocol and code frozen and pushed (04da045) before any RL; pilot, RL-strength receipt, probes, alpha, n1–n3 cells and the n4 forecast pushed (661a84d) before any n4 trajectory existed. [expt_v4/PROTOCOL.md](expt_v4/PROTOCOL.md), [night4.py](expt_v4/night4.py), [night4.sh](expt_v4/night4.sh); full numbers in [expt_v4/results/night4/analysis.json](expt_v4/results/night4/analysis.json).

**Takeaway.** law+alpha's n4 regret (1.08 pts [0.55, 1.82]) is entirely below uniform random's (2.22 [2.03, 2.63]), so the frozen decision rule says POSITIVE. Read with care: the plain law also beats random here (0.93 [0.44, 1.73]), law+alpha is not better than the law (paired difference [−0.23, +0.51]), and the simplest rule, "the best environment on n3", has the lowest regret (0.12 [0.00, 1.49]). alpha does fix the ranking: alone it ranks observed n4 utility at Spearman 0.63 where the law's predictions rank it at −0.10, but its top pick (m03) is not the best environment, and inside the law its coefficient (+1.1 pts per SD) changes the pick at two budgets only, to e02, which is no better.

Same 16 candidates (e00–e11 and Night 2's mixtures m00–m03), scales (4,496 / 27,824 / 104,784 / 604,432 parameters, re-pretrained here with Night 2's frozen code; start target joint 0.266 / 0.307 / 0.324 / 0.357), probes, target set (4,000 prompts) and budgets (12.8k / 25.6k / 51.2k generated tokens) as Night 2. New: a pre-registered n3 pilot picked the RL strength, 3 seeds instead of 2, and alpha.

| step | result |
|---|---|
| RL strength pilot (n3, F = between-env / within-env variance) | S1 (Night 2: lr 1e-4, KL 1.0) F 4.6, mean +0.30 pts; **S2 (lr 3e-4, KL 0.1) F 171.3, mean −1.61 pts: chosen**; S3 (1e-3, 0.1) F 62.8, mean −3.97 pts |
| Main matrix | 192 trajectories, 576 cells, all present; positive cells n1 18, n2 46, n3 41, n4 17 of 144; mean final KL 0.12 / 0.18 / 0.22 / 0.27 |
| n4 regime | forgetting: the mean environment loses 1.3 / 2.0 / 2.4 pts; only m01 and m02 gain (best +0.08 m01, +0.39 m01, +0.42 m02); e00 loses 10.8 pts at 51.2k |
| alpha vs the law's features at n4 | corr with log ρ 0.16, with H 0.10 (alpha is new information) |

| choice rule at n4 (mean over 3 budgets) | picks (12.8k, 25.6k, 51.2k) | regret (pts) | 95% interval | law+alpha minus rule, 95% interval |
|---|---|---|---|---|
| law+alpha | e02, e02, e08 | 1.08 | [0.55, 1.82] | – |
| ρ–H law (Eq. 7) | e08, e08, e08 | 0.93 | [0.44, 1.73] | [−0.23, +0.51] |
| alpha alone | m03, m03, m03 | 0.65 | [0.36, 1.16] | [−0.26, +1.01] |
| best fixed on n3 | m02, m02, m02 | 0.12 | [0.00, 1.49] | [−0.28, +1.51] |
| uniform random | all 16 | 2.22 | [2.03, 2.63] | **[−1.69, −0.67]** |

Intervals: 2,000 bootstrap draws resampling the three seeds per scale and the 4,000 target prompts, every rule refit per draw. alpha alone also beats random (paired [−1.92, −1.21]).

### What the numbers say

- Under a strength that actually moves the policy (KL 0.27 at n4 vs ~0.004 in Night 2), environments separate cleanly (F 171 vs 4.6), and most of them hurt the target. Beating random then mostly means avoiding the few disastrous environments (e00, e10, e03, e07, e11), which the law, alpha and the n3 baseline all do.
- alpha measures what it was built to measure: environments whose few-step gradient points toward the target transfer better (Spearman 0.63; gradient cosine alone 0.64, k-step NLL drop alone 0.61). Eq. 7's own forecast does not rank n4 at all (−0.10); adding alpha brings it to 0.45.
- Picking the single best environment is a harder test than ranking, and there alpha does not help: the top-alpha environment m03 ends near zero, the best (m01/m02) gain under half a point, and the n3 winner m02 carries over to n4.
- Caveats: one starting checkpoint per scale (intervals are conditional on pretraining), three seeds, and a forgetting regime where 127 of 144 n4 cells are not positive.

### Execution notes

- Night 2's checkpoints are on skampere1, so n1–n4 were re-pretrained here with the frozen expt_v2 code (n4 took 4,932 s). The first n3/n4 pretrains were stopped at 12:31/12:33 by an infrastructure stop and restarted from scratch (`*_pretrain.interrupted_1223.log`, not committed). The driver was stopped twice by a shell time limit (about 14:45 and 16:47); in-flight cells were rerun from scratch with the same seeds, no completed cell was redone or dropped. The n4 alpha probe ran early, as soon as n4 pretraining ended; it is not an outcome.

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

Intervals: 2,000 bootstrap resamples of start-policy repeats (per scale) and seeds (per repeat), law and best-fixed label refit each time. The law has higher regret than every other rule in 100% of resamples (QA 11-25-2026: not reproduced; rho-only ties the law in 100% of 2,000 recomputed draws, highest-start ties in 1,195 and is worse than the law in 804; the NO ADVANTAGE verdict stands). Bootstrap intervals on a max-minus-pick quantity lean high (resampling adds noise to the max), so the best-fixed interval sits partly above its point value.

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

| choice rule at n4, mean over the three budgets (QA 11-25-2026: previously labelled 102.4k tokens; recomputed at 102.4k: law 0.88, best fixed 0.11, highest mixed share 4.06, random 4.18, oracle 3.82, H only 4.16, highest start 8.51, rho only 10.36) | regret (pts) |
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

**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Night 2 (GINC) completed all 384 cells at $0 with a tie against baselines (law pick +0.0375 pp, interval includes zero). The known-MDP sanity family (expt_v3) gives positive transfer (20 of 22 candidates, mean +3.45 pts) and separates ρ from H (corr 0.82): the ρ–H law beats random (regret 0.98 vs 4.32 pts) but not the best fixed environment from small models (0.51), verdict CHOICE ONLY on that night, and Night 3's repeat is NO ADVANTAGE. Night 4 and Night 5 (fresh start checkpoints) are POSITIVE by the frozen rule; Night 5 law+alpha regret is 0.96 [0.56, 1.73] versus random 2.23 [2.08, 2.72], and P1–P3 hold (refreshed 11-27-2026 from the sections above).

**Snapshot:**
```text
GINC night 2 (expt_v2): 384/384 cells, n4 law pick e08 +0.0375 pp [-0.35,+0.45], TIE WITH BASELINES
known MDP (expt_v3):    gate 20/22 positive at n4, corr(log rho,H)=0.820
                        regret: law 0.98 | best-fixed-small 0.51 | random 4.32 | rho-only 9.70 pts
                        noisy solved env b15: rho 110,943, predicted +7.46, observed -2.73 pts
verdict (expt_v3): CHOICE ONLY
```
