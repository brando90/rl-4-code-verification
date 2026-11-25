#!/bin/bash
# TLDR: 18c pre-evaluation of the base Qwen3-1.7B on this stack (same items, n=8, as 18b's eval_pre.json). Usage: GPU=5 bash pre_eval.sh
set -uo pipefail
source $(dirname "$0")/env.sh
export CUDA_VISIBLE_DEVICES=${GPU:?set GPU}
c18_gpu_free || { echo "GPU $GPU busy"; exit 3; }
[ -s $RES/eval_pre.json ] && { echo "pre exists"; exit 0; }
$PY $C18B/eval.py --model $MODELS_DIR/qwen3_1p7b --out $RES/eval_pre.json --envs all --gsm8k-parquet $GSM8K --name pre && echo "PRE EVAL OK"
