#!/usr/bin/env bash
# TLDR: Wait until one of GPUs 4/5/6 (never 0-2, which belong to truongvo) is fully idle, then relaunch
# the Qwen3.6-27B route control with tp=2 paired with GPU 7, which OOM'd at tp=1 (16.32 GiB KV cache
# needed vs 15.44 GiB available at gpu_memory_utilization=0.88).
set -uo pipefail
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
LOG="$WORK/run_all_e01_gpu7.log"
free_partner() {
  for g in 6 5 4; do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g")
    util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits -i "$g")
    # also confirm no rl4cv job of ours still queued/running on that GPU
    if [ "$used" -lt 500 ] && [ "$util" -lt 5 ] && ! pgrep -f "run_all_e01.sh $WORK/jobs_gpu$g.txt" >/dev/null; then
      echo "$g"; return 0
    fi
  done
  return 1
}
echo "$(date '+%m-%d-%Y %H:%M:%S') WAITING for a free partner GPU (6, then 5, then 4) for tp=2 27B control" >> "$LOG"
while true; do
  PARTNER=$(free_partner) && break
  sleep 60
done
echo "$(date '+%m-%d-%Y %H:%M:%S') Partner GPU $PARTNER free; launching tp=2 27B control on 7,$PARTNER" >> "$LOG"
export CUDA_VISIBLE_DEVICES="7,$PARTNER"
bash "$WORK/run_all_e01.sh" "$WORK/jobs_gpu7.txt" "$LOG"
