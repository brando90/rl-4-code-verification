#!/bin/bash
#SBATCH -J e20_smoke_train
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 16
#SBATCH --mem=96G
#SBATCH -t 03:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%j.log
# TLDR: Experiment 20 trainer smoke test: build the TRL venv overlay inside the vLLM 0.30.0 image (once), then run 2 GRPO
# updates of arm A (seed 1) with the log-probability mismatch check (gate: <= 1% of completion tokens with |delta| > 0.05
# on the recomputed sampling support). Writes <run>/smoke_logprob_check.json and runtime_versions.json.
set -uo pipefail
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Slurm must assign the smoke GPU}"
E20=$SCRATCH/rl4cv_sherlock/e20; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$SCRATCH/rl4cv_sherlock/grading
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif
VENV=$E20/venv_trl; RUNS=$E20/smoke_train
MODEL=$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf
mkdir -p $RUNS $B/cache
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN|OAUTH_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
ENV="PYTHONPATH=$E20/code:$G/rl4cv/src,VERIBENCH_ROOT=$B/rl4cv_gen/external/veribench,RL4CV_SRC=$G/rl4cv/src,E20_ROOT=$E20,E20_GRADING=$G,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=8,VLLM_WORKER_MULTIPROC_METHOD=spawn,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,HF_HOME=$B/cache/hf,LD_LIBRARY_PATH=$CL,PATH=$VENV/bin:$G/bin:/usr/local/bin:/usr/bin:/bin"
# 1. venv overlay with TRL (system site packages = the image's torch/vllm/transformers); pinned.
if [ ! -x $VENV/bin/python ]; then
  apptainer exec -B /scratch $SIF python3 -m venv --system-site-packages $VENV || exit $?
fi
if ! apptainer exec -B /scratch --env PATH=$VENV/bin:/usr/local/bin:/usr/bin:/bin $SIF python -c 'from importlib.metadata import version; assert version("trl") == "1.16.0" and version("scipy") == "1.18.1"'; then
  apptainer exec -B /scratch --env PATH=$VENV/bin:/usr/local/bin:/usr/bin:/bin $SIF python -m pip install --no-cache-dir "trl==1.16.0" "scipy==1.18.1" 2>&1 | tail -3 || exit $?
fi
apptainer exec --nv -B /scratch,/home/groups --env $ENV $SIF python - <<'PY' | tee $RUNS/runtime_versions.json
import json, torch, transformers, vllm, trl, accelerate, sys
print(json.dumps({"python": sys.version.split()[0], "torch": torch.__version__, "cuda": torch.version.cuda, "transformers": transformers.__version__,
                  "vllm": vllm.__version__, "trl": trl.__version__, "accelerate": accelerate.__version__, "gpu": torch.cuda.get_device_name(0)}, indent=1))
PY
# 2. two updates of arm A with the mismatch check.
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env $ENV $SIF python $E20/code/train_e20.py --arm A --seed 1 --run-root $RUNS \
  --model $MODEL --pack $E20/phase0/train_pack --train-ids $E20/phase0/ids/train_ids_sorted.txt --updates 2 --save-at 2 --full-state-every 2 --smoke
rc=$?
echo "smoke rc=$rc wall=$(( $(date +%s)-T0 ))s"; cat $RUNS/A_s1/smoke_logprob_check.json 2>/dev/null | head -40; tail -3 $RUNS/A_s1/log.jsonl 2>/dev/null | cut -c1-600
exit $rc
