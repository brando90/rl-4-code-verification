#!/usr/bin/env bash
# TLDR: Shared claim-based generation queue for experiment 01 (master decision 09-30-2026 17:10,
# Trigger Rule 57; orchestration only). Every free single-GPU driver pulls the next unclaimed job
# from $WORK/shared_queue.txt, in file order (smallest-to-largest, as written). One writer per job:
# a claim is `mkdir $WORK/claims/<mode>_<label>`, atomic even across concurrent GPU drivers racing
# the same line. STAGE=gen only -- scoring stays on the separate score_worker.sh CPU queue.
# Usage: CUDA_VISIBLE_DEVICES=<n> bash queue_worker.sh <gpu-log>
set -uo pipefail
REPO=/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
CLAIMS="$WORK/claims"; QUEUE="$WORK/shared_queue.txt"
LOG="${1:-$WORK/queue_worker_$CUDA_VISIBLE_DEVICES.log}"
mkdir -p "$CLAIMS"

cd "$REPO"
source .venv/bin/activate
export PATH=/usr/local/cuda-12.8/bin:$PATH
export PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
export TASK_IDS=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/task_ids_vbv1.txt
export LAKE_DIR=$REPO/external/veribench_scorer/veribench_dataset/lean_src
export SCORER=$REPO/external/veribench_scorer
export OUT=$WORK/out
export STAGE=gen BATCH=256

log() { echo "$(date '+%m-%d-%Y %H:%M:%S') $*" >> "$LOG"; }
log "QUEUE WORKER START gpu=$CUDA_VISIBLE_DEVICES"

while true; do
  claimed=""
  while IFS=' ' read -r MODE MODEL REV LABEL TP; do
    [ -z "$MODE" ] && continue
    key="${MODE}_${LABEL}"
    if mkdir "$CLAIMS/$key" 2>/dev/null; then
      claimed="$MODE|$MODEL|$REV|$LABEL|${TP:-1}"
      break
    fi
  done < "$QUEUE"
  if [ -z "$claimed" ]; then
    log "QUEUE EMPTY on gpu=$CUDA_VISIBLE_DEVICES, exiting"
    break
  fi
  IFS='|' read -r MODE MODEL REV LABEL TP <<< "$claimed"
  log "CLAIMED $MODE $LABEL tp=$TP on gpu=$CUDA_VISIBLE_DEVICES"
  if bash experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh \
      "$MODE" "$MODEL" "$REV" "$LABEL" "$TP" >> "$LOG" 2>&1; then
    log "DONE $MODE $LABEL on gpu=$CUDA_VISIBLE_DEVICES"
  else
    log "FAILED $MODE $LABEL on gpu=$CUDA_VISIBLE_DEVICES -- claim stays (one writer per job; investigate before retrying)"
  fi
done
