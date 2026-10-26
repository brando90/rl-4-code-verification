#!/bin/bash
#SBATCH -J e20_p0_collect
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH -t 01:00:00
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%j.log
# TLDR: Join the complete saved-generation score tables and audit durable compiler evidence on a CPU node.
set -eo pipefail
type module >/dev/null 2>&1 || source /etc/profile
module load python/3.12.1
set -u
E20=$SCRATCH/rl4cv_sherlock/e20
export CUDA_VISIBLE_DEVICES="" RL4CV_SRC="$SCRATCH/rl4cv_sherlock/grading/rl4cv/src"
python3.12 "$E20/code/build_phase0_cells_e20.py"
python3.12 "$E20/code/collect_phase0_cpu_e20.py"
