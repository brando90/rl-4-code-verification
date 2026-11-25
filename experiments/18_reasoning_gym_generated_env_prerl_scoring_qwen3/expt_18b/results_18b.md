# Experiment 18b results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/results_18b.md>

**TLDR:** The ρ-H law ranks the 16 environments better than chance on held-out gain (Spearman +0.476, 95% CI [+0.04, +0.74]) but does not pick a good environment: its top choice (rg/mini_sudoku/L2) has top-1 regret 0.382 against 0.232 expected for a random pick. Qwen3-1.7B, thinking off, custom PyTorch/HF GRPO, vLLM 0.30.0 evaluation, no DT; 32 runs (16 environments x 2 seeds), all Slurm jobs exit 0 (Sherlock H100). `analyze.py` re-run as frozen reproduces the stored output exactly.


## Results (frozen `analyze.py` output; table `results/results_18b_table.md`, json `results/results_18b.json`, per-run table `results/supp_18b.md`)

Outcome = held-out gain (mean over 6 target components of post minus pre pass rate; base model 0.343), 2-seed mean per environment. Mean gain +0.106, range -0.196 to +0.338, 10 of 16 environments positive; best environment rg/leg_counting/L3.

| forecast | Spearman [95% CI] | Kendall tau-b [95% CI] | top-1 regret [CI] | top-3 regret | pick |
|---|---|---|---|---|---|
| rho_h (the law) | +0.476 [+0.04, +0.74] | +0.283 [-0.02, +0.56] | 0.382 [0.00, 0.38] | 0.146 | rg/mini_sudoku/L2 |
| law_alpha | +0.368 [-0.23, +0.78] | +0.250 [-0.19, +0.62] | 0.040 [0.00, 0.36] | 0.119 | rg/leg_counting/L2 |
| alpha | -0.391 [-0.72, +0.08] | -0.283 [-0.56, +0.02] | 0.452 [0.19, 0.47] | 0.288 | rg/family_relationships/L0 |
| difficulty | -0.193 [-0.73, +0.41] | -0.159 [-0.62, +0.34] | 0.302 [0.05, 0.48] | 0.281 | rg/simple_equations/L0 (5 tied) |
| smaller_model | -0.326 [-0.81, +0.32] | -0.217 [-0.64, +0.27] | 0.469 [0.42, 0.53] | 0.469 | rg/letter_counting/L1 |
| random | -0.235 [-0.60, +0.25] | -0.133 [-0.43, +0.18] | 0.250 [0.01, 0.50] | 0.248 | rg/family_relationships/L2 |
| rho_only (secondary) | -0.268 [-0.70, +0.29] | -0.167 [-0.51, +0.21] | 0.469 [0.19, 0.47] | 0.294 | rg/basic_arithmetic/L0 |
| H_only (secondary) | +0.579 [+0.03, +0.89] | +0.450 [+0.04, +0.77] | 0.024 [0.00, 0.47] | 0.156 | rg/simple_equations/L0 |
| pass_band (secondary) | +0.156 [-0.42, +0.63] | +0.100 [-0.33, +0.48] | 0.469 [0.00, 0.47] | 0.232 | rg/basic_arithmetic/L0 |

Random pick expected regret: top-1 0.232, top-3 0.210. "Beats random" (Spearman CI lower bound > 0): rho_h and H_only only.

- **Noise ceiling:** seed-seed Spearman +0.488, 2-seed reliability +0.656, maximum reachable forecast Spearman about +0.810. Above the 0.3 threshold, so the test can rank environments. The two seeds of one environment differ by 0.138 gain on average (largest rg/family_relationships/L2: -0.128 vs +0.303); the signs agree in 12 of 16 environments.
- **Primary comparisons (paired bootstrap difference of Spearman, rho_h minus other):** vs alpha +0.868 [+0.08, +1.38], vs difficulty +0.670 [-0.05, +1.22], vs smaller_model +0.803 [-0.15, +1.46]; also vs law_alpha +0.109 [-0.43, +0.71] and vs random +0.712 [+0.06, +1.18]. Only the comparison with alpha excludes zero.
- **Negative findings:** the law's top-1 regret (0.382) is worse than a random pick (0.232) and the bootstrap interval of its regret reaches its own point value; its top-3 regret (0.146) is better than random (0.210). alpha (alignment) alone is negatively related to gain. The 0.6B-model signal and difficulty are not better than random. H_only does as well or better than the full law (Spearman +0.579, top-1 regret 0.024), so the b_rho term does not help here (it is the 1.7B-fit sign, kept as frozen). In-environment gain does not predict held-out gain (rg/basic_arithmetic/L0: in-env +0.385, held-out -0.132).
- **Descriptive check, not frozen:** environments whose runs generate more response tokens gain more (Spearman of mean training response tokens vs gain +0.606; 82,490 to 7,592,719 response tokens per run (QA 11-25-2026: the original range 82,545 to 7,020,465 is of two-seed environment means)). Matched rollouts therefore do not mean matched tokens; this can confound any forecast that tracks response length.
- 16 environments is small: the CIs are wide, and the picks of law_alpha and H_only having low regret rests on one environment each.
- **Plots:** `results/plots/spearman_ci.png`, `regret_top1.png`, `forecast_vs_gain.png`, `seed_seed.png` (made by `analysis_supp_18b.py`, descriptive).

## Deviations from the frozen plan

1. Amendments 1 and 2 and Erratum 1 of `PROTOCOL_18b.md` (learning rate 1e-5; the pool rule of at least 640 distinct questions; a text fix), all dated 10-21-2026 before any job.
2. 6 workers on Sherlock replaced the planned 32-task train and post-eval arrays (QOSMaxSubmitJobPerUserLimit); same cells, seeds, code and GPU type.
3. Bootstrap intervals are the stored 10,000-draw output; `analyze.py` was re-run on 2026-11-09 with numpy only and the resulting json equals the stored one exactly (Spearman, Kendall, regret, CIs, noise ceiling, paired differences). The loaded model-weight revision was not checked.
4. `analysis_supp_18b.py`, the per env x seed table, the token check and the plots are added after the frozen analysis and are descriptive; no frozen number depends on them.

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| 2026-10-21 07:50 | Sherlock | 48809665 | smoke (H100, `gpu`) | pending | package sha256 59970656...6e5e uploaded to $SCRATCH/e18b/code; prepare_login OK; Slurm est. start 21:45 (backfill may be earlier). Forecast/protocol freeze commit f0cb64b9 (06:37) predates this job. |
| 2026-10-21 08:46 | Sherlock | 48809665 | smoke | COMPLETED exit 0 | 8m54s on sh04-01n07 (H100). Peak host RSS 17.1 GB. Est. 32 runs: 2.6 to 39.4 H100-h depending on the env; `train.sbatch` `-t` raised 01:30 to 02:00 (1.5 x 1.23 h). |
| 2026-10-21 09:08 | Sherlock | 48818451 | pre-eval | pending | `-p gpu`, mail END,FAIL to both Brando addresses |
| 2026-10-21 09:09 | Sherlock | 48818682 (array 0-5) | worker pool: train then post-eval per cell, 32 cells | pending | `slurm/worker.sbatch`, 12 h each, H100 80GB. Replaces the planned train array 0-31 and post-eval array 0-31: the `gpu` QOS allows 100 queued tasks per user and 93 were already used, so the 32-task train array failed with QOSMaxSubmitJobPerUserLimit (nothing from it was queued). Workers claim cells by mkdir in `$SCRATCH/e18b/claims`, skip cells whose post json exists, stop claiming after 9 h; failures go to `$SCRATCH/e18b/failed_cells.txt`. |
| 2026-10-21 09:09 | Sherlock | 48818684 | analyze | pending (afterany 48818451:48818682) | CPU |

Deviation from the plan: workers instead of arrays (same cells, same seeds, same code, same H100 type). If cells remain after the workers end, resubmit `sbatch slurm/worker.sbatch` after clearing the claims of unfinished cells, then rerun `analyze.sbatch`.

## Completion (checked 2026-11-09 ~01:00 PT by sacct on Sherlock)

| job id | what | final state | ended (PT) |
|---|---|---|---|
| 48809665 | smoke | COMPLETED 0:0 | 2026-10-21 08:46 |
| 48818451 | pre-eval | COMPLETED 0:0 | 2026-10-21 11:32 |
| 48818682_0 | worker | COMPLETED 0:0 | 2026-10-30 16:15 |
| 48818682_1 | worker | COMPLETED 0:0 | 2026-10-31 15:05 |
| 48818682_2 | worker | COMPLETED 0:0 | 2026-10-31 18:43 |
| 48818682_3 | worker | COMPLETED 0:0 | 2026-11-02 00:40 |
| 48818682_4 | worker | COMPLETED 0:0 | 2026-11-03 18:21 |
| 48818682_5 | worker | COMPLETED 0:0 | 2026-11-06 03:53 |
| 48818684 | analyze | COMPLETED 0:0 | 2026-11-06 03:59 |

All jobs ran on Sherlock H100 (`gpu`); no other GPU type was used and `$SCRATCH/e18b/failed_cells.txt` is absent from the archive (no failed cells). FarmShare L40S fallback was not used.

## Output provenance

- Archive: `$SCRATCH/e18b/e18b_results.tgz` on Sherlock, 109765 bytes, sha256 `9ab4e1498512738e2d9055f3ebd71a94ba44caf4372f954304167b82b04c31b1` (remote and local match). Copy kept at `results/e18b_results.tgz`, unpacked beside it.
- Checked by script on 2026-11-09 (`results/verification_2026-11-09.json`): 32/32 train summaries (40 updates, 10,240 rollouts each; 98,780,367 training response tokens in total), 32/32 post-evals (6 target components x 256 items x 8 samples), all raw gains, 9 Spearman point estimates and 9 top-choice regrets recomputed and matching. Frozen forecast sha256 `31a533e3...a704ce` matches the forecast on main (final newline stripped, as `verify_forecast` does); freeze commit f0cb64b9 predates every job.
- Not regenerated: the bootstrap intervals (stored 10,000-draw output). Not checked: the exact loaded model-weight revision.
- Matched budget is rollouts (10,240 per run), not equal realised tokens.
- Difficulty-only has five tied top environments; its regret (0.3024) averages the ties, while the table prints one pick name.
- Headline numbers (from `results_18b_table.md`; Spearman of forecast vs held-out gain over 16 envs): rho-H +0.476 [+0.04, +0.74] but its top pick (rg/mini_sudoku/L2, gain -0.044) has regret 0.382 vs 0.232 expected for a random pick. Not an environment-selection success.
