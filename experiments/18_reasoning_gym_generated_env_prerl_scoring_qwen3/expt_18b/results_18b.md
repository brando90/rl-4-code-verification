# Experiment 18b results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/results_18b.md>

**TLDR:** Not run yet. Protocol, selection (16 environments), forecasts, code, CPU tests and the Sherlock package are committed; no Slurm job has been submitted.

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| 2026-10-21 07:50 | Sherlock | 48809665 | smoke (H100, `gpu`) | pending | package sha256 59970656...6e5e uploaded to $SCRATCH/e18b/code; prepare_login OK; Slurm est. start 21:45 (backfill may be earlier). Forecast/protocol freeze commit f0cb64b9 (06:37) predates this job. |
| | Sherlock | | pre-eval | not submitted | |
| | Sherlock | | train array 0-31 | not submitted | |
| | Sherlock | | post-eval array 0-31 (aftercorr) | not submitted | |
| | Sherlock | | analyze | not submitted | |
