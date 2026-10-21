#!/bin/bash
# TLDR: 18b training array: one H100 per (env, seed) = tasks.tsv line SLURM_ARRAY_TASK_ID+1, 32 tasks; 40 GRPO steps on Qwen3-1.7B, writes $RUNS/<run>/ckpt. A run with train_summary.json is skipped. Wall time is set from the smoke (SUBMIT.md step 4).
#SBATCH -J e18b_train
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MEM:80GB
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 02:00:00
#SBATCH --array=0-31
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/env.sh
LDENV=$(e18b_ldenv)
read ENV SEED <<< "$(e18b_task $SLURM_ARRAY_TASK_ID)"
N=$(e18b_run_name $ENV $SEED)
echo "task $SLURM_ARRAY_TASK_ID: $ENV seed $SEED -> $N on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
gpy $CODE/train.py --env $ENV --seed $SEED --out $RUNS/$N --model-path $MODELS_DIR/qwen3_1p7b
echo "TRAIN TASK OK"
