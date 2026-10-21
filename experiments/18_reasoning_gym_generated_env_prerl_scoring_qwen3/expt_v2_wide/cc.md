# Agent prompt: run experiment 18a v2 (wide)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-v2-wide/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/cc.md>

**TLDR:** Run the frozen 18a v2 measurement on FarmShare: prepare, smoke, full chain, record every Slurm job id in `results_v2.md`, bring back `e18v2_results.tgz`, then report exactly what `PROTOCOL_v2.md`'s analysis plan says. Do not change sets, seeds, sampling or the alignment definition; any change is `expt_v3`.

## Prompt

You are running experiment 18a v2 in `brando90/rl-4-code-verification`, branch `ub9/e18a-v2-wide` (PR only, never `main`).

1. Read `PROTOCOL_v2.md` (frozen), `families_v2.json` and `SUBMIT.md`.
2. Follow `SUBMIT.md` on FarmShare: `prepare.sh` → `PREPARE OK`; `smoke.sbatch` → `SMOKE OK` with sane tag/capped rates; then `submit_full.sh` (or the split route when QOS gpu is short).
3. Write every job id (smoke, gen parts, embed, score, analyze, reruns) into `../results_v2.md` and push after each submission.
4. When `analyze` finishes, unpack `e18v2_results.tgz` into `expt_v2_wide/results/`, commit and push.
5. Report from `summary_18a_v2.json`: takeaway first, at most 5 number bullets (Q2: 0.6B→1.7B Spearman with family-bootstrap CI and verdict; Q1: the 8-family verdict with its four checks and the v1 subset's percentile among random 8-family subsets; band counts; monotone share; incomplete cells), one next step for 18b.
6. Incomplete or failed cells are rerun with the identical command or listed with the exact error; never dropped or resampled for their scores.
