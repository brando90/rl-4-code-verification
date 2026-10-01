#!/usr/bin/env bash
# TLDR: Watch one GPU's local driver log for "ALL JOBS ON THIS GPU DONE", then switch that GPU's
# tmux pane to pull from the shared claim-based queue (master decision 09-30-2026 17:10) so it never
# idles while shared_queue.txt still has unclaimed jobs.
set -uo pipefail
GPU="$1"; LOG="$2"
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
SENTINEL="ALL JOBS ON THIS GPU DONE"

# grep -c always prints a count (0 on no match) but exits 1 then; don't let `||` double-print.
n0=$(grep -c "$SENTINEL" "$LOG" 2>/dev/null); n0=${n0:-0}
while true; do
  n=$(grep -c "$SENTINEL" "$LOG" 2>/dev/null); n=${n:-0}
  [ "$n" -gt "$n0" ] && break
  sleep 15
done
echo "$(date '+%m-%d-%Y %H:%M:%S') local queue finished on gpu=$GPU, switching to shared_queue.txt" >> "$LOG"
tmux send-keys -t "rl4cv-e01-gen-gpu${GPU}" "export CUDA_VISIBLE_DEVICES=$GPU && bash $WORK/queue_worker.sh $LOG" Enter
