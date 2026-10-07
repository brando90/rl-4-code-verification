#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 4 ]]; then echo "usage: $0 SCALE GPU MODEL_PATH CHECKPOINT_ROOT [HYDRA_OVERRIDES...]" >&2; exit 2; fi
SCALE=$1 GPU=$2 PHASE1C_MODEL_PATH=$3 CHECKPOINT_ROOT=$4
shift 4
EXTRA_ARGS=("$@")
case "$SCALE" in
  1.7B) REQUIRED_FREE_BYTES=100000000000 ;;
  4B) REQUIRED_FREE_BYTES=250000000000 ;;
  8B) REQUIRED_FREE_BYTES=450000000000 ;;
  *) exit 2;;
esac
NEMO=/lfs/skampere3/0/vmadan/vendor/nemo_rl_v040_cuda128
DATA=/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1
WANDB_ENV=/lfs/skampere3/0/vmadan/rl-env-scaling-laws/ensure_wandb_env.sh
export PATH=/lfs/skampere3/0/vmadan/vendor/nemo_rl_pinned_ccbcd4cc/.uv-bootstrap/bin:"$PATH"
export PHASE1C_MODEL_PATH
export PHASE1C_RUN_NAME="paper1-phase1c-${SCALE}-sft-v1"
export PHASE1C_CHECKPOINT_DIR="$CHECKPOINT_ROOT/$PHASE1C_RUN_NAME/checkpoints"
export PHASE1C_LOG_DIR="$CHECKPOINT_ROOT/$PHASE1C_RUN_NAME/logs"
export PHASE1C_TENSORBOARD_DIR="$CHECKPOINT_ROOT/$PHASE1C_RUN_NAME/tb"
test -d "$PHASE1C_MODEL_PATH"
test -f "$DATA/matched_sft_train.jsonl"
mkdir -p "$CHECKPOINT_ROOT"
test "$(df --output=avail -B1 "$CHECKPOINT_ROOT" | tail -1)" -gt "$REQUIRED_FREE_BYTES"
test -f "$WANDB_ENV"
source "$WANDB_ENV" >/dev/null
test "${WANDB_MODE:-}" = online
test "${#WANDB_API_KEY}" -ge 20
"$NEMO/.venv/bin/python" - <<'PY'
import wandb
assert wandb.Api(timeout=10).viewer, "W&B authentication failed"
PY

case "$SCALE" in
  1.7B) EXPECTED_DIR=Qwen3-1.7B-Base-ea980cb0; EXPECTED_REV=ea980cb0a6c2ae4b936e82123acc929f1cec04c1 ;;
  4B) EXPECTED_DIR=Qwen3-4B-Base-906bfd4b; EXPECTED_REV=906bfd4b4dc7f14ee4320094d8b41684abff8539 ;;
  8B) EXPECTED_DIR=Qwen3-8B-Base-49e3418f; EXPECTED_REV=49e3418fbbbca6ecbdf9608b4d22e5a407081db4 ;;
esac
test "$(basename "$PHASE1C_MODEL_PATH")" = "$EXPECTED_DIR"
test "$(cat "$PHASE1C_MODEL_PATH/REVISION")" = "$EXPECTED_REV"
"$NEMO/.venv/bin/python" - "$PHASE1C_MODEL_PATH" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
cfg = json.loads((root / "config.json").read_text())
assert cfg.get("model_type") == "qwen3", cfg.get("model_type")
assert cfg.get("max_position_embeddings") == 32768, cfg.get("max_position_embeddings")
assert (root / "tokenizer_config.json").is_file()
assert list(root.glob("*.safetensors")), "missing model weights"
PY

RUN_ROOT="$CHECKPOINT_ROOT/$PHASE1C_RUN_NAME"
mkdir -p "$PHASE1C_CHECKPOINT_DIR" "$PHASE1C_LOG_DIR" "$PHASE1C_TENSORBOARD_DIR" "$RUN_ROOT/provenance"
cp "$DATA/phase1c_production_sft.yaml" "$DATA/phase1c_production_manifest.json" \
  "$DATA/matched_sft_recipe.json" "$RUN_ROOT/provenance/"
sha256sum "$DATA/matched_sft_train.jsonl" "$DATA/matched_sft_validation.jsonl" \
  "$DATA/phase1c_production_sft.yaml" "$DATA/phase1c_production_manifest.json" \
  > "$RUN_ROOT/provenance/sha256sums.txt"
if [[ "${PHASE1C_PREFLIGHT_ONLY:-0}" == 1 ]]; then
  echo "phase1c production preflight passed: $SCALE"
  exit 0
fi
cd "$NEMO"
CUDA_VISIBLE_DEVICES="$GPU" exec .venv/bin/python -u examples/run_sft.py \
  --config "$DATA/phase1c_production_sft.yaml" "${EXTRA_ARGS[@]}"
