#!/usr/bin/env bash
# TLDR: Train one locked continuation with fresh AdamW state, resumable segments and hashed exports.
set -euo pipefail
CONDITION="${1:?R or E}"; SHORT="${2:?1p7b,4b,8b,14b}"; GPUS="${3:?device IDs}"; MODE="${4:-production}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK=/lfs/skampere1/0/brando9/rl4cv_e08
case "$CONDITION" in R|E) ;; *) exit 2;; esac
case "$SHORT" in 1p7b) SIZE=1.7B;; 4b) SIZE=4B;; 8b) SIZE=8B;; 14b) SIZE=14B;; *) exit 2;; esac
export CUDA_VISIBLE_DEVICES="$GPUS"
export HF_HOME="$WORK/cache/huggingface" HF_HUB_OFFLINE=1 UV_CACHE_DIR="$WORK/cache/uv" UV_PYTHON_INSTALL_DIR="$WORK/cache/uv_python"
export E08_MODEL_PATH="$WORK/ckpt/$SIZE/hf/step_658"
ROOT="$WORK/sft_v3/ckpt/v3_${CONDITION}_${SHORT}"
export E08_TRAIN_JSONL="$WORK/sft_v3/s_v3_${CONDITION}_nemo.jsonl" E08_VAL_JSONL="$WORK/sft_v3/s_v3_${CONDITION}_val_dummy.jsonl"
EXTRA=()
if [ "$MODE" = dry ]; then
  [ "$CONDITION:$SHORT" = E:1p7b ] || exit 2
  ROOT="$WORK/sft_v3/dry_run"
  mkdir -p "$ROOT"
  head -16 "$E08_TRAIN_JSONL" > "$ROOT/train16.jsonl"
  export E08_TRAIN_JSONL="$ROOT/train16.jsonl" E08_VAL_JSONL="$ROOT/train16.jsonl"
  STEPS=8
  EXTRA=(sft.val_period=8 sft.val_batches=8 sft.val_global_batch_size=2 sft.val_at_start=true)
elif [ "$MODE" = production ]; then
  test -f "$HERE/results/dry_run_v3.json"
  python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["status"] == "PASS"' "$HERE/results/dry_run_v3.json"
  STEPS="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(" ".join(str(d["checkpoints"][k]["step"]) for k in ("f0p5","f1p0")))' "$HERE/results/sft_schedule_v3_${CONDITION}.json")"
else exit 2; fi
grep -q '^\*\*Status:\*\* LOCKED' "$HERE/PROTOCOL.md"
export E08_CHECKPOINT_DIR="$ROOT/checkpoints" E08_LOG_DIR="$ROOT/logs" E08_TENSORBOARD_DIR="$ROOT/tb" E08_RUN_NAME="rl4cv-e08-v3-${CONDITION}-${SHORT}-${MODE}"
# Keep dashboard UNIX sockets below Linux's 107-byte pathname limit.
export RAY_TMPDIR="/tmp/e8v3_$(id -u)/${CONDITION}_${SHORT}_${MODE:0:1}"
mkdir -p "$RAY_TMPDIR" "$ROOT/driver_logs" "$ROOT/hf"
unset PYTHONPATH
cd "$WORK/nemo_rl"
for K in $STEPS; do
  if [ ! -f "$ROOT/hf/step_$K/SHA256SUMS" ]; then
    if [ ! -d "$E08_CHECKPOINT_DIR/step_$K" ]; then
      uv run examples/run_sft.py --config "$HERE/configs/e08_v3_${CONDITION}_${SIZE}.yaml" sft.max_num_steps="$K" "${EXTRA[@]}" > "$ROOT/driver_logs/segment_to_step_$K.log" 2>&1
      test -d "$E08_CHECKPOINT_DIR/step_$K"
    fi
    export CUDA_VISIBLE_DEVICES=""
    uv run examples/converters/convert_dcp_to_hf.py --config "$E08_CHECKPOINT_DIR/step_$K/config.yaml" \
      --dcp-ckpt-path "$E08_CHECKPOINT_DIR/step_$K/policy/weights" --hf-ckpt-path "$ROOT/hf/step_$K" > "$ROOT/driver_logs/export_step_$K.log" 2>&1
    for F in tokenizer.json tokenizer_config.json vocab.json merges.txt generation_config.json; do
      if [ ! -f "$ROOT/hf/step_$K/$F" ] && [ -f "$E08_MODEL_PATH/$F" ]; then cp "$E08_MODEL_PATH/$F" "$ROOT/hf/step_$K/$F"; fi
    done
    (cd "$ROOT/hf/step_$K" && find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' | sort | xargs sha256sum > SHA256SUMS)
    export CUDA_VISIBLE_DEVICES="$GPUS"
  fi
  echo "$(date -u +%FT%TZ) exported $CONDITION $SIZE step $K"
done
