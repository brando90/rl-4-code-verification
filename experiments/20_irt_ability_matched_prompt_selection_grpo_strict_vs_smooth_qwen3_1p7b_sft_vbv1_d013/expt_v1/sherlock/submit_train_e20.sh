#!/bin/bash
# TLDR: Submit one experiment 20 training run on Sherlock. usage: submit_train_e20.sh <ARM> <SEED> <UPDATES> [RUNS_DIR] [PHASE0_CELLS] [IRT_ITEMS]
set -euo pipefail
ARM=$1; SEED=$2; UPDATES=$3; RUNS=${4:-$SCRATCH/rl4cv_sherlock/e20/train/runs}; C=$SCRATCH/rl4cv_sherlock/e20/code
mkdir -p $SCRATCH/rl4cv_sherlock/e20/train/logs $RUNS
EXP="ALL,ARM=$ARM,SEED=$SEED,UPDATES=$UPDATES,RUNS=$RUNS"
[ -n "${5:-}" ] && EXP="$EXP,PHASE0_CELLS=$5"
[ -n "${6:-}" ] && EXP="$EXP,IRT_ITEMS=$6"
J=$(sbatch --parsable -J e20_train_${ARM}_s${SEED} --export=$EXP $C/train.sbatch)
echo "train $ARM seed $SEED updates $UPDATES: job $J (runs in $RUNS)"
