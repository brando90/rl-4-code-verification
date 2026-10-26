#!/bin/bash
# TLDR: 18b pre-evaluation of the base Qwen3-1.7B (vLLM, image): 6 target components x 256 items x 8 samples + the 64-item probe subset of each of the 16 envs -> $RES/eval_pre.json. Resumable (skips if the file exists).
#SBATCH -J e18b_pre
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 03:00:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/env.sh
LDENV=$(e18b_ldenv)
gpy $CODE/eval.py --model $MODELS_DIR/qwen3_1p7b --out $RES/eval_pre.json --envs all --gsm8k-parquet $GSM8K --name pre
echo "PRE EVAL OK"
