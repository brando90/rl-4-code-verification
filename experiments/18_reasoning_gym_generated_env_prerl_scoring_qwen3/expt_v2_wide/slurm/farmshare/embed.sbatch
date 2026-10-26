#!/bin/bash
# TLDR: experiment 18a v2 alignment embeddings: one L40S per model (array 0-1), transformers forward pass over every set's 256 prompts.
#SBATCH -J e18v2_embed
#SBATCH -p gpu
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 03:00:00
#SBATCH --array=0-1%1
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/env.sh
TAGS=(qwen3_0p6b qwen3_1p7b); TAG=${TAGS[$SLURM_ARRAY_TASK_ID]}
source $FS_HF/bin/activate
python $CODE/embed.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG
echo "EMBED OK"
