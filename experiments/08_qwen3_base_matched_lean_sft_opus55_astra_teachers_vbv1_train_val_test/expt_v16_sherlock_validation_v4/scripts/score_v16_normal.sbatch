#!/bin/bash
#SBATCH -J v16score_n
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=8G
#SBATCH -t 02:00:00
#SBATCH --array=0-23
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/v4_validation/score_v16/logs/normal_%A_%a.out
# AT-477 extra capacity: one sample per array task, in reverse order (base s7 first) so it meets the dev worker
# from the other end; skips any sample the dev worker already touched or that is claimed.
export G=$SCRATCH/rl4cv_sherlock/grading B=$SCRATCH/rl4cv_sherlock/v4_validation
export W=$B/score_v16
type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1
module load python/3.12.1 >/dev/null 2>&1; export PY=$(command -v python3.12)
list=(); for L in v16_v4_20260830 v16_v4_20260831 v16_base; do for k in 0 1 2 3 4 5 6 7; do list+=("$L $k"); done; done
i=$(( 23 - SLURM_ARRAY_TASK_ID )); bash $W/score_one.sh ${list[$i]} --if-untouched
