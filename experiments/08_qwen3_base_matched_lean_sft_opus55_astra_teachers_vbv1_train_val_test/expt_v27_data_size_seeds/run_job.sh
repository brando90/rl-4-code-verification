#!/usr/bin/env bash
# TLDR: Run V27 preparation (model, token gate, ladder subsets) or one training run (runs.tsv row = array task id) in Slurm.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the experiment directory}"
MODE="${1:?prepare or train}"
module load python/3.14.2 py-pytorch/2.9.1_py314 py-transformers/4.57.3_py314
export HF_HOME="$PWD/cache/huggingface"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
mkdir -p logs
trap 'rc=$?; printf "{\"job_id\":\"%s\",\"array_task\":\"%s\",\"mode\":\"%s\",\"exit_code\":%s,\"finished_utc\":\"%s\"}\n" "$SLURM_JOB_ID" "${SLURM_ARRAY_TASK_ID:-}" "$MODE" "$rc" "$(date -u +%FT%TZ)" > "logs/exit_${SLURM_JOB_ID}.json"' EXIT
if [ "$MODE" = prepare ]; then
  export CUDA_VISIBLE_DEVICES=""
  python3 -u train_v27.py prepare
elif [ "$MODE" = train ]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Slurm must assign one GPU}"
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
  nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv
  free -g | head -2
  python3 -u train_v27.py train --index "${SLURM_ARRAY_TASK_ID:?train runs as an array task}"
else
  exit 2
fi
