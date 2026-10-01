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
- `jobs_gpu{3,4,5,6,7}.txt`, `shared_queue.txt` — job manifests (`<mode> <hf_model_id> <revision> <label> [tp]` per line).
