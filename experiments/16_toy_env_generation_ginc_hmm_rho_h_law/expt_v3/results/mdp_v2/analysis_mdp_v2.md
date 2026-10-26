# expt_v3 known-MDP, Night 3 (mdp_v2): verdict NO ADVANTAGE

Start target value by scale (mean of 3 repeats): s1 (38 params) 0.181, s2 (72 params) 0.241, s3 (140 params) 0.305, s4 (276 params) 0.378, s5 (548 params) 0.436, s6 (5252 params) 0.509.
Gate: 20 of 22 candidates positive at s6, 102.4k tokens (pass). Positive cells overall: 378/396.
corr(log rho, H) over all 396 probes: 0.819 (separated); noise-free probes: 0.800.
T1 True, T2 beats random False, T2 beats all baselines False.

| features | RMSE at s6 (pts) | rank acc |
|---|---|---|
| rho-H | 3.26 | 0.515 |
| rho-only | 3.28 | 0.558 |
| H-only | 3.43 | 0.517 |
| budget-scale-only | 3.59 | 0.500 |

| choice rule at s6 | mean regret (pts) | 95% CI (2000 bootstrap) | law minus rule, 95% CI | share law lower |
|---|---|---|---|---|
| rho-H law | 10.78 | [9.53, 12.28] | - | - |
| rho-only | 10.78 | [9.53, 12.28] | [+0.00, +0.00] | 0.00 |
| H-only | 4.77 | [3.84, 6.21] | [+3.57, +8.39] | 0.00 |
| uniform random | 4.42 | [4.21, 4.93] | [+4.96, +7.78] | 0.00 |
| best fixed from s1-s5 | 1.47 | [0.18, 2.93] | [+8.68, +9.92] | 0.00 |
| highest start success | 10.78 | [9.02, 12.28] | [+0.00, +1.58] | 0.00 |
| highest mixed-group share | 4.20 | [3.98, 4.67] | [+5.20, +7.93] | 0.00 |
| exact-gradient oracle | 3.37 | [3.00, 3.98] | [+5.86, +8.70] | 0.00 |

Best fixed label from s1-s5: b12_r3_sl0_sg0.0.
Law pick b15_r3_sl6_sg0.5: -3.75 pts (SD over 15 runs 2.33; repeat means [-1.28, -4.04, -5.92]); observed best b08_r2_sl0_sg0.0 +8.20; oracle pick m03_r012_sl0_sg0.0; mean over candidates +3.68.
Spearman at s6: law vs observed -0.02, law vs oracle 0.19, observed vs oracle 0.66.

Noise diagnostic (same fitted law): noisy candidates' rho is 1.8x their noise-free twin (geometric mean); mean abs prediction error on noisy candidates 2.71 pts with standard rho vs 2.50 with noise-free rho. Diagnostic law fit on noise-free features: regret 4.77 pts, pick b06_r1_sl6_sg0.0.

| env (s6, max budget) | observed U (pts) | SD 15 runs | law pred | oracle U | rho | rho noise-free | H | start success |
|---|---|---|---|---|---|---|---|---|
| b08_r2_sl0_sg0.0 | 8.2 | 1.19 | 5.32 | 30.22 | 7536 | 7536 | 0.308 | 0.054 |
| b09_r2_sl0_sg0.5 | 8.11 | 1.15 | 5.29 | 30.22 | 8064 | 7930 | 0.277 | 0.055 |
| m00_r12_sl2_sg0.5 | 7.19 | 1.09 | 5.75 | 45.2 | 16777 | 15234 | 0.598 | 0.23 |
| b12_r3_sl0_sg0.0 | 6.06 | 2.61 | 6.15 | 30.92 | 74945 | 74945 | 0.815 | 0.351 |
| m05_r123_sl0_sg0.5 | 6.0 | 1.0 | 5.44 | 43.66 | 15825 | 13295 | 0.354 | 0.147 |
| b02_r0_sl6_sg0.0 | 5.89 | 0.84 | 6.03 | 42.87 | 10296 | 10296 | 0.867 | 0.313 |
| b03_r0_sl6_sg0.5 | 5.58 | 1.14 | 5.91 | 42.87 | 11265 | 10280 | 0.763 | 0.312 |
| m03_r012_sl0_sg0.0 | 5.54 | 1.29 | 5.02 | 49.11 | 2247 | 2247 | 0.153 | 0.025 |
| b13_r3_sl0_sg0.5 | 5.47 | 2.53 | 6.05 | 30.92 | 89602 | 74120 | 0.719 | 0.338 |
| b07_r1_sl6_sg0.5 | 4.1 | 0.91 | 6.14 | 33.72 | 21337 | 15217 | 0.903 | 0.581 |
| m02_r03_sl6_sg0.5 | 4.02 | 1.46 | 6.07 | 38.75 | 27682 | 9422 | 0.822 | 0.658 |
| b04_r1_sl0_sg0.0 | 3.69 | 1.14 | 4.83 | 30.51 | 845 | 845 | 0.071 | 0.009 |
| b06_r1_sl6_sg0.0 | 3.67 | 0.77 | 6.17 | 33.71 | 15492 | 15492 | 0.945 | 0.572 |
| b05_r1_sl0_sg0.5 | 3.44 | 1.1 | 4.8 | 30.51 | 781 | 784 | 0.054 | 0.008 |
| m01_r023_sl6_sg0.0 | 2.84 | 0.99 | 5.64 | 36.23 | 10628 | 10628 | 0.542 | 0.713 |
| m04_r123_sl6_sg0.0 | 2.19 | 0.51 | 5.66 | 27.21 | 12995 | 12995 | 0.542 | 0.804 |
| b00_r0_sl0_sg0.0 | 1.37 | 0.53 | 4.52 | 2.17 | 66 | 66 | 0.008 | 0.001 |
| b01_r0_sl0_sg0.5 | 1.36 | 0.76 | 4.59 | 2.17 | 134 | 144 | 0.015 | 0.002 |
| b10_r2_sl6_sg0.0 | 0.97 | 0.53 | 5.75 | 21.27 | 12524 | 12524 | 0.621 | 0.846 |
| b11_r2_sl6_sg0.5 | 0.92 | 0.93 | 6.22 | 21.27 | 38453 | 12582 | 0.923 | 0.845 |
| b14_r3_sl6_sg0.0 | -2.01 | 1.49 | 5.05 | 3.31 | 4410 | 4410 | 0.125 | 0.982 |
| b15_r3_sl6_sg0.5 | -3.75 | 2.33 | 6.32 | 3.31 | 106797 | 4374 | 0.923 | 0.981 |

| noisy env | rho | rho noise-free | pred (std rho) | pred (noise-free rho) | observed |
|---|---|---|---|---|---|
| b01_r0_sl0_sg0.5 | 134 | 144 | +4.59 | +4.60 | +1.36 |
| b03_r0_sl6_sg0.5 | 11265 | 10280 | +5.91 | +6.03 | +5.58 |
| b05_r1_sl0_sg0.5 | 781 | 784 | +4.80 | +4.81 | +3.44 |
| b07_r1_sl6_sg0.5 | 21337 | 15217 | +6.14 | +6.15 | +4.10 |
| b09_r2_sl0_sg0.5 | 8064 | 7930 | +5.29 | +5.35 | +8.11 |
| b11_r2_sl6_sg0.5 | 38453 | 12582 | +6.22 | +5.76 | +0.92 |
| b13_r3_sl0_sg0.5 | 89602 | 74120 | +6.05 | +6.14 | +5.47 |
| b15_r3_sl6_sg0.5 | 106797 | 4374 | +6.32 | +5.04 | -3.75 |
| m00_r12_sl2_sg0.5 | 16777 | 15234 | +5.75 | +5.86 | +7.19 |
| m02_r03_sl6_sg0.5 | 27682 | 9422 | +6.07 | +5.55 | +4.02 |
| m05_r123_sl0_sg0.5 | 15825 | 13295 | +5.44 | +5.49 | +6.00 |
