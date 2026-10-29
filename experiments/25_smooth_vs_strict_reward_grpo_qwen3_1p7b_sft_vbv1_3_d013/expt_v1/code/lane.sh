#!/bin/bash
# TLDR: Launch one Exp 25 trainer run (arm A or B) on one GPU of a host that has the e25 tree (code/ + grading/), the trainer dir, the e08 pack and a venv with vLLM 0.30 + TRL 1.16. No Slurm, no Sherlock.
# usage: lane.sh <gpu> <arm A|B> <seed> <run_root> [train_e25.py args...]
# env: ROOT (e25 tree, default /lfs/<host>/0/brando9/rl4cv_e25), VENV (python venv, default $ROOT/venv_trl), MODEL (checkpoint dir), PORT
set -uo pipefail
GPU=$1; ARM=$2; SEED=$3; RUN=$4; shift 4
H=$(hostname -s); ROOT=${ROOT:-/lfs/$H/0/brando9/rl4cv_e25}; VENV=${VENV:-$ROOT/venv_trl}
D=${DATA:-$ROOT/data}; T=${TRAINER:-$ROOT/trainer}
MODEL=${MODEL:-/lfs/mercury1/0/brando9/rl4cv_e21_logprob_mismatch/ckpt/step_658}
export CUDA_VISIBLE_DEVICES=$GPU MASTER_PORT=${PORT:-$((29500+GPU))} HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8 VLLM_WORKER_MULTIPROC_METHOD=spawn
export PYTHONPATH=$T:$ROOT/grading/rl4cv/src RL4CV_SRC=$ROOT/grading/rl4cv/src
export VERIBENCH_ROOT=$D/rl4cv_e20/external/veribench E20_ROOT=$ROOT E20_GRADING=$ROOT/grading
export XDG_CACHE_HOME=$RUN/cache VLLM_CACHE_ROOT=$RUN/cache/vllm TRITON_CACHE_DIR=$RUN/cache/triton VLLM_USE_FLASHINFER_SAMPLER=0
mkdir -p "$RUN"
T0=$(date +%s)
$VENV/bin/python $T/train_e25.py --arm $ARM --seed $SEED --run-root "$RUN" --model "$MODEL" --pack $D/rl4cv_e08/pack_train539 \
  --train-ids $D/rl4cv_e23_fp16_smoke/ids_train.txt "$@"
echo "rc=$? wall=$(( $(date +%s)-T0 ))s"
