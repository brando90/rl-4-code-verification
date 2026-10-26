# Experiment 18a v2 (wide): step-by-step submit instructions

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-v2-wide/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/SUBMIT.md>

**TLDR:** FarmShare is the primary route. Untar the package into `~/e18a_v2/code`, run `prepare.sh` once in the OnDemand JupyterLab terminal, submit `smoke.sbatch`, check it, then `submit_full.sh`. Record every job id in `../results_v2.md`. v2 reuses v1's CPU venv (`~/venvs/e18a`), GSM8K file and Qwen3-0.6B/1.7B snapshots (`~/e18a/models`) and the shared `~/venvs/fs_hf`. Sherlock (AT-476 image) is the fallback if FarmShare's GPU queue stalls for more than a day.

## FarmShare (primary)

Rules: GPU jobs `-p gpu --qos=gpu --gres=gpu:1`; QOS gpu allows 4 running and 32 submitted tasks per user, **shared with every other experiment**; ≤ 2-day wall (scripts use 12 h, resumable); CPU jobs `-p normal`; mail `END,FAIL` to brandojazz@gmail.com and brando.science@gmail.com, one mail per array (already in every script); nothing heavy on login nodes (the JupyterLab terminal is a compute node).

1. **Open the terminal.** OnDemand → JupyterLab (Small, 2 h) → Terminal.
2. **Code into `~/e18a_v2/code`.** Upload `e18v2_pkg.tgz` (Jupyter upload arrow) into `~`, then
   `mkdir -p ~/e18a_v2/code && tar xzf ~/e18v2_pkg.tgz -C ~/e18a_v2/code && sha256sum ~/e18v2_pkg.tgz` (compare with `e18v2_pkg.tgz.sha256`).
3. **Prepare (once, ~5–15 min):** `bash ~/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/prepare.sh`
   It must print `item sets: N (expect N)`, the tests `passed` and `PREPARE OK`. `build.py` refuses any item set whose hash differs from the frozen probe (`probe_v2.jsonl`), so a different Reasoning Gym build cannot slip in.
4. **Check GPU room:** `squeue -r -h -u $USER -q gpu | wc -l`. Smoke needs 1 slot; the full chain needs 12 (gen 10 + embed 2).
5. **Smoke:** `cd ~/e18a_v2 && sbatch ~/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/smoke.sbatch` → job id into `results_v2.md`.
   Pass: log `~/e18a_v2/logs/e18v2_smoke_<id>.log` ends with `SMOKE OK`; GPU = L40S; a table of 14 sets (12 families' top levels + 2 targets); a tok/s line and a 1.7B GPU-h bound. If most tag rates are near 0 or nearly everything is capped, stop and report (protocol is frozen; a fix is `expt_v3`).
6. **Full chain:** `bash ~/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/submit_full.sh`
   It refuses when QOS gpu lacks 12 free slots. Then submit part of gen: `GEN_ARRAY=0-3 bash submit_full.sh` (0.6B, the cheaper half, plus embed), later the rest with `sbatch --array=4-9%2 …/gen.sbatch`, and finally `bash …/submit_tail.sh <embed id> <gen id 1> <gen id 2>` (score afterany all gen jobs, analyze afterany score + embed). Every id goes to `~/e18a_v2/job_ids.txt`; copy them into `results_v2.md`.
   Gen runs `%2` so other experiments keep two GPUs; when nothing else of yours waits: `scontrol update JobId=<gen id> ArrayTaskThrottle=4`.
7. **Monitor:** `squeue -u $USER`, `sacct -j <id> --format=JobID,State,Elapsed,NodeList`, `tail ~/e18a_v2/logs/e18v2_gen_<A>_<i>.log`; finished sets: `ls ~/e18a_v2/run/raw/*/ | grep -c jsonl`.
8. **A task hit the wall or failed:** resubmit just that index; it skips finished sets: `cd ~/e18a_v2 && sbatch --array=<i> …/gen.sbatch`; then rerun `score.sbatch` and `analyze.sbatch`. Record the new ids.
9. **Bring results back:** `analyze.sbatch` writes `~/e18a_v2/e18v2_results.tgz` (results/, scored/, emb/, manifest, timing; no raw text). Download with OnDemand Files, unpack into `expt_v2_wide/results/`, commit, push. If v1's `~/e18a/run/results/envs_18a.jsonl` exists when analyze runs, the same-family replication check is included; otherwise rerun `analyze.sbatch` after v1 finishes.

## Sherlock (fallback)

Only if FarmShare's queue stalls for more than a day, and never duplicating cells FarmShare already finished. Everything lives in `$SCRATCH/e18a_v2`.

1. Code into `$SCRATCH/e18a_v2/code` (OnDemand upload of the same tgz).
2. Login node, downloads only: `bash $SCRATCH/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/sherlock/prepare_login.sh` (needs `$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif` from AT-476).
3. `cd $SCRATCH/e18a_v2 && D=code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/sherlock`
   - build: `B1=$(sbatch --parsable $D/cpu.sbatch build)`
   - smoke: `sbatch --dependency=afterok:$B1 --array=0 $D/gen.sbatch smoke` → `SMOKE OK`
   - full: `G=$(sbatch --parsable $D/gen.sbatch); E=$(sbatch --parsable $D/embed.sbatch); S=$(sbatch --parsable --dependency=afterany:$G $D/cpu.sbatch score); sbatch --dependency=afterany:$S:$E $D/cpu.sbatch analyze`
4. GPUs: `-C 'GPU_SKU:L40S|GPU_SKU:H100_SXM5'` (bf16; no V100). Never `-p dev` for sbatch.

## Output

`$RUN/results/envs_18a_v2.jsonl` (one row per environment and model, schema `envs_18a_v2/v1`), `targets_18a_v2.jsonl` (12 rows), `summary_18a_v2.json` (analyses 1–7 of `PROTOCOL_v2.md`).
