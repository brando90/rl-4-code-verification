#!/bin/bash
# AT-1788 stage 4 relaunch 2 (Nov 9 10:50): same as full_run.sh, B s0 on GPU 3 (GPUs 5 and 7 taken by another user); every lane resumes from state_latest.
# Each lane retries up to 8 times and resumes from state_latest (saved every 8 updates and at 16/32/48) if the trainer dies (e.g. another user's out-of-memory); a gate ABORT or RUN_DONE ends the lane.
# Checkpoints are linked to /dfs/scratch1/brando9/at1788_ckpt because /lfs/skampere1/0 has only about 12 GB free. Usage: bash full_run.sh  (env LANES="gpu arm seed ..." to override)
S=/lfs/skampere1/0/brando9; R=$S/rl4cv_e25; W=$S/rl4cv_e23_fp16_smoke; OUT=$S/at1788/full; CK=/dfs/scratch1/brando9/at1788_ckpt
export ROOT=$R VENV=$W/venv DATA=$S/at1787/data TRAINER=$R/code MODEL=$R/ckpt/step_658_float16
mkdir -p $OUT
lane() {  # gpu arm seed
  G=$1; A=$2; SD=$3; RUN=$OUT/${A}_s${SD}_lr5e-6; D=$RUN/${A}_s${SD}; C=$CK/${A}_s${SD}
  mkdir -p $D $C/state_latest
  [ -e $D/state_latest ] || ln -s $C/state_latest $D/state_latest
  for u in 008 016 024 032 040 048; do mkdir -p $C/ckpt_u$u; [ -e $D/ckpt_u$u ] || ln -s $C/ckpt_u$u $D/ckpt_u$u; done
  for try in 1 2 3 4 5 6 7 8; do
    [ -f $D/RUN_DONE ] && break
    [ -f $D/ABORT.json ] && break
    RES=""
    if [ -s $D/state_latest/state.json ]; then
      MD=$($VENV/bin/python -c "import json;print(json.load(open('$D/state_latest/state.json'))['model_dir'])")
      RES="--resume-model $MD"
    fi
    echo "$(date -Is) lane $A s$SD gpu $G try $try resume='$RES'" >> $OUT/${A}_s${SD}.attempts
    bash $R/code/lane.sh $G $A $SD $RUN --updates 48 --lr 5e-6 --dtype float16 --vllm-gpu-memory-utilization 0.35 --logit-chunk 1024 --vllm-max-num-seqs 128 --save-at 16,32,48 --full-state-every 8 $RES >> $OUT/${A}_s${SD}.log 2>&1
    sleep 120
  done
  echo "$(date -Is) lane $A s$SD finished (RUN_DONE: $([ -f $D/RUN_DONE ] && echo yes || echo no), ABORT: $([ -f $D/ABORT.json ] && echo yes || echo no))" >> $OUT/${A}_s${SD}.attempts
}
[ -e $OUT/full_start_epoch ] || date +%s > $OUT/full_start_epoch
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader > $OUT/gpus_at_start.txt
lane 2 A 0 & sleep 30
lane 4 A 1 & sleep 30
lane 3 B 0 & sleep 30
lane 6 B 1 &
wait
echo FULL_RUN_DONE
