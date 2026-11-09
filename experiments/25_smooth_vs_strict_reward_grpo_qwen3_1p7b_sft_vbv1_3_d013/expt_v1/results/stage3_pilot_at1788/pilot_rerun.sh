#!/bin/bash
# AT-1788 stage 3 rerun (Nov 9): the two lanes that died from another user's OOM on Oct 29. Same flags as pilot_launch.sh, on free GPUs 2 (A 1e-6) and 4 (B 5e-6). Cap: ~28 A100-h total pilot (hive Nov 8).
S=/lfs/skampere1/0/brando9; R=$S/rl4cv_e25; W=$S/rl4cv_e23_fp16_smoke; OUT=$S/at1788
export ROOT=$R VENV=$W/venv DATA=$S/at1787/data TRAINER=$R/code MODEL=$R/ckpt/step_658_float16
date +%s > $OUT/pilot_rerun_start_epoch
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader > $OUT/gpus_at_rerun_start.txt
for X in "2 A 1e-6" "4 B 5e-6"; do set -- $X
  ( bash $R/code/lane.sh $1 $2 0 $OUT/pilot_$2_lr$3 --updates 12 --lr $3 --dtype float16 --vllm-gpu-memory-utilization 0.35 --logit-chunk 1024 --no-save --vllm-max-num-seqs 128 > $OUT/pilot_$2_lr$3.log 2>&1 ) &
  sleep 20
done
wait
echo PILOT_RERUN_DONE
