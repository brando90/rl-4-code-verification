#!/bin/bash
# AT-477: materialize + score the 08 v4 validation generations (v12 frozen settings) with the AT-475 Lean grader.
# Run inside Slurm: srun -p dev -c 4 --mem=16G -t 02:00:00 bash score_v16.sh   (resumable: finished scores are skipped)
set -uo pipefail
export G=$SCRATCH/rl4cv_sherlock/grading B=$SCRATCH/rl4cv_sherlock/v4_validation
export W=$B/score_v16
type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1
module load python/3.12.1 >/dev/null 2>&1; export PY=$(command -v python3.12)
mkdir -p $W/logs
echo "start $(date -Is) host=$(hostname) job=${SLURM_JOB_ID:-none}"
for s in 20260830 20260831 base; do
  L=v16_v4_$s; [ $s = base ] && L=v16_base
  if [ ! -d $W/$L/jobs ]; then
    PYTHONPATH=$G/rl4cv/src $PY -m rl4cv.veribench.jobs --gen $B/$s/full/raw.jsonl --out-root $W/$L/jobs --name $L | tail -1
  fi
done
for L in v16_v4_20260830 v16_v4_20260831 v16_base; do for k in 0 1 2 3 4 5 6 7; do echo "$L $k"; done; done |
xargs -P ${NP:-4} -L 1 bash -c 'L=$0; k=$1; n=${L}_s$k; o=$W/$L/scores/$n
  [ -f $o/scsc_${n}_${n}.json ] && { echo "$n done-before"; exit 0; }
  t0=$(date +%s); PYTHON=$PY $G/score_sherlock.sh $W/$L/jobs/$n $B/run/validation_pack $o > $W/logs/$n.log 2>&1
  echo "$n rc=$? $(( $(date +%s)-t0 ))s"'
n=$(ls $W/*/scores/*/scsc_*.json 2>/dev/null | grep -vc _cache)
echo "score files: $n of 24"
cd $W && tar czf $W/v16_scores.tgz */scores logs && ls -la $W/v16_scores.tgz
echo "end $(date -Is)"
