# expt_v3 known-MDP sanity: verdict CHOICE ONLY

Gate: 20 of 22 candidates positive at n4, 102.4k tokens (pass). Positive cells overall: 236/255.
corr(log rho, H) over all probes: 0.820 (separated); by scale: 72: 0.801, 276: 0.815, 1604: 0.831, 18692: 0.842

| features | RMSE at n4 (pts) | rank acc | regret (pts) |
|---|---|---|---|
| rho-H | 3.51 | 0.645 | 0.98 |
| rho-only | 3.45 | 0.554 | 9.70 |
| H-only | 3.46 | 0.541 | 4.92 |
| budget-scale-only | 3.54 | 0.500 | 4.32 |

| choice rule at n4 | mean regret (pts) |
|---|---|
| rho-H law | 0.98 |
| rho-only | 9.70 |
| H-only | 4.92 |
| uniform random | 4.32 |
| best fixed from n1-n3 (b12_r3_sl0_sg0.0) | 0.51 |
| highest start success | 8.58 |
| highest mixed-group share | 4.16 |
| exact-gradient oracle | 3.77 |

Law pick b13_r3_sl0_sg0.5: +6.76 pts (5-seed SD 1.02); observed best b08_r2_sl0_sg0.0 +7.63; oracle pick m03_r012_sl0_sg0.0; mean over candidates +3.45.
Spearman at n4: law vs observed 0.38, law vs oracle 0.01, observed vs oracle 0.54, observed vs log rho 0.21, observed vs H 0.17.
Noise trap: noisy candidates have log rho +0.69 vs clean; observed U +3.58 vs +3.33 pts; law predicts +6.23 vs +5.96.

| env | observed U (pts) | seed SD | law pred | exact-grad oracle U | rho | H | start success | admitted |
|---|---|---|---|---|---|---|---|---|
| b08_r2_sl0_sg0.0 | 7.63 | 1.52 | 6.73 | 33.05 | 8166 | 0.343 | 0.056 | 0.056 |
| b12_r3_sl0_sg0.0 | 7.53 | 0.8 | 7.4 | 14.09 | 77632 | 0.83 | 0.393 | 0.393 |
| b09_r2_sl0_sg0.5 | 7.03 | 1.26 | 6.89 | 33.05 | 8783 | 0.317 | 0.062 | 0.062 |
| b13_r3_sl0_sg0.5 | 6.76 | 1.02 | 7.87 | 14.09 | 98228 | 0.755 | 0.38 | 0.38 |
| m00_r12_sl2_sg0.5 | 6.11 | 0.76 | 6.74 | 45.99 | 15446 | 0.536 | 0.215 | 0.215 |
| b02_r0_sl6_sg0.0 | 5.15 | 0.46 | 5.32 | 43.25 | 9450 | 0.83 | 0.261 | 0.261 |
| m05_r123_sl0_sg0.5 | 5.13 | 0.58 | 7.34 | 44.69 | 16128 | 0.363 | 0.158 | 0.158 |
| b03_r0_sl6_sg0.5 | 5.03 | 0.52 | 5.69 | 43.25 | 10288 | 0.742 | 0.265 | 0.265 |
| m02_r03_sl6_sg0.5 | 3.87 | 0.65 | 6.51 | 39.44 | 28954 | 0.805 | 0.664 | 0.664 |
| m03_r012_sl0_sg0.0 | 3.81 | 0.93 | 6.08 | 49.88 | 2278 | 0.154 | 0.026 | 0.026 |
| b06_r1_sl6_sg0.0 | 3.48 | 0.58 | 5.43 | 34.65 | 15773 | 0.954 | 0.535 | 0.535 |
| b07_r1_sl6_sg0.5 | 3.46 | 1.22 | 5.88 | 34.65 | 20593 | 0.897 | 0.542 | 0.542 |
| b04_r1_sl0_sg0.0 | 2.92 | 0.8 | 5.05 | 31.13 | 572 | 0.049 | 0.006 | 0.006 |
| b05_r1_sl0_sg0.5 | 2.88 | 0.78 | 5.06 | 31.13 | 556 | 0.035 | 0.005 | 0.005 |
| m01_r023_sl6_sg0.0 | 2.48 | 1.22 | 6.42 | 36.51 | 10287 | 0.511 | 0.709 | 0.709 |
| m04_r123_sl6_sg0.0 | 2.33 | 0.7 | 6.61 | 27.06 | 13030 | 0.524 | 0.792 | 0.792 |
| b10_r2_sl6_sg0.0 | 1.38 | 0.41 | 6.29 | 20.99 | 12276 | 0.609 | 0.848 | 0.848 |
| b11_r2_sl6_sg0.5 | 0.92 | 0.47 | 6.42 | 20.99 | 38641 | 0.92 | 0.854 | 0.854 |
| b01_r0_sl0_sg0.5 | 0.89 | 0.38 | 2.72 | 1.18 | 47 | 0.005 | 0.001 | 0.001 |
| b00_r0_sl0_sg0.0 | 0.76 | 0.21 | 3.6 | 1.18 | 118 | 0.014 | 0.002 | 0.002 |
| b14_r3_sl6_sg0.0 | -0.88 | 0.41 | 6.61 | 2.91 | 3079 | 0.08 | 0.988 | 0.988 |
| b15_r3_sl6_sg0.5 | -2.73 | 0.74 | 7.46 | 2.91 | 110943 | 0.919 | 0.988 | 0.988 |
