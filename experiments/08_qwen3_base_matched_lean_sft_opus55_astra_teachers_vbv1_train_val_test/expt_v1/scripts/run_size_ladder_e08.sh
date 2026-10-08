#!/usr/bin/env bash
# TLDR: Run the validation ladder (PROTOCOL § 9) for one trained size: for each of its 5 exported token-fraction checkpoints (in step order), refresh the
# frozen ladder manifest's weights hash, then generate + kernel-score the 135 × 8 validation cells with `run_ladder_e08.sh` on the given GPUs; also
# extracts the size's training logs to the committed CSV first. Usage: bash run_size_ladder_e08.sh <size> <gpu_ids_csv> [tp]
set -uo pipefail
SIZE="${1:?size}"; GPUS="${2:?gpus}"; TP="${3:-1}"
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
REPO="$WORK/rl-4-code-verification"; EXP="$REPO/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
S="$EXP/expt_v1/scripts"; PY="$REPO/.venv/bin/python"
ts() { date -u +%FT%TZ; }
STEPS="$(python3 -c "import json;print(' '.join(str(s) for s in json.load(open('$EXP/expt_v1/results/sft_schedule.json'))['distinct_checkpoint_steps']))")"
SZ="${SIZE//./p}"
mkdir -p "$EXP/expt_v1/results/train_logs"
( cd "$WORK/nemo_rl" && UV_CACHE_DIR="$WORK/cache/uv" env -u PYTHONPATH uv run python "$S/extract_train_logs_e08.py" --tb-dir "$WORK/ckpt/$SIZE/logs" --size "$SIZE" \
    --out-csv "$EXP/expt_v1/results/train_logs/sft_${SZ}_steps.csv" --out-json "$EXP/expt_v1/results/train_logs/sft_${SZ}_summary.json" ) 2>&1 | grep -v arn | tail -1
for K in $STEPS; do
  HF="$WORK/ckpt/$SIZE/hf/step_$K"
  [ -f "$HF/SHA256SUMS" ] || { echo "[$(ts)] $SIZE step_$K not exported yet ($HF); stopping" >&2; exit 1; }
  "$PY" "$S/make_ladder_manifest_e08.py" > /dev/null || exit 1
  FRAC="$(python3 -c "
import json; d=json.load(open('$EXP/expt_v1/results/sft_schedule.json'))['checkpoints']
print(sorted({f for f,v in d.items() if v['step']==$K}, key=float)[0].replace('.','p'))")"
  LABEL="sft_${SZ}_f${FRAC}"
  echo "[$(ts)] ladder $LABEL (step $K) on GPUs $GPUS tp=$TP"
  bash "$S/run_ladder_e08.sh" validation "$LABEL" "$HF" local "$GPUS" "$TP" > "$WORK/ladder/driver_${LABEL}_validation.log" 2>&1
  RC=$?; echo "[$(ts)] ladder $LABEL exit=$RC"; [ "$RC" = 0 ] || exit 1
done
echo "[$(ts)] $SIZE ladder done"
