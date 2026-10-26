#!/bin/bash
# TLDR: experiment 18a v2 scoring on CPU: array 0-7 = (model i/4, set shard i%4), Reasoning Gym score_answer / GSM8K exact numeric match.
#SBATCH -J e18v2_score
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 06:00:00
#SBATCH --array=0-7
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/env.sh
TAGS=(qwen3_0p6b qwen3_1p7b); TAG=${TAGS[$(( SLURM_ARRAY_TASK_ID / 4 ))]}
$E18A_VENV/bin/python $CODE/score.py --run $RUN --model-tag $TAG --shard $(( SLURM_ARRAY_TASK_ID % 4 )) --nshards 4
echo "SCORE OK"
