# Experiment 18a v2 (wide) results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-v2-wide/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/results_v2.md>

**TLDR:** No measurement yet. `PROTOCOL_v2.md` was frozen on 10-20-2026 in its own commit before any v2 job. Every Slurm job id goes in the table below as it is submitted; results follow `PROTOCOL_v2.md`'s analysis plan exactly.

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| | FarmShare | | smoke (Qwen3-1.7B, 14 sets x 8 items x 4) | not yet submitted | after `prepare.sh` |
| | FarmShare | | gen array 0-9%2 (0.6B shards 0-3, 1.7B shards 0-5) | not yet submitted | 10 QOS gpu slots |
| | FarmShare | | embed array 0-1%1 | not yet submitted | 2 QOS gpu slots |
| | FarmShare | | score array 0-7 (afterany gen) | not yet submitted | CPU |
| | FarmShare | | analyze (afterany score + embed) | not yet submitted | CPU |

## Results

Pending. Written from `expt_v2_wide/results/summary_18a_v2.json`: analyses 1–7.
