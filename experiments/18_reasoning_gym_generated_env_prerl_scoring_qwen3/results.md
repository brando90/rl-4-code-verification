# Experiment 18a results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/results.md>

**TLDR:** No measurement yet. Smoke 1861295 passed (SMOKE OK, 6 min). Gen part 1 (Qwen3-4B, all 4 shards) is queued as 1861305; the rest of the chain (gen 0-4, embed, score, analyze) goes in when FarmShare's 32-job QOS gpu submit limit has room (Exp 22 holds 28). The protocol was frozen on 10-20-2026 before any job; every Slurm job id goes in the table below as it is submitted, and results follow `PROTOCOL.md`'s analysis plan exactly.

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| 10-20-2026 17:22 | FarmShare | 1861295 | smoke (Qwen3-4B, 10 sets x 8 items x 4) | COMPLETED 0:06:11, exit 0 | after `prepare.sh`: PREPARE OK, 38 item sets, 57 tests passed. SMOKE OK on L40S: 10 sets, answer-tag rate 1.00 on 7, 0.75 simple_equations, 0.19 word_sorting (capped 0.56, mean 2398 tok), 0.00 mini_sudoku (mean 31 tok); capped 0 on 8 of 10; 812 tok/s at tiny batch, 4B full-run upper bound 23.1 GPU-h |
| 10-20-2026 17:38 | FarmShare | 1861305 | gen part 1: array 5-8%4 (qwen3_4b shards 0-3 of 4) | PENDING | split from `submit_full.sh` because QOS gpu allows 32 submitted tasks per user and Exp 22 held 28 |
| | | | gen part 2: array 0-4 (qwen3_0p6b 2 shards, qwen3_1p7b 3 shards) | not yet submitted | needs 5 free slots |
| | | | embed array 0-2 | not yet submitted | needs 3 free slots |
| | | | score array 0-2 (afterany: both gen parts) | not yet submitted | CPU |
| | | | analyze (afterany: score + embed) | not yet submitted | CPU |

## Results

Pending. Written from `expt_v1/results/summary_18a.json`: analysis 1 (pairwise Spearman + CIs, Kendall's W, verdict), 2 (monotone families per size), 3 (learnable band per size, Jaccard, mean level), 4 (coordinate correlations), 5 (target baselines), and the list of incomplete cells.
