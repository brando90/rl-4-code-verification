#!/bin/bash
# AT-477: score one sample job (<label>_s<k>) with a claim, so dev and normal-partition workers never score the same one.
# usage: score_one.sh <label> <k> [--if-untouched]   (inside Slurm; W, G, B, PY as in score_v16.sh)
set -uo pipefail
L=$1; k=$2; n=${L}_s$k; o=$W/$L/scores/$n; c=$W/claims/$n; me=${SLURM_JOB_ID:-$$}
mkdir -p $W/claims $W/logs
[ -f $o/scsc_${n}_${n}.json ] && { echo "$n done-before"; exit 0; }
if [ "${3:-}" = "--if-untouched" ] && [ -d $o ]; then echo "$n touched-by-other"; exit 0; fi
mkdir $c 2>/dev/null || { echo "$n claimed-by $(cat $c/job 2>/dev/null)"; exit 0; }
echo $me > $c/job
t=$W/$L/scores/.tmp_${n}_$me; rm -rf $t
t0=$(date +%s); PYTHON=$PY $G/score_sherlock.sh $W/$L/jobs/$n $B/run/validation_pack $t > $W/logs/$n.$me.log 2>&1; rc=$?
if [ $rc = 0 ] && [ -f $t/scsc_${n}_${n}.json ]; then rm -rf $o; mv $t $o; fi
rm -rf $c; echo "$n rc=$rc $(( $(date +%s)-t0 ))s job=$me host=$(hostname -s)"
