# V27 results: SFT data-size ablation with seeds, Qwen3-1.7B-Base, v4 recipe, VeriBench V1 validation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v27_data_size_seeds/results.md>

**Takeaway:** Validation pass@1 rises steeply with SFT data (pooled over two seeds: 0.09% / 0.14% / 1.11% / 5.09% at 12.5 / 25 / 50 / 100%), and both 25→50 and 50→100 are data effects, not seed noise. The 50→100 step (+3.98 pts [+2.22, +6.02]) is 2.3 pts larger than experiment 17's curve predicts, so more 1.7B SFT data of this kind is still a lever and experiment 17's curve is not fit for data planning at this scale: its floored prediction lies inside the pooled 95% CI at only 2 of 4 rungs (pre-registered bar: at least 3).

**Status:** COMPLETE. 6 trained checkpoints, 48 of 48 score directories (6 checkpoints x 8 samples), 6,480 of 6,480 validation cells (135 tasks x 8 samples x 6 checkpoints). Validation split only; test split never loaded. Slurm and provider spend $0. Protocol: [PROTOCOL.md](PROTOCOL.md) (locked 10-20-2026 before any job). The 100% rung is the two existing v4 seeds from [expt_v16](../expt_v16_sherlock_validation_v4/results.md).

## Results per checkpoint and rung

| System | Successes / cells | pass@1 [95% CI] | pass@8 tasks / 135 [95% CI] | length-capped | mean tokens |
|---|---|---|---|---|---|
| 12.5% v27_f0p125_s20260830 | 1 / 1080 | 0.09% [0.00%, 0.28%] | 1 (0.74%) [0.00%, 2.22%] | 588 | 8043 |
| 12.5% v27_f0p125_s20260831 | 1 / 1080 | 0.09% [0.00%, 0.28%] | 1 (0.74%) [0.00%, 2.22%] | 477 | 6171 |
| 12.5% sft_1p7B_f0p125 (SNAP ladder) | 4 / 1080 | 0.37% [0.00%, 0.83%] | 3 (2.22%) [0.00%, 5.19%] | - | - |
| 25% v27_f0p25_s20260830 | 2 / 1080 | 0.19% [0.00%, 0.46%] | 2 (1.48%) [0.00%, 3.70%] | 295 | 6056 |
| 25% v27_f0p25_s20260831 | 1 / 1080 | 0.09% [0.00%, 0.28%] | 1 (0.74%) [0.00%, 2.22%] | 276 | 6116 |
| 25% sft_1p7B_f0p25 (SNAP ladder) | 1 / 1080 | 0.09% [0.00%, 0.28%] | 1 (0.74%) [0.00%, 2.22%] | - | - |
| 50% v27_f0p5_s20260830 | 12 / 1080 | 1.11% [0.46%, 1.94%] | 9 (6.67%) [2.96%, 11.11%] | 283 | 6142 |
| 50% v27_f0p5_s20260831 | 12 / 1080 | 1.11% [0.46%, 1.94%] | 9 (6.67%) [2.96%, 11.11%] | 230 | 5874 |
| 50% sft_1p7B_f0p5 (SNAP ladder) | 19 / 1080 | 1.76% [0.74%, 2.96%] | 11 (8.15%) [3.70%, 13.33%] | - | - |
| 100% v16_v4_20260830 | 52 / 1080 | 4.81% [2.50%, 7.50%] | 18 (13.33%) [8.15%, 19.26%] | 180 | 5541 |
| 100% v16_v4_20260831 | 58 / 1080 | 5.37% [3.15%, 8.06%] | 24 (17.78%) [11.85%, 24.44%] | 189 | 5493 |
| 100% sft_1p7B_f1p0 (SNAP ladder) | 53 / 1080 | 4.91% [2.69%, 7.59%] | 20 (14.81%) [8.89%, 21.48%] | - | - |

## Rungs versus experiment 17's curve

| Rung | pooled pass@1 [95% CI] | seed-mean pass@8 [95% CI] | seed spread pass@1 / pass@8 | E17 (floored) | inside CI | minus SNAP ladder rung, pts [CI] |
|---|---|---|---|---|---|---|
| 12.5% | 0.09% [0.00%, 0.23%] | 0.74% [0.00%, 1.85%] | 0.00 / 0.00 pts | 0.00% | yes | -0.28 [-0.79, +0.05] |
| 25% | 0.14% [0.00%, 0.32%] | 1.11% [0.00%, 2.59%] | 0.09 / 0.74 pts | 0.66% | no | +0.05 [-0.19, +0.28] |
| 50% | 1.11% [0.56%, 1.81%] | 6.67% [3.70%, 10.37%] | 0.00 / 0.00 pts | 2.80% | no | -0.65 [-1.71, +0.32] |
| 100% | 5.09% [2.92%, 7.59%] | 15.56% [10.00%, 21.85%] | 0.56 / 4.44 pts | 4.50% | yes | +0.19 [-0.88, +1.25] |

## Rung-to-rung gains versus seed noise

A step counts as a data effect only if the gain exceeds the 100% seed spread (0.56 pts pass@1, 4.4 pts pass@8) and its 95% CI excludes 0.

| Step | pass@1 gain, pts [95% CI] (bar) | verdict | pass@8 gain, pts [95% CI] (bar) | verdict | E17 predicted gain | observed - E17 |
|---|---|---|---|---|---|---|
| 12.5% -> 25% | +0.05 [-0.14, +0.28] (0.56) | not distinguishable from seed noise | +0.37 [-1.11, +2.22] (4.44) | not distinguishable from seed noise | +0.66 | -0.61 |
| 25% -> 50% | +0.97 [+0.42, +1.67] (0.56) | data effect | +5.56 [+2.59, +8.89] (4.44) | data effect | +2.14 | -1.17 |
| 50% -> 100% | +3.98 [+2.22, +6.02] (0.56) | data effect | +8.89 [+5.19, +12.96] (4.44) | data effect | +1.71 | +2.27 |
| 12.5% -> 100% | +5.00 [+2.92, +7.45] (0.56) | data effect | +14.81 [+9.63, +20.74] (4.44) | data effect | +4.50 | +0.50 |

E17 curve over the 4 rungs: RMSE 0.93 pts; prediction inside the pooled 95% CI at 2 of 4 rungs.

## Pre-registered predictions, scored

| Prediction (PROTOCOL.md) | Outcome |
|---|---|
| Monotone: 12.5% ≤ 25% ≤ 50% ≤ 100% pooled pass@1 | Met (0.09 / 0.14 / 1.11 / 5.09%). |
| 12.5% and 25% each below 2%, many length-capped generations | Met. Length-capped 588 and 477 of 1080 at 12.5%, 295 and 276 at 25%. |
| 12.5→25 not a data effect | Met (+0.05 pts, +0.37 pts pass@8). |
| 50→100 a data effect | Met (+3.98 pts pass@1, +8.89 pts pass@8). |
| 25→50 uncertain, about even odds of clearing both bars | Cleared both bars (+0.97 pts pass@1, +5.56 pts pass@8). |
| 12.5→100 clears both bars | Met. |
| E17 inside the pooled CI at ≥ 3 of 4 rungs | **Not met**: 2 of 4 (12.5% and 100%). It over-predicts 25% (0.66% vs 0.14% [0.00, 0.32]) and 50% (2.80% vs 1.11% [0.56, 1.81]). The prediction that it under-predicts at 12.5% also failed: the floored prediction (0.00%) lies inside the CI. |
| Complete runs match or beat the ladder rungs | **Not met by point estimate** at 12.5% (-0.28 pts) and 50% (-0.65 pts); +0.05 at 25%. All three CIs include 0, so within noise. |

## Interpretation (rule fixed before the runs)

50→100 is a data effect, and the curve does not track the rungs: the observed rung-to-rung shape is convex (+0.05, +0.97, +3.98 pts for successive doubling steps) where experiment 17's curve is concave (+0.66, +2.14, +1.71). By the pre-registered rule this means more SFT data of this kind is still a lever at 1.7B, and experiment 17's curve is not fit for data planning at this scale. The complete runs did not beat the ladder rungs by more than noise, so there is no schedule artifact to flag in the ladder. Flag for experiments 15 and 17: the curve was fit on 12–50% rungs from single-seed runs, and the 12.5–50% predictions are in-sample for it.

## Deviation to disclose

Run index 4 (f0p5_s20260830) failed twice on a cuDNN memory-efficient attention backward error (Slurm jobs 48791582_4 and 49215877_4). The final run (job 49234972) used `train_v27_nocudnn.py`, the same code with the cuDNN SDPA backend switched off. `train_v27.py` in this folder is unchanged, and the `code_sha256` recorded in all six runs' identity files is the same. The switch changes the attention kernel, not the recipe, so it is not expected to change results, but it is not tested here: seed 20260830 at 50% (12/1080) matches seed 20260831 (12/1080, trained with the default backend). `train_v27_nocudnn.py` is on Sherlock in the expt_v27 folder and was not copied into this repo at write-up time (no connection to Sherlock open).

Other runs of this chain: the collect job 48791613 and my reruns 49215891 and 49215883 were cancelled; the collector that produced the results is 49234975 (ended 10-28-2026 08:46).

## Files

- [results/tables_v27.md](results/tables_v27.md): the tables above as `analyze_v27.py` wrote them.
- [results/summary_v27.json](results/summary_v27.json): all numbers.
- [results/analysis/](results/analysis/): per-checkpoint cell and task CSVs (12 files for V27 and 4 for the v16 100% rung, about 1.1 MB).
- Reproduce: `python analyze_v27.py --v27-root <extracted expt_v27_results.tgz> --v16-data <expt_v16 data dir> --out results`.

**TLDR-end:** [rl4cv: SFT data-size ablation v27] Pooled pass@1 is 0.09 / 0.14 / 1.11 / 5.09% at 12.5 / 25 / 50 / 100% of data; 25→50 and 50→100 are data effects, and experiment 17's curve fits only 2 of 4 rungs, so more 1.7B SFT data is still a lever.
