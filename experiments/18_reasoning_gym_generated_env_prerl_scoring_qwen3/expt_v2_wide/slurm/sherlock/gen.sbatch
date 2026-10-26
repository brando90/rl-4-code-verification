#!/bin/bash
# TLDR: Sherlock fallback generation array (same tasks.tsv as FarmShare): vLLM 0.30.0 in the AT-476 image on one L40S or H100; resumable. Smoke: sbatch --array=0 gen.sbatch smoke
#SBATCH -J e18v2_gen
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 12:00:00
#SBATCH --array=0-9%4
#SBATCH -o logs/%x_%A_%a.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/sherlock/env.sh
LDENV=$(e18a_ldenv)
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
gpy() { apptainer exec --nv -B /scratch --env "$APPENV$LDENV" $SIF python3 "$@"; }
if [ "${1:-}" = smoke ]; then
  SETS=$(e18a_py -c "
import json; f = json.load(open('$CODE/families_v2.json'))['families']
pick = [f[round(i * (len(f) - 1) / 11)] for i in range(12)]
print(','.join([f'rg/{x[\"family\"]}/L{max(x[\"levels\"])}' for x in pick] + ['rg/gsm_symbolic', 'gsm8k/test256']))")
  gpy $CODE/generate.py --run $RUN --model-tag qwen3_1p7b --model-path $MODELS_DIR/qwen3_1p7b --sets $SETS --limit-items 8 --n 4 --out-subdir smoke
  gpy $CODE/embed.py --run $RUN --model-tag qwen3_1p7b --model-path $MODELS_DIR/qwen3_1p7b --limit-items 8 --out-subdir smoke
  e18a_py $CODE/score.py --run $RUN --model-tag qwen3_1p7b --raw-subdir smoke --sets $SETS
  e18a_py $CODE/analyze.py --run $RUN --subdir smoke --smoke-group-size 4
  echo "SMOKE OK"; exit 0
fi
read TAG SHARD NSHARDS <<< "$(e18v2_task $SLURM_ARRAY_TASK_ID)"
gpy $CODE/generate.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --shard $SHARD --nshards $NSHARDS
echo "GEN TASK OK"
