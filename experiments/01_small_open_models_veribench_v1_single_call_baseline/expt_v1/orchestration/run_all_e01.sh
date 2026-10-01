#!/usr/bin/env bash
# TLDR: Run a sequential list of (mode model revision label [tp]) jobs for experiment 01 on one GPU.
# Usage: CUDA_VISIBLE_DEVICES=<n> bash run_all_e01.sh <jobs-file> <gpu-log>
# jobs-file: one job per line: "eval|probe <hf_id> <revision> <label> [tp]"
# Resumable: run_model.sh itself skips finished generation cells and job/score dirs are write-once,
# so rerunning this script (or a relaunched line) after a crash just continues.
set -uo pipefail
REPO=/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
JOBS_FILE="$1"; LOG="${2:-$WORK/run_all_e01_$CUDA_VISIBLE_DEVICES.log}"

cd "$REPO"
source .venv/bin/activate
export PATH=/usr/local/cuda-12.8/bin:$PATH
export PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
export TASK_IDS=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/task_ids_vbv1.txt
export LAKE_DIR=$REPO/external/veribench_scorer/veribench_dataset/lean_src
export SCORER=$REPO/external/veribench_scorer
export OUT=$WORK/out

while IFS=' ' read -r MODE MODEL REV LABEL TP; do
  [ -z "$MODE" ] && continue
  TP="${TP:-1}"
  echo "$(date '+%m-%d-%Y %H:%M:%S') START $MODE $MODEL $LABEL tp=$TP (gpu=$CUDA_VISIBLE_DEVICES)" >> "$LOG"
  if bash experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh "$MODE" "$MODEL" "$REV" "$LABEL" "$TP" >> "$LOG" 2>&1; then
    echo "$(date '+%m-%d-%Y %H:%M:%S') DONE $MODE $MODEL $LABEL" >> "$LOG"
  else
    echo "$(date '+%m-%d-%Y %H:%M:%S') FAILED $MODE $MODEL $LABEL (exit $?) -- continuing with remaining jobs" >> "$LOG"
  fi
done < "$JOBS_FILE"
echo "$(date '+%m-%d-%Y %H:%M:%S') ALL JOBS ON THIS GPU DONE" >> "$LOG"
