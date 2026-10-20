# Agent prompt: run experiment 18a (expt_v1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/cc.md>

**TLDR:** Run the frozen 18a measurement on FarmShare: prepare, smoke, full chain, record every Slurm job id in `results.md`, bring back `e18a_results.tgz`, then write the results exactly as `PROTOCOL.md`'s analysis plan says. Do not change sampling, sets, seeds or the alignment definition; any change is `expt_v2`.

## Prompt

You are running experiment 18a in `brando90/rl-4-code-verification`, branch `ub9/e18a-reasoning-gym-env-scoring` (PR only, never `main`).

1. Read `../PROTOCOL.md` (frozen) and `SUBMIT.md`.
2. Follow `SUBMIT.md` on FarmShare: `prepare.sh` must print `PREPARE OK`; `smoke.sbatch` must print `SMOKE OK` with sane tag/capped rates; then `submit_full.sh`.
3. Write every job id (smoke, gen, embed, score, analyze, any rerun) into `../results.md` and push after each submission.
4. When `analyze` finishes, unpack `e18a_results.tgz` into `expt_v1/results/`, commit and push.
5. Report from `summary_18a.json`: takeaway first, at most 5 number bullets (pairwise Spearman with CIs and the verdict, Kendall's W, band counts per size, monotone families per size, incomplete cells), one next step for 18b.
6. Incomplete or failed cells are rerun with the identical command or listed with the exact error; never dropped or resampled for their scores.

TL;DR: prepare → smoke → full chain → job ids in results.md → results tgz on the branch → frozen analysis.
