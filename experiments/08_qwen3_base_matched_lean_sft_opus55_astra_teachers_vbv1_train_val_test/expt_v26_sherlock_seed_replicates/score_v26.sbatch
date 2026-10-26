#!/bin/bash
#SBATCH -J rl4cv_v26_score
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH --array=0-7
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
# Lean-score one sample (array index k = sample 0..7) of one V26 label with AT-477's score_one.sh (veribench
# score_scsc.py --skip-tc at 59059a2, AT-475 grading dir). Never on dev: 4 parallel Lean runs exceed its 16G cap.
# usage (via submit.sh): sbatch -t 03:00:00 score_v26.sbatch <label>
L=$1; k=$SLURM_ARRAY_TASK_ID
export G=$SCRATCH/rl4cv_sherlock/grading B=$SCRATCH/rl4cv_sherlock/v4_validation
export W=${SLURM_SUBMIT_DIR:?}/score
type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1
module load python/3.12.1 >/dev/null 2>&1; export PY=$(command -v python3.12)
bash $SLURM_SUBMIT_DIR/score_one.sh $L $k
test -f $W/$L/scores/${L}_s$k/scsc_${L}_s${k}_${L}_s$k.json || { echo "no score file for ${L}_s$k"; exit 1; }
