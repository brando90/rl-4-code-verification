# Stand-in test of analyze_v26.py on the expt_v16 (AT-477) Sherlock scores

Run 10-20-2026 before any V26 job. The three V26 labels are stood in by v16 data (1.7B seed 20260832 := v16_v4_20260830, 4B seed 20260830 := v16_v4_20260831, 4B seed 20260831 := v16_base), so only the machinery is tested: the two real v16 rows, SNAP rows and v16 paired differences reproduce expt_v16's committed tables exactly (4.81% [2.50%, 7.50%], 5.37% [3.15%, 8.06%], -0.09% [-1.30%, 1.11%], -0.56% [-2.22%, 1.11%]), and an identical stand-in pair gives a 0.00% difference. A run with no V26 files reports the three systems as missing.

Command: `python analyze_v26.py --v16-data <at477 data> --system v26_1p7b_s20260832:v16_v4_20260830:<raw>:<scores> ... --out <tmp>`

| System | Successes / cells | pass@1 [95% CI] | pass@8 tasks / 135 [95% CI] |
|---|---|---|---|
| 1.7B v4 seed 20260830 (Sherlock, expt_v16) | 52 / 1080 | 4.81% [2.50%, 7.50%] | 18 (13.33%) [8.15%, 19.26%] |
| 1.7B v4 seed 20260831 (Sherlock, expt_v16) | 58 / 1080 | 5.37% [3.15%, 8.06%] | 24 (17.78%) [11.85%, 24.44%] |
| 1.7B v4 recipe seed 20260832 (Sherlock, V26) | 52 / 1080 | 4.81% [2.50%, 7.50%] | 18 (13.33%) [8.15%, 19.26%] |
| 4B v4 recipe seed 20260830 (Sherlock, V26) | 58 / 1080 | 5.37% [3.15%, 8.06%] | 24 (17.78%) [11.85%, 24.44%] |
| 4B v4 recipe seed 20260831 (Sherlock, V26) | 0 / 1080 | 0.00% [0.00%, 0.00%] | 0 (0.00%) [0.00%, 0.00%] |
| pool_1.7B | 162 / 3240 | 5.00% [2.84%, 7.56%] | n/a |
| pool_4B | 58 / 2160 | 2.69% [1.57%, 4.03%] | n/a |
| 1.7B sft_1p7B_f1p0 step 658 (SNAP) | 53 / 1080 | 4.91% [2.69%, 7.59%] | 20 (14.81%) [8.89%, 21.48%] |
| 4B sft_4B_f1p0 step 658 (SNAP) | 100 / 1080 | 9.26% [6.02%, 13.06%] | 33 (24.44%) [17.04%, 31.85%] |
| Qwen3-4B-Base e05 (SNAP) | 3 / 1080 | 0.28% [0.00%, 0.65%] | 3 (2.22%) [0.00%, 5.19%] |

| Seed spread | Seeds | pass@1 mean (SD) [range] | pass@8 mean (SD) [range] |
|---|---|---|---|
| 1.7B | 3 | 5.00% (0.32%) [0.56%] | 14.81% (2.57%) [4.44%] |
| 4B | 2 | 2.69% (3.80%) [5.37%] | 8.89% (12.57%) [17.78%] |

| Paired difference (task bootstrap) | pass@1 diff [95% CI] | pass@8 diff [95% CI] |
|---|---|---|
| v26_1p7b_s20260832 - v16_v4_20260830 | 0.00% [0.00%, 0.00%] | 0.00% [0.00%, 0.00%] |
| v26_1p7b_s20260832 - v16_v4_20260831 | -0.56% [-2.22%, 1.11%] | -4.44% [-8.89%, 0.00%] |
| v26_1p7b_s20260832 - sft_1p7B_f1p0 | -0.09% [-1.30%, 1.11%] | -1.48% [-5.93%, 2.96%] |
| v26_4b_s20260830 - sft_4B_f1p0 | -3.89% [-5.83%, -2.22%] | -6.67% [-11.85%, -2.22%] |
| v26_4b_s20260831 - sft_4B_f1p0 | -9.26% [-13.06%, -6.02%] | -24.44% [-31.85%, -17.04%] |
| v26_4b_s20260830 - v26_4b_s20260831 | 5.37% [3.15%, 8.06%] | 17.78% [11.85%, 24.44%] |
| pool_4B - pool_1.7B | -2.31% [-3.78%, -1.06%] | n/a |
| pool_4B - sft_4B_f1p0 | -6.57% [-9.21%, -4.26%] | n/a |
| pool_1.7B - sft_1p7B_f1p0 | 0.09% [-0.96%, 1.11%] | n/a |
