#!/bin/bash
# TLDR: Sherlock fallback CPU steps inside the image: `build` (items + tests), `score` (all 3 models) or `analyze`; usage: sbatch cpu.sbatch <build|score|analyze>
#SBATCH -J e18v2_cpu
#SBATCH -p normal
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/sherlock/env.sh
case "$1" in
  build)   e18a_py $CODE/build.py --out $RUN --gsm8k-parquet $B/gsm8k_test.parquet
           cd $B/code && e18a_py -m pytest -q -p no:cacheprovider tests/test_e18a_v2_wide.py ;;
  score)   for t in qwen3_0p6b qwen3_1p7b; do e18a_py $CODE/score.py --run $RUN --model-tag $t; done ;;
  analyze) e18a_py $CODE/analyze.py --run $RUN --out $RUN/results
           tar czf $B/e18v2_results.tgz -C $RUN results scored emb items/manifest.json ;;
  *) echo "usage: cpu.sbatch <build|score|analyze>"; exit 2 ;;
esac
echo "CPU $1 OK"
