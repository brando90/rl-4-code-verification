#!/bin/bash
# TLDR: Sherlock fallback generation array (same tasks.tsv as FarmShare): vLLM 0.30.0 in the AT-476 image on one L40S or H100; resumable. Smoke: sbatch --array=0 gen.sbatch smoke
#SBATCH -J e18a_gen
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 12:00:00
#SBATCH --array=0-8%4
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/sherlock/env.sh
LDENV=$(e18a_ldenv)
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
gpy() { apptainer exec --nv -B /scratch --env "$APPENV$LDENV" $SIF python3 "$@"; }
if [ "${1:-}" = smoke ]; then
  SETS=rg/basic_arithmetic/L3,rg/leg_counting/L3,rg/simple_equations/L3,rg/coin_flip/L3,rg/letter_counting/L3,rg/word_sorting/L3,rg/family_relationships/L3,rg/mini_sudoku/L3,rg/gsm_symbolic,gsm8k/test256
  gpy $CODE/generate.py --run $RUN --model-tag qwen3_4b --model-path $MODELS_DIR/qwen3_4b --sets $SETS --limit-items 8 --n 4 --out-subdir smoke
  gpy $CODE/embed.py --run $RUN --model-tag qwen3_4b --model-path $MODELS_DIR/qwen3_4b --limit-items 8 --out-subdir smoke
  e18a_py $CODE/score.py --run $RUN --model-tag qwen3_4b --raw-subdir smoke
  e18a_py $CODE/analyze.py --run $RUN --subdir smoke --smoke-group-size 4
  echo "SMOKE OK"; exit 0
fi
read TAG SHARD NSHARDS <<< "$(e18a_task $SLURM_ARRAY_TASK_ID)"
gpy $CODE/generate.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --shard $SHARD --nshards $NSHARDS
echo "GEN TASK OK"
