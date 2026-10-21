#!/bin/bash
# TLDR: experiment 18a v2 frozen analysis on CPU: envs_18a_v2.jsonl, targets_18a_v2.jsonl, summary_18a_v2.json in $RUN/results, then the results tarball.
#SBATCH -J e18v2_analyze
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 02:00:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/env.sh
V1=$HOME/e18a/run/results/envs_18a.jsonl   # v1's results, if analyzed already (same-family replication check)
$E18A_VENV/bin/python $CODE/analyze.py --run $RUN --out $RUN/results $( [ -f $V1 ] && echo --v1-envs $V1 )
tar czf $E18V2_HOME/e18v2_results.tgz -C $RUN results scored emb items/manifest.json $(cd $RUN && ls raw/*/timing.jsonl)
ls -la $E18V2_HOME/e18v2_results.tgz
echo "ANALYZE OK"
