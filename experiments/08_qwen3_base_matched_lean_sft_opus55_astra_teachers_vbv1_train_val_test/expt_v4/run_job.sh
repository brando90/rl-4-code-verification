#!/usr/bin/env bash
# TLDR: Run admitted Sherlock preparation or one full train-only SFT replication inside Slurm.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the experiment directory}"
MODE="${1:?prepare or train}"
module load python/3.14.2 py-pytorch/2.9.1_py314 py-transformers/4.57.3_py314
export HF_HOME="$PWD/cache/huggingface"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
mkdir -p logs
trap 'rc=$?; printf "{\"job_id\":\"%s\",\"exit_code\":%s,\"finished_utc\":\"%s\"}\n" "$SLURM_JOB_ID" "$rc" "$(date -u +%FT%TZ)" > "logs/exit_${SLURM_JOB_ID}.json"' EXIT
if [ "$MODE" = prepare ]; then
  export CUDA_VISIBLE_DEVICES=""
  python3 -u train_sherlock.py prepare
elif [ "$MODE" = train ]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Slurm must assign one GPU}"
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
  nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv
  python3 -u train_sherlock.py train --seed "${2:?seed}"
else
  exit 2
fi
