# Experiment 01 orchestration — committed copies

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/orchestration/README.md>

**TLDR:** Copies, for the git record, of the shell scripts and job manifests driving experiment 01's GPU generation and CPU scoring on `skampere1`. No secrets, no raw generations.

These are **copies**. The live, actually-executing scripts stay at `$WORK` = `/lfs/skampere1/0/brando9/rl4cv_e01/` on the host (run directly from tmux panes with hardcoded absolute paths); editing the files here does not affect the running job. See `expt_v1/CKPT_e01.md` → "LIVE STATUS SNAPSHOT" for what's running where right now.

- `run_all_e01.sh` — sequential per-GPU driver: runs each line of a `jobs_gpu<N>.txt` manifest through `run_model.sh`.
- `queue_worker.sh` — the shared claim-based queue driver: every free GPU pulls the next unclaimed job from `shared_queue.txt` (one atomic `mkdir` claim per job).
- `score_worker.sh` — the separate CPU scoring queue (`STAGE=score`, never loads a model), capped at `MAX_CONCURRENT` concurrent `score_scsc.py` processes.
- `wait_and_rebatch.sh` — one-shot: waits for a generation job to reach a target row count, then kills and relaunches it with a larger `--batch`, losing no in-flight work.
- `wait_and_launch_gpu7_tp2.sh` — one-shot: waits for a free partner GPU, then relaunches the Qwen3.6-27B route control at `tensor-parallel-size 2`.
- `switch_to_queue.sh` — one-shot: watches a GPU's local job list for completion, then switches that GPU to `queue_worker.sh`.
- `watchdog_e01.sh` — the dispatch-level watchdog (heartbeat, dead-worker relaunch, idle-worker nudge, issue-#3 notifications).
- `score_worker_shared.sh` (added 09-30-2026 21:50, master) — identical to `score_worker.sh` but reads `shared_queue.txt` instead of `jobs_gpu*.txt`; `score_worker.sh` never saw the shared-queue jobs (`qwen3-1.7b`/`qwen3.5-2b`/`qwen3.5-9b`) after the claim-queue switch, so they weren't being scored. Runs alongside `score_worker.sh`, not instead of it.
- `wait_and_merge_27b_shard2.sh` (added 09-30-2026 21:52, master) — one-shot: parallelizes the Qwen3.6-27B route control's last generation batch across the otherwise-idle GPUs 4+5 (a second `tensor-parallel-size 2` generate call over `task_ids_27b_shard2.txt`, the last 256 task ids). Waits for the main job (GPUs 2+7) to reach row 640, kills it (by GPU-UUID compute-app list), waits for the shard to finish its 256 rows, merges the shard into the main generation file, then reruns `run_model.sh eval` with `STAGE=gen` so the manifest check passes and jobs get materialized for scoring.
- `jobs_gpu{3,4,5,6,7}.txt`, `shared_queue.txt`, `task_ids_27b_shard2.txt` — job/task-id manifests (`<mode> <hf_model_id> <revision> <label> [tp]` per line for the job files).
