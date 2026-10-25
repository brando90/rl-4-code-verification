#!/bin/bash
# usage: lane.sh <gpu> <dtype> <loss_scale> <port>   (arm A, seed 0, 2 updates, smoke mode, proxy reward)
W=/lfs/skampere1/0/brando9/rl4cv_e23_fp16_smoke; cd $W
G=$1; D=$2; LS=$3; PORT=$4
export CUDA_VISIBLE_DEVICES=$G MASTER_PORT=$PORT HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8 VLLM_WORKER_MULTIPROC_METHOD=spawn
export PYTHONPATH=$W/code:/lfs/skampere1/0/brando9/rl4cv_e20/src RL4CV_SRC=/lfs/skampere1/0/brando9/rl4cv_e20/src VERIBENCH_ROOT=/lfs/skampere1/0/brando9/rl4cv_e20/external/veribench
export XDG_CACHE_HOME=$W/cache VLLM_CACHE_ROOT=$W/cache/vllm TRITON_CACHE_DIR=$W/cache/triton VLLM_USE_FLASHINFER_SAMPLER=0
mkdir -p run/$D cache
T0=$(date +%s)
venv/bin/python code/train_e20.py --arm A --seed 0 --run-root run/$D --model ckpt/$D --pack ../rl4cv_e08/pack_train539 --train-ids ids_train.txt \
  --updates 2 --save-at 2 --full-state-every 2 --smoke --dtype $( [ $D = fp16 ] && echo float16 || echo bfloat16 ) --loss-scale $LS --reward-proxy
echo "rc=$? wall=$(( $(date +%s)-T0 ))s"
