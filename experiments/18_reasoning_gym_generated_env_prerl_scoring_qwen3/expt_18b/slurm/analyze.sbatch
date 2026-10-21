#!/bin/bash
# TLDR: 18b analysis (CPU, image): forecasts vs realised held-out gain -> $RES/results_18b.json and results_18b_table.md; packs everything small into $B/e18b_results.tgz. afterany so partial results are analysed too.
#SBATCH -J e18b_analyze
#SBATCH -p normal
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 00:30:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $SCRATCH/e18b/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/slurm/env.sh
e18b_py $CODE/analyze.py --root $RES --out $RES/results_18b.json --md $RES/results_18b_table.md
mkdir -p $RES/train_logs
for d in $RUNS/*__s[01]; do n=$(basename $d); for f in train_log.jsonl train_summary.json; do [ -f $d/$f ] && cp $d/$f $RES/train_logs/$n.$f || true; done; done
tar czf $B/e18b_results.tgz -C $RES eval_pre.json post results_18b.json results_18b_table.md train_logs
echo "ANALYZE OK"
