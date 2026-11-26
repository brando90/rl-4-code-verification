# Experiment 18c results (token-matched rerun of 18b), 11-25-2026

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18c/results_18c.md>
**Google Doc:** <https://docs.google.com/document/d/1EbbYTxScKzbATvN7GNWBpPa5-dD0uCrecR0B3cerhgo/edit>

**TLDR:** All 48 runs finished on budget (every run 2,000,111 to 2,170,979 response tokens, none overshoot, none budget_limited, no failed cell, no re-run). The frozen rho_h law again ranks the 16 environments better than chance but not significantly: Spearman **+0.482** (95% CI [-0.04, +0.80]; 18b +0.476 [+0.04, +0.74]), top-1 regret **0.209** vs 0.197 expected for a random pick (18b 0.382 vs 0.232), so it still does not beat a random pick on regret. Only H_only beats random by the CI rule (+0.544 [+0.09, +0.83], regret 0.081). The token confound did not go away: mean response length per rollout vs gain is **+0.476** [-0.07, +0.83] (18b +0.606), above my forecast of +0.25. Cross-check 18c vs 18b environment gain: Spearman +0.659. 3-seed reliability +0.663.

**Harness and model:** custom PyTorch/HF GRPO (`expt_18b` `grpo.py`, `train.py` via `train18c.py`), Qwen3-1.7B (revision `70d244cc...`) thinking off, vLLM 0.30.0 post-evaluation, skampere2 H200 (GPUs 4 to 7). No agent harness, no model API, no DT label, no spend. Protocol and forecasts frozen in commit 88b7b196 (12:06 PST) before the first job (12:17 PST).

## Jobs (skampere2, brando9, 11-25-2026 PT)

| host | job id | what | result |
|---|---|---|---|
| skampere2 | job-c5d6288f | pre-eval of base model (GPU 5), 12:14 | exit 0 (`PRE EVAL OK`, after `VLLM_USE_FLASHINFER_SAMPLER=0`, commit 5790bab5) |
| skampere2 | job-744bb910 | worker GPU 4, 12:17, 13 cells | exit 0, ended 17:36 |
| skampere2 | job-d89be4d9 | worker GPU 5, 12:18, 11 cells | exit 0, ended 17:24 |
| skampere2 | job-280d0157 | worker GPU 6, 12:18, 11 cells | exit 0, ended 17:32 |
| skampere2 | job-b8e7c87c | worker GPU 7, 12:18, 13 cells | exit 0, ended 17:43 |

48 of 48 cells done, no `failed_cells.txt`, nothing re-run. Training time summed over the 48 runs 17.8 H200-h (evaluation not included); wall time 5.4 h with 4 GPUs.

## Primary result (frozen `analyze18c.py` run as is; output reproduced byte for byte on a second run)

Outcome = held-out gain (mean over 6 target components of post minus pre pass rate), 3-seed mean per environment. Mean gain +0.123 (18b +0.106); best environment rg/leg_counting/L3 (+0.320). Table notes: the line "16 with both seeds" and the "Noise ceiling" line of the 18b `analyze.py` header use only the first seed pair (0, 1); the 3-seed numbers are in the confound section below.

| forecast | Spearman [95% CI] | Kendall [95% CI] | regret top-1 [CI] | regret top-3 | pick |
|---|---|---|---|---|---|
| rho_h | +0.482 [-0.04, +0.80] | +0.333 [-0.05, +0.66] | +0.209 [+0.00, +0.21] | +0.089 | rg/mini_sudoku/L2 |
| law_alpha | +0.100 [-0.41, +0.61] | +0.100 [-0.27, +0.49] | +0.081 [+0.00, +0.19] | +0.084 | rg/leg_counting/L2 |
| alpha | -0.494 [-0.80, -0.02] | -0.367 [-0.67, -0.04] | +0.183 [+0.15, +0.51] | +0.337 | rg/family_relationships/L0 |
| difficulty | -0.143 [-0.68, +0.48] | -0.103 [-0.54, +0.40] | +0.185 [+0.06, +0.33] | +0.172 | rg/simple_equations/L0 |
| smaller_model | -0.015 [-0.52, +0.53] | +0.000 [-0.41, +0.42] | +0.319 [+0.02, +0.47] | +0.265 | rg/letter_counting/L1 |
| random | -0.126 [-0.63, +0.47] | -0.050 [-0.47, +0.39] | +0.506 [+0.00, +0.51] | +0.315 | rg/family_relationships/L2 |
| rho_only | -0.250 [-0.74, +0.33] | -0.183 [-0.59, +0.24] | +0.040 [+0.00, +0.51] | +0.290 | rg/basic_arithmetic/L0 |
| H_only | +0.544 [+0.09, +0.83] | +0.367 [+0.05, +0.66] | +0.081 [+0.02, +0.08] | +0.055 | rg/simple_equations/L0 |
| pass_band | +0.147 [-0.37, +0.67] | +0.150 [-0.25, +0.56] | +0.040 [+0.00, +0.51] | +0.196 | rg/basic_arithmetic/L0 |

| env | seeds | gain | GSM8K gain | RG-5 gain | tag-rate change | in-env gain |
|---|---|---|---|---|---|---|
| rg/simple_equations/L0 | 3 | +0.239 | +0.107 | +0.265 | -0.004 | +0.182 |
| rg/mini_sudoku/L2 | 3 | +0.112 | -0.123 | +0.158 | -0.151 | -0.055 |
| rg/family_relationships/L0 | 3 | +0.137 | -0.097 | +0.184 | +0.001 | +0.285 |
| rg/basic_arithmetic/L0 | 3 | +0.280 | +0.097 | +0.316 | +0.046 | +0.436 |
| rg/family_relationships/L1 | 3 | -0.042 | -0.354 | +0.021 | +0.053 | +0.484 |
| rg/basic_arithmetic/L2 | 3 | +0.305 | +0.127 | +0.340 | +0.039 | +0.589 |
| rg/letter_counting/L3 | 3 | -0.154 | -0.587 | -0.067 | +0.053 | +0.122 |
| rg/leg_counting/L2 | 3 | +0.239 | +0.068 | +0.273 | +0.020 | +0.454 |
| rg/basic_arithmetic/L3 | 3 | +0.297 | +0.144 | +0.327 | +0.005 | +0.253 |
| rg/mini_sudoku/L0 | 3 | +0.154 | -0.189 | +0.223 | -0.140 | +0.606 |
| rg/leg_counting/L3 | 3 | +0.320 | +0.156 | +0.353 | -0.020 | +0.562 |
| rg/leg_counting/L1 | 3 | +0.283 | +0.118 | +0.316 | +0.014 | +0.812 |
| rg/word_sorting/L0 | 3 | -0.134 | -0.424 | -0.076 | -0.400 | -0.015 |
| rg/letter_counting/L1 | 3 | +0.002 | -0.376 | +0.077 | +0.037 | +0.199 |
| rg/mini_sudoku/L1 | 3 | +0.118 | -0.079 | +0.158 | +0.002 | +0.413 |
| rg/family_relationships/L2 | 3 | -0.186 | -0.590 | -0.105 | +0.053 | +0.185 |

Random pick expected regret: top-1 +0.197, top-3 +0.184. "Beats random" (Spearman CI lower bound > 0): H_only only (rho_h's lower bound is -0.04; on the fully matched subset, which here is all 16 environments, -0.002).

Paired bootstrap difference of Spearman, rho_h minus other: vs alpha +0.976 [+0.04, +1.56] (excludes 0); vs law_alpha +0.382 [-0.30, +1.02], vs difficulty +0.625 [-0.15, +1.21], vs smaller_model +0.497 [-0.46, +1.21], vs random +0.609 [-0.18, +1.28] (all include 0).

## Token-confound check (the reason for 18c)

- Run classes: 48 matched, 0 overshoot, 0 budget_limited. Realised tokens per run: min 2,000,111, mean 2,040,443, max 2,170,979. Updates per run: min 13, median 33.5, max 977 (cap 1,000 never reached).
- Spearman of mean response length per rollout (3-seed mean) vs 3-seed gain: **+0.476** [-0.07, +0.83] (18b +0.606, a different statistic: training response tokens). Total tokens vs gain +0.685; total tokens differ by only 8% across runs here, so that number reflects the one-update overshoot, which is larger when responses are long. I did not test it further.
- So matching the budget did not remove the link between response length and gain: environments whose responses stay long (mini_sudoku, basic_arithmetic/L2 and L3, leg_counting) still gain more.
- 11 of the 48 runs (letter_counting/L3 x3, family_relationships/L2 x3, letter_counting/L1 seeds 0 and 1, family_relationships/L0 seed 0, family_relationships/L1 seeds 1 and 2) ended with responses of about 8 tokens per rollout and took 934 to 977 updates to reach 2M tokens. Their gains are -0.25 to -0.14, except family_relationships/L1 and L0 seeds that did not collapse (+0.26, +0.34, +0.32) and letter_counting/L1 seed 2 (+0.295, 25 updates). So in these environments a run either collapses to 8-token answers (negative gain) or does not (positive gain). This is read from the per-run table; I did not look into why it collapses.
- 3-seed reliability **+0.663** (mean pairwise seed Spearman +0.396; pairs +0.388, +0.332, +0.468); max reachable forecast Spearman about +0.814 (18b +0.656).
- Cross-check with 18b: Spearman of 18c vs 18b environment gain **+0.659**; mean gain 18c +0.123, 18b +0.106.
- Fully matched subset: all 16 environments qualify, so it equals the primary table.
- `rg/basic_arithmetic/L0` is flagged `repeat_limited` (4,929 distinct questions in its stream); it used 1,486 to 1,580 distinct questions in about 85 updates, so no question repeats were forced.

## Predictions from `PROTOCOL_18c.md` scored (written before any job)

| prediction | observed | verdict |
|---|---|---|
| short-response environments take about 700 to 977 updates, the others 10 to 45 | 11 runs took 934 to 977 updates (letter_counting/L3 and family_relationships/L2 all seeds, plus 5 runs of letter_counting/L1, family_relationships/L0 and /L1); basic_arithmetic/L0 only 82 to 91; the other 34 runs 13 to 196 updates, 28 of them within 10 to 45 | partly right: the collapsed set is close, basic_arithmetic/L0 not |
| P(no run reaches the 1,000-update cap) = 80% | max 977, none budget_limited | right |
| length-vs-gain Spearman +0.25; 70% below +0.45; 85% below +0.606 | +0.476 | point estimate and the +0.45 bound wrong; below +0.606 right |
| rho_h Spearman +0.30; P(CI lower > 0) = 30%; P(point > 0) = 75% | +0.482, lower bound -0.04 | point > 0 right; lower bound > 0 did not happen; point estimate too low |
| H_only +0.35; law_alpha +0.25 | +0.544; +0.100 | both off (H_only higher, law_alpha lower) |
| alpha, difficulty, smaller_model, random between -0.4 and +0.2 | -0.494, -0.143, -0.015, -0.126 | alpha outside, other three inside |
| rho_h top-1 regret 0.25; P(better than random expected) = 45% | 0.209 vs random 0.197 | regret value close; not better than random |
| mean gain +0.08 | +0.123 | too low |
| 3-seed reliability 0.65; P(>= 0.6) = 60% | +0.663 | right |
| 18c vs 18b environment gain Spearman +0.5 | +0.659 | too low |

## Deviations and limits

- H200 instead of H100; base reference re-measured on this stack; HF generate and vLLM are not bit-reproducible, so 18b's seeds 0 and 1 are not reproduced exactly.
- 16 environments is small: CIs are wide, and the low-regret picks of law_alpha, H_only and rho_only rest on one environment each. Regret of rho_h (0.209) is within noise of a random pick.
- The protocol's cross-check and confound statistic use the 3-seed mean; per-run gains vary by seed (five environments differ by more than 0.4 in gain between seeds, up to 0.59 for family_relationships/L0, whose seed 0 ran 956 updates at 8 tokens per rollout and gained -0.25 while seeds 1 and 2 ran 31 and 38 updates and gained +0.34 and +0.32).

## Files

`results/eval_pre.json`, `results/post/`, `results/train/` (summaries and logs), `results/results_18c.json`, `results/results_18c_table.md`, `results/perrun_18c.md`; reproduce with `python analyze18c.py --root results --out results/results_18c.json` (needs numpy and the repo's `src`).

## Per-run table

| env | seed | updates | response tokens | mean len/rollout | class | distinct questions | gain [95% CI] |
|---|---|---|---|---|---|---|---|
| rg/simple_equations/L0 | 0 | 36 | 2,009,431 | 218.0 | matched | 1152 | +0.307 [+0.290, +0.325] |
| rg/simple_equations/L0 | 1 | 41 | 2,078,041 | 198.0 | matched | 1312 | +0.306 [+0.287, +0.325] |
| rg/simple_equations/L0 | 2 | 60 | 2,032,156 | 132.3 | matched | 1920 | +0.104 [+0.083, +0.124] |
| rg/mini_sudoku/L2 | 0 | 14 | 2,006,139 | 559.7 | matched | 448 | +0.073 [+0.055, +0.090] |
| rg/mini_sudoku/L2 | 1 | 16 | 2,020,738 | 493.3 | matched | 512 | +0.041 [+0.024, +0.059] |
| rg/mini_sudoku/L2 | 2 | 18 | 2,017,122 | 437.7 | matched | 576 | +0.221 [+0.203, +0.238] |
| rg/family_relationships/L0 | 0 | 956 | 2,000,277 | 8.2 | matched | 30240 | -0.250 [-0.270, -0.229] |
| rg/family_relationships/L0 | 1 | 31 | 2,053,307 | 258.7 | matched | 992 | +0.342 [+0.324, +0.359] |
| rg/family_relationships/L0 | 2 | 38 | 2,027,757 | 208.4 | matched | 1216 | +0.319 [+0.299, +0.338] |
| rg/basic_arithmetic/L0 | 0 | 89 | 2,004,985 | 88.0 | matched | 1561 | +0.261 [+0.244, +0.278] |
| rg/basic_arithmetic/L0 | 1 | 82 | 2,038,471 | 97.1 | matched | 1486 | +0.295 [+0.276, +0.313] |
| rg/basic_arithmetic/L0 | 2 | 91 | 2,037,679 | 87.5 | matched | 1580 | +0.284 [+0.265, +0.302] |
| rg/family_relationships/L1 | 0 | 74 | 2,021,788 | 106.7 | matched | 2368 | +0.263 [+0.246, +0.281] |
| rg/family_relationships/L1 | 1 | 964 | 2,000,111 | 8.1 | matched | 30845 | -0.146 [-0.166, -0.128] |
| rg/family_relationships/L1 | 2 | 934 | 2,000,162 | 8.4 | matched | 29885 | -0.242 [-0.262, -0.222] |
| rg/basic_arithmetic/L2 | 0 | 22 | 2,034,852 | 361.3 | matched | 704 | +0.332 [+0.315, +0.350] |
| rg/basic_arithmetic/L2 | 1 | 24 | 2,129,887 | 346.7 | matched | 768 | +0.281 [+0.264, +0.298] |
| rg/basic_arithmetic/L2 | 2 | 19 | 2,028,452 | 417.0 | matched | 608 | +0.302 [+0.285, +0.319] |
| rg/letter_counting/L3 | 0 | 972 | 2,000,848 | 8.0 | matched | 30179 | -0.161 [-0.186, -0.138] |
| rg/letter_counting/L3 | 1 | 975 | 2,000,486 | 8.0 | matched | 30274 | -0.161 [-0.185, -0.137] |
| rg/letter_counting/L3 | 2 | 977 | 2,001,788 | 8.0 | matched | 30342 | -0.140 [-0.163, -0.115] |
| rg/leg_counting/L2 | 0 | 27 | 2,054,955 | 297.3 | matched | 864 | +0.312 [+0.294, +0.329] |
| rg/leg_counting/L2 | 1 | 66 | 2,008,196 | 118.9 | matched | 2112 | +0.125 [+0.104, +0.145] |
| rg/leg_counting/L2 | 2 | 27 | 2,068,577 | 299.3 | matched | 864 | +0.280 [+0.263, +0.298] |
| rg/basic_arithmetic/L3 | 0 | 14 | 2,007,821 | 560.2 | matched | 448 | +0.293 [+0.276, +0.309] |
| rg/basic_arithmetic/L3 | 1 | 16 | 2,170,979 | 530.0 | matched | 512 | +0.310 [+0.292, +0.327] |
| rg/basic_arithmetic/L3 | 2 | 22 | 2,041,029 | 362.4 | matched | 704 | +0.287 [+0.269, +0.306] |
| rg/mini_sudoku/L0 | 0 | 14 | 2,079,451 | 580.2 | matched | 448 | +0.146 [+0.128, +0.165] |
| rg/mini_sudoku/L0 | 1 | 13 | 2,004,965 | 602.5 | matched | 416 | +0.016 [-0.002, +0.034] |
| rg/mini_sudoku/L0 | 2 | 14 | 2,046,468 | 571.0 | matched | 448 | +0.300 [+0.283, +0.317] |
| rg/leg_counting/L3 | 0 | 27 | 2,109,319 | 305.2 | matched | 864 | +0.347 [+0.329, +0.364] |
| rg/leg_counting/L3 | 1 | 17 | 2,036,432 | 467.9 | matched | 544 | +0.307 [+0.290, +0.325] |
| rg/leg_counting/L3 | 2 | 18 | 2,155,978 | 467.9 | matched | 576 | +0.307 [+0.290, +0.324] |
| rg/leg_counting/L1 | 0 | 86 | 2,005,969 | 91.1 | matched | 2661 | +0.271 [+0.254, +0.288] |
| rg/leg_counting/L1 | 1 | 21 | 2,151,802 | 400.3 | matched | 668 | +0.333 [+0.317, +0.350] |
| rg/leg_counting/L1 | 2 | 37 | 2,018,448 | 213.1 | matched | 1168 | +0.245 [+0.228, +0.262] |
| rg/word_sorting/L0 | 0 | 22 | 2,104,919 | 373.7 | matched | 704 | -0.280 [-0.298, -0.262] |
| rg/word_sorting/L0 | 1 | 79 | 2,065,896 | 102.2 | matched | 2528 | +0.138 [+0.121, +0.157] |
| rg/word_sorting/L0 | 2 | 21 | 2,059,788 | 383.1 | matched | 672 | -0.260 [-0.277, -0.243] |
| rg/letter_counting/L1 | 0 | 976 | 2,001,419 | 8.0 | matched | 30093 | -0.137 [-0.159, -0.114] |
| rg/letter_counting/L1 | 1 | 977 | 2,001,914 | 8.0 | matched | 30124 | -0.153 [-0.176, -0.129] |
| rg/letter_counting/L1 | 2 | 25 | 2,047,063 | 319.9 | matched | 798 | +0.295 [+0.277, +0.313] |
| rg/mini_sudoku/L1 | 0 | 13 | 2,115,006 | 635.5 | matched | 416 | +0.223 [+0.202, +0.241] |
| rg/mini_sudoku/L1 | 1 | 196 | 2,000,282 | 39.9 | matched | 6271 | -0.139 [-0.158, -0.120] |
| rg/mini_sudoku/L1 | 2 | 14 | 2,036,809 | 568.3 | matched | 448 | +0.272 [+0.253, +0.290] |
| rg/family_relationships/L2 | 0 | 961 | 2,000,645 | 8.1 | matched | 30752 | -0.209 [-0.231, -0.187] |
| rg/family_relationships/L2 | 1 | 976 | 2,000,777 | 8.0 | matched | 31232 | -0.157 [-0.176, -0.137] |
| rg/family_relationships/L2 | 2 | 952 | 2,001,887 | 8.2 | matched | 30464 | -0.190 [-0.210, -0.168] |
