#!/bin/bash
#SBATCH -J e20_p0_partial
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH --array=0-31
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%A_%a.log
# TLDR: Experiment 20 Phase 0a partial credit, isolated D-109 revision 2: experiment 13's declaration adapter (factored_reward) on the same 32 job
# directories, one CPU each, D-109 durable capture; resumable (a finished partial_<job>.json is skipped).
E20=$SCRATCH/rl4cv_sherlock/e20; G=$SCRATCH/rl4cv_sherlock/grading
c=$(( SLURM_ARRAY_TASK_ID / 8 )); k=$(( SLURM_ARRAY_TASK_ID % 8 )); n=e20_p0_c${c}_s${k}
o=$E20/phase0/partial/$n
expected=$o/partial_$n.json; receipt=$o/completion_receipt.txt
if [ -f "$expected" ] && [ -f "$receipt" ]; then echo "$n done-before"; exit 0; fi
if [ -e "$o" ]; then
  attempt=$E20/phase0/partial/attempts/$n/$(date -u +%Y%m%dT%H%M%SZ)_${SLURM_JOB_ID:-manual}_${SLURM_ARRAY_TASK_ID:-na}
  mkdir -p "$(dirname "$attempt")"
  mv "$o" "$attempt"
  echo "$n preserved-prior-attempt=$attempt"
fi
type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1 || true
module load python/3.12.1 >/dev/null 2>&1 || true
for key in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN|OAUTH_TOKEN' || true); do unset "$key"; done
export CUDA_VISIBLE_DEVICES="" PYTHONPATH="$G/rl4cv/src" PATH="$G/bin:$PATH" RL4CV_SRC=$G/rl4cv/src E20_GRADING=$G
mkdir -p "$o"
t0=$(date +%s); python3.12 "$E20/code/cpu_partial_d109_v2/partial_credit_e20.py" --job-dir "$E20/phase0/jobs/$n" --out "$expected" --evidence-root "$o/compiler_diagnostics"; rc=$?
if [ "$rc" -eq 0 ] && [ ! -f "$expected" ]; then
  echo "$n partial-credit runner returned 0 without expected output $expected" >&2
  rc=1
fi
if [ "$rc" -eq 0 ]; then
  printf 'completed_at=%s\njob=%s\narray_task=%s\nexpected_output=%s\n' "$(date -u +%FT%TZ)" "${SLURM_JOB_ID:-manual}" "${SLURM_ARRAY_TASK_ID:-na}" "$expected" > "$receipt"
fi
echo "$n rc=$rc $(( $(date +%s)-t0 ))s host=$(hostname -s)"; exit $rc
