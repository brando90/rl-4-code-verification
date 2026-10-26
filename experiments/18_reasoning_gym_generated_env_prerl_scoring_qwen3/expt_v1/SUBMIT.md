# Experiment 18a: step-by-step submit instructions

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/SUBMIT.md>

**TLDR:** FarmShare is the primary route: put the package in `~/e18a/code`, run `prepare.sh` once in the OnDemand JupyterLab terminal, submit `smoke.sbatch`, check it, then `submit_full.sh`. Record every job id in `../results.md`. Sherlock (AT-476 image) is the fallback only if FarmShare's GPU queue stalls for more than a day.

## FarmShare (primary)

Rules: GPU jobs `-p gpu --qos=gpu --gres=gpu:1`, at most 4 GPUs at once (arrays `%4`), ≤ 2-day wall; CPU jobs `-p normal`; mail `END,FAIL` to brandojazz@gmail.com and brando.science@gmail.com (already in every script); nothing heavy on login nodes (the JupyterLab terminal is a compute node).

1. **Open the terminal.** OnDemand → JupyterLab (Small, 2 h) → Terminal.
2. **Put the code in `~/e18a/code`** (a repo-shaped tree: `src/rl4cv/`, `experiments/18_…/`, `tests/test_e18a_reasoning_gym.py`). Either
   - upload `e18a_pkg.tgz` with the Jupyter file browser's upload arrow into `~`, then
     `mkdir -p ~/e18a/code && tar xzf ~/e18a_pkg.tgz -C ~/e18a/code && sha256sum ~/e18a_pkg.tgz`
     (compare with the sha256 next to the tarball), or
   - clone the branch: `git clone -b ub9/e18a-reasoning-gym-env-scoring https://github.com/brando90/rl-4-code-verification.git ~/e18a/code` (private repo: needs a token; remove it from `.git/config` afterwards).
3. **Prepare (once, ~10–15 min):** `bash ~/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/prepare.sh`
   It must end with `38`, `57 passed` (or more) and `PREPARE OK`. It builds `~/venvs/e18a`, checks the GSM8K sha256, downloads the three Qwen3 snapshots into `~/e18a/models/<tag>` and builds `~/e18a/run/items`.
4. **Check GPU room:** `squeue -r -h -u $USER -q gpu | wc -l` (QOS gpu allows 32 submitted array tasks per user, shared with other experiments; the full chain needs 12).
5. **Smoke:** `cd ~/e18a && sbatch ~/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/smoke.sbatch` → record the job id in `results.md`.
   Check `~/e18a/logs/e18a_smoke_<id>.log` ends with `SMOKE OK`. Pass looks like: GPU = L40S; a table of 10 sets with answer-tag rates mostly > 0.5 and capped rates < 0.2; a tokens/s line and a GPU-h bound for the 4B run. If tag rates are near 0 or everything is capped, stop and report (the protocol is frozen; a fix becomes `expt_v2`).
6. **Full chain:** `bash ~/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/submit_full.sh`
   It prints and appends to `~/e18a/job_ids.txt`: `gen` (array 0-8%4, 12 h wall each), `embed` (array 0-2), `score` (afterany gen) and `analyze` (afterany score + embed). Record all four ids in `results.md` and push.
7. **Monitor:** `squeue -u $USER`, `sacct -j <id> --format=JobID,State,Elapsed,NodeList`, `tail ~/e18a/logs/e18a_gen_<A>_<i>.log`. Finished sets: `ls ~/e18a/run/raw/*/*__*.jsonl | wc -l` (114 = 38 sets x 3 models when done).
8. **A task hit the wall or failed:** resubmit just that index, it skips finished sets: `cd ~/e18a && sbatch --array=<i> …/gen.sbatch`; then rerun `score.sbatch` (same index = model) and `analyze.sbatch`. Record the new ids.
9. **Bring results back:** `analyze.sbatch` writes `~/e18a/e18a_results.tgz` (results/, scored/, emb/, manifest, timing; no raw text). Download it with OnDemand Files, unpack into `expt_v1/results/` on the branch, commit and push. Raw generations stay on FarmShare.

## Sherlock (fallback)

Use only if FarmShare's queue stalls for more than a day (and nothing duplicates a FarmShare run). Everything lives in `$SCRATCH/e18a`.

1. Code into `$SCRATCH/e18a/code` (OnDemand upload or clone, as above).
2. Login node, downloads only: `bash $SCRATCH/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/sherlock/prepare_login.sh` (needs `$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif` from AT-476).
3. `cd $SCRATCH/e18a && D=code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/sherlock`
   - build: `B1=$(sbatch --parsable $D/cpu.sbatch build)`
   - smoke: `sbatch --dependency=afterok:$B1 --array=0 $D/gen.sbatch smoke` → `SMOKE OK`
   - full: `G=$(sbatch --parsable $D/gen.sbatch); E=$(sbatch --parsable $D/embed.sbatch); S=$(sbatch --parsable --dependency=afterany:$G $D/cpu.sbatch score); sbatch --dependency=afterany:$S:$E $D/cpu.sbatch analyze`
4. GPUs: `-C 'GPU_SKU:L40S|GPU_SKU:H100_SXM5'` for all three models (bf16; V100 has no bf16, so it is excluded; A30 MIG dev slices are too small). Never `-p dev` for sbatch.

## Output

`$RUN/results/envs_18a.jsonl` (96 rows, schema `envs_18a/v1` in `PROTOCOL.md`), `targets_18a.jsonl` (18 rows), `summary_18a.json`. 18b (AT-566) reads `envs_18a.jsonl`.
