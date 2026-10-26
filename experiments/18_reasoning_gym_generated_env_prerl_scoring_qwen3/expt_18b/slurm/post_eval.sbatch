#!/bin/bash
# TLDR: 18b post-evaluation array: vLLM on run <i>'s checkpoint (same items/seeds as pre-eval) -> $RES/post/post_<run>.json, then deletes the checkpoint. Submitted with --dependency=aftercorr:<train array id>.
#SBATCH -J e18b_post
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 01:00:00
#SBATCH --array=0-31
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/env.sh
LDENV=$(e18b_ldenv)
read ENV SEED <<< "$(e18b_task $SLURM_ARRAY_TASK_ID)"
N=$(e18b_run_name $ENV $SEED)
gpy $CODE/eval.py --model $RUNS/$N/ckpt --out $RES/post/post_$N.json --envs $ENV --gsm8k-parquet $GSM8K --name $N
[ -s $RES/post/post_$N.json ] && rm -rf $RUNS/$N/ckpt   # keep train_log.jsonl and train_summary.json
echo "POST EVAL OK $N"
