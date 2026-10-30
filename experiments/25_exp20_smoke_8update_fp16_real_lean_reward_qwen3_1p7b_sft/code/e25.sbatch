#!/bin/bash
#SBATCH -J e25_real_lean
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:H100_SXM5
#SBATCH -c 24
#SBATCH --mem=128G
#SBATCH -t 03:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/e25/logs/%x_%j.log
# TLDR: Experiment 25: Exp 24's 8-update fp16 smoke (vLLM and trainer fp16, fp32 master weights, loss scale 16384, arm A, seed 0) with the REAL frozen Lean strict reward.
set -uo pipefail
E20=$SCRATCH/rl4cv_sherlock/e20; E25=$E20/e25; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$SCRATCH/rl4cv_sherlock/grading
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif; VENV=$E20/venv_trl
MODEL=$E25/ckpt_fp16
RUNS=$E25/runs
mkdir -p $RUNS $E25/logs $B/cache
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN|OAUTH_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
ENV="PYTHONPATH=$E25/code:$E20/code:$G/rl4cv/src,VERIBENCH_ROOT=$B/rl4cv_gen/external/veribench,RL4CV_SRC=$G/rl4cv/src,E20_ROOT=$E20,E20_GRADING=$G,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=8,VLLM_WORKER_MULTIPROC_METHOD=spawn,VLLM_USE_FLASHINFER_SAMPLER=0,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,HF_HOME=$B/cache/hf,LD_LIBRARY_PATH=$CL,PATH=$VENV/bin:$G/bin:/usr/local/bin:/usr/bin:/bin"
EXTRA=""
RUN=$RUNS/A_s0
if [ -f $RUN/state_latest/state.json ]; then
  RES=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['model_dir'])" $RUN/state_latest/state.json)
  echo "resuming from $RES"; EXTRA="$EXTRA --resume-model $RES"
fi
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env $ENV $SIF python $E25/code/train_e25.py --arm A --seed 0 --run-root $RUNS \
  --model $MODEL --pack $E20/phase0/train_pack --train-ids $E20/phase0/ids/train_ids_sorted.txt --updates 8 --save-at 8 --full-state-every 4 \
  --smoke --dtype float16 --loss-scale 16384 $EXTRA
rc=$?
echo "train rc=$rc wall=$(( $(date +%s)-T0 ))s host=$(hostname -s)"
tail -2 $RUN/log.jsonl 2>/dev/null | cut -c1-400
exit $rc
