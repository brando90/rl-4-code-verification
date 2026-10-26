#!/bin/bash
# TLDR: experiment 18a frozen analysis on CPU: envs_18a.jsonl, targets_18a.jsonl, summary_18a.json in $RUN/results.
#SBATCH -J e18a_analyze
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/env.sh
cd $E18A_HOME/code
$E18A_VENV/bin/python $CODE/analyze.py --run $RUN --out $RUN/results
tar czf $E18A_HOME/e18a_results.tgz -C $RUN results scored emb items/manifest.json $(cd $RUN && ls raw/*/timing.jsonl)
ls -la $E18A_HOME/e18a_results.tgz
echo "ANALYZE OK"
