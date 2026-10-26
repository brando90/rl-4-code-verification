#!/bin/bash
#SBATCH -J e20_p0_score
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH -t 03:00:00
#SBATCH --array=0-31
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%A_%a.log
# TLDR: Experiment 20 Phase 0a scoring: 32 job directories (4 chunks x 8 sample indices, about 135 files each) through
# score_e20.sh (frozen scorer 59059a2 --skip-tc + D-109 durable capture) on the normal partition, one CPU each.
E20=$SCRATCH/rl4cv_sherlock/e20
c=$(( SLURM_ARRAY_TASK_ID / 8 )); k=$(( SLURM_ARRAY_TASK_ID % 8 )); n=e20_p0_c${c}_s${k}
o=$E20/phase0/scores/$n
expected=$o/scsc_${n}_${n}.json; receipt=$o/completion_receipt.txt
if [ -f "$expected" ] && [ -f "$receipt" ]; then echo "$n done-before"; exit 0; fi
if [ -e "$o" ]; then
  attempt=$E20/phase0/scores/attempts/$n/$(date -u +%Y%m%dT%H%M%SZ)_${SLURM_JOB_ID:-manual}_${SLURM_ARRAY_TASK_ID:-na}
  mkdir -p "$(dirname "$attempt")"
  mv "$o" "$attempt"
  echo "$n preserved-prior-attempt=$attempt"
fi
t0=$(date +%s); bash "$E20/code/score_e20.sh" "$E20/phase0/jobs/$n" "$E20/phase0/train_pack" "$o"; rc=$?
if [ "$rc" -eq 0 ] && [ ! -f "$expected" ]; then
  echo "$n scorer returned 0 without expected output $expected" >&2
  rc=1
fi
if [ "$rc" -eq 0 ]; then
  printf 'completed_at=%s\njob=%s\narray_task=%s\nexpected_output=%s\n' "$(date -u +%FT%TZ)" "${SLURM_JOB_ID:-manual}" "${SLURM_ARRAY_TASK_ID:-na}" "$expected" > "$receipt"
fi
echo "$n rc=$rc $(( $(date +%s)-t0 ))s host=$(hostname -s)"; exit $rc
