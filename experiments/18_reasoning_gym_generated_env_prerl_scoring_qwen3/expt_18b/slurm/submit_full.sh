#!/bin/bash
# TLDR: submit the whole 18b chain from $B (after smoke OK): pre-eval, train array (32), post-eval array (aftercorr on train), analyze (afterany pre+post). Appends the ids to $B/job_ids.txt. Mail goes to both addresses (set in every script).
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd $B
D=$CODE/slurm
PRE=$(sbatch --parsable $D/pre_eval.sbatch)
TR=$(sbatch --parsable $D/train.sbatch)
PO=$(sbatch --parsable --dependency=aftercorr:$TR $D/post_eval.sbatch)
AN=$(sbatch --parsable --dependency=afterany:$PRE:$PO $D/analyze.sbatch)
echo "$(date -Is) pre=$PRE train=$TR post=$PO analyze=$AN" | tee -a $B/job_ids.txt
