#!/bin/bash
#SBATCH -J e20_p0_retry
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH -t 01:00:00
#SBATCH --array=0
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%A_%a.log
# TLDR: Retry only an infrastructure-failed saved cell through unchanged score_sherlock.sh and D-109 capture.
set -eo pipefail
type module >/dev/null 2>&1 || source /etc/profile
module load python/3.12.1
set -u
E20=$SCRATCH/rl4cv_sherlock/e20
attempt=${E20_RETRY_ATTEMPT:-2}
name=${E20_RETRY_NAME:?Explicit immutable retry job name required}
job=$E20/phase0/retry_jobs/$name
out=$E20/phase0/retries/strict/$name
test -d "$job"
test ! -e "$out"
mkdir -p "$out"
export CUDA_VISIBLE_DEVICES=""
bash "$E20/code/score_e20.sh" "$job" "$E20/phase0/train_pack" "$out"
test -f "$out/scsc_${name}_${name}.json"
printf 'completed_at=%s\njob=%s\narray_task=%s\nattempt=%s\n' "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" "$SLURM_ARRAY_TASK_ID" "$attempt" > "$out/completion_receipt.txt"
