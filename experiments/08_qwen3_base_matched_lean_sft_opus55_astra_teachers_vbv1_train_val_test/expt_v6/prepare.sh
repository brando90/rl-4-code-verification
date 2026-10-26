#!/usr/bin/env bash
# TLDR: Revalidate the executable-example curriculum and prepare both model sizes without allocating a GPU.
set -euo pipefail
export TINY_RUN_ROOT=/lfs/skampere1/0/eth127/rl4cv_tiny_training
export CUDA_VISIBLE_DEVICES=""
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
cd "$HERE"
"$PY" prepare_curriculum.py > "$TINY_RUN_ROOT/curriculum.log" 2>&1
TINY_TRAIN_ROOT="$TINY_RUN_ROOT/onep7" "$PY" experiment.py prepare --size 1.7B > "$TINY_RUN_ROOT/prepare_onep7.log" 2>&1 &
first=$!
TINY_TRAIN_ROOT="$TINY_RUN_ROOT/four" "$PY" experiment.py prepare --size 4B > "$TINY_RUN_ROOT/prepare_four.log" 2>&1 &
second=$!
status=0
wait "$first" || status=1
wait "$second" || status=1
printf '{"exit_code":%s}\n' "$status" > "$TINY_RUN_ROOT/preparation_exit.json"
exit "$status"
