# Experiment 18a results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/results.md>

**TLDR:** No measurement yet. Smoke 1861295 passed (SMOKE OK, 6 min). The whole chain is now on FarmShare: gen part 1 (Qwen3-4B, 4 shards) 1861305 has 3 of 4 shards done (GEN TASK OK) and shard 3 running; gen part 2 (0.6B + 1.7B) 1861865, embed 1861866, score 1861867 (afterany both gen parts) and analyze 1861868 (afterany score + embed) were submitted 10-20-2026 22:06. The protocol was frozen on 10-20-2026 before any job; every Slurm job id goes in the table below as it is submitted, and results follow `PROTOCOL.md`'s analysis plan exactly.

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| 10-20-2026 17:22 | FarmShare | 1861295 | smoke (Qwen3-4B, 10 sets x 8 items x 4) | COMPLETED 0:06:11, exit 0 | after `prepare.sh`: PREPARE OK, 38 item sets, 57 tests passed. SMOKE OK on L40S: 10 sets, answer-tag rate 1.00 on 7, 0.75 simple_equations, 0.19 word_sorting (capped 0.56, mean 2398 tok), 0.00 mini_sudoku (mean 31 tok); capped 0 on 8 of 10; 812 tok/s at tiny batch, 4B full-run upper bound 23.1 GPU-h |
| 10-20-2026 17:38 | FarmShare | 1861305 | gen part 1: array 5-8%4 (qwen3_4b shards 0-3 of 4) | 5-7 COMPLETED (0:10:56, 0:21:47, 1:59:59; GEN TASK OK), 8 RUNNING at 22:05 | split from `submit_full.sh` because QOS gpu allows 32 submitted tasks per user and Exp 22 held 28 |
| 10-20-2026 22:06 | FarmShare | 1861865 | gen part 2: array 0-4%4 (qwen3_0p6b 2 shards, qwen3_1p7b 3 shards) | PENDING | submitted when QOS gpu use fell to 23/32; one slot left free for Zip-Mix Stage A |
| 10-20-2026 22:06 | FarmShare | 1861866 | embed array 0-2%4 | PENDING | QOS gpu 31/32 after this |
| 10-20-2026 22:06 | FarmShare | 1861867 | score array 0-2 (afterany: 1861305, 1861865) | PENDING (Dependency) | CPU |
| 10-20-2026 22:06 | FarmShare | 1861868 | analyze (afterany: 1861867, 1861866) | PENDING (Dependency) | CPU; writes ~/e18a/e18a_results.tgz |

## Results

Pending. Written from `expt_v1/results/summary_18a.json`: analysis 1 (pairwise Spearman + CIs, Kendall's W, verdict), 2 (monotone families per size), 3 (learnable band per size, Jaccard, mean level), 4 (coordinate correlations), 5 (target baselines), and the list of incomplete cells.
