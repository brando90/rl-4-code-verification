#!/usr/bin/env bash
# TLDR: Non-model host watchdog for experiment 08's long jobs on skampere1 (agents-config Rule 48): every run takes the pipeline lock
# ($WORK/pipeline/lock, shared with pipeline_e08.py so recovery never races the orchestrator or an operator), reads $WORK/watchdog/jobs.tsv
# (name, tmux session, launch command, done-marker glob, optional freshness file:max_age_s), records boot and process identities, counts the
# session's real child processes, flags a live-but-stale job (fresh file older than max_age_s) with STALE_<name> without killing it, and for a
# job whose tmux session is gone and whose done marker is absent relaunches it ONCE per incident (the launchers are resumable: finished
# segments, generations and scored shards are skipped, never duplicated); a second death writes CRITICAL_<name> and stops touching that job.
# A reboot is one incident for every job. It never kills anything, never duplicates a live session, never emails and makes no model calls.
# Usage: watchdog_e08.sh            one check (cron every 15 min)
#        watchdog_e08.sh --reboot   @reboot: wait for the filesystems, then one check
#        watchdog_e08.sh --selftest harmless self-test with a fake job (sleep), verifies relaunch-once semantics, cleans up
set -uo pipefail
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
WD="$WORK/watchdog"; mkdir -p "$WD"
JOBS="${E08_WATCHDOG_JOBS:-$WD/jobs.tsv}"
LOG="$WD/watchdog.log"; STATUS="$WD/status.json"
ts() { date -u +%FT%TZ; }
log() { echo "[$(ts)] $*" >> "$LOG"; }
BOOT="$(cat /proc/sys/kernel/random/boot_id)"
MODE="${1:-check}"
if [ "$MODE" = "--reboot" ]; then sleep 120; fi
if [ "$MODE" = "--selftest" ]; then
  T="$WD/selftest"; rm -rf "$T"; mkdir -p "$T"
  printf 'selftest\twd-selftest-e08\tsleep 3; touch %s/done\t%s/done\n' "$T" "$T" > "$T/jobs.tsv"
  tmux kill-session -t wd-selftest-e08 2>/dev/null
  E08_WATCHDOG_JOBS="$T/jobs.tsv" E08_WATCHDOG_STATE="$T" "$0" check; r1=$(grep -c "RELAUNCH selftest" "$LOG")
  sleep 1; tmux kill-session -t wd-selftest-e08 2>/dev/null; rm -f "$T/done"
  E08_WATCHDOG_JOBS="$T/jobs.tsv" E08_WATCHDOG_STATE="$T" "$0" check; r2=$(grep -c "RELAUNCH selftest" "$LOG"); c2=$(ls "$T"/CRITICAL_selftest 2>/dev/null | wc -l)
  tmux kill-session -t wd-selftest-e08 2>/dev/null; rm -rf "$T"
  if [ "$r1" -ge 1 ] && [ "$r2" -eq "$r1" ] && [ "$c2" = 1 ]; then log "SELFTEST PASS (relaunched once, second death marked CRITICAL, no duplicate)"; echo "SELFTEST PASS"; exit 0; fi
  log "SELFTEST FAIL r1=$r1 r2=$r2 critical=$c2"; echo "SELFTEST FAIL"; exit 1
fi
STATE="${E08_WATCHDOG_STATE:-$WD}"; mkdir -p "$STATE"
mkdir -p "$WORK/pipeline"; exec 9>"$WORK/pipeline/lock"
flock -w 900 9 || { log "lock $WORK/pipeline/lock busy for 900 s; skipping this check (no recovery without the lock)"; exit 0; }
PREV_BOOT="$(cat "$STATE/boot_id" 2>/dev/null || true)"
if [ -n "$PREV_BOOT" ] && [ "$PREV_BOOT" != "$BOOT" ]; then
  log "REBOOT detected: $PREV_BOOT -> $BOOT; one recovery allowed again for every job"
  rm -f "$STATE"/recovered_* "$STATE"/CRITICAL_*
fi
echo "$BOOT" > "$STATE/boot_id"
[ -f "$JOBS" ] || { log "no jobs file ($JOBS)"; exit 0; }
rows="["
while IFS=$'\t' read -r name session cmd marker fresh; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue;; esac
  state="unknown"; pid=""; kids=0; age=""
  if compgen -G "$marker" > /dev/null; then state="done"
  elif tmux has-session -t "$session" 2>/dev/null; then
    state="running"; pid="$(tmux list-panes -t "$session" -F '#{pane_pid}' 2>/dev/null | head -1)"
    [ -n "$pid" ] && kids="$(pstree -p "$pid" 2>/dev/null | grep -o '([0-9]*)' | wc -l)"
    if [ -n "$fresh" ]; then
      ff="${fresh%%:*}"; maxage="${fresh##*:}"
      if [ -f "$ff" ]; then age=$(( $(date +%s) - $(stat -c %Y "$ff") )); else age="missing"; fi
      if [ "$age" = missing ] || [ "$age" -gt "$maxage" ]; then
        state="stale"; [ -f "$STATE/STALE_$name" ] || { echo "$(ts) age=$age max=$maxage kids=$kids" > "$STATE/STALE_$name"; log "STALE $name: session $session alive ($kids processes) but $ff age=$age s > $maxage s; not killing"; }
      else rm -f "$STATE/STALE_$name"; fi
    fi
  elif [ -f "$STATE/CRITICAL_$name" ]; then state="critical"
  elif [ -f "$STATE/recovered_$name" ]; then
    state="critical"; echo "$(ts) second death after one recovery" > "$STATE/CRITICAL_$name"; log "CRITICAL $name: session $session dead again after its one recovery; not relaunching"
  else
    tmux new-session -d -s "$session" "$cmd" && { echo "$(ts) boot=$BOOT" > "$STATE/recovered_$name"; state="relaunched"; log "RELAUNCH $name in tmux $session: $cmd"; } || { state="relaunch_failed"; log "RELAUNCH FAILED $name"; }
  fi
  rows="$rows{\"name\":\"$name\",\"session\":\"$session\",\"state\":\"$state\",\"pane_pid\":\"$pid\",\"processes\":$kids,\"fresh_age_s\":\"$age\"},"
done < "$JOBS"
rows="${rows%,}]"
echo "{\"checked_utc\":\"$(ts)\",\"boot_id\":\"$BOOT\",\"host\":\"$(hostname)\",\"jobs\":$rows}" > "$STATUS"
log "check ok: $(echo "$rows" | tr -d '\n' | cut -c1-300)"
