#!/bin/bash
# TLDR: submit the full experiment 18a v2 chain after the smoke passed: gen array (10 tasks, %2) -> score (afterany) -> analyze; embed (2 tasks, %1) runs alongside. 12 QOS gpu slots in all. Prints and saves every job id.
# usage: bash submit_full.sh                 (everything, when QOS gpu has 12 free slots)
#        GEN_ARRAY=4-9 bash submit_full.sh   (QOS gpu short: only that part of gen + embed; later the rest with
#        sbatch --array=<idx>%2 gen.sbatch, then bash submit_tail.sh <embed id> <every gen id>)
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd $E18V2_HOME
D=$CODE/slurm/farmshare
USED=$(squeue -r -h -u $USER -q gpu | wc -l)
echo "GPU tasks already queued/running for $USER on QOS gpu: $USED (limit 32 submitted, 4 running); this chain needs 12"
if [ $(( USED + 12 )) -gt 32 ] && [ -z "${GEN_ARRAY:-}" ]; then echo "not enough QOS gpu room: set GEN_ARRAY to a part that fits"; exit 3; fi
GEN=$(sbatch --parsable ${GEN_ARRAY:+--array=$GEN_ARRAY%2} $D/gen.sbatch)
EMB=$(sbatch --parsable $D/embed.sbatch)
echo "$(date -Is) gen=$GEN${GEN_ARRAY:+[$GEN_ARRAY]} embed=$EMB" | tee -a $E18V2_HOME/job_ids.txt
if [ -n "${GEN_ARRAY:-}" ]; then echo "partial gen: submit the rest, then: bash $D/submit_tail.sh $EMB $GEN <other gen ids>"; exit 0; fi
bash $D/submit_tail.sh $EMB $GEN
