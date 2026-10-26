#!/bin/bash
# TLDR: Submit one experiment 20 validation evaluation on Sherlock: eval_gen.sbatch (GPU) then eval_score.sbatch (CPU array of 8)
# with an afterok dependency. usage: submit_eval_e20.sh <label> <model_dir>   (run on Sherlock, e.g. through sherlockctl exec)
set -euo pipefail
LABEL=$1; MODEL_DIR=$2; C=$SCRATCH/rl4cv_sherlock/e20/code
mkdir -p $SCRATCH/rl4cv_sherlock/e20/eval/logs
[ -f $MODEL_DIR/config.json ] || { echo "no model at $MODEL_DIR" >&2; exit 66; }
G=$(sbatch --parsable --export=ALL,LABEL=$LABEL,MODEL_DIR=$MODEL_DIR $C/eval_gen.sbatch)
S=$(sbatch --parsable --dependency=afterok:$G --export=ALL,LABEL=$LABEL $C/eval_score.sbatch)
echo "eval $LABEL: gen job $G, score array $S (afterok:$G), model $MODEL_DIR"
