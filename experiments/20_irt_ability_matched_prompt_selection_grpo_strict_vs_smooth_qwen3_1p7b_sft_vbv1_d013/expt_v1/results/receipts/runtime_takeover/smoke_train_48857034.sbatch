#!/bin/bash
#SBATCH -J e20_smoke_train
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 16
#SBATCH --mem=96G
#SBATCH -t 00:45:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%j.log
# TLDR: Experiment 20 training job for one arm x seed (export ARM, SEED, UPDATES, RUNS; optional PHASE0_CELLS, IRT_ITEMS):
# runs train_e20.py inside the vLLM 0.30.0 image with the TRL venv overlay, auto-resuming from <run>/state_latest when it
# exists (the pilot's 16-update runs continue as the first third of their main runs). One L40S or H100, 16 CPUs for the
# parallel Lean scorers.
set -uo pipefail
E20=$SCRATCH/rl4cv_sherlock/e20; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$SCRATCH/rl4cv_sherlock/grading
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif; VENV=$E20/venv_trl
MODEL=$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf
: "${ARM:?} ${SEED:?} ${UPDATES:=48} ${RUNS:=$E20/train/runs}"
mkdir -p $RUNS $E20/train/logs $B/cache
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN|OAUTH_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
ENV="PYTHONPATH=$E20/code:$G/rl4cv/src,VERIBENCH_ROOT=$B/rl4cv_gen/external/veribench,RL4CV_SRC=$G/rl4cv/src,E20_ROOT=$E20,E20_GRADING=$G,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=8,VLLM_WORKER_MULTIPROC_METHOD=spawn,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,HF_HOME=$B/cache/hf,LD_LIBRARY_PATH=$CL,PATH=$VENV/bin:$G/bin:/usr/local/bin:/usr/bin:/bin"
EXTRA=""
[ -n "${PHASE0_CELLS:-}" ] && EXTRA="$EXTRA --phase0-cells $PHASE0_CELLS"
[ -n "${IRT_ITEMS:-}" ] && EXTRA="$EXTRA --irt-items $IRT_ITEMS"
RUN=$RUNS/${ARM}_s${SEED}
if [ -f $RUN/state_latest/state.json ]; then
  RES=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['model_dir'])" $RUN/state_latest/state.json)
  echo "resuming from $RES"; EXTRA="$EXTRA --resume-model $RES"
fi
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env $ENV $SIF python $E20/code/train_e20.py --arm $ARM --seed $SEED --run-root $RUNS \
  --model $MODEL --pack $E20/phase0/train_pack --train-ids $E20/phase0/ids/train_ids_sorted.txt --updates $UPDATES --smoke $EXTRA
rc=$?
echo "train rc=$rc wall=$(( $(date +%s)-T0 ))s arm=$ARM seed=$SEED updates=$UPDATES host=$(hostname -s)"
tail -2 $RUN/log.jsonl 2>/dev/null | cut -c1-400
exit $rc
