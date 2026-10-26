#!/bin/bash
# TLDR: 18b worker pool (replaces train array + post-eval array because gpu QOS allows 100 queued tasks/user): each worker claims tasks 0-31 via mkdir, trains then post-evals inline.
#SBATCH -J e18b_worker
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MEM:80GB
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 12:00:00
#SBATCH --array=0-5
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -uo pipefail
source $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/env.sh
LDENV=$(e18b_ldenv)
mkdir -p $B/claims $RES/post
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
for TID in $(seq 0 31); do
  if [ $SECONDS -gt 32400 ]; then echo "stop claiming: 9h used"; break; fi
  read ENV SEED <<< "$(e18b_task $TID)"
  N=$(e18b_run_name $ENV $SEED)
  [ -s $RES/post/post_$N.json ] && continue
  mkdir $B/claims/$N 2>/dev/null || continue
  echo "== task $TID $ENV seed $SEED -> $N on $(hostname) t=$SECONDS"
  if gpy $CODE/train.py --env $ENV --seed $SEED --out $RUNS/$N --model-path $MODELS_DIR/qwen3_1p7b && gpy $CODE/eval.py --model $RUNS/$N/ckpt --out $RES/post/post_$N.json --envs $ENV --gsm8k-parquet $GSM8K --name $N; then
    [ -s $RES/post/post_$N.json ] && rm -rf $RUNS/$N/ckpt; echo "DONE $N t=$SECONDS"
  else
    echo "FAILED $N" | tee -a $B/failed_cells.txt
  fi
done
echo WORKER END
