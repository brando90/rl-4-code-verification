#!/bin/bash
# TLDR: submit the full experiment 18a chain after the smoke passed: gen array -> score (afterany) -> analyze; embed runs alongside. Prints and saves every job id.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd $E18A_HOME
D=$CODE/slurm/farmshare
echo "GPU jobs already queued/running for $USER on QOS gpu: $(squeue -r -h -u $USER -q gpu | wc -l) (limit 32 submitted, 4 running)"
GEN=$(sbatch --parsable $D/gen.sbatch)
EMB=$(sbatch --parsable $D/embed.sbatch)
SCO=$(sbatch --parsable --dependency=afterany:$GEN $D/score.sbatch)
ANA=$(sbatch --parsable --dependency=afterany:$SCO:$EMB $D/analyze.sbatch)
echo "$(date -Is) gen=$GEN embed=$EMB score=$SCO analyze=$ANA" | tee -a $E18A_HOME/job_ids.txt
