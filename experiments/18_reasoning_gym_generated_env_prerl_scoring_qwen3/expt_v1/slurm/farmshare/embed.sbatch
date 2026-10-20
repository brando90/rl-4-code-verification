#!/bin/bash
# TLDR: experiment 18a alignment embeddings: one L40S per model (array 0-2), transformers forward pass over all 38 x 256 prompts.
#SBATCH -J e18a_embed
#SBATCH -p gpu
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 02:00:00
#SBATCH --array=0-2%4
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/env.sh
TAGS=(qwen3_0p6b qwen3_1p7b qwen3_4b); TAG=${TAGS[$SLURM_ARRAY_TASK_ID]}
source $FS_HF/bin/activate
python $CODE/embed.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG
echo "EMBED OK"
