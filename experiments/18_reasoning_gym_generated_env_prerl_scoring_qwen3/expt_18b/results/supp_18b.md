## Per env x seed (held-out target = mean of 6 components; pre is the same base-model value for every run)

Base model held-out pass rate (6-component mean, 8 samples x 256 items per component): 0.343.

| env | seed | pre | post | gain [95% CI, items] | in-env gain | train response tokens | train reward first 5 / last 5 steps | skipped steps |
|---|---|---|---|---|---|---|---|---|
| rg/simple_equations/L0 | 0 | 0.343 | 0.653 | +0.310 [+0.292, +0.328] | +0.285 | 2,390,913 | 0.74 / 0.96 | 0 |
| rg/simple_equations/L0 | 1 | 0.343 | 0.659 | +0.316 [+0.299, +0.335] | +0.305 | 2,213,852 | 0.73 / 0.94 | 0 |
| rg/mini_sudoku/L2 | 0 | 0.343 | 0.467 | +0.125 [+0.107, +0.143] | +0.303 | 6,099,989 | 0.05 / 0.31 | 0 |
| rg/mini_sudoku/L2 | 1 | 0.343 | 0.130 | -0.213 [-0.232, -0.194] | -0.031 | 1,690,013 | 0.09 / 0.05 | 0 |
| rg/family_relationships/L0 | 0 | 0.343 | 0.040 | -0.302 [-0.320, -0.284] | -0.717 | 91,080 | 0.81 / 0.00 | 0 |
| rg/family_relationships/L0 | 1 | 0.343 | 0.416 | +0.073 [+0.055, +0.092] | +0.283 | 122,058 | 0.82 / 1.00 | 0 |
| rg/basic_arithmetic/L0 | 0 | 0.343 | 0.210 | -0.133 [-0.153, -0.112] | +0.389 | 86,322 | 0.80 / 0.93 | 0 |
| rg/basic_arithmetic/L0 | 1 | 0.343 | 0.212 | -0.130 [-0.149, -0.110] | +0.381 | 88,386 | 0.64 / 0.94 | 0 |
| rg/family_relationships/L1 | 0 | 0.343 | 0.258 | -0.085 [-0.108, -0.060] | +0.156 | 1,880,242 | 0.36 / 0.79 | 0 |
| rg/family_relationships/L1 | 1 | 0.343 | 0.648 | +0.306 [+0.288, +0.322] | +0.488 | 1,376,792 | 0.40 / 0.79 | 0 |
| rg/basic_arithmetic/L2 | 0 | 0.343 | 0.551 | +0.208 [+0.189, +0.229] | +0.250 | 4,918,705 | 0.42 / 0.66 | 0 |
| rg/basic_arithmetic/L2 | 1 | 0.343 | 0.619 | +0.276 [+0.259, +0.293] | +0.412 | 6,054,417 | 0.41 / 0.57 | 0 |
| rg/letter_counting/L3 | 0 | 0.343 | 0.159 | -0.183 [-0.201, -0.165] | +0.111 | 99,163 | 0.33 / 0.34 | 0 |
| rg/letter_counting/L3 | 1 | 0.343 | 0.134 | -0.209 [-0.225, -0.192] | +0.111 | 84,544 | 0.30 / 0.33 | 0 |
| rg/leg_counting/L2 | 0 | 0.343 | 0.655 | +0.312 [+0.297, +0.329] | +0.559 | 5,187,203 | 0.68 / 0.99 | 0 |
| rg/leg_counting/L2 | 1 | 0.343 | 0.627 | +0.284 [+0.266, +0.302] | +0.443 | 3,015,142 | 0.58 / 0.86 | 0 |
| rg/basic_arithmetic/L3 | 0 | 0.343 | 0.662 | +0.320 [+0.302, +0.337] | +0.459 | 6,268,140 | 0.19 / 0.53 | 0 |
| rg/basic_arithmetic/L3 | 1 | 0.343 | 0.592 | +0.250 [+0.231, +0.267] | +0.215 | 7,227,895 | 0.22 / 0.31 | 0 |
| rg/mini_sudoku/L0 | 0 | 0.343 | 0.653 | +0.311 [+0.294, +0.328] | +0.600 | 6,393,130 | 0.27 / 0.81 | 0 |
| rg/mini_sudoku/L0 | 1 | 0.343 | 0.585 | +0.242 [+0.224, +0.261] | +0.730 | 6,921,962 | 0.33 / 0.87 | 0 |
| rg/leg_counting/L3 | 0 | 0.343 | 0.691 | +0.348 [+0.331, +0.366] | +0.584 | 3,545,954 | 0.51 / 0.87 | 0 |
| rg/leg_counting/L3 | 1 | 0.343 | 0.670 | +0.328 [+0.309, +0.345] | +0.592 | 5,669,316 | 0.47 / 0.81 | 0 |
| rg/leg_counting/L1 | 0 | 0.343 | 0.684 | +0.341 [+0.324, +0.358] | +0.826 | 2,589,494 | 0.55 / 0.97 | 0 |
| rg/leg_counting/L1 | 1 | 0.343 | 0.578 | +0.236 [+0.219, +0.251] | +0.826 | 2,002,046 | 0.55 / 0.96 | 0 |
| rg/word_sorting/L0 | 0 | 0.343 | 0.306 | -0.037 [-0.056, -0.018] | +0.350 | 5,258,540 | 0.01 / 0.34 | 0 |
| rg/word_sorting/L0 | 1 | 0.343 | 0.046 | -0.296 [-0.314, -0.279] | -0.018 | 223,654 | 0.01 / 0.00 | 0 |
| rg/letter_counting/L1 | 0 | 0.343 | 0.199 | -0.143 [-0.167, -0.119] | -0.037 | 82,600 | 0.30 / 0.17 | 0 |
| rg/letter_counting/L1 | 1 | 0.343 | 0.223 | -0.120 [-0.142, -0.097] | +0.213 | 82,490 | 0.29 / 0.43 | 0 |
| rg/mini_sudoku/L1 | 0 | 0.343 | 0.587 | +0.244 [+0.226, +0.263] | +0.684 | 6,448,212 | 0.10 / 0.74 | 0 |
| rg/mini_sudoku/L1 | 1 | 0.343 | 0.587 | +0.245 [+0.226, +0.262] | -0.041 | 7,592,719 | 0.17 / 0.27 | 0 |
| rg/family_relationships/L2 | 0 | 0.343 | 0.215 | -0.128 [-0.147, -0.109] | +0.078 | 83,432 | 0.30 / 0.49 | 0 |
| rg/family_relationships/L2 | 1 | 0.343 | 0.646 | +0.303 [+0.286, +0.321] | +0.262 | 2,991,962 | 0.34 / 0.73 | 0 |

Seed agreement: mean |seed0 - seed1| gain 0.138, max 0.431 (rg/family_relationships/L2); Pearson +0.568; same sign in 12/16 envs.
Gain range over envs: -0.196 to +0.338; 10/16 envs have positive 2-seed gain.

Descriptive check (not a frozen test): Spearman of env mean training response tokens vs gain +0.606; training response tokens per run range 82,545 to 7,020,465 (mean of 2 seeds).
GSM8K-only gain is negative in 8/16 envs; the RG-5 gain is positive in 10/16.

## Paired Spearman differences (frozen analyze.py output)

| comparison | diff | 95% CI |
|---|---|---|
| rho_h-law_alpha | +0.109 | [-0.43, +0.71] |
| rho_h-alpha | +0.868 | [+0.08, +1.38] |
| rho_h-difficulty | +0.670 | [-0.05, +1.22] |
| rho_h-smaller_model | +0.803 | [-0.15, +1.46] |
| rho_h-random | +0.712 | [+0.06, +1.18] |
