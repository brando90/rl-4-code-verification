# expt_v4 protocol: Night 4, a target-alignment term alpha added to the rho-H law (frozen before any RL)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v4/PROTOCOL.md>

**TLDR:** Does adding a target-alignment term alpha (how much a few steps of RL on an environment move the target, measured from the start policy) to Equation 7 fix environment choice on the GINC tiny-transformer family? Decision rule, rules compared, seeds and analysis are frozen here, before the pilot or any main GRPO trajectory exists.

Written 10-20-2026 12:45 PDT by ultimate_brando9. At this point only the n1/n2 starting checkpoints existed (n3/n4 pretraining running) and no GRPO step of Night 4 had been taken. Code: `night4.py` (stages), `night4.sh` (order), tests `tests/test_e16_night4.py`.

## Why

- Night 2 (`expt_v2`): Eq. 7 tied the baselines; policies barely moved (final KL ~0.004, between-environment spread of n3 utilities ~0.1–0.2 points), so the test had little power.
- Night 3 (`expt_v3`, known MDP): law regret 10.78 [9.53, 12.28] vs random 4.42, NO ADVANTAGE. rho is inflated by reward noise and tracks learnability, not transfer to the target. Nothing in Eq. 7 says whether learning an environment helps the target; alpha is that missing term.

## Unchanged from expt_v2

- GINC four-token HMM family, the 16 candidates (e00–e11 and Night 2's frozen generated mixtures m00–m03, `mixtures.json` copied unchanged), four transformer scales n1–n4, pretraining (steps, data, seeds), probes (rho, H from `expt_v2.run probe`), rewards, GRPO implementation (`expt_v2.policy.grpo`), budgets 25/50/100 steps = 12,800/25,600/51,200 generated tokens, prompt pools (train 20,000 seed 13, in-env 512 seed 12) and the primary target (4,000 prompts, seed 99, joint exact match).
- Night 2's checkpoints live on skampere1; the four scales are re-pretrained here with the identical frozen code and seeds (CPU, one thread). Checkpoint hashes are in `results/night4/n*_meta.json`. The n3/n4 pretrains were interrupted once (12:31/12:33) by an infrastructure stop and restarted from scratch; the partial logs are kept as `*_pretrain.interrupted_1223.log`.

## RL strength (pre-registered pilot)

- Candidates, weakest first: S1 = Night 2 (Adam lr 1e-4, KL 1.0), S2 = (3e-4, 0.1), S3 = (1e-3, 0.1). Everything else as Night 2.
- Pilot: n3, all 16 environments, pilot seeds 100 and 101, S2 and S3 (S1's statistic comes from Night 2's committed n3 cells, seeds 0/1). Pilot trajectories are excluded from every later analysis.
- Statistic per setting: F = between-environment variance of seed-mean final-budget utility / mean within-environment variance of a seed mean. Admissible: mean final n3 utility > −5 points. Chosen: the highest F among admissible; any setting within 5% of the best F counts as tied and the weakest tied one wins. The choice is frozen (`rl_setting.json` + hash) before alpha probes and main RL.

## alpha (target alignment), per (scale, environment), from the start policy

- Target-dev set: 512 target prompts at seed 98 (disjoint seed from the seed-99 evaluation set; target-dev never trains anything).
- grad_cos: cosine between the environment's GRPO policy-gradient (256 prompts seed 14 × 8 samples seed 15, KL term off since its gradient is zero at the start policy) and the gradient of teacher-forced target-dev NLL of the oracle continuation.
- dev_nll_drop: drop in target-dev NLL after k = 10 GRPO steps on the environment at the frozen strength, mean over probe seeds 21 and 22.
- alpha = mean of the within-scale z-scores of grad_cos and dev_nll_drop. Probe cost: 8,192 + 2 × 5,120 generated tokens per cell, not counted in the budgets.

## Main matrix

- 4 scales × 16 environments × seeds 0, 1, 2 = 192 GRPO trajectories, 576 budget cells; utility = target joint exact-match gain over the start policy. Order: n1–n3 first; the n4 forecast is frozen (`forecast_n4.json`, with hashes of every input) before any n4 trajectory; `freeze` refuses to run if an n4 outcome exists.

## Rules compared at n4 (fit on n1–n3, seed-mean observations)

1. law: Eq. 7 (`rl4cv.utility_model`, RHO_H, reference scales n1 and n3), unchanged.
2. law+alpha: Eq. 7's design row plus b_alpha × standardized alpha (standardized over the training cells), ordinary least squares.
3. alpha-alone: highest n4 alpha.
4. best-fixed-n3: highest mean n3 utility over budgets and seeds.
5. uniform random: expected utility of a uniformly chosen environment.
Exact ties are resolved by averaging all tied environments. Each rule picks per budget.

## Primary outcome and decision rule

- Primary: n4 allocation regret in joint exact-match points (best observed n4 environment minus the chosen one, seed means), averaged over the three budgets.
- Uncertainty: 2,000 bootstrap draws, each resampling the three training seeds with replacement independently per scale and the 4,000 target prompts (multinomial), refitting every rule on the resampled n1–n3 data; the point estimate uses the frozen choices. 95% percentile intervals.
- **POSITIVE** iff the upper end of law+alpha's 95% interval is below the lower end of uniform random's. **NOT ESTABLISHED** if law+alpha's point regret is below random's but the intervals overlap. Otherwise **NO ADVANTAGE**.
- Secondary (reported, not decisive): paired bootstrap differences law+alpha minus each other rule, and alpha-alone minus random/law/best-fixed; Spearman of alpha, its two parts, and both laws' predictions with observed final n4 utility; correlation of alpha with log rho and H at n4; positive-cell counts and final KL per scale.

## Hygiene

- CPU only (this machine), nice 10, one PyTorch thread per process, at most 4 concurrent processes, $0, no hosted inference.
- No outcome-based reruns, dropped cells, extra seeds or changed budgets. Stages are resumable and write immutable per-cell files; an interrupted cell is rerun from scratch with the same seed, and the interruption is logged in results.md.
