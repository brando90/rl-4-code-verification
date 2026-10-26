#!/bin/bash
# TLDR: experiment 18a generation array: one L40S per (model, shard) from tasks.tsv, vLLM, 16 samples x 256 items per set; resumable (finished sets are skipped).
#SBATCH -J e18a_gen
#SBATCH -p gpu
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 12:00:00
#SBATCH --array=0-8%4
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/env.sh
read TAG SHARD NSHARDS <<< "$(e18a_task $SLURM_ARRAY_TASK_ID)"
echo "task $SLURM_ARRAY_TASK_ID: $TAG shard $SHARD/$NSHARDS on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
source $FS_HF/bin/activate
python $CODE/generate.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --shard $SHARD --nshards $NSHARDS
echo "GEN TASK OK"
