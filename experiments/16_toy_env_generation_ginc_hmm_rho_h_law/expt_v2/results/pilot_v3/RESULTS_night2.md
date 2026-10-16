# Night 2 results: 16_toy_env_generation_ginc_hmm_rho_h_law

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3/RESULTS_night2.md>

**TLDR:** TIE WITH BASELINES. All 384 budget cells completed; 224/384 have strictly positive joint target utility.

Positive prevalence: 58.3333 [56.5104, 60.1562] percent, p-val=n/a (descriptive; user threshold 30%). Final-budget positive trajectories: 79/128.

Primary target is joint exact-match agreement with the sequential Bayes oracle over 4,000 common target prompts. Units below are percentage points. Intervals use 2,000 paired prompt/seed bootstrap draws (seed 1616), conditional on fixed pretraining checkpoints and frozen selections. Only two training seeds: intervals do not establish broad training robustness or cover forecast-selection uncertainty. One-sided exact seed sign-flip p-values test zero mean advantage; minimum attainable p-value is 0.25.

| Budget | Method | Chosen environment(s) | Utility [95% interval] | p-val | Regret |
|---:|---|---|---:|---:|---:|
| 12800 | H-only | e09 | 0.0750 [-0.3500, 0.4878] | 0.250 | 0.175 |
| 25600 | H-only | e09 | -0.0375 [-0.4878, 0.4250] | 0.750 | 0.388 |
| 51200 | H-only | e09 | 0.1375 [-0.3750, 0.6250] | 0.500 | 0.200 |
| 12800 | best-fixed-n3 | e09 | 0.0750 [-0.3500, 0.4878] | 0.250 | 0.175 |
| 25600 | best-fixed-n3 | e09 | -0.0375 [-0.4878, 0.4250] | 0.750 | 0.388 |
| 51200 | best-fixed-n3 | e09 | 0.1375 [-0.3750, 0.6250] | 0.500 | 0.200 |
| 12800 | budget-scale-only | e00, e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, m00, m01, m02, m03 | 0.0195 [-0.2141, 0.2578] | 0.500 | 0.230 |
| 25600 | budget-scale-only | e00, e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, m00, m01, m02, m03 | 0.0414 [-0.1954, 0.2813] | 0.250 | 0.309 |
| 51200 | budget-scale-only | e00, e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, m00, m01, m02, m03 | 0.0555 [-0.1875, 0.3064] | 0.250 | 0.282 |
| 12800 | highest-mixed-share | m00 | 0.0500 [-0.3750, 0.5003] | 0.500 | 0.200 |
| 25600 | highest-mixed-share | m00 | 0.0375 [-0.4750, 0.5128] | 0.500 | 0.312 |
| 51200 | highest-mixed-share | m00 | 0.0125 [-0.3253, 0.3750] | 0.500 | 0.325 |
| 12800 | highest-pass-variance | e01 | -0.1125 [-0.5128, 0.2750] | 1.000 | 0.362 |
| 25600 | highest-pass-variance | e01 | 0.0500 [-0.3750, 0.4250] | 0.250 | 0.300 |
| 51200 | highest-pass-variance | e01 | 0.3375 [-0.0750, 0.7500] | 0.250 | 0.000 |
| 12800 | rho-H | e08 | 0.1000 [-0.3000, 0.4878] | 0.500 | 0.150 |
| 25600 | rho-H | e08 | 0.0500 [-0.3250, 0.4250] | 0.500 | 0.300 |
| 51200 | rho-H | e08 | 0.0375 [-0.3500, 0.4500] | 0.500 | 0.300 |
| 12800 | rho-only | e04 | 0.2375 [-0.1000, 0.5753] | 0.250 | 0.013 |
| 25600 | rho-only | e04 | 0.2250 [-0.1250, 0.5500] | 0.250 | 0.125 |
| 51200 | rho-only | e04 | 0.1625 [-0.2000, 0.5125] | 0.250 | 0.175 |
| 12800 | uniform-random | e00, e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, m00, m01, m02, m03 | 0.0195 [-0.2141, 0.2578] | 0.500 | 0.230 |
| 25600 | uniform-random | e00, e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, m00, m01, m02, m03 | 0.0414 [-0.1954, 0.2813] | 0.250 | 0.309 |
| 51200 | uniform-random | e00, e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, m00, m01, m02, m03 | 0.0555 [-0.1875, 0.3064] | 0.250 | 0.282 |

## Paired advantage of Equation 7 at 51,200 tokens

| Baseline | Difference [95% interval] | p-val |
|---|---:|---:|
| H-only | -0.1000 [-0.5628, 0.3875] | 1.000 |
| best-fixed-n3 | -0.1000 [-0.5628, 0.3875] | 1.000 |
| budget-scale-only | -0.0180 [-0.3470, 0.3266] | 0.750 |
| highest-mixed-share | 0.0250 [-0.4250, 0.5000] | 0.500 |
| highest-pass-variance | -0.3000 [-0.7753, 0.1750] | 1.000 |
| rho-only | -0.1250 [-0.5506, 0.2750] | 1.000 |
| uniform-random | -0.0180 [-0.3470, 0.3266] | 0.750 |

## Frozen prediction accuracy at n4

| Features | RMSE [95% candidate bootstrap] | Pairwise rank accuracy | Mean bias (prediction minus observation) |
|---|---:|---:|---:|
| rho-H | 0.3513 [0.2747, 0.4276] p-val=n/a | 0.4722 p-val=n/a | +0.306 |
| rho-only | 0.3289 [0.2580, 0.3966] p-val=n/a | 0.4806 p-val=n/a | +0.282 |
| H-only | 0.3203 [0.2478, 0.3886] p-val=n/a | 0.4972 p-val=n/a | +0.274 |
| budget-scale-only | 0.3191 [0.2471, 0.3896] p-val=n/a | 0.5000 p-val=n/a | +0.272 |

Candidate bootstrap treats the fixed candidates as a descriptive sampling population, preserving all budgets for each candidate; mixtures share components, so this is not evidence of independent environment-family replication. Pairwise rank accuracy has no inferential interval here (one frozen fit); it is descriptive. Raw per-prompt token hits and cell tables are committed beside this report. Forecast input hashes and the append-only ledger establish chronology.

## n4 environment table at 51,200 tokens

| Environment | Observed joint utility | Predicted utility | Token utility |
|---|---:|---:|---:|
| e00 | -0.063 | +0.308 | -0.487 |
| e01 | +0.337 | +0.343 | +0.038 |
| e02 | +0.287 | +0.390 | -0.006 |
| e03 | -0.175 | +0.396 | -0.181 |
| e04 | +0.162 | +0.371 | -0.016 |
| e05 | +0.100 | +0.323 | -0.094 |
| e06 | +0.025 | +0.369 | -0.222 |
| e07 | -0.063 | +0.349 | -0.309 |
| e08 | +0.037 | +0.449 | -0.162 |
| e09 | +0.137 | +0.379 | +0.069 |
| e10 | -0.350 | +0.329 | -0.437 |
| e11 | -0.225 | +0.428 | -0.334 |
| m00 | +0.012 | +0.333 | -0.069 |
| m01 | +0.312 | +0.322 | +0.169 |
| m02 | +0.212 | +0.353 | -0.041 |
| m03 | +0.137 | +0.322 | +0.041 |

**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Night 2 verdict: TIE WITH BASELINES; 224/384 positive budget cells.
