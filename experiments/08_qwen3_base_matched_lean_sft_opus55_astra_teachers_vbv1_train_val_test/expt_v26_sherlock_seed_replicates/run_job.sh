#!/usr/bin/env bash
# TLDR: Run V26 preparation (both models, token gate) or one training run inside Slurm; expt_v4's run_job.sh with arms.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the experiment directory}"
MODE="${1:?prepare or train}"
module load python/3.14.2 py-pytorch/2.9.1_py314 py-transformers/4.57.3_py314
export HF_HOME="$PWD/cache/huggingface"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
mkdir -p logs
trap 'rc=$?; printf "{\"job_id\":\"%s\",\"mode\":\"%s\",\"args\":\"%s\",\"exit_code\":%s,\"finished_utc\":\"%s\"}\n" "$SLURM_JOB_ID" "$MODE" "${*:2}" "$rc" "$(date -u +%FT%TZ)" > "logs/exit_${SLURM_JOB_ID}.json"' EXIT
if [ "$MODE" = prepare ]; then
  export CUDA_VISIBLE_DEVICES=""
  python3 -u train_v26.py prepare
elif [ "$MODE" = train ]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Slurm must assign one GPU}"
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
  nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv
  free -g | head -2
  python3 -u train_v26.py train --arm "${2:?arm}" --seed "${3:?seed}"
else
  exit 2
fi
