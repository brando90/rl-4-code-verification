#!/bin/bash
# TLDR: 18b smoke on one H100: CPU tests in the image, then 2 full-size GRPO steps (32 prompts x 8, cap 1024) on a long-response and a short-response env, then a vLLM post-eval of the smoke checkpoint; prints the measured step time and the run-time estimate.
#SBATCH -J e18b_smoke
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MEM:80GB
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 01:00:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/env.sh
LDENV=$(e18b_ldenv)
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
cd $B/code && e18b_py -m pytest -q -p no:cacheprovider tests/test_e18b.py -x -q && cd $B
S=$RUNS/smoke; rm -rf $S; mkdir -p $S
for ENV in rg/basic_arithmetic/L2 rg/family_relationships/L1; do
  N=$(e18b_run_name $ENV 0)
  gpy $CODE/train.py --smoke --env $ENV --seed 0 --out $S/$N --model-path $MODELS_DIR/qwen3_1p7b --steps 2
  nvidia-smi --query-gpu=memory.used --format=csv,noheader
done
N=$(e18b_run_name rg/basic_arithmetic/L2 0)
gpy $CODE/eval.py --model $S/$N/ckpt --out $S/post_smoke.json --envs rg/basic_arithmetic/L2 --targets rg/syllogism,gsm8k/test256 --n 2 --limit-items 16 --gsm8k-parquet $GSM8K
e18b_py - <<'PY'
import json, glob, os
S = os.environ["RUNS"] + "/smoke"
for f in sorted(glob.glob(S + "/*/train_summary.json")):
    d = json.load(open(f)); sec = d["mean_step_seconds"]
    print(os.path.basename(os.path.dirname(f)), "mean step s", sec, "tokens", d["response_tokens"])
    print("  est. one 40-step run:", round((sec * 40 + 150) / 3600, 2), "h incl. ~150 s load/save; 32 runs:", round(32 * (sec * 40 + 150) / 3600, 1), "H100-h")
PY
echo "SMOKE OK"
