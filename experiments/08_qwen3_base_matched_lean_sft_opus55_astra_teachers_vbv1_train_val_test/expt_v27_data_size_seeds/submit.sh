#!/usr/bin/env bash
# TLDR: Submit the whole V27 chain once: prep -> train array (6, %3) -> gen array (aftercorr, %3) -> 6 score arrays (8, %4)
# -> collector; every job id is appended to jobs_v27.tsv.
# usage: cd $SCRATCH/rl4cv_sherlock/expt_v27 && bash submit.sh
set -euo pipefail
cd "$(dirname "$0")"
test ! -e jobs_v27.tsv || { echo 'Existing submission receipt: inspect jobs_v27.tsv before another launch.' >&2; exit 2; }
test ! -e runs || { echo 'runs/ exists: a trajectory may already be here; inspect before another launch.' >&2; exit 2; }
mkdir -p logs
MAIL=(--mail-type=BEGIN,END,FAIL --mail-user=brandojazz@gmail.com,brando.science@gmail.com)
DEP=(--kill-on-invalid-dep=yes)
sb() { sbatch --parsable --account=sanmi -D "$PWD" "${MAIL[@]}" "$@"; }
rec() { printf '%s\t%s\n' "$1" "$2" >> jobs_v27.tsv; }
N=$(( $(wc -l < runs.tsv) - 1 )); LAST=$(( N - 1 ))
printf 'phase\tjob_id\n' > jobs_v27.tsv
PREP=$(sb -p normal -c 4 --mem=32G -t 02:00:00 -J rl4cv-v27-prepare -o "$PWD/logs/%x_%j.out" run_job.sh prepare)
rec prepare "$PREP"
# Training: expt_v4's resources (one 80 GB GPU, 4 cores, 64G); the 50% runs need ~35 min, 2 h covers model load and queue noise.
TR=$(sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c 4 --mem=64G -t 02:00:00 --array="0-$LAST%3" \
  --dependency="afterok:$PREP" "${DEP[@]}" -J rl4cv-v27-train -o "$PWD/logs/%x_%A_%a.out" run_job.sh train)
rec train_array "$TR"
# Generation task i starts when training task i succeeds (aftercorr); 5 h because small-data checkpoints may run Base-like.
GEN=$(sb -t 05:00:00 --array="0-$LAST%3" --dependency="aftercorr:$TR" "${DEP[@]}" -J rl4cv-v27-gen \
  -o "$PWD/logs/%x_%A_%a.out" gen_v27.sbatch)
rec gen_array "$GEN"
ALL="$PREP:$TR:$GEN"
while IFS=$'\t' read -r IDX FRAC SEED RUN LABEL; do
  [ "$IDX" = index ] && continue
  SC=$(sb -t 03:00:00 --dependency="afterok:${GEN}_${IDX}" "${DEP[@]}" -J "rl4cv-v27-score-$RUN" \
    -o "$PWD/logs/%x_%A_%a.out" score_v27.sbatch "$LABEL")
  rec "score_$RUN" "$SC"
  ALL="$ALL:$SC"
done < runs.tsv
COL=$(sb -p normal -c 1 --mem=4G -t 01:00:00 --dependency="afterany:$ALL" -J rl4cv-v27-collect -o "$PWD/logs/%x_%j.out" \
  collect_v27.sh)
rec collect "$COL"
cat jobs_v27.tsv
squeue -u "$USER" -o '%.14i %.30j %.9P %.8T %.24R' | grep -E 'JOBID|rl4cv-v27' || true
