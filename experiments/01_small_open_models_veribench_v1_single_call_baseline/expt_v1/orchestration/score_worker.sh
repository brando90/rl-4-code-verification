#!/usr/bin/env bash
# TLDR: Separate CPU scoring queue for experiment 01, decoupled from the GPU generation drivers
# (master decision 09-30-2026 16:00). Scans every declared (mode model rev label tp) line across
# jobs_gpu*.txt; for any whose generation is done (raw/gen_<name>.jsonl exists) but not yet scored
# (no summaries/summary_<name>.json) and not already in flight, launches STAGE=score run_model.sh
# (orchestration only; never loads a model). Caps concurrent score_scsc.py leaf processes at MAX_CONCURRENT
# because skampere1's load average is high from other users' jobs.
set -uo pipefail
REPO=/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
LOG=$WORK/score_worker.log
MAX_CONCURRENT=${MAX_CONCURRENT:-6}

cd "$REPO"
source .venv/bin/activate
export PATH=/usr/local/cuda-12.8/bin:$PATH
export PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
export TASK_IDS=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/task_ids_vbv1.txt
export LAKE_DIR=$REPO/external/veribench_scorer/veribench_dataset/lean_src
export SCORER=$REPO/external/veribench_scorer
export OUT=$WORK/out
export STAGE=score
export CUDA_VISIBLE_DEVICES=""   # scoring never touches a GPU

name_for() { if [ "$1" = eval ]; then echo "${2}_g1"; else echo "${2}_g8"; fi; }
running() { pgrep -cf "score_scsc.py --job-dir" 2>/dev/null || echo 0; }

log() { echo "$(date '+%m-%d-%Y %H:%M:%S') $*" >> "$LOG"; }
log "START max_concurrent=$MAX_CONCURRENT"

while true; do
  while IFS=' ' read -r MODE MODEL REV LABEL TP; do
    [ -z "${MODE:-}" ] && continue
    NAME=$(name_for "$MODE" "$LABEL")
    SUMMARY="$OUT/summaries/summary_${NAME}.json"
    LOCK="$OUT/.scoring_${NAME}"
    # jobs/<name>_s0 is only materialized by the gen stage AFTER its manifest check passes (every
    # declared cell present), so its existence is the real "generation fully done" signal -- the raw
    # gen_<name>.jsonl file exists (and is being appended to) long before that.
    [ -d "$OUT/jobs/${NAME}_s0" ] || continue
    [ -f "$SUMMARY" ] && continue
    [ -f "$LOCK" ] && continue
    while [ "$(running)" -ge "$MAX_CONCURRENT" ]; do sleep 15; done
    touch "$LOCK"
    log "LAUNCH $MODE $MODEL $LABEL tp=${TP:-1} (name=$NAME)"
    ( bash experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh \
        "$MODE" "$MODEL" "$REV" "$LABEL" "${TP:-1}" >> "$WORK/score_${NAME}.log" 2>&1
      RC=$?
      rm -f "$LOCK"
      log "FINISHED $NAME (exit $RC)" ) &
    sleep 2
  done < <(cat "$WORK"/jobs_gpu*.txt)
  sleep 30
done
