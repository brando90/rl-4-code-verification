#!/bin/bash
# TLDR: experiment 18a scoring on CPU (one task per model): Reasoning Gym score_answer / GSM8K exact numeric match.
#SBATCH -J e18a_score
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 04:00:00
#SBATCH --array=0-2
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/env.sh
TAGS=(qwen3_0p6b qwen3_1p7b qwen3_4b); TAG=${TAGS[$SLURM_ARRAY_TASK_ID]}
$E18A_VENV/bin/python $CODE/score.py --run $RUN --model-tag $TAG
echo "SCORE OK"
