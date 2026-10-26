#!/bin/bash
# TLDR: Sherlock fallback alignment embeddings, one GPU per model (array 0-2), transformers inside the AT-476 image.
#SBATCH -J e18a_embed
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 02:00:00
#SBATCH --array=0-2
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/sherlock/env.sh
LDENV=$(e18a_ldenv)
TAGS=(qwen3_0p6b qwen3_1p7b qwen3_4b); TAG=${TAGS[$SLURM_ARRAY_TASK_ID]}
apptainer exec --nv -B /scratch --env "$APPENV$LDENV" $SIF python3 $CODE/embed.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG
echo "EMBED OK"
