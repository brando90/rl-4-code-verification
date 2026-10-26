#!/bin/bash
#SBATCH -J e20_p0_materialize
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH -t 00:30:00
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%j.log
# TLDR: Materialize only the saved 4,312 Phase 0 generations into CPU scorer jobs; no generation or model calls.
set -euo pipefail
E20=$SCRATCH/rl4cv_sherlock/e20
set +u
type module >/dev/null 2>&1 || source /etc/profile
module load python/3.12.1
set -u
export CUDA_VISIBLE_DEVICES="" RL4CV_SRC="$SCRATCH/rl4cv_sherlock/grading/rl4cv/src"
python3.12 "$E20/code/materialize_e20.py"
