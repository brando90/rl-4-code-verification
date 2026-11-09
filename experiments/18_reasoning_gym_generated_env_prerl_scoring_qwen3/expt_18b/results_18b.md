# Experiment 18b results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/results_18b.md>

**TLDR:** All Slurm jobs finished with exit 0 (Sherlock, H100, no DT): smoke 48809665, pre-eval 48818451, 6-worker pool 48818682 (32 cells = 16 envs x 2 seeds), analyze 48818684 (done 2026-11-06 03:59 PT). Outputs are in `results/` (32 train summaries, 32 post-evals, `eval_pre.json`, `results_18b.json`, `results_18b_table.md`, original `e18b_results.tgz`). No failed cells. Model Qwen/Qwen3-1.7B, thinking off; harness: custom PyTorch/HF GRPO (transformers 5.17.0, torch 2.13.0+cu130), vLLM 0.30.0 evaluation. Full analysis and plots are separate (AT-771); this file records job ids and output provenance only.

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
