# Experiment 18b results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/results_18b.md>

**TLDR:** Submitted 2026-10-21 09:09 PT on Sherlock. Smoke passed (job 48809665, 8m54s, exit 0; slowest probe rg basic_arithmetic L2: 107 s/step, 1.23 h per 40-step run; fast probe family_relationships L1: 3.5 s/step). Pre-eval, a 6-worker pool for the 32 train+post-eval cells, and analyze are queued. No results yet.

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| 2026-10-21 07:50 | Sherlock | 48809665 | smoke (H100, `gpu`) | pending | package sha256 59970656...6e5e uploaded to $SCRATCH/e18b/code; prepare_login OK; Slurm est. start 21:45 (backfill may be earlier). Forecast/protocol freeze commit f0cb64b9 (06:37) predates this job. |
| 2026-10-21 08:46 | Sherlock | 48809665 | smoke | COMPLETED exit 0 | 8m54s on sh04-01n07 (H100). Peak host RSS 17.1 GB. Est. 32 runs: 2.6 to 39.4 H100-h depending on the env; `train.sbatch` `-t` raised 01:30 to 02:00 (1.5 x 1.23 h). |
| 2026-10-21 09:08 | Sherlock | 48818451 | pre-eval | pending | `-p gpu`, mail END,FAIL to both Brando addresses |
| 2026-10-21 09:09 | Sherlock | 48818682 (array 0-5) | worker pool: train then post-eval per cell, 32 cells | pending | `slurm/worker.sbatch`, 12 h each, H100 80GB. Replaces the planned train array 0-31 and post-eval array 0-31: the `gpu` QOS allows 100 queued tasks per user and 93 were already used, so the 32-task train array failed with QOSMaxSubmitJobPerUserLimit (nothing from it was queued). Workers claim cells by mkdir in `$SCRATCH/e18b/claims`, skip cells whose post json exists, stop claiming after 9 h; failures go to `$SCRATCH/e18b/failed_cells.txt`. |
| 2026-10-21 09:09 | Sherlock | 48818684 | analyze | pending (afterany 48818451:48818682) | CPU |

Deviation from the plan: workers instead of arrays (same cells, same seeds, same code, same H100 type). If cells remain after the workers end, resubmit `sbatch slurm/worker.sbatch` after clearing the claims of unfinished cells, then rerun `analyze.sbatch`.
