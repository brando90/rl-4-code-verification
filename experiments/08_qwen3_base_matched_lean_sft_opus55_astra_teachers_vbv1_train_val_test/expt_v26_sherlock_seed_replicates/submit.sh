#!/usr/bin/env bash
# TLDR: Submit the whole V26 chain once: prep -> 3 trainings -> 3 generations -> 3x8 scoring -> collector; ids in jobs_v26.tsv.
# usage: cd $SCRATCH/rl4cv_sherlock/expt_v26 && bash submit.sh
set -euo pipefail
cd "$(dirname "$0")"
test ! -e jobs_v26.tsv || { echo 'Existing submission receipt: inspect jobs_v26.tsv before another launch.' >&2; exit 2; }
mkdir -p logs
MAIL=(--mail-type=BEGIN,END,FAIL --mail-user=brandojazz@gmail.com,brando.science@gmail.com)
DEP=(--kill-on-invalid-dep=yes)
sb() { sbatch --parsable --account=sanmi -D "$PWD" "${MAIL[@]}" "$@"; }
rec() { printf '%s\t%s\n' "$1" "$2" >> jobs_v26.tsv; }
printf 'phase\tjob_id\n' > jobs_v26.tsv
PREP=$(sb -p normal -c 4 --mem=32G -t 02:00:00 -J rl4cv-v26-prepare -o "$PWD/logs/%x_%j.out" run_job.sh prepare)
rec prepare "$PREP"
ALL="$PREP"
# arm seed train-cpus train-mem train-wall gen-wall (1p7b = expt_v4's resources; 4b = host optimizer, see PROTOCOL.md)
for spec in "1p7b 20260832 4 64G 04:00:00 06:00:00" "4b 20260830 16 128G 12:00:00 10:00:00" "4b 20260831 16 128G 12:00:00 10:00:00"; do
  read -r ARM SEED CPUS MEM TWALL GWALL <<< "$spec"
  RUN=${ARM}_s$SEED; L=v26_$RUN
  TR=$(sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c "$CPUS" --mem="$MEM" -t "$TWALL" \
    --dependency="afterok:$PREP" "${DEP[@]}" -J "rl4cv-v26-train-$RUN" -o "$PWD/logs/%x_%j.out" run_job.sh train "$ARM" "$SEED")
  rec "train_$RUN" "$TR"
  GEN=$(sb -t "$GWALL" --dependency="afterok:$TR" "${DEP[@]}" -J "rl4cv-v26-gen-$RUN" -o "$PWD/logs/%x_%j.out" \
    gen_v26.sbatch "$RUN" "$L")
  rec "gen_$RUN" "$GEN"
  SC=$(sb -t 03:00:00 --dependency="afterok:$GEN" "${DEP[@]}" -J "rl4cv-v26-score-$RUN" -o "$PWD/logs/%x_%A_%a.out" \
    score_v26.sbatch "$L")
  rec "score_$RUN" "$SC"
  ALL="$ALL:$TR:$GEN:$SC"
done
COL=$(sb -p normal -c 1 --mem=4G -t 01:00:00 --dependency="afterany:$ALL" -J rl4cv-v26-collect -o "$PWD/logs/%x_%j.out" \
  collect_v26.sh)
rec collect "$COL"
cat jobs_v26.tsv
squeue -u "$USER" -o '%.10i %.28j %.9P %.8T %.20R' | grep -E 'JOBID|rl4cv-v26' || true
