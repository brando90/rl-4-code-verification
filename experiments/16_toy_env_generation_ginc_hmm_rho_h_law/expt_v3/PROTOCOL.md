# expt_v3 protocol: known-MDP sanity family (frozen before any RL row)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v3/PROTOCOL.md>

Written 10-15-2026 23:34 PDT by ultimate_brando9, before `results/mdp_v1/rl_*.jsonl` existed. Only start policies and six development trajectories (n4, used to check that the code runs and that RL can move the target) were looked at.

## Why

Night 1 (GINC HMM) was in a forgetting regime; Night 2 (`expt_v2`, Codex on skampere1) got positive point utilities but gains of a few tenths of a point, inside the noise, and the law tied the baselines. A known MDP checks the pipeline itself where the truth is computable: the target value is exact (dynamic programming, no evaluation noise), and an exact-gradient oracle says which training distribution is right without sampling.

## Family

- Chain of 16 states in 4 regions, goal at the end, 4 actions; the correct action moves forward, the rest stay. Each region has its own hidden linear map from state features to the correct action. One action = one generated token.
- Response = episode from a start state until the goal or the horizon T(s0) = (16 − s0) + slack. Reward = 1 on the goal + N(0, sigma²). Episodes that hit the horizon are capped: kept in the group baseline, not admitted.
- Target: every start state, slack 4, no noise; exact success probability, averaged over start states.
- Candidates (22): 16 base settings (one region × slack {0, 6} × sigma {0, 0.5}) and 6 generator mixtures (random 2–4 region subsets, slack {0, 2, 6}, sigma {0, 0.5}; seed 1616).
- Scales: MLPs with 72 / 276 / 1,604 / 18,692 parameters, behavior-cloned 60 / 80 / 100 / 140 steps on a noisy demonstrator (correct 50%, regions 2–3 four times rarer).
- RL: GRPO, group 8, batch 16 start states, leave-one-out advantages, token-normalized loss, exact KL to the start policy with coefficient 1.0 on visited states, Adam lr 3e-3. Budgets 25.6k / 51.2k / 102.4k generated tokens. Five training seeds; an observation is the five-seed mean.
- Probes: 512 start-state groups of 8 under the start policy; rho and H from `rl4cv.experience.measure_environment`, unchanged.
- Oracle: from the same start policy, as many Adam steps as GRPO took to reach 102.4k tokens, on the exact expected success of the candidate (same KL).

## Tests (same as README T1/T2; Eq. 7 from `rl4cv.utility_model`, unchanged)

- **Gate:** at least 3 candidates with positive n4 utility at 102.4k tokens (five-seed mean) before T1/T2 are read.
- **Separation:** |corr(log rho, H)| across the 88 (scale, candidate) probes below 0.85.
- **T1:** Eq. 7 fit on n1–n3 predicts n4 with lower RMSE and higher pairwise rank accuracy than budget-and-scale only.
- **T2:** at n4 the law's allocation regret is below uniform random and below each of: best fixed candidate from n1–n3, highest start success, highest mixed-group share.
- **Verdict:** SUCCESS if T1 and T2 hold against every baseline; CHOICE ONLY if T2 beats random but not every baseline; NO ADVANTAGE otherwise. NOT YET MEANINGFUL if the gate fails.
- **Sanity readouts (descriptive):** Spearman of law prediction and of observed utility against the exact-gradient oracle at n4; whether the high-rho noisy candidates (sigma 0.5) fool the law; five-seed SD of the picked candidate.

## Night 3 addendum (mdp_v2), frozen before any Night 3 RL row

Written 10-16-2026 23:50 PDT by ultimate_brando9, before `results/mdp_v2/rl_*.jsonl` existed. Only start policies (`results/mdp_v2/start_*.json`) were looked at. Code: `run_mdp_v2.py` (imports `run_mdp.py` unchanged), `analyze_mdp_v2.py`.

**Why.** Night 2b gave CHOICE ONLY from one start policy per scale, with no interval on regret, and n2/n3 start values tied (0.437 / 0.444), so the scale axis was weak. The noisy candidate b15 had rho 110,943 (36x its noise-free twin) and the law predicted +7.46 where -2.73 was observed.

**What changes (everything else as above: chain, 22 candidates, 3 budgets, 5 seeds, GRPO, KL 1.0, oracle).**
- Six scales, smaller models get fewer behavior-cloning steps so the start target value rises clearly: s1 (2 wide, 1 layer, 30 steps, 38 params), s2 (4, 1, 60, 72), s3 (8, 1, 60, 140), s4 (16, 1, 60, 276), s5 (32, 1, 80, 548), s6 (64, 2, 100, 5,252). Mean start target value over 3 repeats: 0.182, 0.241, 0.305, 0.378, 0.436, 0.509. The held-out scale is s6; the law is fit on s1-s5.
- Three start-policy repeats per scale (behavior-cloning seed 0/1/2), each with its own probes and its own five RL seeds (15 runs per cell).
- An observation (scale, candidate, budget) is the mean utility over the 15 runs; its rho is the geometric mean and its H the mean over the three repeats' probes. Utility is measured against each repeat's own start value.
- Each probe is also measured on the candidate's noise-free twin (same start states and rollouts, sigma 0). This is a diagnostic only: the law, gate, T1 and T2 use the standard probe.

**Tests.** Gate, separation (over all 396 probes), T1, T2 and the verdict rule are unchanged, read at s6.

**Intervals.** Allocation regret at s6 for the law and every baseline (rho-only, H-only, uniform random, best fixed from s1-s5, highest start success, highest mixed-group share, exact-gradient oracle) gets a 95% percentile bootstrap interval, 2,000 resamples. A resample draws, independently per scale, 3 of the 3 repeats with replacement and, for each drawn repeat, 5 of the 5 seeds with replacement (the same draw for every candidate and budget, so choices stay paired); probes follow their repeats; the law and the best-fixed label are refit on each resample. Also reported: the interval of the paired difference law minus each baseline, and the share of resamples where the law has lower regret. The point estimates and the verdict come from the full data, not the bootstrap.

**Noise diagnostic.** For every s6 candidate: standard rho next to noise-free rho, and the law's prediction with each (same fitted law). Reported: mean absolute prediction error on the noisy (sigma 0.5) candidates with standard vs noise-free rho, b15 in particular, and, separately labelled as diagnostic, the regret of a law fit on noise-free features.
