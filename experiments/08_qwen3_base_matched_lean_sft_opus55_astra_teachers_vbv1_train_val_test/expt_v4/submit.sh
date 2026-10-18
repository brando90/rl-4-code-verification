#!/usr/bin/env bash
# TLDR: Submit CPU preparation, then two serial full-training jobs with success dependencies and no resampling.
set -euo pipefail
cd "$(dirname "$0")"
test ! -e jobs.tsv || { echo 'Existing submission receipt: inspect jobs.tsv before another launch.' >&2; exit 2; }
mkdir -p logs
PREP=$(sbatch --parsable --account=sanmi --partition=normal --cpus-per-task=4 --mem=16G --time=01:00:00 \
  --job-name=rl4cv-sherlock-prepare --output="$PWD/logs/%j.out" run_job.sh prepare)
printf 'phase\tjob_id\nprepare\t%s\n' "$PREP" > jobs.tsv
ONE=$(sbatch --parsable --account=sanmi --partition=gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' \
  --cpus-per-task=4 --mem=64G --time=04:00:00 --dependency="afterok:$PREP" --kill-on-invalid-dep=yes \
  --job-name=rl4cv-sherlock-sft-seed0 --output="$PWD/logs/%j.out" run_job.sh train 20260830)
printf 'seed_20260830\t%s\n' "$ONE" >> jobs.tsv
TWO=$(sbatch --parsable --account=sanmi --partition=gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' \
  --cpus-per-task=4 --mem=64G --time=04:00:00 --dependency="afterok:$ONE" --kill-on-invalid-dep=yes \
  --job-name=rl4cv-sherlock-sft-seed1 --output="$PWD/logs/%j.out" run_job.sh train 20260831)
printf 'seed_20260831\t%s\n' "$TWO" >> jobs.tsv
FINAL=$(sbatch --parsable --account=sanmi --partition=normal --cpus-per-task=1 --mem=2G --time=02:00:00 \
  --dependency="afterany:$PREP:$ONE:$TWO" --job-name=rl4cv-sherlock-finalize --output="$PWD/logs/%j.out" \
  --wrap='module load python/3.14.2; python3 -u finalize.py')
printf 'finalize\t%s\n' "$FINAL" >> jobs.tsv
cat jobs.tsv
