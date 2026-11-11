#!/bin/bash
# AT-2925: Exp 25 third seed (seed 2) for arm A and arm B, same trainer flags as AT-1788 full_run4.sh; outputs on /dfs/scratch1 because /lfs is full; training lanes on GPUs 0 and 1, evaluation workers on GPUs 2 and 3 (GPUs 6 and 7 left alone). Resumable: rerun this script.
S=/lfs/skampere1/0/brando9; R=$S/rl4cv_e25; W=$S/rl4cv_e23_fp16_smoke; E8=$S/rl4cv_e08; OUT=/dfs/scratch1/brando9/at2925/full; CK=/dfs/scratch1/brando9/at2925_ckpt; EV=/dfs/scratch1/brando9/at2925/evals
export ROOT=$R VENV=$W/venv DATA=$S/at1787/data TRAINER=$R/code MODEL=$R/ckpt/step_658_float16
export PACK=$E8/pack_views/validation IDS=$E8/sft_v3/inputs/vbv1_validation_task_ids.txt VERIBENCH_ROOT=$S/rl4cv_e20/external/veribench
mkdir -p $OUT $EV/locks
# clear locks left by a killed job for evaluations that did not finish
for l in $EV/locks/*; do [ -e "$l" ] || continue; b=$(basename $l); [ -s $EV/$b/summary_eval_$b.json ] || rmdir $l; done
evalworker() {  # gpu
  G=$1; LOG=$EV/queue_gpu$G.log
  END=$(( $(date +%s) + 12*3600 ))
  while [ $(date +%s) -lt $END ]; do
    PEND=0; RAN=0
    for U in 016 032 048; do for L in A_s2 B_s2; do
      B=${L}_u$U; NS=8; [ $U = 048 ] && NS=32
      [ -s $EV/$B/summary_eval_$B.json ] && continue
      [ -d $EV/locks/$B ] && continue
      PEND=$((PEND+1))
      [ -f $CK/$L/ckpt_u$U/DONE ] || continue
      USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $G)
      if [ "$USED" -gt 2000 ]; then echo "$(date -Is) GPU $G busy ($USED MiB)" >> $LOG; continue; fi
      mkdir $EV/locks/$B 2>/dev/null || continue
      echo "$(date -Is) start eval $B ($NS samples) on GPU $G" >> $LOG
      bash $R/code/eval_local.sh $B $CK/$L/ckpt_u$U/model $EV/$B $G 0.85 $NS > $EV/$B.log 2>&1
      echo "$(date -Is) end eval $B rc=$?" >> $LOG
      RAN=1; break 2
    done; done
    [ $PEND -eq 0 ] && { echo "$(date -Is) nothing left, worker ends" >> $LOG; break; }
    [ $RAN -eq 0 ] && sleep 180
  done
}
lane() {  # gpu arm seed
  G=$1; A=$2; SD=$3; RUN=$OUT/${A}_s${SD}_lr5e-6; D=$RUN/${A}_s${SD}; C=$CK/${A}_s${SD}
  mkdir -p $D $C/state_latest
  [ -e $D/state_latest ] || ln -s $C/state_latest $D/state_latest
  for u in 008 016 024 032 040 048; do mkdir -p $C/ckpt_u$u; [ -e $D/ckpt_u$u ] || ln -s $C/ckpt_u$u $D/ckpt_u$u; done
  for try in 1 2 3 4 5 6 7 8 9 10 11 12; do
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
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader > $OUT/gpus_at_start5.txt
evalworker 2 &
sleep 20; evalworker 3 &
sleep 20
lane 0 A 2 & sleep 30
lane 1 B 2 &
wait
echo FULL_RUN_DONE
