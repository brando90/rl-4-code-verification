#!/bin/bash
# TLDR: 18c worker on ONE GPU: claims tasks of tasks.tsv by mkdir, trains (token-matched), post-evals, keeps small outputs, drops the checkpoint. Usage: GPU=5 bash worker.sh
set -uo pipefail
source $(dirname "$0")/env.sh
export CUDA_VISIBLE_DEVICES=${GPU:?set GPU}
NT=$(wc -l < $C18/skampere/tasks.tsv)
while [ ! -s $RES/eval_pre.json ]; do sleep 30; done   # the pre-evaluation comes first
for TID in $(seq 0 $((NT-1))); do
  if [ $SECONDS -gt 39600 ]; then echo "stop claiming: 11h used"; break; fi
  read ENV SEED <<< "$(c18_task $TID)"
  N=$(c18_run_name $ENV $SEED)
  [ -s $RES/post/post_$N.json ] && continue
  mkdir $B/claims/$N 2>/dev/null || continue
  echo "== task $TID $ENV seed $SEED -> $N on $(hostname) GPU $GPU t=$SECONDS"
  c18_gpu_free || { echo "FAILED $N (GPU busy)" | tee -a $B/failed_cells.txt; rmdir $B/claims/$N; continue; }
  if $PY $C18/train18c.py --env $ENV --seed $SEED --out $RUNS/$N --model-path $MODELS_DIR/qwen3_1p7b > $B/logs/train_$N.log 2>&1 \
     && cp $RUNS/$N/train_summary.json $RES/train/$N.train_summary.json && cp $RUNS/$N/train_log.jsonl $RES/train/$N.train_log.jsonl \
     && $PY $C18B/eval.py --model $RUNS/$N/ckpt --out $RES/post/post_$N.json --envs $ENV --gsm8k-parquet $GSM8K --name $N > $B/logs/eval_$N.log 2>&1; then
    [ -s $RES/post/post_$N.json ] && rm -rf $RUNS/$N/ckpt; echo "DONE $N t=$SECONDS"
  else
    echo "FAILED $N" | tee -a $B/failed_cells.txt
  fi
done
echo "WORKER END GPU $GPU"
