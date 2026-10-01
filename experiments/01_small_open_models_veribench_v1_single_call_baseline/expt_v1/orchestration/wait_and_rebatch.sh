#!/usr/bin/env bash
# TLDR: Wait for gen_<name>.jsonl to reach a target row count, then kill that GPU's driver+generate
# process and relaunch the SAME line with BATCH=256 (master decision 09-30-2026 16:00). Generation
# resumes and skips already-finished cells, so no in-flight work is lost.
set -uo pipefail
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
GEN_FILE="$1"; TARGET="$2"; GPU="$3"; JOBS_FILE="$4"; LOG="$5"

while true; do
  n=$(wc -l < "$GEN_FILE" 2>/dev/null || echo 0)
  if [ "$n" -ge "$TARGET" ]; then break; fi
  sleep 20
done
echo "$(date '+%m-%d-%Y %H:%M:%S') REBATCH TRIGGER: $GEN_FILE reached $n rows (target $TARGET)" >> "$LOG"

# Kill this GPU's driver loop and the vLLM generate process it owns (never another GPU's).
DRIVER_PID=$(ps aux | awk -v j="$JOBS_FILE" '$0 ~ "run_all_e01.sh " j {print $2}' | head -1)
[ -n "$DRIVER_PID" ] && kill "$DRIVER_PID" 2>/dev/null
# Match by the generate process whose CUDA_VISIBLE_DEVICES env matches this GPU.
for p in $(pgrep -f "rl4cv.veribench.generate"); do
  if tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | grep -qx "CUDA_VISIBLE_DEVICES=$GPU"; then
    kill "$p" 2>/dev/null
    echo "$(date '+%m-%d-%Y %H:%M:%S') killed generate pid $p on GPU $GPU" >> "$LOG"
  fi
done
# The generate.py wrapper's vLLM EngineCore/Worker children run as SEPARATE multiprocessing
# processes (not a child that dies with the parent) and keep holding GPU memory after the
# wrapper is killed -- learned the hard way on GPU 3 (orphaned EngineCore held ~71 GiB for
# 20+ minutes, failing every subsequent launch with "insufficient free memory"). Kill every
# compute-app process actually bound to each target GPU's UUID, then wait for memory to
# actually drop before relaunching.
IFS=',' read -ra GPUS <<< "$GPU"
for g in "${GPUS[@]}"; do
  uuid=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v i="$g" '$1==i {print $2}')
  [ -z "$uuid" ] && continue
  nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader | awk -F', ' -v u="$uuid" '$1==u {print $2}' | while read -r cp; do
    [ -n "$cp" ] && kill -9 "$cp" 2>/dev/null && echo "$(date '+%m-%d-%Y %H:%M:%S') killed orphaned compute-app pid $cp on GPU $g" >> "$LOG"
  done
done
for g in "${GPUS[@]}"; do
  for _ in $(seq 1 30); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g" 2>/dev/null || echo 999999)
    [ "$used" -lt 500 ] && break
    sleep 5
  done
  echo "$(date '+%m-%d-%Y %H:%M:%S') GPU $g memory after cleanup: ${used:-unknown} MiB" >> "$LOG"
done
tmux send-keys -t "rl4cv-e01-gen-gpu${GPU##*,}" "export CUDA_VISIBLE_DEVICES=$GPU STAGE=gen BATCH=256 && bash $WORK/run_all_e01.sh $JOBS_FILE $LOG" Enter
echo "$(date '+%m-%d-%Y %H:%M:%S') relaunched with BATCH=256 on gpu=$GPU" >> "$LOG"
