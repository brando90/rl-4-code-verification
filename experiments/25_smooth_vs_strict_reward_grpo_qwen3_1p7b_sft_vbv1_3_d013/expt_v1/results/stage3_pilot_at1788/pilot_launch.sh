#!/bin/bash
# AT-1788 stage 3: lr pilot, arms A/B x lr {1e-6,5e-6}, 12 updates, seed 0, 16 groups x 8, fp16, 12288 tokens, no checkpoints. Runs on skampere1 A100s 2,1,4,6 (vLLM util 0.35, shares with other users' jobs).
S=/lfs/skampere1/0/brando9; R=$S/rl4cv_e25; W=$S/rl4cv_e23_fp16_smoke; OUT=$S/at1788
export ROOT=$R VENV=$W/venv DATA=$S/at1787/data TRAINER=$R/code MODEL=$R/ckpt/step_658_float16
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader > $OUT/gpus_at_start.txt
date +%s > $OUT/pilot_start_epoch
i=0
for X in "2 A 1e-6" "1 B 1e-6" "4 A 5e-6" "6 B 5e-6"; do set -- $X
  ( bash $R/code/lane.sh $1 $2 0 $OUT/pilot_$2_lr$3 --updates 12 --lr $3 --dtype float16 --vllm-gpu-memory-utilization 0.35 --logit-chunk 1024 --no-save --vllm-max-num-seqs 128 > $OUT/pilot_$2_lr$3.log 2>&1 ) &
  sleep 20
done
wait
echo PILOT_DONE
