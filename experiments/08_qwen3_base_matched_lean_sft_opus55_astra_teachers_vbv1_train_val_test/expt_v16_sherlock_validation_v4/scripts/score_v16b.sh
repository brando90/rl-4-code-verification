#!/bin/bash
# AT-477 rerun driver for dev (resumable): clears claims of jobs no longer running, then scores what is left, 4 at a time.
# srun -p dev -c 4 --mem=16G -t 02:00:00 bash score_v16b.sh
set -uo pipefail
export G=$SCRATCH/rl4cv_sherlock/grading B=$SCRATCH/rl4cv_sherlock/v4_validation
export W=$B/score_v16
type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1
module load python/3.12.1 >/dev/null 2>&1; export PY=$(command -v python3.12)
echo "start $(date -Is) host=$(hostname) job=${SLURM_JOB_ID:-none}"
live=" $(squeue -u $USER -h -o %A | tr '\n' ' ') "
for c in $W/claims/*/; do [ -d "$c" ] || continue; j=$(cat $c/job 2>/dev/null); case "$live" in *" $j "*) ;; *) echo "stale claim $c ($j)"; rm -rf $c;; esac; done
for L in v16_v4_20260830 v16_v4_20260831 v16_base; do for k in 0 1 2 3 4 5 6 7; do echo "$L $k"; done; done |
  xargs -P ${NP:-4} -L 1 bash $W/score_one.sh
echo "score files: $(ls $W/*/scores/*/scsc_*.json 2>/dev/null | wc -l) of 24"
cd $W && tar czf $W/v16_scores.tgz */scores/v16_* logs && ls -la $W/v16_scores.tgz
echo "end $(date -Is)"
