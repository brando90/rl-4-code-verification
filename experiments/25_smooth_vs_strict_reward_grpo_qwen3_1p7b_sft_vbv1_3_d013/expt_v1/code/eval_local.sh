#!/bin/bash
# TLDR: Local (no Slurm, no Sherlock) validation evaluation of one checkpoint: 135 D-013 validation tasks x 8 samples with the frozen v12 evaluation sampler (seed 91, T 0.6, top-p 0.95, top-k 20, 12,288 tokens, thinking on, stop <|im_end|>) through rl4cv.veribench.generate, then job dirs and strict scoring with the local scorer (eval_score_jobs.py). Replaces Exp 20's eval_gen.sbatch + eval_score.sbatch.
# usage: eval_local.sh <LABEL> <MODEL_DIR (config dtype decides vLLM dtype)> <OUT_DIR> <GPU> [GPU_UTIL=0.85] [SAMPLES=8]
# env: ROOT (e25 tree: code/ + grading/), VENV (python with vllm), PACK (validation pack), IDS (validation task ids), VERIBENCH_ROOT
set -uo pipefail
L=$1; M=$2; O=$3; GPU=$4; UTIL=${5:-0.85}; NS=${6:-8}
: "${ROOT:?}" "${VENV:?}" "${PACK:?}" "${IDS:?}" "${VERIBENCH_ROOT:?}"
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
mkdir -p "$O" "$O/cache"
export CUDA_VISIBLE_DEVICES=$GPU HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 VLLM_WORKER_MULTIPROC_METHOD=spawn
export PYTHONPATH=$ROOT/grading/rl4cv/src RL4CV_SRC=$ROOT/grading/rl4cv/src
export XDG_CACHE_HOME=$O/cache VLLM_CACHE_ROOT=$O/cache/vllm TRITON_CACHE_DIR=$O/cache/triton VLLM_USE_FLASHINFER_SAMPLER=0
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader -i "$GPU" | tee "$O/gpu.txt"
T0=$(date +%s)
if [ ! -s "$O/raw.jsonl" ] || [ "$(wc -l < "$O/raw.jsonl")" -lt $((135*NS)) ]; then
  $VENV/bin/python -m rl4cv.veribench.generate --pack "$PACK" --task-ids "$IDS" --model "$M" --label "e25_eval_$L" --samples "$NS" --thinking on --seed 91 \
    --stop-token '<|im_end|>' --max-tokens 12288 --max-model-len 20480 --temperature 0.6 --top-p 0.95 --top-k 20 --batch 128 --tensor-parallel-size 1 \
    --gpu-memory-utilization "$UTIL" --out "$O/raw.jsonl" > "$O/gen.log" 2>&1 || { echo "generation failed rc=$?"; exit 3; }
fi
T1=$(date +%s)
echo "{\"gen_wall_seconds\": $((T1-T0)), \"cells\": $(wc -l < "$O/raw.jsonl")}" > "$O/gen_timing.json"
rm -rf "$O/jobs"; $VENV/bin/python -m rl4cv.veribench.jobs --gen "$O/raw.jsonl" --out-root "$O/jobs" --name "eval_$L" | tail -1
$VENV/bin/python "$HERE/eval_score_jobs.py" --root "$ROOT" --jobs-root "$O/jobs" --name "eval_$L" --pack "$PACK" --out "$O" --samples "$NS" --workers 8
