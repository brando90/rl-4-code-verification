#!/usr/bin/env bash
# TLDR: Task-scoped watchdog for experiment 01's Claude worker on skampere1. Every INTERVAL seconds it writes a
# heartbeat, relaunches a dead worker from its checkpoint (max 3), nudges an idle worker whose jobs stopped and
# whose checkpoint went stale (max 24, at most hourly), posts events to issue #3, and exits on STATUS_e01 = DONE/BLOCKED.
# Usage: bash watchdog_e01.sh            (live)
#        DRY_RUN=1 ONCE=1 S=<fake-session> bash watchdog_e01.sh   (simulation: logs actions, executes none)
set -uo pipefail
export PATH=/dfs/scratch0/brando9/bin:/lfs/skampere1/0/brando9/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
REPO=$WORK/rl-4-code-verification
S=${S:-rl4cv-e01-qwen-vbv1-baseline}
CKPT=$REPO/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01.md
STATUS=$WORK/STATUS_e01
BRIEF=$WORK/DISPATCH_e01.md
LOG=${LOG:-$WORK/watchdog_e01.log}
STATE=${STATE:-$WORK/watchdog_e01.state}
INTERVAL=${INTERVAL:-600}; NUDGE_AFTER_MIN=${NUDGE_AFTER_MIN:-45}
MAX_RELAUNCH=3; MAX_NUDGE=24
DRY=${DRY_RUN:-0}; ONCE=${ONCE:-0}

log() { echo "$(date '+%m-%d-%Y %H:%M:%S') $*" >> "$LOG"; }
act() { if [ "$DRY" = 1 ]; then log "DRY-RUN would run: $*"; else "$@"; fi; }
notify() {
  log "NOTIFY: $1"
  act gh issue comment 3 -R brando90/rl-4-code-verification \
    --body "**Experiment 01 watchdog (skampere1, $(date '+%m-%d-%Y %H:%M')):** $1" >> "$LOG" 2>&1
  [ "$DRY" = 1 ] || echo "$1" | mail -s "rl4cv e01 watchdog" brando.science@gmail.com >> "$LOG" 2>&1 || true
}
worker_pid() { local pp; pp=$(tmux list-panes -t "=$S" -F '#{pane_pid}' 2>/dev/null | head -1)
  [ -n "$pp" ] && pgrep -P "$pp" | head -1; }
# Experiment job processes: generation, run_model.sh, the frozen scorer (vLLM runs inside the generate process tree).
jobs_alive() { pgrep -u "${USER:-$(whoami)}" -f 'rl4cv\.|run_model\.sh|score_scsc|vllm' | wc -l; }
send() { act tmux send-keys -t "=$S:" -l "$1"; act tmux send-keys -t "=$S:" Enter; }

relaunches=$(grep -c ' RELAUNCH ' "$LOG" 2>/dev/null); relaunches=${relaunches:-0}
nudges=$(grep -c ' NUDGE ' "$LOG" 2>/dev/null); nudges=${nudges:-0}
last_nudge=0
log "START session=$S dry=$DRY interval=$INTERVAL relaunches=$relaunches nudges=$nudges"
while true; do
  now=$(date +%s); st=$(cat "$STATUS" 2>/dev/null || echo UNKNOWN)
  wp=$(worker_pid); nj=$(jobs_alive)
  ck=-1; [ -f "$CKPT" ] && ck=$(( (now - $(stat -c %Y "$CKPT")) / 60 ))
  echo "$(date '+%m-%d-%Y %H:%M:%S') boot=$(cat /proc/sys/kernel/random/boot_id) status=$st worker_pid=${wp:-none} job_procs=$nj ckpt_age_min=$ck relaunches=$relaunches nudges=$nudges" > "$STATE"
  case "$st" in DONE|BLOCKED) notify "worker reports **$st**; watchdog stopping. See \`expt_v1/CKPT_e01.md\` and \`results.md\`."; exit 0 ;; esac
  if [ -z "$wp" ]; then
    if [ "$relaunches" -ge "$MAX_RELAUNCH" ]; then
      notify "worker process gone and all $MAX_RELAUNCH relaunches used; stopping. Experiment job processes still alive: $nj. Needs the master or Brando."; exit 1
    fi
    relaunches=$((relaunches + 1)); log "RELAUNCH $relaunches"
    tmux has-session -t "=$S" 2>/dev/null || act tmux new -d -s "$S" -c "$REPO"
    send "cd $REPO && /dfs/scratch0/brando9/bin/clauded --remote-control $S --model claude-sonnet-5 --effort high 'Resume experiment 01: read $BRIEF, then expt_v1/CKPT_e01.md, and continue from the recorded next step. Check tmux ls and nvidia-smi first; never start a second copy of a stage that is still running.'"
    notify "worker process was gone (status=$st, checkpoint age ${ck} min, $nj job processes alive); relaunched it from the checkpoint ($relaunches/$MAX_RELAUNCH)."
  elif [ "$nj" -eq 0 ] && [ "$ck" -ge "$NUDGE_AFTER_MIN" ] && [ $((now - last_nudge)) -ge 3600 ]; then
    if [ "$nudges" -ge "$MAX_NUDGE" ]; then
      notify "worker idle with no jobs after $MAX_NUDGE hourly nudges (checkpoint age ${ck} min); stopping. Attach: \`ssh skampere1.stanford.edu -t tmux attach -t $S\`"; exit 1
    fi
    nudges=$((nudges + 1)); last_nudge=$now; log "NUDGE $nudges"
    send "Watchdog check-in ($(date '+%m-%d-%Y %H:%M')): no experiment 01 GPU or scorer jobs are running and CKPT_e01.md is ${ck} min old. Continue the full declared set from the checkpoint's next step; if everything is finished, commit, clean up and write DONE to $STATUS; if truly blocked, write BLOCKED with the reason."
    [ "$nudges" -eq 1 ] || [ $((nudges % 6)) -eq 0 ] && notify "worker idle with no jobs and a ${ck}-min-old checkpoint; nudged it ($nudges/$MAX_NUDGE)."
  fi
  [ "$ONCE" = 1 ] && exit 0
  sleep "$INTERVAL"
done
