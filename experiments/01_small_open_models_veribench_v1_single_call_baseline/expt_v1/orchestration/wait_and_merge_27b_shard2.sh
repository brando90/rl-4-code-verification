#!/usr/bin/env bash
# TLDR: Parallelize the 27B route control's last batch across idle GPUs 4+5 (master decision
# 09-30-2026 21:52, Trigger Rule 57; orchestration only). The main job (GPUs 2+7) runs batches
# [129-384] then [385-640]; a second tp=2 generate on GPUs 4+5 covers the LAST 256 task ids
# (shard2) in parallel. This watcher waits for the main file to reach 640 rows (finishing its
# own batch 385-640, about to start the now-redundant last batch), kills the main job (by
# GPU-UUID compute-app list, the same fix wait_and_rebatch.sh uses, so EngineCore/Worker children
# don't orphan GPU memory), waits for shard2 to finish its 256 rows, merges shard2 into the main
# file (only once the main writer is confirmed dead), then reruns run_model.sh eval for the 27B
# with STAGE=gen so the manifest check passes and jobs get materialized for score_worker.sh.
set -uo pipefail
WORK=/lfs/skampere1/0/brando9/rl4cv_e01
REPO=$WORK/rl-4-code-verification
MAIN=$WORK/out/raw/gen_qwen3.6-27b-local_g1.jsonl
SHARD2=$WORK/out/raw/gen_qwen3.6-27b-local_g1.shard2.jsonl
LOG=$WORK/run_all_e01_gpu7.log
MAIN_GPUS="2 7"

log() { echo "$(date '+%m-%d-%Y %H:%M:%S') $*" >> "$LOG"; }

log "27B SHARD2 WATCHER START (waiting for main to reach 640 rows)"
while true; do
  n=$(wc -l < "$MAIN" 2>/dev/null); n=${n:-0}
  [ "$n" -ge 640 ] && break
  sleep 30
done
log "main reached $n rows; killing main 27B job on GPUs $MAIN_GPUS before it starts the now-redundant last batch"

# Kill the main generate wrapper (matched by CUDA_VISIBLE_DEVICES in /proc/<pid>/environ).
for p in $(pgrep -f "rl4cv.veribench.generate"); do
  envs=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null)
  if echo "$envs" | grep -qx "CUDA_VISIBLE_DEVICES=2,7"; then
    kill "$p" 2>/dev/null
    log "killed main generate wrapper pid $p"
  fi
done
# Kill every compute-app process actually bound to GPU 2 or 7 (catches orphaned EngineCore/Worker).
for g in $MAIN_GPUS; do
  uuid=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v i="$g" '$1==i {print $2}')
  [ -z "$uuid" ] && continue
  nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader | awk -F', ' -v u="$uuid" '$1==u {print $2}' | while read -r cp; do
    [ -n "$cp" ] && kill -9 "$cp" 2>/dev/null && log "killed orphaned compute-app pid $cp on GPU $g"
  done
done
for g in $MAIN_GPUS; do
  for _ in $(seq 1 30); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g" 2>/dev/null || echo 999999)
    [ "$used" -lt 500 ] && break
    sleep 5
  done
  log "GPU $g memory after cleanup: ${used:-unknown} MiB"
done

log "waiting for shard2 ($SHARD2) to reach 256 rows"
while true; do
  n2=$(wc -l < "$SHARD2" 2>/dev/null); n2=${n2:-0}
  [ "$n2" -ge 256 ] && break
  sleep 30
done
log "shard2 reached $n2 rows; main writer confirmed dead, merging"
cat "$SHARD2" >> "$MAIN"
mn=$(wc -l < "$MAIN")
log "merged shard2 into main; main now has $mn rows (want 896)"

cd "$REPO"
source .venv/bin/activate
export PATH=/usr/local/cuda-12.8/bin:$PATH
export PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
export TASK_IDS=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/task_ids_vbv1.txt
export LAKE_DIR=$REPO/external/veribench_scorer/veribench_dataset/lean_src
export SCORER=$REPO/external/veribench_scorer
export OUT=$WORK/out
export STAGE=gen BATCH=256
# generate.py unconditionally constructs the vLLM engine even with 0 cells left to run (it only
# skips already-done PROMPTS, not engine construction), and tp=1 OOMs on this model's KV cache
# sizing (the same wall that forced tp=2 originally) -- so this verification call still needs a
# real tp=2 GPU pair, even though it will generate nothing. Reuse 2,7 (now free: main was killed).
export CUDA_VISIBLE_DEVICES=2,7
log "rerunning run_model.sh eval for qwen3.6-27b-local (STAGE=gen, tp=2 on 2,7, 0 cells to generate) to pass the manifest check and materialize jobs"
bash experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh \
  eval Qwen/Qwen3.6-27B 6a9e13bd6fc8f0983b9b99948120bc37f49c13e9 qwen3.6-27b-local 2 >> "$LOG" 2>&1
log "27B SHARD2 WATCHER DONE (manifest check + job materialization complete; ready for score_worker.sh)"
