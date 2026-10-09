#!/usr/bin/env bash
# TLDR: Run experiment 08's matched NeMo RL SFT for one Qwen3 Base size as a chain of segments that each stop at the next precomputed
# token-fraction checkpoint step (results/sft_schedule.json) and resume from the previous one (weights, optimizer, scheduler and dataloader
# state), then export every checkpoint to Hugging Face format with a SHA-256 manifest. Resumable: finished segments and exports are skipped.
# Usage: bash launch_sft_e08.sh <size: 1.7B|4B|8B|14B> <gpu_ids_csv> [max_steps_override]
#   max_steps_override (dry run only): run a single segment of that many steps into $E08_CKPT_ROOT_OVERRIDE instead of the schedule.
# Env: E08_WORK (default /lfs/skampere1/0/brando9/rl4cv_e08); E08_CKPT_ROOT_OVERRIDE, E08_TRAIN_JSONL_OVERRIDE (dry run).
set -uo pipefail
SIZE="${1:?size}"; GPUS="${2:?gpu ids}"; OVERRIDE_STEPS="${3:-}"
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
REPO="$WORK/rl-4-code-verification"
EXP="$REPO/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
NEMO="$WORK/nemo_rl"
case "$SIZE" in
  1.7B) SNAP=models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1 ;;
  4B)   SNAP=models--Qwen--Qwen3-4B-Base/snapshots/906bfd4b4dc7f14ee4320094d8b41684abff8539 ;;
  8B)   SNAP=models--Qwen--Qwen3-8B-Base/snapshots/49e3418fbbbca6ecbdf9608b4d22e5a407081db4 ;;
  14B)  SNAP=models--Qwen--Qwen3-14B-Base/snapshots/0b0bd3732e2c374d483664439ea334928b65f304 ;;
  *) echo "unknown size $SIZE" >&2; exit 2 ;;
esac
export CUDA_VISIBLE_DEVICES="$GPUS"
export HF_HOME="$WORK/cache/huggingface" HF_HUB_OFFLINE=1 UV_CACHE_DIR="$WORK/cache/uv" UV_PYTHON_INSTALL_DIR="$WORK/cache/uv_python"
export RAY_TMPDIR="/tmp/user/$(id -u)/e08ray_${SIZE//./p}"; mkdir -p "$RAY_TMPDIR"
export E08_MODEL_PATH="$WORK/cache/huggingface/hub/$SNAP"
ROOT="${E08_CKPT_ROOT_OVERRIDE:-$WORK/ckpt/$SIZE}"
export E08_CHECKPOINT_DIR="$ROOT/checkpoints" E08_LOG_DIR="$ROOT/logs" E08_TENSORBOARD_DIR="$ROOT/tb" E08_RUN_NAME="rl4cv-e08-sft-$SIZE"
export E08_TRAIN_JSONL="${E08_TRAIN_JSONL_OVERRIDE:-$WORK/sft/s_v1_nemo.jsonl}" E08_VAL_JSONL="$WORK/sft/s_v1_val_dummy.jsonl"
unset PYTHONPATH
mkdir -p "$E08_CHECKPOINT_DIR" "$E08_LOG_DIR" "$E08_TENSORBOARD_DIR" "$ROOT/hf" "$ROOT/driver_logs"
CONFIG="$EXP/expt_v1/configs/e08_sft_${SIZE}.yaml"
if [ "$SIZE" = 14B ]; then
  IFS=',' read -ra VISIBLE <<< "$GPUS"
  LAYOUT_ARGS=()
  [ -z "${E08_SFT_LAYOUT_ID:-}" ] || LAYOUT_ARGS=(--layout-id "$E08_SFT_LAYOUT_ID")
  CONFIG="$("$REPO/.venv/bin/python" "$EXP/expt_v1/scripts/sft_layout_e08.py" --gpus "${#VISIBLE[@]}" --root "$ROOT" "${LAYOUT_ARGS[@]}")" || exit 2
fi
ts() { date -u +%FT%TZ; }
test -d "$E08_MODEL_PATH" || { echo "model snapshot missing: $E08_MODEL_PATH" >&2; exit 2; }
test -f "$E08_TRAIN_JSONL" || { echo "train jsonl missing: $E08_TRAIN_JSONL" >&2; exit 2; }
test -f "$CONFIG" || { echo "config missing: $CONFIG" >&2; exit 2; }
if [ -n "$OVERRIDE_STEPS" ]; then STEPS="$OVERRIDE_STEPS"; else
  STEPS="$(python3 -c "import json;print(' '.join(str(s) for s in json.load(open('$EXP/expt_v1/results/sft_schedule.json'))['distinct_checkpoint_steps']))")"
fi
echo "[$(ts)] $SIZE on GPUs $GPUS: segments ending at steps: $STEPS; checkpoints -> $E08_CHECKPOINT_DIR"
cd "$NEMO"
for K in $STEPS; do
  if [ -d "$E08_CHECKPOINT_DIR/step_$K" ]; then echo "[$(ts)] step_$K exists; skipping segment"; continue; fi
  echo "[$(ts)] segment -> step $K"
  uv run examples/run_sft.py --config "$CONFIG" sft.max_num_steps="$K" > "$ROOT/driver_logs/segment_to_step_${K}.log" 2>&1
  RC=$?
  echo "[$(ts)] segment -> step $K exit=$RC"
  if [ "$RC" != 0 ] || [ ! -d "$E08_CHECKPOINT_DIR/step_$K" ]; then echo "[$(ts)] segment to step $K failed (rc=$RC); stopping" >&2; exit 1; fi
done
# Export every checkpoint to Hugging Face format (one GPU-free process each) and write the hash manifest.
for K in $STEPS; do
  OUT="$ROOT/hf/step_$K"
  if [ -f "$OUT/config.json" ] && [ -f "$OUT/SHA256SUMS" ]; then echo "[$(ts)] hf export step_$K exists; skipping"; continue; fi
  echo "[$(ts)] exporting step_$K -> $OUT"
  CUDA_VISIBLE_DEVICES="" uv run examples/converters/convert_dcp_to_hf.py --config "$E08_CHECKPOINT_DIR/step_$K/config.yaml" \
    --dcp-ckpt-path "$E08_CHECKPOINT_DIR/step_$K/policy/weights" --hf-ckpt-path "$OUT" > "$ROOT/driver_logs/export_step_${K}.log" 2>&1 || { echo "export failed for step_$K" >&2; exit 1; }
  # Tokenizer files: the converter copies the tokenizer from the model path; make sure the pinned ones are present.
  for f in tokenizer.json tokenizer_config.json vocab.json merges.txt generation_config.json; do [ -f "$OUT/$f" ] || cp "$E08_MODEL_PATH/$f" "$OUT/$f" 2>/dev/null || true; done
  (cd "$OUT" && sha256sum $(ls | grep -v SHA256SUMS) > SHA256SUMS)
done
echo "[$(ts)] $SIZE done"
