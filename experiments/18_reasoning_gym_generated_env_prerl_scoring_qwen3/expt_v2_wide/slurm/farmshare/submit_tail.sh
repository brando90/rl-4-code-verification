#!/bin/bash
# TLDR: submit score (afterany: every gen job) and analyze (afterany: score + embed) for experiment 18a v2; usage: bash submit_tail.sh <embed id> <gen id> [<gen id> ...]
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd $E18V2_HOME
D=$CODE/slurm/farmshare
EMB=$1; shift
DEP=$(IFS=:; echo "$*")
SCO=$(sbatch --parsable --dependency=afterany:$DEP $D/score.sbatch)
ANA=$(sbatch --parsable --dependency=afterany:$SCO:$EMB $D/analyze.sbatch)
echo "$(date -Is) score=$SCO (after gen $*) analyze=$ANA (after score + embed $EMB)" | tee -a $E18V2_HOME/job_ids.txt
