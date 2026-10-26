#!/usr/bin/env bash
# TLDR: Validate eight expansion updates, exported inference and fixed-set loss before production.
set -euo pipefail
GPU="${1:?device}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
WORK=/lfs/skampere1/0/brando9/rl4cv_e08
D="$WORK/sft_v3/dry_run"
export CUDA_VISIBLE_DEVICES="$GPU"
bash "$HERE/train_continuation.sh" E 1p7b "$GPU" dry
export CUDA_VISIBLE_DEVICES="$GPU"
export PYTHONPATH="$REPO/src" HF_HOME="$WORK/cache/huggingface" HF_HUB_OFFLINE=1
export VERIBENCH_ROOT="$REPO/external/veribench" PATH="/usr/local/cuda-12.8/bin:$PATH"
export CUDA_HOME=/usr/local/cuda-12.8 CUDA_PATH=/usr/local/cuda-12.8
export FLASHINFER_WORKSPACE_BASE="$WORK/sft_v3/flashinfer"
PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
"$WORK/venv_gen/bin/python" -m rl4cv.veribench.generate --pack "$PACK" --model "$D/hf/step_8" \
  --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 \
  --batch 1024 --samples 1 --task-ids "$WORK/preflight_ids.txt" --label v3_dry_step8 --out "$D/gen_preflight.jsonl" > "$D/vllm.log" 2>&1
export CUDA_VISIBLE_DEVICES=""
"$WORK/nemo_rl/.venv/bin/python" "$HERE/verify_training.py" E 1p7b --dry > "$D/verification.log" 2>&1
cp "$D/hf/step_8/SHA256SUMS" "$HERE/results/dry_export_SHA256SUMS"
# This exact subtree contains disposable weights only; logs, receipts and generations remain.
rm -rf "$D/checkpoints" "$D/hf"
echo "$(date -u +%FT%TZ) dry run passed; disposable weights removed"
