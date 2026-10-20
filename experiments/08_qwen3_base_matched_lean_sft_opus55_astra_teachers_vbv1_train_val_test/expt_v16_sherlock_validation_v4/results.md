# V16 results: Sherlock 08 v4 checkpoints on VeriBench V1 validation

**Takeaway:** Sherlock-trained v4 matches the SNAP v1 rung (pass@1 4.81% and 5.37% vs 4.91%; paired differences
-0.09 and +0.46 points, CIs include zero), so the Sherlock train-generate-score pipeline reproduces the SNAP result.

- v4 seed 20260830: 52/1080 successes, pass@1 4.81% [2.50, 7.50], pass@8 18/135 = 13.3% [8.1, 19.3].
- v4 seed 20260831: 58/1080, pass@1 5.37% [3.15, 8.06], pass@8 24/135 = 17.8% [11.9, 24.4].
- Two-seed pool: 110/2160, pass@1 5.09% [2.92, 7.59]; paired vs SNAP `sft_1p7B_f1p0`: +0.19 points [-0.88, 1.25].
- Seed spread: pass@8 differs by 4.4 points (CI [-8.9, 0.0]); per-sample successes range 4-9 per 135 tasks.
- Base: 0/1080 on Sherlock and on SNAP. Its format failures are separate: 643/1080 hit the length cap, 493 had no extractable
  Lean code, 485 came only through the bare-block fallback, 102 had file blocks; 8 compiled, none passed the gate.

**Next step:** use Sherlock for further 08 rungs; the seed spread says report two seeds per rung.

## Tables

| System | Successes / 1080 | pass@1 (mean of 8) [95% CI] | pass@8 tasks / 135 [95% CI] |
|---|---|---|---|
| v4 seed 20260830 (Sherlock) | 52 | 4.81% [2.50%, 7.50%] | 18 (13.33%) [8.15%, 19.26%] |
| v4 seed 20260831 (Sherlock) | 58 | 5.37% [3.15%, 8.06%] | 24 (17.78%) [11.85%, 24.44%] |
| Qwen3-1.7B-Base (Sherlock) | 0 | 0.00% [0.00%, 0.00%] | 0 (0.00%) [0.00%, 0.00%] |
| v1 sft_1p7B_f1p0 step 658 (SNAP) | 53 | 4.91% [2.69%, 7.59%] | 20 (14.81%) [8.89%, 21.48%] |
| Qwen3-1.7B-Base e05 (SNAP) | 0 | 0.00% [0.00%, 0.00%] | 0 (0.00%) [0.00%, 0.00%] |

| Paired difference (task bootstrap) | pass@1 diff [95% CI] | pass@8 diff [95% CI] |
|---|---|---|
| v16_v4_20260830 - sft_1p7B_f1p0 | -0.09% [-1.30%, 1.11%] | -1.48% [-5.93%, 2.96%] |
| v16_v4_20260831 - sft_1p7B_f1p0 | 0.46% [-0.93%, 1.94%] | 2.96% [-2.22%, 8.15%] |
| v16_v4_20260830 - v16_v4_20260831 | -0.56% [-2.22%, 1.11%] | -4.44% [-8.89%, 0.00%] |
| v16_v4_20260830 - v16_base | 4.81% [2.50%, 7.50%] | 13.33% [8.15%, 19.26%] |
| v16_v4_20260831 - v16_base | 5.37% [3.15%, 8.06%] | 17.78% [11.85%, 24.44%] |
| v16_base - base_1p7B_e05 | 0.00% [0.00%, 0.00%] | 0.00% [0.00%, 0.00%] |
| v4_two_seed_pool - sft_1p7B_f1p0 | 0.19% [-0.88%, 1.25%] | n/a |

## Format and length (per system, 1080 cells)

| System | Extracted | Capped at length | Compiles | Mean generated tokens |
|---|---|---|---|---|
| v16_v4_20260830 | 900 | 180 | 52 | 5541 |
| v16_v4_20260831 | 894 | 189 | 58 | 5493 |
| v16_base | 587 | 643 | 8 | 7830 |
