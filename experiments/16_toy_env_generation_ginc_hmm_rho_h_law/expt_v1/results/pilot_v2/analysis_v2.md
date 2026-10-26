| scale | params | pretrain loss | start greedy acc tgtMix9_L10_pretrain_concepts | start greedy acc tgtA_S8_sh4_n64_L12_heldout |
|---|---|---|---|---|
| n1 | 4,496 | 2.343 | 0.425 | 0.385 |
| n2 | 27,824 | 2.215 | 0.482 | 0.447 |
| n3 | 104,784 | 2.177 | 0.502 | 0.469 |
| n4 | 604,432 | 2.143 | 0.511 | 0.463 |

In-environment held-out accuracy gain after the largest budget, mean over envs and seeds (pts): 4,496 params +15.1, 27,824 params +19.8, 104,784 params +20.2, 604,432 params +20.9.

### Target tgtMix9_L10_pretrain_concepts

Held-out scale 604,432 params; 144 observations; mean |seed0 − seed1| utility gap 0.94 pts; SD of utility across envs at held scale, max budget 14.00 pts; excluded (ρ = 0): none.

| features | RMSE (pts) | rank acc | regret (pts) | LOSO RMSE | LOSO rank acc | LOSO regret | coefficients |
|---|---|---|---|---|---|---|---|
| rho-H | 12.18 | 0.742 | 0.00 | 10.03 | 0.663 | 0.04 | b0=-0.1063, bN=-0.0191, bC=-0.1670, b_rho=-0.4436, b_H=+0.4591 |
| rho-only | 12.79 | 0.677 | 0.00 | 10.39 | 0.635 | 0.04 | b0=-0.0965, bN=-0.0171, bC=-0.1670, b_rho=+0.0120 |
| H-only | 12.75 | 0.662 | 0.00 | 10.36 | 0.633 | 0.04 | b0=-0.0984, bN=-0.0175, bC=-0.1670, b_H=+0.0171 |
| budget-scale-only | 12.82 | 0.500 | 12.63 | 10.40 | 0.500 | 9.14 | b0=-0.0929, bN=-0.0164, bC=-0.1670 |

| choice rule at held-out scale | mean regret (pts, lower is better) |
|---|---|
| ρ–H law (Eq. 7) | 0.00 |
| uniform random candidate | 12.63 |
| best fixed env from small scales (e10_S4_sh4_n64_L24) | 0.00 |
| highest start success | 1.86 |
| highest mixed-group share | 0.00 |

At the held-out scale and the largest budget (51.2k generated tokens): law pick e10_S4_sh4_n64_L24 (-3.80 pts), oracle e10_S4_sh4_n64_L24 (-3.80 pts), candidate mean -18.09 pts.

| env | observed U (pts) | predicted U (pts) | ρ | H | start success |
|---|---|---|---|---|---|
| e10_S4_sh4_n64_L24 | -3.80 | -11.03 | 376,186 | 0.800 | 0.471 |
| e02_S4_sh8_n64_L16 | -5.94 | -17.66 | 363,212 | 0.763 | 0.556 |
| e06_S8_sh8_n64_L24 | -6.07 | -13.88 | 355,190 | 0.766 | 0.457 |
| e03_S8_sh4_n64_L12 | -6.28 | -17.82 | 302,037 | 0.683 | 0.288 |
| e09_S12_sh2_n64_L24 | -6.48 | -19.11 | 218,052 | 0.537 | 0.156 |
| e07_S12_sh4_n64_L8 | -7.11 | -24.69 | 236,537 | 0.554 | 0.188 |
| e05_S8_sh2_n64_L4 | -9.57 | -17.88 | 184,780 | 0.469 | 0.120 |
| e08_S12_sh8_n2_L16 | -29.67 | -19.81 | 323,312 | 0.706 | 0.302 |
| e12_S12_sh4_n2_L4 | -33.07 | -19.85 | 215,541 | 0.530 | 0.160 |
| e11_S8_sh8_n2_L4 | -33.11 | -19.08 | 325,474 | 0.711 | 0.312 |
| e04_S8_sh4_n2_L12 | -35.65 | -21.41 | 266,253 | 0.616 | 0.202 |
| e01_S4_sh2_n2_L4 | -40.38 | -18.42 | 289,342 | 0.662 | 0.215 |

| scale (params) | Spearman(U, log ρ) | Spearman(U, H) | Spearman(U, start success) | mean U | max U |
|---|---|---|---|---|---|
| 4,496 | +0.34 | +0.32 | +0.38 | -9.09 | -1.18 |
| 27,824 | +0.43 | +0.47 | +0.52 | -12.92 | -1.99 |
| 104,784 | +0.46 | +0.46 | +0.48 | -14.82 | -2.40 |
| 604,432 | +0.49 | +0.48 | +0.45 | -18.09 | -3.80 |

### Target tgtA_S8_sh4_n64_L12_heldout

Held-out scale 604,432 params; 144 observations; mean |seed0 − seed1| utility gap 0.89 pts; SD of utility across envs at held scale, max budget 13.09 pts; excluded (ρ = 0): none.

| features | RMSE (pts) | rank acc | regret (pts) | LOSO RMSE | LOSO rank acc | LOSO regret | coefficients |
|---|---|---|---|---|---|---|---|
| rho-H | 11.49 | 0.649 | 0.10 | 9.39 | 0.674 | 0.04 | b0=-0.0992, bN=-0.0193, bC=-0.1661, b_rho=-0.4687, b_H=+0.4951 |
| rho-only | 12.06 | 0.639 | 0.10 | 9.81 | 0.629 | 0.04 | b0=-0.0887, bN=-0.0172, bC=-0.1661, b_rho=+0.0226 |
| H-only | 12.03 | 0.634 | 0.10 | 9.77 | 0.640 | 0.04 | b0=-0.0908, bN=-0.0176, bC=-0.1661, b_H=+0.0281 |
| budget-scale-only | 12.09 | 0.500 | 11.17 | 9.86 | 0.500 | 8.52 | b0=-0.0819, bN=-0.0158, bC=-0.1661 |

| choice rule at held-out scale | mean regret (pts, lower is better) |
|---|---|
| ρ–H law (Eq. 7) | 0.10 |
| uniform random candidate | 11.17 |
| best fixed env from small scales (e10_S4_sh4_n64_L24) | 0.10 |
| highest start success | 1.71 |
| highest mixed-group share | 0.10 |

At the held-out scale and the largest budget (51.2k generated tokens): law pick e10_S4_sh4_n64_L24 (-3.64 pts), oracle e03_S8_sh4_n64_L12 (-3.35 pts), candidate mean -16.00 pts.

| env | observed U (pts) | predicted U (pts) | ρ | H | start success |
|---|---|---|---|---|---|
| e03_S8_sh4_n64_L12 | -3.35 | -16.50 | 302,037 | 0.683 | 0.288 |
| e10_S4_sh4_n64_L24 | -3.64 | -8.55 | 376,186 | 0.800 | 0.471 |
| e07_S12_sh4_n64_L8 | -4.84 | -24.61 | 236,537 | 0.554 | 0.188 |
| e09_S12_sh2_n64_L24 | -5.74 | -18.82 | 218,052 | 0.537 | 0.156 |
| e06_S8_sh8_n64_L24 | -5.76 | -11.79 | 355,190 | 0.766 | 0.457 |
| e02_S4_sh8_n64_L16 | -6.04 | -15.80 | 363,212 | 0.763 | 0.556 |
| e05_S8_sh2_n64_L4 | -7.06 | -17.98 | 184,780 | 0.469 | 0.120 |
| e11_S8_sh8_n2_L4 | -25.14 | -17.64 | 325,474 | 0.711 | 0.312 |
| e12_S12_sh4_n2_L4 | -29.44 | -19.66 | 215,541 | 0.530 | 0.160 |
| e08_S12_sh8_n2_L16 | -30.10 | -18.45 | 323,312 | 0.706 | 0.302 |
| e01_S4_sh2_n2_L4 | -33.25 | -17.27 | 289,342 | 0.662 | 0.215 |
| e04_S8_sh4_n2_L12 | -37.68 | -20.74 | 266,253 | 0.616 | 0.202 |

| scale (params) | Spearman(U, log ρ) | Spearman(U, H) | Spearman(U, start success) | mean U | max U |
|---|---|---|---|---|---|
| 4,496 | +0.34 | +0.36 | +0.38 | -8.13 | -0.78 |
| 27,824 | +0.31 | +0.37 | +0.47 | -11.84 | -1.25 |
| 104,784 | +0.41 | +0.41 | +0.44 | -14.15 | -2.56 |
| 604,432 | +0.23 | +0.24 | +0.17 | -16.00 | -3.35 |
