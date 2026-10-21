# Experiment 18b: step-by-step submit instructions (Sherlock H100)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/SUBMIT.md>

**TLDR:** put the package in `$SCRATCH/e18b/code`, run `prepare_login.sh` on the login node, submit `smoke.sbatch` and read its time estimate, then `submit_full.sh` (pre-eval, a 32-task train array, a 32-task post-eval array chained with `aftercorr`, and an analyze job chained with `afterany`). Record every job id in `results_18b.md` (the first job must be submitted after the commit that froze `PROTOCOL_18b.md` and `forecasts_18b.json`). Nothing here has run yet; the smoke gives the first measured step time.

Rules: GPU jobs `-p gpu -G 1`, H100 via `-C GPU_MEM:80GB` (fp32 master weights + Adam states need about 36 GB, so not L40S for training); never `-p dev` for sbatch; mail `END,FAIL` to brandojazz@gmail.com and brando.science@gmail.com is inside every script (one mail per array). Needs the AT-476 image `$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif` (vLLM 0.30.0, torch 2.13.0+cu130) and, optionally, 18a's `$SCRATCH/e18a` (models, pylib, GSM8K are reused when present; otherwise `prepare_login.sh` downloads them).

1. **Package.** `e18b_pkg.tgz` is repo-shaped (`src/rl4cv/`, `experiments/18_…/expt_v1/` and `expt_18b/`, `tests/test_e18b.py`). OnDemand Files > Upload it to `$SCRATCH`, then in the OnDemand shell:
   `mkdir -p $SCRATCH/e18b/code && tar xzf $SCRATCH/e18b_pkg.tgz -C $SCRATCH/e18b/code && sha256sum $SCRATCH/e18b_pkg.tgz` (compare with the sha256 next to the tarball).
2. **Prepare (login node, downloads only, ~10 min):** `bash $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/prepare_login.sh` → must end `PREPARE (login) OK`.
3. **Smoke:** `cd $SCRATCH/e18b && sbatch $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/smoke.sbatch`. Record the job id. Pass looks like: GPU = H100; the 18b CPU tests pass; two 2-step GRPO runs print step rows (`mean_reward`, `grad_norm` finite, `stepped true`, `mean_step_seconds`); memory line under 70 GB; a vLLM eval of the smoke checkpoint prints pass rates; then `est. one 40-step run: X h` and `SMOKE OK`. If a step takes more than 90 s or memory is above 75 GB, stop and report: lower `micro_batch_seqs` is NOT allowed to change the protocol silently (it only changes memory, not the result, so it may be changed and recorded; the sampling/budget numbers may not).
4. **Set the wall time from the smoke:** the array asks `-t 01:30:00` (design estimate ≈ 30 s/step → ~25 min/run). If the smoke says one run needs more than 60 min, edit `#SBATCH -t` in `train.sbatch` to 1.5 x the estimate before submitting.
5. **Full chain:** `bash $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/submit_full.sh` → prints `pre=… train=… post=… analyze=…` (also appended to `$SCRATCH/e18b/job_ids.txt`). Record all four ids in `results_18b.md`.
6. **Monitor:** `squeue -u $USER`, `sacct -j <id> --format=JobID,State,Elapsed,NodeList`, `tail $SCRATCH/e18b/logs/e18b_train_<A>_<i>.log`; done runs: `ls $SCRATCH/e18b/runs/*/train_summary.json | wc -l` (32) and `ls $SCRATCH/e18b/results/post | wc -l` (32). H100 nodes are few (about 3 public), so the array may run mostly serially: expect 32 x ~30 min ≈ 16 h worst case; pre-eval (L40S or H100) runs alongside.
7. **A train task fails or times out:** `train.py` skips finished runs, so resubmit just that index: `sbatch --array=<i> train.sbatch`; its post-eval task stays pending with `DependencyNeverSatisfied` (aftercorr needs success): `scancel <PO>_<i>`, then submit the post-eval for it by hand after the rerun: `sbatch --array=<i> --dependency=afterok:<new train id> post_eval.sbatch`; rerun `analyze.sbatch` at the end (analyze reads whatever exists and reports the number of environments with 2 seeds).
8. **Bring results back:** `$SCRATCH/e18b/e18b_results.tgz` (eval JSONs, results_18b.json, results_18b_table.md, train logs; about 1 MB). Fetch with OnDemand `…/files/fs//scratch/users/brando9/e18b/e18b_results.tgz?download=1`, unpack into `expt_18b/results/`, fill in `results_18b.md` (jobs table, takeaway first, ≤ 5 number bullets, one next step), commit and push on PR #17. Checkpoints are deleted by the post-eval job; train logs stay.

## What the jobs do

| job | script | resources | writes |
|---|---|---|---|
| smoke | `smoke.sbatch` | 1 H100, 1 h | `$RUNS/smoke/*`, step-time estimate |
| pre-eval | `pre_eval.sbatch` | 1 L40S/H100, ≤ 3 h | `$RES/eval_pre.json` (base model: 6 target components × 256 items × 8 samples + 16 env probes × 64 items × 8) |
| train | `train.sbatch` array 0-31 (`tasks.tsv`: env × seed) | 1 H100, ≤ 1.5 h each | `$RUNS/<run>/{train_log.jsonl,train_summary.json,ckpt}` |
| post-eval | `post_eval.sbatch` array 0-31, `aftercorr:<train>` | 1 L40S/H100, ≤ 1 h each | `$RES/post/post_<run>.json`, then deletes `ckpt` |
| analyze | `analyze.sbatch`, `afterany:<pre>:<post>` | CPU, 30 min | `$RES/results_18b.json`, `results_18b_table.md`, `e18b_results.tgz` |

## Time estimate (design, to be replaced by the smoke number)

Per step: HF `generate` of 256 sequences (≤ 1024 new tokens; stops when every sequence has ended) ≈ 5-40 s depending on the environment, forward/backward on the mixed groups ≈ 5-10 s → ~15-50 s, assumed 30 s average; 40 steps ≈ 20 min + ~2.5 min load/save. Pre-eval ≈ 20k samples (≈ 15 min on vLLM), each post-eval ≈ 9k samples + load ≈ 6 min. Total ≈ 32 × 23 + 32 × 6 min + 15 min ≈ 18 H100/L40S-GPU-h (≤ 16 h serial on H100 for training alone). Smoke ≈ 0.3 h.
